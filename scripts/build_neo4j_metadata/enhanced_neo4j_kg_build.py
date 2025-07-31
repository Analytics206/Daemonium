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
                 embedding_model: str = "llama3.1:latest",
                 use_sentence_transformer: bool = False,
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
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.embedding_model = embedding_model
        self.use_sentence_transformer = use_sentence_transformer
        
        # Initialize embedding model based on preference
        if self.use_sentence_transformer:
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.logger.info("Using SentenceTransformer for embeddings: all-MiniLM-L6-v2")
        else:
            self.sentence_model = None
            self.logger.info(f"Using Ollama for embeddings: {self.embedding_model}")
        
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
        
        if self.use_sentence_transformer:
            embedding = self.sentence_model.encode([text])[0]
        else:
            embedding = self.get_ollama_embedding(text)
        
        self.embedding_cache[text] = embedding
        return embedding
    
    def find_similar_content(self, nodes: List[Dict], threshold: float = 0.7) -> List[Tuple[Dict, Dict, float]]:
        """Find similar content using optimized sentence transformers"""
        similar_pairs = []
        
        # Limit the number of nodes to prevent O(n²) explosion
        max_nodes = 200  # Reasonable limit for similarity comparison
        if len(nodes) > max_nodes:
            self.logger.warning(f"Limiting similarity analysis to {max_nodes} nodes (from {len(nodes)})")
            nodes = nodes[:max_nodes]
        
        # Pre-compute embeddings for efficiency
        embeddings = {}
        for i, node in enumerate(nodes):
            text = node.get('content', node.get('title', ''))
            if text:
                embeddings[i] = self.get_embedding(text[:200])  # Limit text length for speed
        
        # Compare embeddings
        for i, node1 in enumerate(nodes):
            if i not in embeddings:
                continue
                
            for j, node2 in enumerate(nodes[i+1:], i+1):
                if j not in embeddings:
                    continue
                    
                # Only compare different types and limit comparisons
                if node1['type'] != node2['type'] and len(similar_pairs) < 500:  # Limit total pairs
                    similarity = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
                    
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
        """Create enhanced semantic relationships using optimized AI analysis"""
        self.logger.info("Creating enhanced semantic relationships...")
        
        # Find similar content pairs with higher threshold to reduce volume
        similar_pairs = self.find_similar_content(all_nodes, threshold=0.75)
        
        self.logger.info(f"Found {len(similar_pairs)} similar content pairs to analyze")
        
        # Limit the number of pairs to process (prevent infinite runtime)
        max_pairs = 100  # Reasonable limit for AI analysis
        if len(similar_pairs) > max_pairs:
            self.logger.warning(f"Limiting analysis to top {max_pairs} most similar pairs")
            similar_pairs = sorted(similar_pairs, key=lambda x: x[2], reverse=True)[:max_pairs]
        
        # Process in batches to avoid overwhelming Ollama
        batch_size = 10
        relationships_created = 0
        
        for i in range(0, len(similar_pairs), batch_size):
            batch = similar_pairs[i:i + batch_size]
            self.logger.info(f"Processing batch {i//batch_size + 1}/{(len(similar_pairs) + batch_size - 1)//batch_size}")
            
            for node1_data, node2_data, similarity in batch:
                try:
                    node1 = node1_data['node']
                    node2 = node2_data['node']
                    
                    # Use rule-based relationship determination for speed
                    relationship_type = self.determine_relationship_fast(node1_data, node2_data)
                    
                    # Only use Ollama for high-similarity pairs that need detailed analysis
                    is_high_similarity = float(similarity) > 0.85
                    use_ai = is_high_similarity and relationships_created < 20
                    
                    if use_ai:  # Limit expensive AI calls
                        content1 = node1_data.get('content', '')[:300]  # Reduced content length
                        content2 = node2_data.get('content', '')[:300]
                        
                        if content1 and content2:
                            ai_relationship = self.analyze_relationship_with_ollama(content1, content2)
                            if ai_relationship != "RELATES_TO":  # Only use if AI found specific relationship
                                relationship_type = ai_relationship
                    
                    # Create the relationship
                    rel = Relationship(
                        node1, relationship_type, node2,
                        similarity_score=float(similarity),
                        method='enhanced_semantic_analysis',
                        ai_determined=use_ai
                    )
                    self.graph.create(rel)
                    relationships_created += 1
                    
                except Exception as e:
                    self.logger.error(f"Error creating relationship: {e}")
                    continue
            
            # Small delay between batches to prevent overwhelming the system
            import time
            time.sleep(1)
        
        self.logger.info(f"Created {relationships_created} enhanced semantic relationships")
    
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
            
            # Force commit any pending transactions
            try:
                self.graph.commit()
            except:
                pass  # May not have an active transaction
            
            # Add a small delay to ensure data is fully committed
            import time
            time.sleep(3)
            
            # Print enhanced stats
            stats_queries = [
                ("Node Types", "MATCH (n) RETURN labels(n)[0] as NodeType, count(n) as Count ORDER BY Count DESC"),
                ("Relationship Types", "MATCH ()-[r]->() RETURN type(r) as RelType, count(r) as Count ORDER BY Count DESC"),
                ("AI-Generated Relations", "MATCH ()-[r {method: 'enhanced_semantic_analysis'}]->() RETURN count(r) as AIRelations"),
                ("Total Nodes", "MATCH (n) RETURN count(n) as TotalNodes"),
                ("Total Relationships", "MATCH ()-[r]->() RETURN count(r) as TotalRelationships")
            ]
                
            print("\nEnhanced Knowledge Graph Statistics:")
            for title, query in stats_queries:
                print(f"\n{title}:")
                print(f"  Query: {query}")
                try:
                    results = list(self.graph.run(query))
                    print(f"  Results count: {len(results)}")
                    if len(results) > 0:
                        print(f"  First result: {dict(results[0])}")
                    
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
            self.logger.error(f"Error building enhanced knowledge graph: {e}")
            raise


# Usage example
if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Build enhanced Neo4j knowledge graph with multi-database support')
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
        builder = EnhancedKnowledgeGraphBuilder(
            ollama_url=OLLAMA_URL,
            ollama_model=OLLAMA_MODEL,
            embedding_model=EMBEDDING_MODEL,
            use_sentence_transformer=USE_SENTENCE_TRANSFORMER,
            target_database=TARGET_DATABASE
        )
        builder.build_enhanced_knowledge_graph()
        print(f"\nEnhanced knowledge graph construction completed successfully in database: {builder.target_database}!")
    except Exception as e:
        print(f"Error building enhanced knowledge graph: {e}")
        raise