#!/usr/bin/env python3
"""
Neo4j Database Utilities for Daemonium Project
Provides consistent database selection across all scripts.
"""

import sys
import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

def get_neo4j_database_config(script_name: str = None, 
                             target_database: str = None,
                             config_path: str = None) -> Dict[str, Any]:
    """
    Get Neo4j database configuration with flexible database selection.
    
    Priority order:
    1. target_database parameter (explicit override)
    2. Command line argument
    3. Environment variable NEO4J_TARGET_DATABASE
    4. Script-specific mapping in config
    5. Default database from config
    
    Args:
        script_name: Name of the calling script (for script-specific mappings)
        target_database: Explicit database override
        config_path: Path to config file (optional)
    
    Returns:
        Dict containing Neo4j configuration with selected database
    """
    
    # Load configuration
    if config_path is None:
        # Auto-detect config path from project structure
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        config_path = project_root / "config" / "default.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    neo4j_config = config['neo4j'].copy()
    
    # Database selection priority
    selected_database = None
    selection_method = "default"
    
    # 1. Explicit parameter override
    if target_database:
        selected_database = target_database
        selection_method = "parameter"
    
    # 2. Command line argument
    elif len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        selected_database = sys.argv[1]
        selection_method = "command_line"
    
    # 3. Environment variable
    elif os.getenv('NEO4J_TARGET_DATABASE'):
        selected_database = os.getenv('NEO4J_TARGET_DATABASE')
        selection_method = "environment"
    
    # 4. Script-specific mapping
    elif script_name and 'script_databases' in neo4j_config:
        script_db = neo4j_config['script_databases'].get(script_name)
        if script_db:
            selected_database = script_db
            selection_method = "script_mapping"
    
    # 5. Default database
    if not selected_database:
        selected_database = neo4j_config['database']
        selection_method = "default"
    
    # Update config with selected database
    neo4j_config['selected_database'] = selected_database
    neo4j_config['selection_method'] = selection_method
    
    # Validate database exists in configuration
    available_databases = [neo4j_config['database']]
    if 'databases' in neo4j_config:
        available_databases.extend(neo4j_config['databases'].values())
    
    if selected_database not in available_databases:
        logger.warning(f"Database '{selected_database}' not found in configuration. Available: {available_databases}")
    
    logger.info(f"Selected Neo4j database: '{selected_database}' (via {selection_method})")
    
    return neo4j_config

def get_neo4j_connection_uri(neo4j_config: Dict[str, Any]) -> str:
    """
    Build Neo4j connection URI from config.
    
    Args:
        neo4j_config: Neo4j configuration dictionary
    
    Returns:
        Bolt connection URI string
    """
    return f"bolt://{neo4j_config['host']}:{neo4j_config['bolt_port']}"

def get_neo4j_auth(neo4j_config: Dict[str, Any]) -> tuple:
    """
    Get Neo4j authentication tuple from config.
    
    Args:
        neo4j_config: Neo4j configuration dictionary
    
    Returns:
        Tuple of (username, password)
    """
    return (neo4j_config['username'], neo4j_config['password'])

def print_database_info(neo4j_config: Dict[str, Any]):
    """
    Print information about available databases and current selection.
    
    Args:
        neo4j_config: Neo4j configuration dictionary
    """
    print(f"\n{'='*50}")
    print("Neo4j Database Configuration")
    print(f"{'='*50}")
    print(f"Selected Database: {neo4j_config['selected_database']}")
    print(f"Selection Method: {neo4j_config['selection_method']}")
    print(f"Host: {neo4j_config['host']}:{neo4j_config['bolt_port']}")
    
    if 'databases' in neo4j_config:
        print(f"\nAvailable Databases:")
        print(f"  • {neo4j_config['database']} (default)")
        for key, db_name in neo4j_config['databases'].items():
            print(f"  • {db_name} ({key})")
    
    if 'script_databases' in neo4j_config:
        print(f"\nScript Mappings:")
        for script, db in neo4j_config['script_databases'].items():
            print(f"  • {script} → {db}")
    
    print(f"{'='*50}\n")

def create_database_if_not_exists(database_name: str, neo4j_config: Dict[str, Any]):
    """
    Create a database if it doesn't exist (Enterprise Edition only).
    
    Args:
        database_name: Name of database to create
        neo4j_config: Neo4j configuration dictionary
    """
    try:
        from py2neo import SystemGraph
        
        uri = get_neo4j_connection_uri(neo4j_config)
        auth = get_neo4j_auth(neo4j_config)
        
        system_graph = SystemGraph(uri, auth=auth)
        
        # Check if database exists
        result = system_graph.run("SHOW DATABASES")
        existing_databases = [record['name'] for record in result]
        
        if database_name not in existing_databases:
            logger.info(f"Creating database: {database_name}")
            system_graph.run(f"CREATE DATABASE `{database_name}`")
            logger.info(f"Database '{database_name}' created successfully")
        else:
            logger.info(f"Database '{database_name}' already exists")
            
    except Exception as e:
        logger.error(f"Failed to create database '{database_name}': {e}")
        raise

# Example usage patterns
def example_usage():
    """Example usage patterns for different scenarios."""
    
    print("Example Usage Patterns:")
    print("=" * 40)
    
    # Pattern 1: Simple script with auto-detection
    print("1. Auto-detection (recommended):")
    print("   config = get_neo4j_database_config('my_script')")
    
    # Pattern 2: Explicit database selection
    print("\n2. Explicit database:")
    print("   config = get_neo4j_database_config(target_database='daemonium_primary')")
    
    # Pattern 3: Command line usage
    print("\n3. Command line:")
    print("   python my_script.py daemonium_comparison")
    
    # Pattern 4: Environment variable
    print("\n4. Environment variable:")
    print("   NEO4J_TARGET_DATABASE=daemonium_experimental python my_script.py")

if __name__ == "__main__":
    # Demo the utility
    script_name = Path(__file__).stem
    config = get_neo4j_database_config(script_name)
    print_database_info(config)
    example_usage()
