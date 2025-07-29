# improved_kg_builder.py

from pymongo import MongoClient
from py2neo import Graph, Node, Relationship
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import requests
import yaml
from pathlib import Path
from urllib.parse import quote_plus
import logging
import re
from typing import List, Dict, Tuple

class EnhancedKnowledgeGraphBuilder:
    def __init__(self, config_path=None,
                 ollama_url="http://localhost:11434",
                 ollama_model="llama3.1:latest",
                 clear_graph=True):

        if config_path is None:
            script_dir = Path(__file__).parent
            project_root = script_dir.parent.parent
            config_path = project_root / 'config' / 'default.yaml'

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        mongo_config = config['mongodb']
        mongo_uri = f"mongodb://{quote_plus(mongo_config['username'])}:{quote_plus(mongo_config['password'])}@{mongo_config['host']}:{mongo_config['port']}/{mongo_config['database']}?authSource=admin"
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[mongo_config['database']]

        # Initialize logging first
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        neo4j_config = config['neo4j']
        neo4j_uri = f"bolt://{neo4j_config['host']}:{neo4j_config['bolt_port']}"
        self.graph = Graph(neo4j_uri, auth=(neo4j_config['username'], neo4j_config['password']))

        # Make graph clearing optional
        if clear_graph:
            self.logger.info("Clearing existing graph...")
            self.graph.delete_all()

        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model

        self.embedding_cache = {}

    def query_ollama(self, prompt: str) -> str:
        try:
            response = requests.post(f"{self.ollama_url}/api/generate", json={"model": self.ollama_model, "prompt": prompt, "stream": False}, timeout=30)
            if response.status_code == 200:
                return response.json().get('response', '')
        except Exception as e:
            self.logger.warning(f"Ollama error: {e}")
        return ""

    def get_embedding(self, text: str) -> np.ndarray:
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        embedding = self.sentence_model.encode([text])[0]
        self.embedding_cache[text] = embedding
        return embedding

    def create_philosophical_concept_node(self, concept: str, category: str = "unknown"):
        node = Node("Concept", name=concept, category=category)
        self.graph.merge(node, "Concept", "name")
        return node

    def enrich_and_connect_text(self, content: str, source_node: Node):
        prompt = f"""
        Extract: 1) philosophical concepts, 2) arguments (claim + support), 3) categories (ethics, metaphysics, etc).
        Format: \nConcepts: [...],\nArguments: [...],\nCategories: [...]
        Text: {content[:1000]}
        """
        response = self.query_ollama(prompt)

        concepts, arguments, categories = [], [], []
        try:
            for line in response.split('\n'):
                if line.startswith('Concepts:'):
                    concepts = [c.strip() for c in line.split(':', 1)[1].split(',') if c.strip()]
                elif line.startswith('Arguments:'):
                    arguments = [a.strip() for a in line.split(':', 1)[1].split(';') if a.strip()]
                elif line.startswith('Categories:'):
                    categories = [c.strip() for c in line.split(':', 1)[1].split(',') if c.strip()]
        except Exception as e:
            self.logger.warning(f"Response parsing error: {e}")

        for concept in concepts:
            concept_node = self.create_philosophical_concept_node(concept)
            self.graph.create(Relationship(source_node, "MENTIONS", concept_node))

        for cat in categories:
            cat_node = Node("Discipline", name=cat)
            self.graph.merge(cat_node, "Discipline", "name")
            self.graph.create(Relationship(source_node, "CATEGORIZED_AS", cat_node))

        for arg in arguments:
            arg_node = Node("Argument", text=arg)
            self.graph.create(arg_node)
            self.graph.create(Relationship(source_node, "CONTAINS_ARGUMENT", arg_node))

    def process_documents(self, collection_name: str, label: str, content_field: str):
        try:
            docs = self.db[collection_name].find()
            doc_count = 0
            for doc in docs:
                content = doc.get(content_field, '')
                if not content:
                    self.logger.warning(f"No content found in field '{content_field}' for document in {collection_name}")
                    continue
                    
                title = doc.get('title', doc.get('name', f"{label}_{doc_count}"))
                source_id = str(doc['_id'])
                
                # Handle different content types
                if isinstance(content, dict):
                    content_text = str(content)
                elif isinstance(content, list):
                    content_text = ' '.join(str(item) for item in content)
                else:
                    content_text = str(content)
                
                node = Node(label, title=title, content=content_text[:500], source_id=source_id)
                self.graph.create(node)
                self.enrich_and_connect_text(content_text, node)
                doc_count += 1
                
            self.logger.info(f"Processed {doc_count} documents from {collection_name}")
        except Exception as e:
            self.logger.error(f"Error processing collection {collection_name}: {e}")

    def link_related_concepts(self):
        query = "MATCH (a:Concept), (b:Concept) WHERE a.name <> b.name RETURN a, b"
        for record in self.graph.run(query):
            a, b = record['a'], record['b']
            sim = cosine_similarity([self.get_embedding(a['name'])], [self.get_embedding(b['name'])])[0][0]
            if sim > 0.75:
                rel = Relationship(a, "SIMILAR_TO", b, similarity=round(sim, 3))
                self.graph.merge(rel)

    def build_graph(self):
        self.logger.info("Starting Enhanced Graph Build...")
        
        # Process each collection with appropriate content fields
        collections_config = [
            ("book_summaries", "BookSummary", "content"),
            ("top_ten_ideas", "TopIdea", "content"),  # Fixed from "ideas" to "content"
            ("aphorisms", "Aphorism", "content"),
            ("idea_summaries", "IdeaSummary", "content"),
            ("bibliography", "Bibliography", "description")  # Bibliography uses description field
        ]
        
        for collection_name, label, content_field in collections_config:
            self.logger.info(f"Processing {collection_name}...")
            self.process_documents(collection_name, label, content_field)
        
        self.logger.info("Linking related concepts...")
        self.link_related_concepts()
        
        # Print statistics
        self.print_graph_statistics()
        
        self.logger.info("Enhanced graph build completed!")

    def print_graph_statistics(self):
        """Print comprehensive graph statistics"""
        try:
            print("\n=== Enhanced Knowledge Graph Statistics ===")
            
            # Node counts by type
            node_query = "MATCH (n) RETURN labels(n)[0] as NodeType, count(n) as Count ORDER BY Count DESC"
            node_results = list(self.graph.run(node_query))
            
            print("\nNode Types:")
            total_nodes = 0
            for record in node_results:
                node_type = record.get('NodeType', 'Unknown')
                count = record.get('Count', 0)
                print(f"  {node_type}: {count} nodes")
                total_nodes += count
            print(f"  Total Nodes: {total_nodes}")
            
            # Relationship counts by type
            rel_query = "MATCH ()-[r]->() RETURN type(r) as RelType, count(r) as Count ORDER BY Count DESC"
            rel_results = list(self.graph.run(rel_query))
            
            print("\nRelationship Types:")
            total_rels = 0
            for record in rel_results:
                rel_type = record.get('RelType', 'Unknown')
                count = record.get('Count', 0)
                print(f"  {rel_type}: {count} relationships")
                total_rels += count
            print(f"  Total Relationships: {total_rels}")
            
            # Concept nodes
            concept_query = "MATCH (c:Concept) RETURN count(c) as ConceptCount"
            concept_results = list(self.graph.run(concept_query))
            if concept_results:
                concept_count = concept_results[0].get('ConceptCount', 0)
                print(f"\nPhilosophical Concepts Extracted: {concept_count}")
            
        except Exception as e:
            self.logger.error(f"Error generating statistics: {e}")

if __name__ == "__main__":
    try:
        builder = EnhancedKnowledgeGraphBuilder(clear_graph=True)
        builder.build_graph()
        print("\n✅ Enhanced knowledge graph construction completed successfully!")
    except Exception as e:
        print(f"❌ Error building enhanced knowledge graph: {e}")
        raise
