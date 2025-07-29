from pymongo import MongoClient
from py2neo import Graph, Node, Relationship
import re
from typing import Dict, List, Any, Tuple
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
import requests
import json
from sklearn.metrics.pairwise import cosine_similarity
import yaml
from pathlib import Path
from urllib.parse import quote_plus

class KnowledgeGraphBuilder:
    def __init__(self, config_path: str = None, 
                 ollama_url: str = "http://localhost:11434", 
                 ollama_model: str = "llama3.1:latest"):
        # Load configuration from config/default.yaml
        if config_path is None:
            # Get the project root directory (go up two levels from script directory)
            script_dir = Path(__file__).parent
            project_root = script_dir.parent.parent
            config_path = project_root / 'config' / 'default.yaml'
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Build MongoDB connection string from config
        mongo_config = config['mongodb']
        mongo_user = quote_plus(mongo_config['username'])
        mongo_pass = quote_plus(mongo_config['password'])
        # Include authSource=admin for proper authentication
        mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_config['host']}:{mongo_config['port']}/{mongo_config['database']}?authSource=admin"
        
        # MongoDB connection
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[mongo_config['database']]
        
        # Build Neo4j connection from config
        neo4j_config = config['neo4j']
        neo4j_uri = f"bolt://{neo4j_config['host']}:{neo4j_config['bolt_port']}"
        
        # Neo4j connection
        self.graph = Graph(neo4j_uri, auth=(neo4j_config['username'], neo4j_config['password']))
        
        # Clear existing graph (optional - remove if you want to preserve data)
        self.graph.delete_all()
        
        # AI Models
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        
        # Cache for embeddings to avoid recomputation
        self.embedding_cache = {}
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def query_ollama(self, prompt: str) -> str:
        """Query Ollama local model"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                self.logger.warning(f"Ollama request failed: {response.status_code}")
                return ""
        except Exception as e:
            self.logger.error(f"Error querying Ollama: {e}")
            return ""
    
    def extract_concepts_with_ollama(self, text: str) -> List[str]:
        """Use Ollama to extract philosophical concepts from text"""
        prompt = f"""
        Extract the key philosophical concepts from this Nietzsche text. 
        Return only the concepts as a comma-separated list, no explanations.
        Focus on philosophical terms, ideas, and themes.
        
        Text: {text[:1000]}  # Limit text length for efficiency
        
        Concepts:"""
        
        response = self.query_ollama(prompt)
        if response:
            concepts = [concept.strip() for concept in response.split(',')]
            return [c for c in concepts if c and len(c.split()) <= 4]  # Filter reasonable concepts
        return []
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get sentence embedding with caching"""
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        
        embedding = self.sentence_model.encode([text])[0]
        self.embedding_cache[text] = embedding
        return embedding
    
    def find_similar_content(self, nodes: List[Dict], threshold: float = 0.7) -> List[Tuple]:
        """Find similar content using sentence transformers"""
        similarities = []
        
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes[i+1:], i+1):
                text1 = node1.get('content', node1.get('title', ''))
                text2 = node2.get('content', node2.get('title', ''))
                
                if text1 and text2:
                    emb1 = self.get_embedding(text1)
                    emb2 = self.get_embedding(text2)
                    
                    similarity = cosine_similarity([emb1], [emb2])[0][0]
                    
                    if similarity > threshold:
                        similarities.append((node1, node2, similarity))
        
        return similarities
    
    def analyze_relationship_with_ollama(self, content1: str, content2: str) -> Dict[str, str]:
        """Use Ollama to analyze the relationship between two pieces of content"""
        prompt = f"""
        Analyze the philosophical relationship between these two Nietzsche texts.
        Return your analysis in this exact format:
        RELATIONSHIP_TYPE: [contradiction/expansion/example/foundation/application]
        EXPLANATION: [brief explanation]
        
        Text 1: {content1[:500]}
        
        Text 2: {content2[:500]}
        """
        
        response = self.query_ollama(prompt)
        
        # Parse the response
        relationship_info = {"type": "RELATED", "explanation": ""}
        
        if response:
            lines = response.strip().split('\n')
            for line in lines:
                if line.startswith('RELATIONSHIP_TYPE:'):
                    rel_type = line.split(':', 1)[1].strip()
                    relationship_info["type"] = rel_type.upper()
                elif line.startswith('EXPLANATION:'):
                    relationship_info["explanation"] = line.split(':', 1)[1].strip()
        
        return relationship_info
    
    def create_book_summary_nodes(self):
        """Create nodes for book summaries"""
        self.logger.info("Creating book summary nodes...")
        
        summaries = self.db.book_summaries.find()
        book_nodes = []
        
        for summary in summaries:
            book_node = Node("Book", 
                           title=summary.get('title', ''),
                           summary=summary.get('content', ''),
                           author='Friedrich Nietzsche',
                           source_id=str(summary['_id']))
            
            self.graph.create(book_node)
            
            # Store for similarity analysis
            book_nodes.append({
                'node': book_node,
                'content': summary.get('content', ''),
                'title': summary.get('title', ''),
                'type': 'Book'
            })
            
            # Extract concepts using both methods
            content = summary.get('content', '')
            
            # Ollama-based concept extraction
            ollama_concepts = self.extract_concepts_with_ollama(content)
            
            # Create concept nodes and relationships
            for concept in ollama_concepts:
                concept_node = Node("Concept", name=concept, extracted_by="ollama")
                self.graph.merge(concept_node, "Concept", "name")
                
                discusses_rel = Relationship(book_node, "DISCUSSES", concept_node)
                self.graph.create(discusses_rel)
        
        return book_nodes
    
    def create_top_ideas_nodes(self):
        """Create nodes for top 10 ideas"""
        self.logger.info("Creating top ideas nodes...")
        
        top_ideas = self.db.top_ten_ideas.find()
        idea_nodes = []
        
        for ideas_doc in top_ideas:
            # Create a container node for the top 10 list
            top_ideas_node = Node("TopIdeasList", 
                                title=ideas_doc.get('title', 'Top 10 Nietzsche Ideas'),
                                source_id=str(ideas_doc['_id']))
            self.graph.create(top_ideas_node)
            
            # Create individual idea nodes
            ideas_list = ideas_doc.get('ideas', [])
            if isinstance(ideas_list, str):
                ideas_list = [idea.strip() for idea in ideas_list.split('\n') if idea.strip()]
            
            for i, idea in enumerate(ideas_list[:10]):
                idea_node = Node("TopIdea", 
                               content=idea,
                               rank=i+1,
                               source_id=f"{ideas_doc['_id']}_idea_{i}")
                self.graph.create(idea_node)
                
                # Store for similarity analysis
                idea_nodes.append({
                    'node': idea_node,
                    'content': idea,
                    'title': f"Top Idea {i+1}",
                    'type': 'TopIdea'
                })
                
                # Connect to the list
                contains_rel = Relationship(top_ideas_node, "CONTAINS", idea_node)
                self.graph.create(contains_rel)
                
                # Extract concepts using Ollama
                ollama_concepts = self.extract_concepts_with_ollama(idea)
                for concept in ollama_concepts:
                    concept_node = Node("Concept", name=concept, extracted_by="ollama")
                    self.graph.merge(concept_node, "Concept", "name")
                    
                    relates_rel = Relationship(idea_node, "RELATES_TO", concept_node)
                    self.graph.create(relates_rel)
        
        return idea_nodes
    
    def create_aphorism_nodes(self):
        """Create nodes for aphorisms"""
        self.logger.info("Creating aphorism nodes...")
        
        aphorisms = self.db.aphorisms.find()
        aphorism_nodes = []
        
        for aphorism in aphorisms:
            aphorism_node = Node("Aphorism",
                               content=aphorism.get('content', ''),
                               source=aphorism.get('source', ''),
                               number=aphorism.get('number', ''),
                               source_id=str(aphorism['_id']))
            self.graph.create(aphorism_node)
            
            # Store for similarity analysis
            aphorism_nodes.append({
                'node': aphorism_node,
                'content': aphorism.get('content', ''),
                'title': f"Aphorism {aphorism.get('number', '')}",
                'type': 'Aphorism'
            })
            
            # Link to books if source is mentioned
            source_book = aphorism.get('source', '')
            if source_book:
                book_nodes = self.graph.nodes.match("Book").where(f"_.title CONTAINS '{source_book}'")
                for book_node in book_nodes:
                    from_rel = Relationship(aphorism_node, "FROM_BOOK", book_node)
                    self.graph.create(from_rel)
            
            # Extract concepts using Ollama
            content = aphorism.get('content', '')
            ollama_concepts = self.extract_concepts_with_ollama(content)
            for concept in ollama_concepts:
                concept_node = Node("Concept", name=concept, extracted_by="ollama")
                self.graph.merge(concept_node, "Concept", "name")
                
                expresses_rel = Relationship(aphorism_node, "EXPRESSES", concept_node)
                self.graph.create(expresses_rel)
        
        return aphorism_nodes
    
    def create_idea_summary_nodes(self):
        """Create nodes for individual idea summaries"""
        nodes = []
        try:
            idea_summaries = self.db.idea_summary.find()
            for summary in idea_summaries:
                # Extract key information
                idea_id = summary.get('_id', str(summary.get('idea_id', 'unknown')))
                title = summary.get('title', 'Unknown Idea')
                content = summary.get('content', '')
                philosopher = summary.get('philosopher', 'Unknown')
                
                # Create node
                node = Node(
                    "IdeaSummary",
                    id=str(idea_id),
                    title=title,
                    content=content[:500],  # Limit content length
                    philosopher=philosopher,
                    source="idea_summaries"
                )
                self.graph.create(node)
                
                nodes.append({
                    'node': node,
                    'content': f"{title}: {content}",
                    'type': 'IdeaSummary'
                })
                
                self.logger.info(f"Created IdeaSummary node: {title}")
                
        except Exception as e:
            self.logger.error(f"Error creating idea summary nodes: {e}")
        
        return nodes
    
    def create_bibliography_nodes(self):
        """Create nodes for bibliography entries"""
        nodes = []
        try:
            bibliographies = self.db.bibliography.find()
            for bib in bibliographies:
                # Extract key information from the bibliography document
                bib_id = str(bib.get('_id', 'unknown'))
                
                # Get the main bibliography data (could be nested under various keys)
                bib_data = None
                for key, value in bib.items():
                    if key != '_id' and isinstance(value, dict) and 'author' in value:
                        bib_data = value
                        break
                
                if not bib_data:
                    self.logger.warning(f"No valid bibliography data found in document {bib_id}")
                    continue
                
                author = bib_data.get('author', 'Unknown Author')
                birth_death = bib_data.get('birth_death', '')
                description = bib_data.get('description', '')
                background = bib_data.get('background', '')
                works = bib_data.get('works', [])
                
                # Create main bibliography node
                bib_node = Node(
                    "Bibliography",
                    id=bib_id,
                    author=author,
                    birth_death=birth_death,
                    description=description[:500],  # Limit length
                    background=background[:500],  # Limit length
                    works_count=len(works),
                    source="bibliography"
                )
                self.graph.create(bib_node)
                
                nodes.append({
                    'node': bib_node,
                    'content': f"{author} ({birth_death}): {description} {background}",
                    'type': 'Bibliography'
                })
                
                self.logger.info(f"Created Bibliography node: {author}")
                
                # Create individual work nodes and connect them to the bibliography
                for work in works:
                    if isinstance(work, dict):
                        work_title = work.get('title', 'Unknown Work')
                        work_year = work.get('year', 'Unknown')
                        work_type = work.get('type', 'Unknown')
                        work_summary = work.get('summary', '')
                        original_title = work.get('original_title', '')
                        
                        # Create work node
                        work_node = Node(
                            "Work",
                            title=work_title,
                            original_title=original_title,
                            year=str(work_year),
                            type=work_type,
                            summary=work_summary[:500],  # Limit length
                            author=author,
                            source="bibliography"
                        )
                        self.graph.create(work_node)
                        
                        # Create relationship between bibliography and work
                        authored_rel = Relationship(bib_node, "AUTHORED", work_node)
                        self.graph.create(authored_rel)
                        
                        nodes.append({
                            'node': work_node,
                            'content': f"{work_title} ({work_year}): {work_summary}",
                            'type': 'Work'
                        })
                        
                        self.logger.info(f"Created Work node: {work_title} by {author}")
                
        except Exception as e:
            self.logger.error(f"Error creating bibliography nodes: {e}")
        
        return nodes
    
    def create_cross_references(self):
        """Create additional relationships between nodes based on shared concepts"""
        self.logger.info("Creating cross-references...")
        
        # Find concepts that appear in multiple contexts
        query = """
        MATCH (c:Concept)<-[r]-(n)
        WITH c, count(r) as connections, collect(n) as nodes
        WHERE connections > 1
        RETURN c, nodes
        """
        
        results = self.graph.run(query)
        
        for record in results:
            concept = record['c']
            nodes = record['nodes']
            
            # Create RELATED_VIA relationships between nodes sharing concepts
            for i, node1 in enumerate(nodes):
                for node2 in nodes[i+1:]:
                    if node1 != node2:
                        rel = Relationship(node1, "RELATED_VIA", node2, 
                                         shared_concept=concept['name'])
                        self.graph.create(rel)
    
    def create_semantic_relationships(self, all_nodes: List[Dict]):
        """Create relationships based on semantic similarity and Ollama analysis"""
        self.logger.info("Creating semantic relationships...")
        
        # Find similar content using sentence transformers
        similarities = self.find_similar_content(all_nodes, threshold=0.6)
        
        for node1_data, node2_data, similarity_score in similarities:
            node1 = node1_data['node']
            node2 = node2_data['node']
            
            # Get deeper relationship analysis from Ollama
            content1 = node1_data['content']
            content2 = node2_data['content']
            
            relationship_info = self.analyze_relationship_with_ollama(content1, content2)
            
            # Create relationship with semantic information
            rel = Relationship(
                node1, 
                relationship_info['type'], 
                node2,
                similarity_score=round(similarity_score, 3),
                explanation=relationship_info['explanation'][:200],  # Limit length
                method="semantic_analysis"
            )
            self.graph.create(rel)
            
            self.logger.info(f"Created {relationship_info['type']} relationship between "
                           f"{node1_data['type']} and {node2_data['type']} "
                           f"(similarity: {similarity_score:.3f})")
    
    def build_knowledge_graph(self):
        """Main method to build the complete knowledge graph with AI enhancement"""
        self.logger.info("Starting AI-enhanced knowledge graph construction...")
        
        try:
            # Create nodes and collect them for similarity analysis
            all_nodes = []
            
            all_nodes.extend(self.create_book_summary_nodes())
            all_nodes.extend(self.create_top_ideas_nodes())
            all_nodes.extend(self.create_aphorism_nodes())
            all_nodes.extend(self.create_idea_summary_nodes())
            all_nodes.extend(self.create_bibliography_nodes())
            
            # Create semantic relationships using AI
            self.create_semantic_relationships(all_nodes)
            
            # Create traditional cross-references (keeping the original method)
            self.create_cross_references()
            
            self.logger.info("AI-enhanced knowledge graph construction completed!")
            
            # Print enhanced stats
            stats_queries = [
                ("Node Types", "MATCH (n) RETURN labels(n)[0] as NodeType, count(n) as Count ORDER BY Count DESC"),
                ("Relationship Types", "MATCH ()-[r]->() RETURN type(r) as RelType, count(r) as Count ORDER BY Count DESC"),
                ("AI-Generated Relations", "MATCH ()-[r {method: 'semantic_analysis'}]->() RETURN count(r) as AIRelations")
            ]
            
            print("\nEnhanced Knowledge Graph Statistics:")
            for title, query in stats_queries:
                print(f"\n{title}:")
                results = list(self.graph.run(query))
                if not results:
                    if "AI-Generated" in title:
                        print("  AI-generated relationships: 0")
                    else:
                        print("  No results found")
                else:
                    for record in results:
                        if 'NodeType' in record:
                            print(f"  {record['NodeType']}: {record['Count']} nodes")
                        elif 'RelType' in record:
                            print(f"  {record['RelType']}: {record['Count']} relationships")
                        elif 'AIRelations' in record:
                            print(f"  AI-generated relationships: {record['AIRelations']}")
                
        except Exception as e:
            self.logger.error(f"Error building knowledge graph: {e}")
            raise

# Usage example
if __name__ == "__main__":
    # Configuration is loaded automatically from config/default.yaml
    # You can optionally specify Ollama settings
    OLLAMA_URL = "http://localhost:11434"  # Default Ollama URL
    OLLAMA_MODEL = "llama3.1:latest"  # or "mistral:latest", "llama3.2:latest", etc.
    
    try:
        builder = KnowledgeGraphBuilder(
            ollama_url=OLLAMA_URL,
            ollama_model=OLLAMA_MODEL
        )
        builder.build_knowledge_graph()
        print("\nKnowledge graph construction completed successfully!")
    except Exception as e:
        print(f"Error building knowledge graph: {e}")
        raise