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
import sys

# Add the utils directory to the path
sys.path.append(str(Path(__file__).parent.parent / 'utils'))
from neo4j_database_utils import (
    get_neo4j_database_config,
    get_neo4j_connection_uri,
    get_neo4j_auth,
    create_database_if_not_exists,
    print_database_info
)

class ImprovedKnowledgeGraphBuilder:
    def __init__(self, config_path: str = None, 
                 ollama_url: str = "http://localhost:11434", 
                 ollama_model: str = "deepseek-r1:latest",
                 embedding_model: str = "deepseek-r1:latest",
                 use_sentence_transformer: bool = False,
                 target_database: str = None):
        
        # Get script name for database selection
        script_name = Path(__file__).stem
        
        # Load configuration with smart database selection
        if config_path is None:
            script_dir = Path(__file__).parent
            project_root = script_dir.parent.parent
            config_path = project_root / 'config' / 'default.yaml'
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Get Neo4j configuration with database selection
        self.neo4j_config = get_neo4j_database_config(script_name, target_database, config_path)
        self.target_database = self.neo4j_config['selected_database']
        
        # Print database selection info
        print_database_info(self.neo4j_config)
        
        # Build MongoDB connection string from config
        mongo_config = config['mongodb']
        mongo_user = quote_plus(mongo_config['username'])
        mongo_pass = quote_plus(mongo_config['password'])
        mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_config['host']}:{mongo_config['port']}/{mongo_config['database']}?authSource=admin"
        
        # MongoDB connection
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[mongo_config['database']]
        
        # Neo4j connection using utility functions
        neo4j_uri = get_neo4j_connection_uri(self.neo4j_config)
        neo4j_auth = get_neo4j_auth(self.neo4j_config)
        
        # Create database if it doesn't exist
        try:
            create_database_if_not_exists(self.target_database, self.neo4j_config)
        except Exception as e:
            logging.warning(f"Could not create database (may already exist): {e}")
        
        # Neo4j connection to specific database
        self.graph = Graph(neo4j_uri, auth=neo4j_auth, name=self.target_database)
        
        logging.info(f"Connected to Neo4j database: {self.target_database}")
        
        # Clear existing graph (optional - remove if you want to preserve data)
        self.graph.delete_all()
        
        # AI Models
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.embedding_model = embedding_model
        self.use_sentence_transformer = use_sentence_transformer
        
        # Initialize embedding model based on preference
        if self.use_sentence_transformer:
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            logging.info("Using SentenceTransformer for embeddings: all-MiniLM-L6-v2")
        else:
            self.sentence_model = None
            logging.info(f"Using Ollama for embeddings: {self.embedding_model}")
        
        # Cache for embeddings to avoid recomputation
        self.embedding_cache = {}
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def query_ollama(self, prompt: str) -> str:
        """Query Ollama local model with optimized timeout"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=10  # Reduced timeout for faster failure
            )
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                self.logger.warning(f"Ollama request failed: {response.status_code}")
                return ""
        except requests.exceptions.Timeout:
            self.logger.warning("Ollama request timed out (10s)")
            return ""
        except Exception as e:
            self.logger.error(f"Error querying Ollama: {e}")
            return ""
    
    def get_ollama_embedding(self, text: str) -> np.ndarray:
        """Get embedding from Ollama model"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                },
                timeout=30
            )
            if response.status_code == 200:
                embedding = response.json().get('embedding', [])
                if embedding:
                    return np.array(embedding)
                else:
                    self.logger.warning("Empty embedding received from Ollama")
                    return np.zeros(4096)  # Default embedding size for llama3.1
            else:
                self.logger.warning(f"Ollama embedding request failed: {response.status_code}")
                return np.zeros(4096)
        except Exception as e:
            self.logger.error(f"Error getting Ollama embedding: {e}")
            return np.zeros(4096)
    
    def extract_concepts_with_ollama(self, text: str) -> List[str]:
        """Use Ollama to extract philosophical concepts from text"""
        prompt = f"""
        Extract the key philosophical concepts from this text. 
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
        
        if self.use_sentence_transformer:
            embedding = self.sentence_model.encode([text])[0]
        else:
            embedding = self.get_ollama_embedding(text)
        
        self.embedding_cache[text] = embedding
        return embedding
    
    def find_similar_content(self, nodes: List[Dict], threshold: float = 0.7) -> List[Tuple]:
        """Find similar content using optimized sentence transformers"""
        similarities = []
        
        # Limit the number of nodes to prevent O(n²) explosion
        max_nodes = 200  # Reasonable limit for similarity comparison
        if len(nodes) > max_nodes:
            self.logger.warning(f"Limiting similarity analysis to {max_nodes} nodes (from {len(nodes)})")
            nodes = nodes[:max_nodes]
        
        # Pre-compute embeddings for efficiency
        embeddings = {}
        for i, node in enumerate(nodes):
            content = node.get('content', '')
            if content:
                embeddings[i] = self.get_embedding(content[:200])  # Limit text length for speed
        
        # Compare embeddings
        for i, node1 in enumerate(nodes):
            if i not in embeddings:
                continue
                
            for j, node2 in enumerate(nodes[i+1:], i+1):
                if j not in embeddings:
                    continue
                    
                # Limit total comparisons to prevent performance issues
                if len(similarities) < 500:  # Limit total pairs
                    similarity = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
                    # Convert numpy.float32 to Python float for Neo4j compatibility
                    similarity = float(similarity)
                    
                    if similarity >= threshold:
                        similarities.append((node1, node2, similarity))
        
        return similarities
    
    def analyze_relationship_with_ollama(self, content1: str, content2: str) -> Dict[str, str]:
        """Use Ollama to analyze the relationship between two pieces of content"""
        prompt = f"""
        Analyze the relationship between these two philosophical texts and provide:
        1. A relationship type (one word like: INFLUENCES, CONTRADICTS, SUPPORTS, EXPLAINS, EXEMPLIFIES)
        2. A brief explanation (max 100 words)
        
        Text 1: {content1[:300]}
        Text 2: {content2[:300]}
        
        Format your response as:
        Type: [RELATIONSHIP_TYPE]
        Explanation: [Brief explanation]
        """
        
        response = self.query_ollama(prompt)
        
        # Parse response
        relationship_type = "RELATES_TO"  # Default
        explanation = "Semantically similar content"
        
        if response:
            lines = response.split('\n')
            for line in lines:
                if line.startswith('Type:'):
                    relationship_type = line.replace('Type:', '').strip().upper()
                elif line.startswith('Explanation:'):
                    explanation = line.replace('Explanation:', '').strip()
        
        return {
            'type': relationship_type,
            'explanation': explanation
        }
    
    def determine_relationship_fast(self, node1_data: Dict, node2_data: Dict) -> str:
        """Fast rule-based relationship determination without AI"""
        type1 = node1_data.get('type', '')
        type2 = node2_data.get('type', '')
        
        # Rule-based relationship mapping
        if type1 == 'Philosopher' and type2 in ['Book', 'Aphorism', 'Idea']:
            return 'CREATED'
        elif type2 == 'Philosopher' and type1 in ['Book', 'Aphorism', 'Idea']:
            return 'CREATED_BY'
        elif type1 == 'Book' and type2 == 'Idea':
            return 'CONTAINS'
        elif type1 == 'Idea' and type2 == 'Book':
            return 'CONTAINED_IN'
        elif type1 == 'PhilosophicalTheme' and type2 == 'PhilosophicalConcept':
            return 'ENCOMPASSES'
        elif type1 == 'PhilosophicalConcept' and type2 == 'PhilosophicalTheme':
            return 'PART_OF'
        elif type1 == type2:  # Same type
            return 'SIMILAR_TO'
        else:
            return 'RELATES_TO'
    
    def create_book_summary_nodes(self):
        """Create nodes for book summaries with correct JSON structure"""
        nodes = []
        try:
            self.logger.info("Creating book summary nodes...")
            book_summaries = self.db.book_summaries.find()
            
            for book in book_summaries:
                # Extract key information from actual JSON structure
                book_id = str(book.get('_id', 'unknown'))
                title = book.get('title', 'Unknown Book')
                author = book.get('author', 'Unknown Author')
                category = book.get('category', 'Book Summary')
                publication_year = book.get('publication_year', 'Unknown')
                summary_sections = book.get('summary', [])
                
                # Create main book summary node
                full_summary = ' '.join([section.get('content', '') for section in summary_sections if isinstance(section, dict)])
                book_node = Node(
                    "BookSummary",
                    id=book_id,
                    title=title,
                    author=author,
                    category=category,
                    publication_year=publication_year,
                    summary=full_summary[:500],  # Limit summary length
                    sections_count=len(summary_sections),
                    source="book_summaries"
                )
                self.graph.create(book_node)
                
                nodes.append({
                    'node': book_node,
                    'content': f"{title} by {author} ({publication_year}): {full_summary}",
                    'type': 'BookSummary'
                })
                
                self.logger.info(f"Created BookSummary node: {title} by {author}")
                
                # Create individual section nodes and connect them
                for section in summary_sections:
                    if isinstance(section, dict):
                        section_title = section.get('section', 'Unknown Section')
                        section_content = section.get('content', '')
                        
                        section_node = Node(
                            "BookSection",
                            title=section_title,
                            content=section_content[:300],  # Limit content
                            book_title=title,
                            author=author,
                            source="book_summaries"
                        )
                        self.graph.create(section_node)
                        
                        # Create relationship
                        contains_rel = Relationship(book_node, "CONTAINS_SECTION", section_node)
                        self.graph.create(contains_rel)
                        
                        nodes.append({
                            'node': section_node,
                            'content': f"{section_title}: {section_content}",
                            'type': 'BookSection'
                        })
                        
                        self.logger.info(f"Created BookSection node: {section_title}")
                        
                        # Extract concepts from section content
                        concepts = self.extract_concepts_with_ollama(section_content)
                        for concept in concepts:
                            concept_node = Node("Concept", name=concept, extracted_by="ollama")
                            self.graph.merge(concept_node, "Concept", "name")
                            
                            discusses_rel = Relationship(section_node, "DISCUSSES", concept_node)
                            self.graph.create(discusses_rel)
                
        except Exception as e:
            self.logger.error(f"Error creating book summary nodes: {e}")
        
        return nodes
    
    def create_top_ideas_nodes(self):
        """Create nodes for top 10 ideas with correct JSON structure"""
        nodes = []
        try:
            self.logger.info("Creating top ideas nodes...")
            top_ideas = self.db.top_10_ideas.find()
            
            for ideas_doc in top_ideas:
                # Extract key information from actual JSON structure
                doc_id = str(ideas_doc.get('_id', 'unknown'))
                author = ideas_doc.get('author', 'Unknown Author')
                category = ideas_doc.get('category', 'Top 10 Ideas')
                ideas_list = ideas_doc.get('top_ideas', [])
                
                # Create main ideas collection node
                main_node = Node(
                    "TopIdeasCollection",
                    id=doc_id,
                    author=author,
                    category=category,
                    ideas_count=len(ideas_list),
                    source="top_10_ideas"
                )
                self.graph.create(main_node)
                
                nodes.append({
                    'node': main_node,
                    'content': f"Top 10 Ideas by {author}",
                    'type': 'TopIdeasCollection'
                })
                
                self.logger.info(f"Created TopIdeasCollection node for: {author}")
                
                # Create individual idea nodes
                for idea in ideas_list:
                    if isinstance(idea, dict):
                        idea_name = idea.get('idea', 'Unknown Idea')
                        idea_description = idea.get('description', '')
                        key_books = idea.get('key_books', [])
                        
                        idea_node = Node(
                            "PhilosophicalIdea",
                            name=idea_name,
                            description=idea_description[:400],  # Limit description
                            author=author,
                            key_books=key_books,
                            books_count=len(key_books),
                            source="top_10_ideas"
                        )
                        self.graph.create(idea_node)
                        
                        # Create relationship
                        contains_rel = Relationship(main_node, "CONTAINS_IDEA", idea_node)
                        self.graph.create(contains_rel)
                        
                        nodes.append({
                            'node': idea_node,
                            'content': f"{idea_name}: {idea_description}",
                            'type': 'PhilosophicalIdea'
                        })
                        
                        self.logger.info(f"Created PhilosophicalIdea node: {idea_name}")
                        
                        # Extract concepts from idea description
                        concepts = self.extract_concepts_with_ollama(idea_description)
                        for concept in concepts:
                            concept_node = Node("Concept", name=concept, extracted_by="ollama")
                            self.graph.merge(concept_node, "Concept", "name")
                            
                            explains_rel = Relationship(idea_node, "EXPLAINS", concept_node)
                            self.graph.create(explains_rel)
                
        except Exception as e:
            self.logger.error(f"Error creating top ideas nodes: {e}")
        
        return nodes
    
    def create_aphorism_nodes(self):
        """Create nodes for aphorisms with correct JSON structure"""
        nodes = []
        try:
            self.logger.info("Creating aphorism nodes...")
            aphorisms = self.db.aphorisms.find()
            
            for aphorism_doc in aphorisms:
                # Extract key information from actual JSON structure
                doc_id = str(aphorism_doc.get('_id', 'unknown'))
                author = aphorism_doc.get('author', 'Unknown Author')
                category = aphorism_doc.get('category', 'Aphorisms')
                aphorisms_data = aphorism_doc.get('aphorisms', {})
                
                # Create main aphorisms collection node
                main_node = Node(
                    "AphorismsCollection",
                    id=doc_id,
                    author=author,
                    category=category,
                    themes_count=len(aphorisms_data.keys()) if isinstance(aphorisms_data, dict) else 0,
                    source="aphorisms"
                )
                self.graph.create(main_node)
                
                nodes.append({
                    'node': main_node,
                    'content': f"Aphorisms by {author}",
                    'type': 'AphorismsCollection'
                })
                
                self.logger.info(f"Created AphorismsCollection node for: {author}")
                
                # Create individual aphorism nodes for each theme
                if isinstance(aphorisms_data, dict):
                    for theme, aphorisms_list in aphorisms_data.items():
                        if isinstance(aphorisms_list, list):
                            for aphorism_text in aphorisms_list:
                                if isinstance(aphorism_text, str) and aphorism_text.strip():
                                    aphorism_node = Node(
                                        "Aphorism",
                                        text=aphorism_text,
                                        theme=theme.replace('_', ' ').title(),
                                        author=author,
                                        source="aphorisms"
                                    )
                                    self.graph.create(aphorism_node)
                                    
                                    # Create relationship
                                    contains_rel = Relationship(main_node, "CONTAINS_APHORISM", aphorism_node)
                                    self.graph.create(contains_rel)
                                    
                                    nodes.append({
                                        'node': aphorism_node,
                                        'content': aphorism_text,
                                        'type': 'Aphorism'
                                    })
                                    
                                    self.logger.info(f"Created Aphorism node: {aphorism_text[:50]}...")
                                    
                                    # Extract concepts from aphorism
                                    concepts = self.extract_concepts_with_ollama(aphorism_text)
                                    for concept in concepts:
                                        concept_node = Node("Concept", name=concept, extracted_by="ollama")
                                        self.graph.merge(concept_node, "Concept", "name")
                                        
                                        expresses_rel = Relationship(aphorism_node, "EXPRESSES", concept_node)
                                        self.graph.create(expresses_rel)
                
        except Exception as e:
            self.logger.error(f"Error creating aphorism nodes: {e}")
        
        return nodes
    
    def create_idea_summary_nodes(self):
        """Create nodes for individual idea summaries"""
        nodes = []
        try:
            self.logger.info("Creating idea summary nodes...")
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
                    source="idea_summary"
                )
                self.graph.create(node)
                
                nodes.append({
                    'node': node,
                    'content': f"{title}: {content}",
                    'type': 'IdeaSummary'
                })
                
                self.logger.info(f"Created IdeaSummary node: {title}")
                
                # Extract concepts from idea summary
                concepts = self.extract_concepts_with_ollama(content)
                for concept in concepts:
                    concept_node = Node("Concept", name=concept, extracted_by="ollama")
                    self.graph.merge(concept_node, "Concept", "name")
                    
                    summarizes_rel = Relationship(node, "SUMMARIZES", concept_node)
                    self.graph.create(summarizes_rel)
                
        except Exception as e:
            self.logger.error(f"Error creating idea summary nodes: {e}")
        
        return nodes
    
    def create_bibliography_nodes(self):
        """Create nodes for bibliography entries with correct JSON structure"""
        nodes = []
        try:
            self.logger.info("Creating bibliography nodes...")
            bibliographies = self.db.bibliography.find()
            
            for bib in bibliographies:
                # Extract key information from the bibliography document
                bib_id = str(bib.get('_id', 'unknown'))
                
                # Check if data is directly at root level (new format)
                if 'author' in bib and isinstance(bib.get('works'), list):
                    bib_data = bib
                else:
                    # Fallback: look for nested data (old format)
                    bib_data = None
                    for key, value in bib.items():
                        if key != '_id' and isinstance(value, dict) and 'author' in value:
                            bib_data = value
                            break
                
                if not bib_data or 'author' not in bib_data:
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
                        
                        # Extract concepts from work summary
                        concepts = self.extract_concepts_with_ollama(work_summary)
                        for concept in concepts:
                            concept_node = Node("Concept", name=concept, extracted_by="ollama")
                            self.graph.merge(concept_node, "Concept", "name")
                            
                            explores_rel = Relationship(work_node, "EXPLORES", concept_node)
                            self.graph.create(explores_rel)
                
        except Exception as e:
            self.logger.error(f"Error creating bibliography nodes: {e}")
        
        return nodes
    
    def create_semantic_relationships(self, all_nodes: List[Dict]):
        """Create relationships based on optimized semantic similarity and AI analysis"""
        self.logger.info("Creating semantic relationships...")
        
        # Find similar content using sentence transformers with higher threshold
        similarities = self.find_similar_content(all_nodes, threshold=0.75)
        
        self.logger.info(f"Found {len(similarities)} similar content pairs to analyze")
        
        # Limit the number of pairs to process (prevent infinite runtime)
        max_pairs = 100  # Reasonable limit for AI analysis
        if len(similarities) > max_pairs:
            self.logger.warning(f"Limiting analysis to top {max_pairs} most similar pairs")
            similarities = sorted(similarities, key=lambda x: x[2], reverse=True)[:max_pairs]
        
        # Process in batches to avoid overwhelming Ollama
        batch_size = 10
        relationships_created = 0
        
        for i in range(0, len(similarities), batch_size):
            batch = similarities[i:i + batch_size]
            self.logger.info(f"Processing batch {i//batch_size + 1}/{(len(similarities) + batch_size - 1)//batch_size}")
            
            for node1_data, node2_data, similarity_score in batch:
                try:
                    node1 = node1_data['node']
                    node2 = node2_data['node']
                    
                    # Use rule-based relationship determination for speed
                    relationship_type = self.determine_relationship_fast(node1_data, node2_data)
                    explanation = "Rule-based semantic relationship"
                    
                    # Only use Ollama for high-similarity pairs that need detailed analysis
                    is_high_similarity = float(similarity_score) > 0.85
                    use_ai = is_high_similarity and relationships_created < 20
                    
                    if use_ai:  # Limit expensive AI calls
                        content1 = node1_data.get('content', '')[:300]  # Reduced content length
                        content2 = node2_data.get('content', '')[:300]
                        
                        if content1 and content2:
                            relationship_info = self.analyze_relationship_with_ollama(content1, content2)
                            if relationship_info['type'] != "RELATES_TO":  # Only use if AI found specific relationship
                                relationship_type = relationship_info['type']
                                explanation = relationship_info['explanation'][:200]
                    
                    # Create relationship with semantic information
                    rel = Relationship(
                        node1, 
                        relationship_type, 
                        node2,
                        similarity_score=float(round(similarity_score, 3)),  # Ensure Python float
                        explanation=explanation,
                        method="semantic_analysis",
                        ai_determined=use_ai
                    )
                    self.graph.create(rel)
                    relationships_created += 1
                    
                    self.logger.info(f"Created {relationship_type} relationship between "
                                   f"{node1_data.get('type', 'Unknown')} and {node2_data.get('type', 'Unknown')} "
                                   f"(similarity: {similarity_score:.3f})")
                    
                except Exception as e:
                    self.logger.error(f"Error creating relationship: {e}")
                    continue
            
            # Small delay between batches to prevent overwhelming the system
            import time
            time.sleep(1)
        
        self.logger.info(f"Created {relationships_created} semantic relationships")
    
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
    
    def build_knowledge_graph(self):
        """Main method to build the complete knowledge graph with AI enhancement"""
        self.logger.info("Starting improved knowledge graph construction...")
        
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
            
            self.logger.info("Improved knowledge graph construction completed!")
            
            # Force commit any pending transactions
            try:
                self.graph.commit()
            except:
                pass  # May not have an active transaction
            
            # Add a small delay to ensure data is fully committed
            import time
            time.sleep(1)
            
            # Print enhanced stats
            stats_queries = [
                ("Node Types", "MATCH (n) RETURN labels(n)[0] as NodeType, count(n) as Count ORDER BY Count DESC"),
                ("Relationship Types", "MATCH ()-[r]->() RETURN type(r) as RelType, count(r) as Count ORDER BY Count DESC"),
                ("AI-Generated Relations", "MATCH ()-[r {method: 'semantic_analysis'}]->() RETURN count(r) as AIRelations"),
                ("Total Nodes", "MATCH (n) RETURN count(n) as TotalNodes"),
                ("Total Relationships", "MATCH ()-[r]->() RETURN count(r) as TotalRelationships")
            ]
                
            print("\nImproved Knowledge Graph Statistics:")
            for title, query in stats_queries:
                print(f"\n{title}:")
                try:
                    results = list(self.graph.run(query))
                    
                    if len(results) == 0:
                        print("  No results found")
                    elif title in ["Total Nodes", "Total Relationships", "AI-Generated Relations"]:
                        # Single value queries
                        record = results[0]
                        
                        if 'AIRelations' in record:
                            count = record['AIRelations'] or 0
                            print(f"  AI-generated relationships: {count}")
                        elif 'TotalNodes' in record:
                            count = record['TotalNodes'] or 0
                            print(f"  Total nodes: {count}")
                        elif 'TotalRelationships' in record:
                            count = record['TotalRelationships'] or 0
                            print(f"  Total relationships: {count}")
                    else:
                        # Multi-row queries (Node Types, Relationship Types)
                        if len(results) == 0:
                            print("  No data found")
                        else:
                            for record in results:
                                if 'NodeType' in record and record['NodeType']:
                                    count = record['Count'] or 0
                                    print(f"  {record['NodeType']}: {count} nodes")
                                elif 'RelType' in record and record['RelType']:
                                    count = record['Count'] or 0
                                    print(f"  {record['RelType']}: {count} relationships")
                except Exception as e:
                    print(f"  Error executing query: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error building knowledge graph: {e}")
            raise

# Usage example
if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Build improved Neo4j knowledge graph with multi-database support')
    parser.add_argument('--database', '-d', type=str, help='Target Neo4j database name')
    parser.add_argument('--ollama-url', type=str, default="http://localhost:11434", help='Ollama server URL')
    parser.add_argument('--ollama-model', type=str, default="llama3.1:latest", help='Ollama model to use for semantic analysis')
    parser.add_argument('--embedding-model', type=str, default="llama3.1:latest", help='Model to use for embeddings (Ollama model name)')
    parser.add_argument('--use-sentence-transformer', action='store_true', help='Use SentenceTransformer instead of Ollama for embeddings')
    args = parser.parse_args()
    
    # Configuration is loaded automatically from config/default.yaml
    # You can optionally specify Ollama settings and target database
    OLLAMA_URL = args.ollama_url
    OLLAMA_MODEL = args.ollama_model
    EMBEDDING_MODEL = args.embedding_model
    USE_SENTENCE_TRANSFORMER = args.use_sentence_transformer
    TARGET_DATABASE = args.database
    
    try:
        builder = ImprovedKnowledgeGraphBuilder(
            ollama_url=OLLAMA_URL,
            ollama_model=OLLAMA_MODEL,
            embedding_model=EMBEDDING_MODEL,
            use_sentence_transformer=USE_SENTENCE_TRANSFORMER,
            target_database=TARGET_DATABASE
        )
        builder.build_knowledge_graph()
        print("\nImproved knowledge graph construction completed successfully!")
    except Exception as e:
        print(f"Error building knowledge graph: {e}")
        raise
