#!/usr/bin/env python3
"""
Neo4j Database Management Script for Daemonium Project
Manages multiple databases in Neo4j Enterprise Edition for comparison purposes.
"""

import sys
import yaml
from pathlib import Path
from py2neo import Graph, SystemGraph
from py2neo.errors import ClientError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Neo4jDatabaseManager:
    def __init__(self, config_path=None):
        """Initialize the Neo4j Database Manager."""
        # Get the script directory and project root
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        
        # Load configuration
        if config_path is None:
            config_path = project_root / "config" / "default.yaml"
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Neo4j configuration
        neo4j_config = self.config['neo4j']
        self.host = neo4j_config['host']
        self.bolt_port = neo4j_config['bolt_port']
        self.username = neo4j_config['username']
        self.password = neo4j_config['password']
        self.default_database = neo4j_config['database']
        self.databases = neo4j_config.get('databases', {})
        
        # Build connection URI
        self.uri = f"bolt://{self.host}:{self.bolt_port}"
        
        # Initialize system graph for database management
        self.system_graph = None
        self.connect_to_system()
    
    def connect_to_system(self):
        """Connect to the Neo4j system database."""
        try:
            self.system_graph = SystemGraph(self.uri, auth=(self.username, self.password))
            logger.info("Connected to Neo4j system database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j system database: {e}")
            sys.exit(1)
    
    def list_databases(self):
        """List all databases in the Neo4j instance."""
        try:
            result = self.system_graph.run("SHOW DATABASES")
            databases = []
            for record in result:
                databases.append({
                    'name': record['name'],
                    'type': record['type'],
                    'status': record['currentStatus'],
                    'default': record['default']
                })
            return databases
        except Exception as e:
            logger.error(f"Failed to list databases: {e}")
            return []
    
    def create_database(self, database_name):
        """Create a new database."""
        try:
            query = f"CREATE DATABASE `{database_name}` IF NOT EXISTS"
            self.system_graph.run(query)
            logger.info(f"Database '{database_name}' created successfully")
            return True
        except ClientError as e:
            logger.error(f"Failed to create database '{database_name}': {e}")
            return False
    
    def drop_database(self, database_name):
        """Drop a database (use with caution!)."""
        if database_name == self.default_database:
            logger.error(f"Cannot drop default database '{database_name}'")
            return False
        
        try:
            query = f"DROP DATABASE `{database_name}` IF EXISTS"
            self.system_graph.run(query)
            logger.info(f"Database '{database_name}' dropped successfully")
            return True
        except ClientError as e:
            logger.error(f"Failed to drop database '{database_name}': {e}")
            return False
    
    def get_database_connection(self, database_name):
        """Get a connection to a specific database."""
        try:
            graph = Graph(self.uri, auth=(self.username, self.password), name=database_name)
            return graph
        except Exception as e:
            logger.error(f"Failed to connect to database '{database_name}': {e}")
            return None
    
    def setup_comparison_databases(self):
        """Set up all databases defined in the configuration."""
        logger.info("Setting up comparison databases...")
        
        # Create all configured databases
        for db_key, db_name in self.databases.items():
            logger.info(f"Creating database: {db_name} ({db_key})")
            self.create_database(db_name)
        
        # List all databases to confirm
        databases = self.list_databases()
        logger.info("Current databases:")
        for db in databases:
            status_indicator = "✓" if db['status'] == 'online' else "✗"
            default_indicator = " (default)" if db['default'] else ""
            logger.info(f"  {status_indicator} {db['name']}{default_indicator} - {db['status']}")
    
    def clear_database(self, database_name):
        """Clear all data from a database."""
        graph = self.get_database_connection(database_name)
        if graph is None:
            return False
        
        try:
            # Delete all nodes and relationships
            graph.run("MATCH (n) DETACH DELETE n")
            logger.info(f"Database '{database_name}' cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to clear database '{database_name}': {e}")
            return False
    
    def get_database_stats(self, database_name):
        """Get statistics for a database."""
        graph = self.get_database_connection(database_name)
        if graph is None:
            return None
        
        try:
            stats = {}
            
            # Count nodes
            result = graph.run("MATCH (n) RETURN count(n) as node_count")
            stats['nodes'] = result.single()['node_count']
            
            # Count relationships
            result = graph.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            stats['relationships'] = result.single()['rel_count']
            
            # Get node labels
            result = graph.run("CALL db.labels()")
            stats['labels'] = [record['label'] for record in result]
            
            # Get relationship types
            result = graph.run("CALL db.relationshipTypes()")
            stats['relationship_types'] = [record['relationshipType'] for record in result]
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get stats for database '{database_name}': {e}")
            return None

def main():
    """Main function to demonstrate database management."""
    manager = Neo4jDatabaseManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "setup":
            manager.setup_comparison_databases()
        
        elif command == "list":
            databases = manager.list_databases()
            print("\nNeo4j Databases:")
            print("-" * 50)
            for db in databases:
                status_indicator = "✓" if db['status'] == 'online' else "✗"
                default_indicator = " (default)" if db['default'] else ""
                print(f"{status_indicator} {db['name']}{default_indicator} - {db['status']}")
        
        elif command == "stats":
            if len(sys.argv) > 2:
                db_name = sys.argv[2]
                stats = manager.get_database_stats(db_name)
                if stats:
                    print(f"\nStatistics for database '{db_name}':")
                    print("-" * 40)
                    print(f"Nodes: {stats['nodes']}")
                    print(f"Relationships: {stats['relationships']}")
                    print(f"Labels: {', '.join(stats['labels']) if stats['labels'] else 'None'}")
                    print(f"Relationship Types: {', '.join(stats['relationship_types']) if stats['relationship_types'] else 'None'}")
            else:
                print("Usage: python manage_neo4j_databases.py stats <database_name>")
        
        elif command == "clear":
            if len(sys.argv) > 2:
                db_name = sys.argv[2]
                confirm = input(f"Are you sure you want to clear database '{db_name}'? (yes/no): ")
                if confirm.lower() == 'yes':
                    manager.clear_database(db_name)
                else:
                    print("Operation cancelled.")
            else:
                print("Usage: python manage_neo4j_databases.py clear <database_name>")
        
        else:
            print("Unknown command. Available commands: setup, list, stats, clear")
    
    else:
        print("Neo4j Database Manager for Daemonium")
        print("Available commands:")
        print("  setup  - Create all configured databases")
        print("  list   - List all databases")
        print("  stats <db_name> - Show database statistics")
        print("  clear <db_name> - Clear all data from database")

if __name__ == "__main__":
    main()
