#!/usr/bin/env python3
"""
Enhanced Neo4j Knowledge Graph Builder for Daemonium Project

This enhanced version incorporates philosopher_summary data and additional improvements:
- Philosopher biographical nodes with temporal relationships
- Enhanced thematic connections between philosophers and ideas
- Work-based relationships and influence networks
- Geographic and temporal clustering
- Improved semantic relationship detection
- Better concept extraction and cross-referencing

Author: Daemonium System
Version: 2.0.0
"""

from pymongo import MongoClient
from py2neo import Graph, Node, Relationship
import re
from typing import Dict, List, Any, Tuple, Optional
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
import requests
import json
from sklearn.metrics.pairwise import cosine_similarity
import yaml
from pathlib import Path
from urllib.parse import quote_plus
from datetime import datetime
import os
import sys

# Add utils directory to path
sys.path.append(str(Path(__file__).parent.parent / 'utils'))
from neo4j_database_utils import get_neo4j_database_config, get_neo4j_connection_uri, get_neo4j_auth, print_database_info, create_database_if_not_exists


class EnhancedKnowledgeGraphBuilder:
    def __init__(self, config_path: str = None, 
                 ollama_url: str = "http://localhost:11434", 
                 ollama_model: str = "llama3.1:latest",
                 target_database: str = None):
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
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
            self.logger.warning(f"Could not create database (may already exist): {e}")
        
        # Neo4j connection to specific database
        self.graph = Graph(neo4j_uri, auth=neo4j_auth, name=self.target_database)
        
        self.logger.info(f"Connected to Neo4j database: {self.target_database}")
        
        # Clear existing graph (optional - remove if you want to preserve data)
        self.graph.delete_all()
        
        # AI Models
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        
        # Cache for embeddings and nodes
        self.embedding_cache = {}
        self.philosopher_nodes = {}
        self.concept_nodes = {}
        
        # Data paths
        script_dir = Path(__file__).parent
        self.project_root = script_dir.parent.parent
        self.json_docs_path = self.project_root / 'json_bot_docs'
        
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
        Extract the key philosophical concepts from this text. 
        Return only the concepts as a comma-separated list, no explanations.
        Focus on philosophical terms, ideas, and themes.
        
        Text: {text[:1000]}
        
        Concepts:"""
        
        response = self.query_ollama(prompt)
        if response:
            concepts = [concept.strip() for concept in response.split(',')]
            return [c for c in concepts if c and len(c.split()) <= 4]
        return []
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get sentence embedding with caching"""
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        
        embedding = self.sentence_model.encode([text])[0]
        self.embedding_cache[text] = embedding
        return embedding
    
    def find_similar_content(self, nodes: List[Dict], threshold: float = 0.7) -> List[Tuple[Dict, Dict, float]]:
        """Find similar content using sentence transformers"""
        similar_pairs = []
        
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                if node1['type'] != node2['type']:  # Only compare different types
                    text1 = node1.get('content', node1.get('title', ''))
                    text2 = node2.get('content', node2.get('title', ''))
                    
                    if text1 and text2:
                        emb1 = self.get_embedding(text1)
                        emb2 = self.get_embedding(text2)
                        similarity = cosine_similarity([emb1], [emb2])[0][0]
                        
                        if similarity > threshold:
                            similar_pairs.append((node1, node2, similarity))
        
        return similar_pairs
    
    def analyze_relationship_with_ollama(self, content1: str, content2: str) -> str:
        """Use Ollama to analyze the relationship between two pieces of content"""
        prompt = f"""
        Analyze the relationship between these two philosophical texts.
        Provide a single relationship type from this list: INFLUENCES, CONTRADICTS, SUPPORTS, DEVELOPS, CRITIQUES, EXEMPLIFIES, APPLIES.
        
        Text 1: {content1[:500]}
        
        Text 2: {content2[:500]}
        
        Relationship type:"""
        
        response = self.query_ollama(prompt)
        if response:
            # Extract the relationship type
            relationship_types = ['INFLUENCES', 'CONTRADICTS', 'SUPPORTS', 'DEVELOPS', 'CRITIQUES', 'EXEMPLIFIES', 'APPLIES']
            for rel_type in relationship_types:
                if rel_type.lower() in response.lower():
                    return rel_type
        
        return "RELATES_TO"  # Default relationship
    
    def load_json_files(self, directory: str) -> List[Dict[str, Any]]:
        """Load all JSON files from a directory, skipping templates"""
        json_files = []
        dir_path = self.json_docs_path / directory
        
        if not dir_path.exists():
            self.logger.warning(f"Directory not found: {dir_path}")
            return []
        
        for file_path in dir_path.glob('*.json'):
            if file_path.name.lower().startswith('template'):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['_source_file'] = file_path.name
                    json_files.append(data)
            except Exception as e:
                self.logger.error(f"Error loading {file_path}: {e}")
        
        return json_files
    
    def create_philosopher_nodes(self) -> List[Dict]:
        """Create nodes for philosophers with biographical information"""
        self.logger.info("Creating philosopher nodes...")
        philosopher_data = self.load_json_files('philosopher_summary')
        nodes = []
        
        for data in philosopher_data:
            # Create main philosopher node
            philosopher_node = Node(
                "Philosopher",
                name=data.get('author', 'Unknown'),
                title=data.get('title', ''),
                birth_year=data.get('birth_year'),
                death_year=data.get('death_year'),
                nationality=data.get('nationality', ''),
                description=data.get('description', ''),
                category=data.get('category', ''),
                source_file=data.get('_source_file', '')
            )
            self.graph.create(philosopher_node)
            self.philosopher_nodes[data.get('author', 'Unknown')] = philosopher_node
            
            nodes.append({
                'node': philosopher_node,
                'type': 'Philosopher',
                'content': data.get('description', ''),
                'title': data.get('author', 'Unknown'),
                'data': data
            })
            
            # Create nodes for philosophical themes/sections
            for section in data.get('sections', []):
                section_node = Node(
                    "PhilosophicalTheme",
                    title=section.get('title', ''),
                    content=section.get('content', ''),
                    philosopher=data.get('author', 'Unknown'),
                    source_file=data.get('_source_file', '')
                )
                self.graph.create(section_node)
                
                # Create relationship between philosopher and theme
                theme_rel = Relationship(philosopher_node, "DEVELOPED", section_node)
                self.graph.create(theme_rel)
                
                nodes.append({
                    'node': section_node,
                    'type': 'PhilosophicalTheme',
                    'content': section.get('content', ''),
                    'title': section.get('title', ''),
                    'philosopher': data.get('author', 'Unknown')
                })
                
                # Create nodes for subsections
                for subsection in section.get('subsections', []):
                    subsection_node = Node(
                        "PhilosophicalConcept",
                        title=subsection.get('title', ''),
                        content=subsection.get('content', ''),
                        philosopher=data.get('author', 'Unknown'),
                        parent_theme=section.get('title', ''),
                        source_file=data.get('_source_file', '')
                    )
                    self.graph.create(subsection_node)
                    
                    # Create relationships
                    concept_rel = Relationship(section_node, "CONTAINS", subsection_node)
                    self.graph.create(concept_rel)
                    
                    phil_concept_rel = Relationship(philosopher_node, "THEORIZED", subsection_node)
                    self.graph.create(phil_concept_rel)
                    
                    nodes.append({
                        'node': subsection_node,
                        'type': 'PhilosophicalConcept',
                        'content': subsection.get('content', ''),
                        'title': subsection.get('title', ''),
                        'philosopher': data.get('author', 'Unknown')
                    })
        
        self.logger.info(f"Created {len(nodes)} philosopher-related nodes")
        return nodes
    
    def create_book_summary_nodes(self) -> List[Dict]:
        """Create nodes for book summaries with enhanced connections"""
        self.logger.info("Creating book summary nodes...")
        book_data = self.load_json_files('book_summary')
        nodes = []
        
        for data in book_data:
            # Create main book summary node
            book_node = Node(
                "BookSummary",
                title=data.get('title', ''),
                author=data.get('author', ''),
                category=data.get('category', ''),
                description=data.get('description', ''),
                source_file=data.get('_source_file', '')
            )
            self.graph.create(book_node)
            
            # Connect to philosopher if exists
            author = data.get('author', '')
            if author in self.philosopher_nodes:
                wrote_rel = Relationship(self.philosopher_nodes[author], "WROTE", book_node)
                self.graph.create(wrote_rel)
            
            nodes.append({
                'node': book_node,
                'type': 'BookSummary',
                'content': data.get('description', ''),
                'title': data.get('title', ''),
                'author': author
            })
            
            # Create nodes for sections
            for section in data.get('sections', []):
                section_node = Node(
                    "BookSection",
                    title=section.get('title', ''),
                    content=section.get('content', ''),
                    book_title=data.get('title', ''),
                    author=data.get('author', ''),
                    source_file=data.get('_source_file', '')
                )
                self.graph.create(section_node)
                
                # Create relationship
                contains_rel = Relationship(book_node, "CONTAINS", section_node)
                self.graph.create(contains_rel)
                
                nodes.append({
                    'node': section_node,
                    'type': 'BookSection',
                    'content': section.get('content', ''),
                    'title': section.get('title', ''),
                    'author': data.get('author', '')
                })
        
        self.logger.info(f"Created {len(nodes)} book summary nodes")
        return nodes
    
    def create_top_ideas_nodes(self) -> List[Dict]:
        """Create nodes for top 10 ideas with enhanced connections"""
        self.logger.info("Creating top ideas nodes...")
        ideas_data = self.load_json_files('top_10_ideas')
        nodes = []
        
        for data in ideas_data:
            author = data.get('author', '')
            
            # Create main ideas collection node
            ideas_node = Node(
                "TopIdeas",
                title=data.get('title', ''),
                author=author,
                category=data.get('category', ''),
                description=data.get('description', ''),
                source_file=data.get('_source_file', '')
            )
            self.graph.create(ideas_node)
            
            # Connect to philosopher if exists
            if author in self.philosopher_nodes:
                developed_rel = Relationship(self.philosopher_nodes[author], "DEVELOPED_IDEAS", ideas_node)
                self.graph.create(developed_rel)
            
            nodes.append({
                'node': ideas_node,
                'type': 'TopIdeas',
                'content': data.get('description', ''),
                'title': data.get('title', ''),
                'author': author
            })
            
            # Create nodes for individual ideas
            for idea in data.get('ideas', []):
                idea_node = Node(
                    "PhilosophicalIdea",
                    title=idea.get('title', ''),
                    content=idea.get('content', ''),
                    explanation=idea.get('explanation', ''),
                    author=author,
                    source_file=data.get('_source_file', '')
                )
                self.graph.create(idea_node)
                
                # Create relationships
                contains_rel = Relationship(ideas_node, "CONTAINS", idea_node)
                self.graph.create(contains_rel)
                
                if author in self.philosopher_nodes:
                    conceived_rel = Relationship(self.philosopher_nodes[author], "CONCEIVED", idea_node)
                    self.graph.create(conceived_rel)
                
                nodes.append({
                    'node': idea_node,
                    'type': 'PhilosophicalIdea',
                    'content': idea.get('content', '') + ' ' + idea.get('explanation', ''),
                    'title': idea.get('title', ''),
                    'author': author
                })
        
        self.logger.info(f"Created {len(nodes)} top ideas nodes")
        return nodes
    
    def create_aphorism_nodes(self) -> List[Dict]:
        """Create nodes for aphorisms with enhanced connections"""
        self.logger.info("Creating aphorism nodes...")
        aphorism_data = self.load_json_files('aphorisms')
        nodes = []
        
        for data in aphorism_data:
            author = data.get('author', '')
            
            # Create main aphorisms collection node
            collection_node = Node(
                "AphorismCollection",
                title=f"{author} - Aphorisms",
                author=author,
                category=data.get('category', ''),
                source_file=data.get('_source_file', '')
            )
            self.graph.create(collection_node)
            
            # Connect to philosopher if exists
            if author in self.philosopher_nodes:
                wrote_rel = Relationship(self.philosopher_nodes[author], "WROTE_APHORISMS", collection_node)
                self.graph.create(wrote_rel)
            
            nodes.append({
                'node': collection_node,
                'type': 'AphorismCollection',
                'content': f"Collection of aphorisms by {author}",
                'title': f"{author} - Aphorisms",
                'author': author
            })
            
            # Handle the actual aphorisms data structure (categories with string arrays)
            aphorisms_dict = data.get('aphorisms', {})
            if isinstance(aphorisms_dict, dict):
                for category, aphorism_list in aphorisms_dict.items():
                    # Create category node
                    category_node = Node(
                        "AphorismCategory",
                        title=category.replace('_', ' ').title(),
                        category=category,
                        author=author,
                        source_file=data.get('_source_file', '')
                    )
                    self.graph.create(category_node)
                    
                    # Connect category to collection
                    cat_rel = Relationship(collection_node, "HAS_CATEGORY", category_node)
                    self.graph.create(cat_rel)
                    
                    nodes.append({
                        'node': category_node,
                        'type': 'AphorismCategory',
                        'content': f"Category: {category.replace('_', ' ').title()}",
                        'title': category.replace('_', ' ').title(),
                        'author': author
                    })
                    
                    # Create individual aphorism nodes
                    if isinstance(aphorism_list, list):
                        for i, aphorism_text in enumerate(aphorism_list):
                            if isinstance(aphorism_text, str):
                                aphorism_node = Node(
                                    "Aphorism",
                                    content=aphorism_text,
                                    category=category,
                                    author=author,
                                    index=i + 1,
                                    source_file=data.get('_source_file', '')
                                )
                                self.graph.create(aphorism_node)
                                
                                # Create relationships
                                contains_rel = Relationship(category_node, "CONTAINS", aphorism_node)
                                self.graph.create(contains_rel)
                                
                                if author in self.philosopher_nodes:
                                    wrote_rel = Relationship(self.philosopher_nodes[author], "WROTE", aphorism_node)
                                    self.graph.create(wrote_rel)
                                
                                nodes.append({
                                    'node': aphorism_node,
                                    'type': 'Aphorism',
                                    'content': aphorism_text,
                                    'title': f"{category.replace('_', ' ').title()} #{i + 1}",
                                    'author': author
                                })
        
        self.logger.info(f"Created {len(nodes)} aphorism nodes")
        return nodes
    
    def create_idea_summary_nodes(self) -> List[Dict]:
        """Create nodes for individual idea summaries"""
        self.logger.info("Creating idea summary nodes...")
        idea_data = self.load_json_files('idea_summary')
        nodes = []
        
        for data in idea_data:
            author = data.get('author', '')
            
            idea_node = Node(
                "IdeaSummary",
                title=data.get('title', ''),
                author=author,
                category=data.get('category', ''),
                description=data.get('description', ''),
                content=data.get('content', ''),
                source_file=data.get('_source_file', '')
            )
            self.graph.create(idea_node)
            
            # Connect to philosopher if exists
            if author in self.philosopher_nodes:
                explored_rel = Relationship(self.philosopher_nodes[author], "EXPLORED", idea_node)
                self.graph.create(explored_rel)
            
            nodes.append({
                'node': idea_node,
                'type': 'IdeaSummary',
                'content': data.get('content', '') + ' ' + data.get('description', ''),
                'title': data.get('title', ''),
                'author': author
            })
        
        self.logger.info(f"Created {len(nodes)} idea summary nodes")
        return nodes
    
    def create_temporal_relationships(self):
        """Create relationships based on temporal proximity of philosophers"""
        self.logger.info("Creating temporal relationships...")
        
        # Get all philosophers with birth years
        philosophers_with_years = []
        for name, node in self.philosopher_nodes.items():
            birth_year = node.get('birth_year')
            if birth_year is not None:
                philosophers_with_years.append((name, node, birth_year))
        
        # Sort by birth year
        philosophers_with_years.sort(key=lambda x: x[2])
        
        # Create CONTEMPORARY and PREDECESSOR relationships
        for i, (name1, node1, year1) in enumerate(philosophers_with_years):
            for name2, node2, year2 in philosophers_with_years[i+1:]:
                year_diff = abs(year2 - year1)
                
                if year_diff <= 50:  # Contemporary (within 50 years)
                    rel = Relationship(node1, "CONTEMPORARY", node2, year_difference=year_diff)
                    self.graph.create(rel)
                elif year_diff <= 200:  # Influenced by (within 200 years)
                    if year1 < year2:  # node1 came first
                        rel = Relationship(node1, "PRECEDED", node2, year_difference=year_diff)
                        self.graph.create(rel)
    
    def create_geographic_relationships(self):
        """Create relationships based on geographic proximity"""
        self.logger.info("Creating geographic relationships...")
        
        # Group philosophers by nationality
        nationality_groups = {}
        for name, node in self.philosopher_nodes.items():
            nationality = node.get('nationality', '')
            if nationality:
                if nationality not in nationality_groups:
                    nationality_groups[nationality] = []
                nationality_groups[nationality].append((name, node))
        
        # Create SAME_NATIONALITY relationships
        for nationality, philosophers in nationality_groups.items():
            for i, (name1, node1) in enumerate(philosophers):
                for name2, node2 in philosophers[i+1:]:
                    rel = Relationship(node1, "SAME_NATIONALITY", node2, nationality=nationality)
                    self.graph.create(rel)
    
    def create_enhanced_semantic_relationships(self, all_nodes: List[Dict]):
        """Create enhanced semantic relationships using AI analysis"""
        self.logger.info("Creating enhanced semantic relationships...")
        
        # Find similar content pairs
        similar_pairs = self.find_similar_content(all_nodes, threshold=0.6)
        
        for node1_data, node2_data, similarity in similar_pairs:
            node1 = node1_data['node']
            node2 = node2_data['node']
            
            # Use Ollama to determine relationship type
            content1 = node1_data.get('content', '')[:500]
            content2 = node2_data.get('content', '')[:500]
            
            relationship_type = self.analyze_relationship_with_ollama(content1, content2)
            
            # Create the relationship
            rel = Relationship(
                node1, relationship_type, node2,
                similarity_score=float(similarity),
                method='enhanced_semantic_analysis',
                ai_determined=True
            )
            self.graph.create(rel)
    
    def create_concept_extraction_relationships(self, all_nodes: List[Dict]):
        """Extract concepts and create concept-based relationships"""
        self.logger.info("Creating concept-based relationships...")
        
        # Extract concepts from all nodes
        node_concepts = {}
        for node_data in all_nodes:
            content = node_data.get('content', '')
            if content:
                concepts = self.extract_concepts_with_ollama(content)
                if concepts:
                    node_concepts[node_data['node']] = concepts
        
        # Create concept nodes and relationships
        for node, concepts in node_concepts.items():
            for concept in concepts:
                # Create or get concept node
                if concept not in self.concept_nodes:
                    concept_node = Node("Concept", name=concept)
                    self.graph.create(concept_node)
                    self.concept_nodes[concept] = concept_node
                
                # Create relationship between node and concept
                rel = Relationship(node, "INVOLVES_CONCEPT", self.concept_nodes[concept])
                self.graph.create(rel)
        
        # Create relationships between nodes sharing concepts
        concept_to_nodes = {}
        for node, concepts in node_concepts.items():
            for concept in concepts:
                if concept not in concept_to_nodes:
                    concept_to_nodes[concept] = []
                concept_to_nodes[concept].append(node)
        
        for concept, nodes in concept_to_nodes.items():
            for i, node1 in enumerate(nodes):
                for node2 in nodes[i+1:]:
                    rel = Relationship(
                        node1, "SHARES_CONCEPT", node2,
                        shared_concept=concept
                    )
                    self.graph.create(rel)
    
    def build_enhanced_knowledge_graph(self):
        """Main method to build the enhanced knowledge graph"""
        self.logger.info("Starting enhanced knowledge graph construction...")
        
        try:
            # Create nodes and collect them for analysis
            all_nodes = []
            
            # Create philosopher nodes first (needed for connections)
            all_nodes.extend(self.create_philosopher_nodes())
            
            # Create other content nodes
            all_nodes.extend(self.create_book_summary_nodes())
            all_nodes.extend(self.create_top_ideas_nodes())
            all_nodes.extend(self.create_aphorism_nodes())
            all_nodes.extend(self.create_idea_summary_nodes())
            
            # Create enhanced relationships
            self.create_temporal_relationships()
            self.create_geographic_relationships()
            self.create_enhanced_semantic_relationships(all_nodes)
            self.create_concept_extraction_relationships(all_nodes)
            
            self.logger.info("Enhanced knowledge graph construction completed!")
            
            # Print comprehensive stats
            stats_queries = [
                ("Node Types", "MATCH (n) RETURN labels(n)[0] as NodeType, count(n) as Count ORDER BY Count DESC"),
                ("Relationship Types", "MATCH ()-[r]->() RETURN type(r) as RelType, count(r) as Count ORDER BY Count DESC"),
                ("Philosophers", "MATCH (p:Philosopher) RETURN p.name as Name, p.nationality as Nationality, p.birth_year as BirthYear ORDER BY p.birth_year"),
                ("AI-Generated Relations", "MATCH ()-[r {ai_determined: true}]->() RETURN count(r) as AIRelations"),
                ("Concept Nodes", "MATCH (c:Concept) RETURN count(c) as ConceptCount"),
                ("Total Nodes", "MATCH (n) RETURN count(n) as TotalNodes"),
                ("Total Relationships", "MATCH ()-[r]->() RETURN count(r) as TotalRelationships")
            ]
            
            print("\nEnhanced Knowledge Graph Statistics:")
            for title, query in stats_queries:
                print(f"\n{title}:")
                results = list(self.graph.run(query))
                if not results:
                    print("  No results found")
                else:
                    for record in results:
                        if 'NodeType' in record:
                            print(f"  {record['NodeType']}: {record['Count']} nodes")
                        elif 'RelType' in record:
                            print(f"  {record['RelType']}: {record['Count']} relationships")
                        elif 'Name' in record:
                            birth_year = record['BirthYear'] if record['BirthYear'] else 'Unknown'
                            nationality = record['Nationality'] if record['Nationality'] else 'Unknown'
                            print(f"  {record['Name']} ({nationality}, {birth_year})")
                        elif 'AIRelations' in record:
                            print(f"  AI-generated relationships: {record['AIRelations']}")
                        elif 'ConceptCount' in record:
                            print(f"  Concept nodes: {record['ConceptCount']}")
                        elif 'TotalNodes' in record:
                            print(f"  Total nodes: {record['TotalNodes']}")
                        elif 'TotalRelationships' in record:
                            print(f"  Total relationships: {record['TotalRelationships']}")
                
        except Exception as e:
            self.logger.error(f"Error building enhanced knowledge graph: {e}")
            raise


# Usage example
if __name__ == "__main__":
    import sys
    
    # Configuration is loaded automatically from config/default.yaml
    OLLAMA_URL = "http://localhost:11434"
    OLLAMA_MODEL = "llama3.1:latest"
    
    # Check for database argument
    target_database = None
    if len(sys.argv) > 1:
        target_database = sys.argv[1]
        print(f"Building knowledge graph in database: {target_database}")
    else:
        print("Building knowledge graph in default database")
        print("Usage: python enhanced_neo4j_kg_build.py [database_name]")
        print("Available databases: daemonium_primary, daemonium_comparison, daemonium_experimental")
    
    try:
        builder = EnhancedKnowledgeGraphBuilder(
            ollama_url=OLLAMA_URL,
            ollama_model=OLLAMA_MODEL,
            target_database=target_database
        )
        builder.build_enhanced_knowledge_graph()
        print(f"\nEnhanced knowledge graph construction completed successfully in database: {builder.target_database}!")
    except Exception as e:
        print(f"Error building enhanced knowledge graph: {e}")
        raise
