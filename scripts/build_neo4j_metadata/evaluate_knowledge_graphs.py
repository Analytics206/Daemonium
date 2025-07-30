#!/usr/bin/env python3
"""
Knowledge Graph Quality Evaluation Script for Daemonium Project

This script evaluates and compares knowledge graphs for philosopher chatbot applications
using established quality metrics including:
- Structural metrics (density, connectivity, clustering)
- Completeness metrics (coverage, population)
- Consistency metrics (semantic coherence)
- Chatbot-specific metrics (query coverage, relationship diversity)

Author: Daemonium System
Version: 1.0.0
"""

import sys
from pathlib import Path
import yaml
import json
import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import statistics
import numpy as np
from collections import defaultdict, Counter
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
import pandas as pd
from io import StringIO

# Add utils directory to path
sys.path.append(str(Path(__file__).parent.parent / 'utils'))
from neo4j_database_utils import (
    get_neo4j_database_config, 
    get_neo4j_connection_uri, 
    get_neo4j_auth,
    print_database_info
)

from py2neo import Graph
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class KnowledgeGraphEvaluator:
    """
    Comprehensive knowledge graph quality evaluator for philosopher chatbot applications.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize the evaluator with configuration."""
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        if config_path is None:
            script_dir = Path(__file__).parent
            project_root = script_dir.parent.parent
            config_path = project_root / 'config' / 'default.yaml'
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize sentence transformer for semantic analysis
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Evaluation results storage
        self.evaluation_results = {}
        
        # Setup reports directory
        self.reports_dir = Path(__file__).parent / 'reports'
        self.reports_dir.mkdir(exist_ok=True)
        
        self.logger.info("Knowledge Graph Evaluator initialized")
        self.logger.info(f"Reports will be saved to: {self.reports_dir}")
    
    def connect_to_database(self, database_name: str) -> Graph:
        """Connect to a specific Neo4j database."""
        try:
            # Get Neo4j configuration for the database
            neo4j_config = get_neo4j_database_config("evaluate_knowledge_graphs", database_name)
            
            # Build connection
            neo4j_uri = get_neo4j_connection_uri(neo4j_config)
            neo4j_auth = get_neo4j_auth(neo4j_config)
            
            graph = Graph(neo4j_uri, auth=neo4j_auth, name=database_name)
            
            self.logger.info(f"Connected to Neo4j database: {database_name}")
            return graph
            
        except Exception as e:
            self.logger.error(f"Failed to connect to database {database_name}: {e}")
            raise
    
    def get_basic_statistics(self, graph: Graph) -> Dict[str, Any]:
        """Get comprehensive basic graph statistics."""
        stats = {}
        
        try:
            # Node statistics
            node_count_query = "MATCH (n) RETURN count(n) as total_nodes"
            result = list(graph.run(node_count_query))
            stats['total_nodes'] = result[0]['total_nodes'] if result else 0
            
            # Relationship statistics
            rel_count_query = "MATCH ()-[r]->() RETURN count(r) as total_relationships"
            result = list(graph.run(rel_count_query))
            stats['total_relationships'] = result[0]['total_relationships'] if result else 0
            
            # Node type distribution with detailed breakdown
            node_types_query = "MATCH (n) RETURN labels(n)[0] as node_type, count(n) as count ORDER BY count DESC"
            result = list(graph.run(node_types_query))
            stats['node_types'] = {record['node_type']: record['count'] for record in result if record['node_type']}
            stats['node_type_count'] = len(stats['node_types'])
            
            # Relationship type distribution with detailed breakdown
            rel_types_query = "MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count ORDER BY count DESC"
            result = list(graph.run(rel_types_query))
            stats['relationship_types'] = {record['rel_type']: record['count'] for record in result if record['rel_type']}
            stats['relationship_type_count'] = len(stats['relationship_types'])
            
            # AI-generated relationships with breakdown
            ai_rel_queries = {
                'semantic_analysis': "MATCH ()-[r]->() WHERE r.method = 'semantic_analysis' RETURN count(r) as count",
                'enhanced_semantic_analysis': "MATCH ()-[r]->() WHERE r.method = 'enhanced_semantic_analysis' RETURN count(r) as count",
                'total_ai': "MATCH ()-[r]->() WHERE r.method IN ['semantic_analysis', 'enhanced_semantic_analysis'] RETURN count(r) as count"
            }
            
            stats['ai_relationships'] = {}
            for ai_type, query in ai_rel_queries.items():
                result = list(graph.run(query))
                stats['ai_relationships'][ai_type] = result[0]['count'] if result else 0
            
            # Property statistics
            property_stats_queries = {
                'nodes_with_content': "MATCH (n) WHERE n.content IS NOT NULL RETURN count(n) as count",
                'nodes_with_summary': "MATCH (n) WHERE n.summary IS NOT NULL RETURN count(n) as count",
                'nodes_with_title': "MATCH (n) WHERE n.title IS NOT NULL RETURN count(n) as count",
                'nodes_with_author': "MATCH (n) WHERE n.author IS NOT NULL RETURN count(n) as count",
                'nodes_with_birth_year': "MATCH (n) WHERE n.birth_year IS NOT NULL RETURN count(n) as count",
                'nodes_with_nationality': "MATCH (n) WHERE n.nationality IS NOT NULL RETURN count(n) as count"
            }
            
            stats['property_statistics'] = {}
            for prop_name, query in property_stats_queries.items():
                try:
                    result = list(graph.run(query))
                    stats['property_statistics'][prop_name] = result[0]['count'] if result else 0
                except:
                    stats['property_statistics'][prop_name] = 0
            
            # Connectivity statistics
            connectivity_queries = {
                'isolated_nodes': "MATCH (n) WHERE NOT EXISTS((n)-[]-()) RETURN count(n) as count",
                'connected_nodes': "MATCH (n) WHERE EXISTS((n)-[]-()) RETURN count(n) as count",
                'leaf_nodes': "MATCH (n) WHERE size((n)-[]-()) = 1 RETURN count(n) as count",
                'hub_nodes': "MATCH (n) WHERE size((n)-[]-()) >= 5 RETURN count(n) as count"
            }
            
            stats['connectivity_statistics'] = {}
            for conn_name, query in connectivity_queries.items():
                try:
                    result = list(graph.run(query))
                    stats['connectivity_statistics'][conn_name] = result[0]['count'] if result else 0
                except:
                    stats['connectivity_statistics'][conn_name] = 0
            
            # Content richness statistics
            content_queries = {
                'avg_content_length': "MATCH (n) WHERE n.content IS NOT NULL RETURN avg(size(n.content)) as avg_length",
                'max_content_length': "MATCH (n) WHERE n.content IS NOT NULL RETURN max(size(n.content)) as max_length",
                'min_content_length': "MATCH (n) WHERE n.content IS NOT NULL RETURN min(size(n.content)) as min_length"
            }
            
            stats['content_statistics'] = {}
            for content_name, query in content_queries.items():
                try:
                    result = list(graph.run(query))
                    value = result[0][content_name.split('_')[0] + '_length'] if result and result[0] else 0
                    stats['content_statistics'][content_name] = round(value, 2) if value else 0
                except:
                    stats['content_statistics'][content_name] = 0
            
            # Temporal statistics (for philosophers)
            temporal_queries = {
                'philosophers_with_birth_year': "MATCH (p:Philosopher) WHERE p.birth_year IS NOT NULL RETURN count(p) as count",
                'earliest_birth_year': "MATCH (p:Philosopher) WHERE p.birth_year IS NOT NULL RETURN min(p.birth_year) as min_year",
                'latest_birth_year': "MATCH (p:Philosopher) WHERE p.birth_year IS NOT NULL RETURN max(p.birth_year) as max_year",
                'avg_birth_year': "MATCH (p:Philosopher) WHERE p.birth_year IS NOT NULL RETURN avg(p.birth_year) as avg_year"
            }
            
            stats['temporal_statistics'] = {}
            for temp_name, query in temporal_queries.items():
                try:
                    result = list(graph.run(query))
                    if result and result[0]:
                        key = temp_name.replace('_birth_year', '').replace('_', '_')
                        if 'avg' in temp_name:
                            stats['temporal_statistics'][temp_name] = round(result[0]['avg_year'], 1) if result[0]['avg_year'] else 0
                        elif 'min' in temp_name:
                            stats['temporal_statistics'][temp_name] = result[0]['min_year'] if result[0]['min_year'] else 0
                        elif 'max' in temp_name:
                            stats['temporal_statistics'][temp_name] = result[0]['max_year'] if result[0]['max_year'] else 0
                        else:
                            stats['temporal_statistics'][temp_name] = result[0]['count'] if result[0]['count'] else 0
                    else:
                        stats['temporal_statistics'][temp_name] = 0
                except:
                    stats['temporal_statistics'][temp_name] = 0
            
            self.logger.info(f"Comprehensive statistics collected: {stats['total_nodes']} nodes, {stats['total_relationships']} relationships, {stats['node_type_count']} node types, {stats['relationship_type_count']} relationship types")
            
        except Exception as e:
            self.logger.error(f"Error collecting basic statistics: {e}")
            stats = {'error': str(e)}
        
        return stats
    
    def calculate_structural_metrics(self, graph: Graph) -> Dict[str, float]:
        """Calculate structural quality metrics."""
        metrics = {}
        
        try:
            # Get basic counts
            stats = self.get_basic_statistics(graph)
            total_nodes = stats.get('total_nodes', 0)
            total_relationships = stats.get('total_relationships', 0)
            
            if total_nodes == 0:
                return {'error': 'No nodes found in graph'}
            
            # Graph density (actual edges / possible edges)
            max_possible_edges = total_nodes * (total_nodes - 1)
            metrics['density'] = total_relationships / max_possible_edges if max_possible_edges > 0 else 0
            
            # Average degree (relationships per node)
            metrics['average_degree'] = (2 * total_relationships) / total_nodes if total_nodes > 0 else 0
            
            # Node degree distribution
            degree_query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            RETURN n, count(r) as degree
            """
            result = list(graph.run(degree_query))
            degrees = [record['degree'] for record in result]
            
            if degrees:
                metrics['degree_std_dev'] = statistics.stdev(degrees) if len(degrees) > 1 else 0
                metrics['max_degree'] = max(degrees)
                metrics['min_degree'] = min(degrees)
                
                # Degree centralization (how much the graph is dominated by high-degree nodes)
                max_possible_degree = total_nodes - 1
                degree_centralization = sum(max(degrees) - d for d in degrees) / ((total_nodes - 1) * (total_nodes - 2)) if total_nodes > 2 else 0
                metrics['degree_centralization'] = degree_centralization
            
            # Clustering coefficient (local connectivity)
            clustering_query = """
            MATCH (n)-[r1]-(m)-[r2]-(o)
            WHERE n <> o
            OPTIONAL MATCH (n)-[r3]-(o)
            RETURN count(r3) * 1.0 / count(*) as clustering_coefficient
            """
            result = list(graph.run(clustering_query))
            metrics['clustering_coefficient'] = result[0]['clustering_coefficient'] if result and result[0]['clustering_coefficient'] else 0
            
            self.logger.info(f"Structural metrics calculated: density={metrics['density']:.4f}, avg_degree={metrics['average_degree']:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error calculating structural metrics: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def calculate_completeness_metrics(self, graph: Graph) -> Dict[str, float]:
        """Calculate completeness and coverage metrics."""
        metrics = {}
        
        try:
            # Schema completeness - check if expected node types are present
            expected_node_types = ['BookSummary', 'TopIdea', 'Aphorism', 'IdeaSummary', 'Philosopher', 'PhilosophicalTheme', 'PhilosophicalConcept']
            
            stats = self.get_basic_statistics(graph)
            present_node_types = set(stats.get('node_types', {}).keys())
            
            schema_completeness = len(present_node_types.intersection(expected_node_types)) / len(expected_node_types)
            metrics['schema_completeness'] = schema_completeness
            
            # Property completeness - check for nodes with missing key properties
            property_completeness_queries = {
                'philosopher_bio_completeness': "MATCH (p:Philosopher) WHERE p.birth_year IS NOT NULL AND p.nationality IS NOT NULL RETURN count(p) * 1.0 / count(*) as completeness",
                'book_metadata_completeness': "MATCH (b:BookSummary) WHERE b.author IS NOT NULL AND b.title IS NOT NULL RETURN count(b) * 1.0 / count(*) as completeness",
                'idea_content_completeness': "MATCH (i:TopIdea) WHERE i.content IS NOT NULL AND i.summary IS NOT NULL RETURN count(i) * 1.0 / count(*) as completeness"
            }
            
            for metric_name, query in property_completeness_queries.items():
                try:
                    result = list(graph.run(query))
                    metrics[metric_name] = result[0]['completeness'] if result and result[0]['completeness'] else 0
                except:
                    metrics[metric_name] = 0
            
            # Linkability completeness - ratio of connected vs isolated nodes
            connected_nodes_query = "MATCH (n) WHERE EXISTS((n)-[]-()) RETURN count(n) as connected"
            isolated_nodes_query = "MATCH (n) WHERE NOT EXISTS((n)-[]-()) RETURN count(n) as isolated"
            
            connected_result = list(graph.run(connected_nodes_query))
            isolated_result = list(graph.run(isolated_nodes_query))
            
            connected_count = connected_result[0]['connected'] if connected_result else 0
            isolated_count = isolated_result[0]['isolated'] if isolated_result else 0
            total_nodes = connected_count + isolated_count
            
            metrics['linkability_completeness'] = connected_count / total_nodes if total_nodes > 0 else 0
            
            self.logger.info(f"Completeness metrics calculated: schema={metrics['schema_completeness']:.2f}, linkability={metrics['linkability_completeness']:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error calculating completeness metrics: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def calculate_consistency_metrics(self, graph: Graph) -> Dict[str, float]:
        """Calculate consistency and coherence metrics."""
        metrics = {}
        
        try:
            # Temporal consistency - check for logical temporal relationships
            temporal_consistency_query = """
            MATCH (p1:Philosopher)-[r:CONTEMPORARY]-(p2:Philosopher)
            WHERE p1.birth_year IS NOT NULL AND p2.birth_year IS NOT NULL
            AND abs(p1.birth_year - p2.birth_year) > 50
            RETURN count(r) as inconsistent_temporal
            """
            
            result = list(graph.run(temporal_consistency_query))
            inconsistent_temporal = result[0]['inconsistent_temporal'] if result else 0
            
            total_temporal_query = "MATCH ()-[r:CONTEMPORARY]-() RETURN count(r) as total"
            result = list(graph.run(total_temporal_query))
            total_temporal = result[0]['total'] if result else 0
            
            metrics['temporal_consistency'] = 1 - (inconsistent_temporal / total_temporal) if total_temporal > 0 else 1
            
            # Overall semantic consistency
            total_relationships = self.get_basic_statistics(graph).get('total_relationships', 0)
            metrics['semantic_consistency'] = 1.0  # Simplified for now
            
            self.logger.info(f"Consistency metrics calculated: temporal={metrics['temporal_consistency']:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error calculating consistency metrics: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def calculate_chatbot_specific_metrics(self, graph: Graph) -> Dict[str, float]:
        """Calculate metrics specific to chatbot applications."""
        metrics = {}
        
        try:
            # Relationship diversity - variety of relationship types
            rel_types = self.get_basic_statistics(graph).get('relationship_types', {})
            metrics['relationship_diversity'] = len(rel_types)
            
            # Semantic richness - presence of AI-generated relationships
            ai_relationships = self.get_basic_statistics(graph).get('ai_relationships', 0)
            total_relationships = self.get_basic_statistics(graph).get('total_relationships', 0)
            metrics['ai_enhancement_ratio'] = ai_relationships / total_relationships if total_relationships > 0 else 0
            
            # Content accessibility - nodes with human-readable labels/descriptions
            total_nodes = self.get_basic_statistics(graph).get('total_nodes', 0)
            accessible_content_query = """
            MATCH (n) 
            WHERE n.title IS NOT NULL OR n.name IS NOT NULL OR n.label IS NOT NULL
            RETURN count(n) as accessible_nodes
            """
            
            result = list(graph.run(accessible_content_query))
            accessible_nodes = result[0]['accessible_nodes'] if result else 0
            metrics['content_accessibility'] = accessible_nodes / total_nodes if total_nodes > 0 else 0
            
            # Philosophical domain coverage
            philosophical_domains = ['ethics', 'metaphysics', 'epistemology', 'aesthetics', 'logic', 'political']
            domain_coverage_query = f"""
            MATCH (n)
            WHERE ANY(domain IN {philosophical_domains} WHERE toLower(n.content) CONTAINS domain OR toLower(n.summary) CONTAINS domain OR toLower(n.description) CONTAINS domain)
            RETURN count(DISTINCT n) as domain_nodes
            """
            
            result = list(graph.run(domain_coverage_query))
            domain_nodes = result[0]['domain_nodes'] if result else 0
            metrics['philosophical_domain_coverage'] = domain_nodes / total_nodes if total_nodes > 0 else 0
            
            self.logger.info(f"Chatbot metrics calculated: diversity={metrics['relationship_diversity']}, AI_ratio={metrics['ai_enhancement_ratio']:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error calculating chatbot-specific metrics: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def calculate_overall_quality_score(self, all_metrics: Dict[str, Dict]) -> float:
        """Calculate an overall quality score from all metrics."""
        try:
            # Define weights for different metric categories
            weights = {
                'structural': 0.25,
                'completeness': 0.30,
                'consistency': 0.25,
                'chatbot_specific': 0.20
            }
            
            # Extract key metrics and normalize them
            structural_score = 0
            if 'structural' in all_metrics:
                s_metrics = all_metrics['structural']
                # Normalize structural metrics (higher density and connectivity is better, but not too high)
                density = min(s_metrics.get('density', 0) * 10, 1.0)  # Scale density
                clustering = s_metrics.get('clustering_coefficient', 0)
                avg_degree = min(s_metrics.get('average_degree', 0) / 10, 1.0)  # Scale average degree
                structural_score = (density + clustering + avg_degree) / 3
            
            completeness_score = 0
            if 'completeness' in all_metrics:
                c_metrics = all_metrics['completeness']
                schema_comp = c_metrics.get('schema_completeness', 0)
                linkability_comp = c_metrics.get('linkability_completeness', 0)
                bio_comp = c_metrics.get('philosopher_bio_completeness', 0)
                completeness_score = (schema_comp + linkability_comp + bio_comp) / 3
            
            consistency_score = 0
            if 'consistency' in all_metrics:
                cons_metrics = all_metrics['consistency']
                temporal_cons = cons_metrics.get('temporal_consistency', 0)
                semantic_cons = cons_metrics.get('semantic_consistency', 0)
                consistency_score = (temporal_cons + semantic_cons) / 2
            
            chatbot_score = 0
            if 'chatbot_specific' in all_metrics:
                cb_metrics = all_metrics['chatbot_specific']
                ai_ratio = cb_metrics.get('ai_enhancement_ratio', 0)
                accessibility = cb_metrics.get('content_accessibility', 0)
                domain_coverage = cb_metrics.get('philosophical_domain_coverage', 0)
                diversity = min(cb_metrics.get('relationship_diversity', 0) / 20, 1.0)  # Scale diversity
                chatbot_score = (ai_ratio + accessibility + domain_coverage + diversity) / 4
            
            # Calculate weighted overall score
            overall_score = (
                structural_score * weights['structural'] +
                completeness_score * weights['completeness'] +
                consistency_score * weights['consistency'] +
                chatbot_score * weights['chatbot_specific']
            )
            
            return min(max(overall_score, 0.0), 1.0)  # Ensure score is between 0 and 1
            
        except Exception as e:
            self.logger.error(f"Error calculating overall quality score: {e}")
            return 0.0
    
    def evaluate_database(self, database_name: str) -> Dict[str, Any]:
        """Evaluate a single knowledge graph database."""
        self.logger.info(f"Starting evaluation of database: {database_name}")
        
        try:
            # Connect to database
            graph = self.connect_to_database(database_name)
            
            # Collect all metrics
            evaluation = {
                'database_name': database_name,
                'evaluation_timestamp': datetime.now().isoformat(),
                'basic_statistics': self.get_basic_statistics(graph),
                'structural': self.calculate_structural_metrics(graph),
                'completeness': self.calculate_completeness_metrics(graph),
                'consistency': self.calculate_consistency_metrics(graph),
                'chatbot_specific': self.calculate_chatbot_specific_metrics(graph)
            }
            
            # Calculate overall quality score
            evaluation['overall_quality_score'] = self.calculate_overall_quality_score(evaluation)
            
            self.logger.info(f"Evaluation completed for {database_name}. Overall score: {evaluation['overall_quality_score']:.3f}")
            
            return evaluation
            
        except Exception as e:
            self.logger.error(f"Error evaluating database {database_name}: {e}")
            return {
                'database_name': database_name,
                'evaluation_timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def compare_databases(self, database_names: List[str]) -> Dict[str, Any]:
        """Compare multiple knowledge graph databases."""
        self.logger.info(f"Starting comparison of databases: {database_names}")
        
        evaluations = {}
        
        # Evaluate each database
        for db_name in database_names:
            evaluations[db_name] = self.evaluate_database(db_name)
        
        # Generate comparison report
        comparison = {
            'comparison_timestamp': datetime.now().isoformat(),
            'databases_evaluated': database_names,
            'individual_evaluations': evaluations,
            'comparison_summary': self._generate_comparison_summary(evaluations)
        }
        
        return comparison
    
    def _generate_comparison_summary(self, evaluations: Dict[str, Dict]) -> Dict[str, Any]:
        """Generate a summary comparison of multiple evaluations."""
        summary = {
            'best_overall': None,
            'best_by_category': {},
            'recommendations': []
        }
        
        try:
            # Find best overall database
            best_score = -1
            best_db = None
            
            for db_name, eval_data in evaluations.items():
                if 'error' not in eval_data:
                    score = eval_data.get('overall_quality_score', 0)
                    if score > best_score:
                        best_score = score
                        best_db = db_name
            
            summary['best_overall'] = {'database': best_db, 'score': best_score}
            
            # Generate recommendations
            if best_db:
                summary['recommendations'].append(f"For philosopher chatbot use, recommend: {best_db} (overall score: {best_score:.3f})")
            
            # Add specific recommendations based on metrics
            for db_name, eval_data in evaluations.items():
                if 'error' not in eval_data:
                    basic_stats = eval_data.get('basic_statistics', {})
                    chatbot_metrics = eval_data.get('chatbot_specific', {})
                    
                    # Check for specific strengths/weaknesses
                    if basic_stats.get('total_nodes', 0) > 1000:
                        summary['recommendations'].append(f"{db_name}: Good content volume ({basic_stats['total_nodes']} nodes)")
                    
                    if chatbot_metrics.get('ai_enhancement_ratio', 0) > 0.1:
                        summary['recommendations'].append(f"{db_name}: Strong AI enhancement ({chatbot_metrics['ai_enhancement_ratio']:.1%} AI relationships)")
                    
                    if chatbot_metrics.get('relationship_diversity', 0) > 15:
                        summary['recommendations'].append(f"{db_name}: High relationship diversity ({chatbot_metrics['relationship_diversity']} types)")
            
        except Exception as e:
            summary['error'] = f"Error generating comparison summary: {e}"
        
        return summary
    
    def save_evaluation_report(self, evaluation_data: Dict[str, Any], output_file: str = None):
        """Save evaluation results to a JSON file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"kg_evaluation_report_{timestamp}.json"
        
        # Ensure file is saved in reports directory
        if not Path(output_file).is_absolute():
            output_file = self.reports_dir / output_file
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(evaluation_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Evaluation report saved to: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving evaluation report: {e}")
    
    def generate_text_report(self, evaluation_data: Dict[str, Any], output_file: str = None) -> str:
        """Generate a comprehensive text report."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"kg_evaluation_text_report_{timestamp}.txt"
        
        # Ensure file is saved in reports directory
        if not Path(output_file).is_absolute():
            output_file = self.reports_dir / output_file
        
        try:
            # Capture the formatted output to string
            original_stdout = sys.stdout
            sys.stdout = text_buffer = StringIO()
            
            # Generate the same formatted output as print_evaluation_summary
            self.print_evaluation_summary(evaluation_data)
            
            # Get the text content
            report_content = text_buffer.getvalue()
            sys.stdout = original_stdout
            
            # Add additional detailed analysis
            additional_content = self._generate_additional_analysis(evaluation_data)
            full_report = report_content + "\n\n" + additional_content
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_report)
            
            self.logger.info(f"Text report saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Error generating text report: {e}")
            return None
    
    def _generate_additional_analysis(self, evaluation_data: Dict[str, Any]) -> str:
        """Generate additional analysis for the text report."""
        analysis = []
        analysis.append("=" * 80)
        analysis.append("DETAILED ANALYSIS AND RECOMMENDATIONS")
        analysis.append("=" * 80)
        
        if 'individual_evaluations' in evaluation_data:
            # Multi-database analysis
            analysis.append("\n📊 COMPARATIVE ANALYSIS:")
            
            evaluations = evaluation_data['individual_evaluations']
            scores = {}
            for db_name, eval_data in evaluations.items():
                if 'error' not in eval_data:
                    scores[db_name] = eval_data.get('overall_quality_score', 0)
            
            if scores:
                best_db = max(scores, key=scores.get)
                worst_db = min(scores, key=scores.get)
                avg_score = sum(scores.values()) / len(scores)
                
                analysis.append(f"\n  • Best performing database: {best_db} (Score: {scores[best_db]:.3f})")
                analysis.append(f"  • Lowest performing database: {worst_db} (Score: {scores[worst_db]:.3f})")
                analysis.append(f"  • Average score across all databases: {avg_score:.3f}")
                analysis.append(f"  • Score range: {scores[best_db] - scores[worst_db]:.3f}")
            
            # Category-wise recommendations
            analysis.append("\n🎯 CATEGORY-WISE RECOMMENDATIONS:")
            
            for db_name, eval_data in evaluations.items():
                if 'error' not in eval_data:
                    analysis.append(f"\n  {db_name.upper()}:")
                    recommendations = self._generate_db_recommendations(eval_data)
                    for rec in recommendations:
                        analysis.append(f"    • {rec}")
        
        else:
            # Single database analysis
            analysis.append("\n🎯 RECOMMENDATIONS:")
            recommendations = self._generate_db_recommendations(evaluation_data)
            for rec in recommendations:
                analysis.append(f"  • {rec}")
        
        analysis.append("\n" + "=" * 80)
        analysis.append("END OF DETAILED ANALYSIS")
        analysis.append("=" * 80)
        
        return "\n".join(analysis)
    
    def _generate_db_recommendations(self, eval_data: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations for a database."""
        recommendations = []
        
        # Analyze completeness
        completeness = eval_data.get('completeness', {})
        if 'schema_completeness' in completeness:
            schema_comp = completeness['schema_completeness']
            if schema_comp < 0.5:
                recommendations.append(f"Low schema completeness ({schema_comp:.1%}). Consider adding missing node types like Philosopher, PhilosophicalTheme.")
        
        # Analyze connectivity
        basic_stats = eval_data.get('basic_statistics', {})
        if 'connectivity_statistics' in basic_stats:
            conn_stats = basic_stats['connectivity_statistics']
            isolated = conn_stats.get('isolated_nodes', 0)
            total_nodes = basic_stats.get('total_nodes', 1)
            if isolated > 0:
                isolation_rate = (isolated / total_nodes) * 100
                recommendations.append(f"Found {isolated} isolated nodes ({isolation_rate:.1f}%). Consider adding relationships to improve connectivity.")
        
        # Analyze AI enhancement
        chatbot = eval_data.get('chatbot_specific', {})
        if 'ai_enhancement_ratio' in chatbot:
            ai_ratio = chatbot['ai_enhancement_ratio']
            if ai_ratio < 0.1:
                recommendations.append(f"Low AI enhancement ratio ({ai_ratio:.1%}). Consider running semantic analysis to add more AI-generated relationships.")
        
        # Analyze structural metrics
        structural = eval_data.get('structural', {})
        if 'density' in structural:
            density = structural['density']
            if density < 0.001:
                recommendations.append(f"Very low graph density ({density:.6f}). Consider adding more cross-references between content.")
            elif density > 0.1:
                recommendations.append(f"High graph density ({density:.6f}). Graph may be over-connected, consider pruning weak relationships.")
        
        # Analyze content richness
        if 'property_statistics' in basic_stats:
            prop_stats = basic_stats['property_statistics']
            content_coverage = prop_stats.get('nodes_with_content', 0) / basic_stats.get('total_nodes', 1)
            if content_coverage < 0.5:
                recommendations.append(f"Low content coverage ({content_coverage:.1%}). Consider enriching nodes with more descriptive content.")
        
        if not recommendations:
            recommendations.append("Database shows good overall quality metrics. Consider monitoring and maintaining current standards.")
        
        return recommendations
    
    def generate_visual_report(self, evaluation_data: Dict[str, Any], output_file: str = None) -> str:
        """Generate visual charts and graphs for the evaluation."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"kg_evaluation_visual_report_{timestamp}.pdf"
        
        # Ensure file is saved in reports directory
        if not Path(output_file).is_absolute():
            output_file = self.reports_dir / output_file
        
        try:
            # Set up the plotting style
            plt.style.use('default')
            sns.set_palette("husl")
            
            with PdfPages(output_file) as pdf:
                if 'individual_evaluations' in evaluation_data:
                    # Multi-database comparison
                    self._create_comparison_charts(evaluation_data, pdf)
                else:
                    # Single database analysis
                    self._create_single_db_charts(evaluation_data, pdf)
            
            self.logger.info(f"Visual report saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Error generating visual report: {e}")
            return None
    
    def _create_comparison_charts(self, evaluation_data: Dict[str, Any], pdf: PdfPages):
        """Create comparison charts for multiple databases."""
        evaluations = evaluation_data['individual_evaluations']
        
        # Extract data for comparison
        db_names = []
        overall_scores = []
        node_counts = []
        rel_counts = []
        ai_ratios = []
        densities = []
        
        for db_name, eval_data in evaluations.items():
            if 'error' not in eval_data:
                db_names.append(db_name)
                overall_scores.append(eval_data.get('overall_quality_score', 0))
                
                basic_stats = eval_data.get('basic_statistics', {})
                node_counts.append(basic_stats.get('total_nodes', 0))
                rel_counts.append(basic_stats.get('total_relationships', 0))
                
                chatbot = eval_data.get('chatbot_specific', {})
                ai_ratios.append(chatbot.get('ai_enhancement_ratio', 0) * 100)
                
                structural = eval_data.get('structural', {})
                densities.append(structural.get('density', 0))
        
        # Create comparison charts
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Knowledge Graph Comparison Dashboard', fontsize=16, fontweight='bold')
        
        # Overall Quality Scores
        axes[0, 0].bar(db_names, overall_scores, color='skyblue', edgecolor='navy')
        axes[0, 0].set_title('Overall Quality Scores')
        axes[0, 0].set_ylabel('Score')
        axes[0, 0].tick_params(axis='x', rotation=45)
        for i, v in enumerate(overall_scores):
            axes[0, 0].text(i, v + 0.01, f'{v:.3f}', ha='center', va='bottom')
        
        # Node Counts
        axes[0, 1].bar(db_names, node_counts, color='lightgreen', edgecolor='darkgreen')
        axes[0, 1].set_title('Total Nodes')
        axes[0, 1].set_ylabel('Count')
        axes[0, 1].tick_params(axis='x', rotation=45)
        for i, v in enumerate(node_counts):
            axes[0, 1].text(i, v + max(node_counts) * 0.01, f'{v:,}', ha='center', va='bottom')
        
        # Relationship Counts
        axes[0, 2].bar(db_names, rel_counts, color='lightcoral', edgecolor='darkred')
        axes[0, 2].set_title('Total Relationships')
        axes[0, 2].set_ylabel('Count')
        axes[0, 2].tick_params(axis='x', rotation=45)
        for i, v in enumerate(rel_counts):
            axes[0, 2].text(i, v + max(rel_counts) * 0.01, f'{v:,}', ha='center', va='bottom')
        
        # AI Enhancement Ratios
        axes[1, 0].bar(db_names, ai_ratios, color='gold', edgecolor='orange')
        axes[1, 0].set_title('AI Enhancement Ratio')
        axes[1, 0].set_ylabel('Percentage (%)')
        axes[1, 0].tick_params(axis='x', rotation=45)
        for i, v in enumerate(ai_ratios):
            axes[1, 0].text(i, v + max(ai_ratios) * 0.01, f'{v:.1f}%', ha='center', va='bottom')
        
        # Graph Density
        axes[1, 1].bar(db_names, densities, color='mediumpurple', edgecolor='purple')
        axes[1, 1].set_title('Graph Density')
        axes[1, 1].set_ylabel('Density')
        axes[1, 1].tick_params(axis='x', rotation=45)
        for i, v in enumerate(densities):
            axes[1, 1].text(i, v + max(densities) * 0.01, f'{v:.6f}', ha='center', va='bottom')
        
        # Radar Chart for Quality Dimensions
        if len(db_names) > 0:
            self._create_radar_chart(evaluations, axes[1, 2])
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
        
        # Create detailed breakdown charts for each database
        for db_name, eval_data in evaluations.items():
            if 'error' not in eval_data:
                self._create_single_db_charts(eval_data, pdf, db_name)
    
    def _create_single_db_charts(self, eval_data: Dict[str, Any], pdf: PdfPages, db_name: str = None):
        """Create detailed charts for a single database."""
        basic_stats = eval_data.get('basic_statistics', {})
        
        if not basic_stats or 'error' in basic_stats:
            return
        
        db_title = db_name if db_name else eval_data.get('database_name', 'Unknown')
        
        # Create node and relationship distribution charts
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Detailed Analysis: {db_title}', fontsize=16, fontweight='bold')
        
        # Node Type Distribution
        if 'node_types' in basic_stats:
            node_types = basic_stats['node_types']
            if node_types:
                types, counts = zip(*list(node_types.items())[:10])  # Top 10
                axes[0, 0].pie(counts, labels=types, autopct='%1.1f%%', startangle=90)
                axes[0, 0].set_title('Node Type Distribution')
        
        # Relationship Type Distribution
        if 'relationship_types' in basic_stats:
            rel_types = basic_stats['relationship_types']
            if rel_types:
                types, counts = zip(*list(rel_types.items())[:10])  # Top 10
                axes[0, 1].pie(counts, labels=types, autopct='%1.1f%%', startangle=90)
                axes[0, 1].set_title('Relationship Type Distribution')
        
        # Property Coverage
        if 'property_statistics' in basic_stats:
            prop_stats = basic_stats['property_statistics']
            total_nodes = basic_stats.get('total_nodes', 1)
            
            properties = []
            coverages = []
            for prop_name, count in prop_stats.items():
                display_name = prop_name.replace('nodes_with_', '').replace('_', ' ').title()
                properties.append(display_name)
                coverages.append((count / total_nodes) * 100)
            
            if properties:
                axes[1, 0].barh(properties, coverages, color='lightblue', edgecolor='blue')
                axes[1, 0].set_title('Property Coverage (%)')
                axes[1, 0].set_xlabel('Coverage Percentage')
                for i, v in enumerate(coverages):
                    axes[1, 0].text(v + 1, i, f'{v:.1f}%', va='center')
        
        # Quality Metrics Radar
        self._create_quality_radar(eval_data, axes[1, 1])
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def _create_radar_chart(self, evaluations: Dict[str, Dict], ax):
        """Create a radar chart comparing quality dimensions across databases."""
        categories = ['Structural', 'Completeness', 'Consistency', 'Chatbot']
        
        # Calculate scores for each database
        db_scores = {}
        for db_name, eval_data in evaluations.items():
            if 'error' not in eval_data:
                scores = []
                
                # Structural score
                structural = eval_data.get('structural', {})
                if structural and 'error' not in structural:
                    density = min(structural.get('density', 0) * 10, 1.0)
                    clustering = structural.get('clustering_coefficient', 0)
                    scores.append((density + clustering) / 2)
                else:
                    scores.append(0)
                
                # Completeness score
                completeness = eval_data.get('completeness', {})
                if completeness and 'error' not in completeness:
                    schema_comp = completeness.get('schema_completeness', 0)
                    linkability_comp = completeness.get('linkability_completeness', 0)
                    scores.append((schema_comp + linkability_comp) / 2)
                else:
                    scores.append(0)
                
                # Consistency score
                consistency = eval_data.get('consistency', {})
                if consistency and 'error' not in consistency:
                    temporal_cons = consistency.get('temporal_consistency', 0)
                    semantic_cons = consistency.get('semantic_consistency', 0)
                    scores.append((temporal_cons + semantic_cons) / 2)
                else:
                    scores.append(0)
                
                # Chatbot score
                chatbot = eval_data.get('chatbot_specific', {})
                if chatbot and 'error' not in chatbot:
                    ai_ratio = chatbot.get('ai_enhancement_ratio', 0)
                    accessibility = chatbot.get('content_accessibility', 0)
                    scores.append((ai_ratio + accessibility) / 2)
                else:
                    scores.append(0)
                
                db_scores[db_name] = scores
        
        # Create radar chart using bar chart instead due to matplotlib compatibility
        if db_scores:
            # Convert to bar chart for compatibility
            x_pos = np.arange(len(categories))
            width = 0.8 / len(db_scores) if db_scores else 0.8
            
            colors = plt.cm.Set3(np.linspace(0, 1, len(db_scores)))
            
            for i, (db_name, scores) in enumerate(db_scores.items()):
                offset = (i - len(db_scores)/2 + 0.5) * width
                ax.bar(x_pos + offset, scores, width, label=db_name, color=colors[i], alpha=0.7)
            
            ax.set_xlabel('Quality Dimensions')
            ax.set_ylabel('Score')
            ax.set_title('Quality Dimensions Comparison')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(categories)
            ax.set_ylim(0, 1)
            ax.legend()
        else:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
    
    def _create_quality_radar(self, eval_data: Dict[str, Any], ax):
        """Create a quality radar chart for a single database."""
        categories = ['Structural', 'Completeness', 'Consistency', 'Chatbot']
        scores = []
        
        # Calculate scores (same logic as in _create_radar_chart)
        structural = eval_data.get('structural', {})
        if structural and 'error' not in structural:
            density = min(structural.get('density', 0) * 10, 1.0)
            clustering = structural.get('clustering_coefficient', 0)
            scores.append((density + clustering) / 2)
        else:
            scores.append(0)
        
        completeness = eval_data.get('completeness', {})
        if completeness and 'error' not in completeness:
            schema_comp = completeness.get('schema_completeness', 0)
            linkability_comp = completeness.get('linkability_completeness', 0)
            scores.append((schema_comp + linkability_comp) / 2)
        else:
            scores.append(0)
        
        consistency = eval_data.get('consistency', {})
        if consistency and 'error' not in consistency:
            temporal_cons = consistency.get('temporal_consistency', 0)
            semantic_cons = consistency.get('semantic_consistency', 0)
            scores.append((temporal_cons + semantic_cons) / 2)
        else:
            scores.append(0)
        
        chatbot = eval_data.get('chatbot_specific', {})
        if chatbot and 'error' not in chatbot:
            ai_ratio = chatbot.get('ai_enhancement_ratio', 0)
            accessibility = chatbot.get('content_accessibility', 0)
            scores.append((ai_ratio + accessibility) / 2)
        else:
            scores.append(0)
        
        # Create bar chart instead of radar chart for compatibility
        x_pos = np.arange(len(categories))
        bars = ax.bar(x_pos, scores, color=['skyblue', 'lightgreen', 'lightcoral', 'gold'], alpha=0.7)
        
        # Add value labels on bars
        for i, (bar, score) in enumerate(zip(bars, scores)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{score:.2f}', ha='center', va='bottom')
        
        ax.set_xlabel('Quality Dimensions')
        ax.set_ylabel('Score')
        ax.set_title('Quality Dimensions')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 1.1)
    
    def print_evaluation_summary(self, evaluation_data: Dict[str, Any]):
        """Print a comprehensive formatted summary of evaluation results."""
        print("\n" + "="*80)
        print("KNOWLEDGE GRAPH EVALUATION SUMMARY")
        print("="*80)
        
        if 'individual_evaluations' in evaluation_data:
            # This is a comparison report
            print(f"\nDatabases Evaluated: {', '.join(evaluation_data['databases_evaluated'])}")
            print(f"Evaluation Time: {evaluation_data['comparison_timestamp']}")
            
            # Print comparison summary
            if 'comparison_summary' in evaluation_data:
                summary = evaluation_data['comparison_summary']
                
                if 'best_overall' in summary and summary['best_overall']:
                    best = summary['best_overall']
                    print(f"\n🏆 BEST OVERALL: {best['database']} (Score: {best['score']:.3f})")
                
                if 'recommendations' in summary:
                    print(f"\n📋 RECOMMENDATIONS:")
                    for rec in summary['recommendations']:
                        print(f"  • {rec}")
            
            # Print detailed comparison table
            print(f"\n📊 DETAILED COMPARISON:")
            print(f"{'Database':<20} {'Score':<8} {'Nodes':<8} {'Rels':<8} {'Types':<8} {'AI%':<8} {'Density':<10}")
            print("-" * 80)
            
            for db_name, eval_data in evaluation_data['individual_evaluations'].items():
                if 'error' not in eval_data:
                    score = eval_data.get('overall_quality_score', 0)
                    basic_stats = eval_data.get('basic_statistics', {})
                    structural = eval_data.get('structural', {})
                    chatbot = eval_data.get('chatbot_specific', {})
                    
                    nodes = basic_stats.get('total_nodes', 0)
                    rels = basic_stats.get('total_relationships', 0)
                    node_types = basic_stats.get('node_type_count', 0)
                    ai_ratio = chatbot.get('ai_enhancement_ratio', 0) * 100
                    density = structural.get('density', 0)
                    
                    print(f"{db_name:<20} {score:<8.3f} {nodes:<8} {rels:<8} {node_types:<8} {ai_ratio:<8.1f} {density:<10.6f}")
                else:
                    print(f"{db_name:<20} ERROR: {eval_data['error'][:50]}...")
            
            # Print detailed statistics for each database
            for db_name, eval_data in evaluation_data['individual_evaluations'].items():
                if 'error' not in eval_data:
                    print(f"\n\n📈 DETAILED STATISTICS FOR {db_name.upper()}:")
                    print("-" * 60)
                    self._print_detailed_stats(eval_data)
        
        else:
            # This is a single database evaluation
            db_name = evaluation_data.get('database_name', 'Unknown')
            score = evaluation_data.get('overall_quality_score', 0)
            
            print(f"\nDatabase: {db_name}")
            print(f"Overall Quality Score: {score:.3f}")
            print(f"Evaluation Time: {evaluation_data.get('evaluation_timestamp', 'Unknown')}")
            
            # Print detailed statistics
            print(f"\n📈 DETAILED STATISTICS:")
            print("-" * 60)
            self._print_detailed_stats(evaluation_data)
        
        print("\n" + "="*80)
    
    def _print_detailed_stats(self, eval_data: Dict[str, Any]):
        """Print detailed statistics for a single evaluation."""
        
        # Basic Statistics
        basic_stats = eval_data.get('basic_statistics', {})
        if basic_stats and 'error' not in basic_stats:
            print(f"\n🔢 BASIC STATISTICS:")
            print(f"  Total Nodes: {basic_stats.get('total_nodes', 0):,}")
            print(f"  Total Relationships: {basic_stats.get('total_relationships', 0):,}")
            print(f"  Node Types: {basic_stats.get('node_type_count', 0)}")
            print(f"  Relationship Types: {basic_stats.get('relationship_type_count', 0)}")
            
            # Node type breakdown
            if 'node_types' in basic_stats:
                print(f"\n  📋 Node Type Distribution:")
                for node_type, count in list(basic_stats['node_types'].items())[:10]:  # Top 10
                    percentage = (count / basic_stats.get('total_nodes', 1)) * 100
                    print(f"    {node_type:<20}: {count:>6,} ({percentage:5.1f}%)")
            
            # Relationship type breakdown
            if 'relationship_types' in basic_stats:
                print(f"\n  🔗 Relationship Type Distribution:")
                for rel_type, count in list(basic_stats['relationship_types'].items())[:10]:  # Top 10
                    percentage = (count / basic_stats.get('total_relationships', 1)) * 100
                    print(f"    {rel_type:<20}: {count:>6,} ({percentage:5.1f}%)")
            
            # AI Relationships breakdown
            if 'ai_relationships' in basic_stats:
                ai_stats = basic_stats['ai_relationships']
                print(f"\n  🤖 AI-Generated Relationships:")
                for ai_type, count in ai_stats.items():
                    if isinstance(count, (int, float)):
                        percentage = (count / basic_stats.get('total_relationships', 1)) * 100 if basic_stats.get('total_relationships', 0) > 0 else 0
                        print(f"    {ai_type.replace('_', ' ').title():<20}: {count:>6,} ({percentage:5.1f}%)")
        
        # Property Statistics
        if 'property_statistics' in basic_stats:
            prop_stats = basic_stats['property_statistics']
            print(f"\n📝 PROPERTY STATISTICS:")
            total_nodes = basic_stats.get('total_nodes', 1)
            for prop_name, count in prop_stats.items():
                percentage = (count / total_nodes) * 100
                display_name = prop_name.replace('nodes_with_', '').replace('_', ' ').title()
                print(f"  {display_name:<20}: {count:>6,} ({percentage:5.1f}%)")
        
        # Connectivity Statistics
        if 'connectivity_statistics' in basic_stats:
            conn_stats = basic_stats['connectivity_statistics']
            print(f"\n🔗 CONNECTIVITY STATISTICS:")
            total_nodes = basic_stats.get('total_nodes', 1)
            for conn_name, count in conn_stats.items():
                percentage = (count / total_nodes) * 100
                display_name = conn_name.replace('_', ' ').title()
                print(f"  {display_name:<20}: {count:>6,} ({percentage:5.1f}%)")
        
        # Content Statistics
        if 'content_statistics' in basic_stats:
            content_stats = basic_stats['content_statistics']
            print(f"\n📄 CONTENT STATISTICS:")
            for content_name, value in content_stats.items():
                display_name = content_name.replace('_', ' ').title()
                print(f"  {display_name:<20}: {value:>10.1f} characters")
        
        # Temporal Statistics
        if 'temporal_statistics' in basic_stats:
            temp_stats = basic_stats['temporal_statistics']
            print(f"\n⏰ TEMPORAL STATISTICS:")
            for temp_name, value in temp_stats.items():
                display_name = temp_name.replace('_', ' ').title()
                if 'year' in temp_name and value > 0:
                    print(f"  {display_name:<25}: {value}")
                elif 'philosophers' in temp_name:
                    print(f"  {display_name:<25}: {value:,}")
        
        # Structural Metrics
        structural = eval_data.get('structural', {})
        if structural and 'error' not in structural:
            print(f"\n🏗️ STRUCTURAL METRICS:")
            metrics_display = {
                'density': ('Graph Density', '{:.6f}'),
                'average_degree': ('Average Degree', '{:.2f}'),
                'clustering_coefficient': ('Clustering Coefficient', '{:.4f}'),
                'degree_centralization': ('Degree Centralization', '{:.4f}'),
                'max_degree': ('Max Degree', '{:,}'),
                'min_degree': ('Min Degree', '{:,}'),
                'degree_std_dev': ('Degree Std Dev', '{:.2f}')
            }
            
            for metric, (display_name, format_str) in metrics_display.items():
                if metric in structural:
                    value = structural[metric]
                    formatted_value = format_str.format(value)
                    print(f"  {display_name:<25}: {formatted_value}")
        
        # Completeness Metrics
        completeness = eval_data.get('completeness', {})
        if completeness and 'error' not in completeness:
            print(f"\n✅ COMPLETENESS METRICS:")
            for metric, value in completeness.items():
                if isinstance(value, (int, float)):
                    display_name = metric.replace('_', ' ').title()
                    percentage = value * 100
                    print(f"  {display_name:<25}: {percentage:5.1f}%")
        
        # Consistency Metrics
        consistency = eval_data.get('consistency', {})
        if consistency and 'error' not in consistency:
            print(f"\n🎯 CONSISTENCY METRICS:")
            for metric, value in consistency.items():
                if isinstance(value, (int, float)):
                    display_name = metric.replace('_', ' ').title()
                    if 'consistency' in metric:
                        percentage = value * 100
                        print(f"  {display_name:<25}: {percentage:5.1f}%")
                    else:
                        print(f"  {display_name:<25}: {value}")
        
        # Chatbot-Specific Metrics
        chatbot = eval_data.get('chatbot_specific', {})
        if chatbot and 'error' not in chatbot:
            print(f"\n🤖 CHATBOT-SPECIFIC METRICS:")
            metrics_display = {
                'relationship_diversity': ('Relationship Diversity', '{:,} types'),
                'ai_enhancement_ratio': ('AI Enhancement Ratio', '{:.1%}'),
                'content_accessibility': ('Content Accessibility', '{:.1%}'),
                'philosophical_domain_coverage': ('Domain Coverage', '{:.1%}')
            }
            
            for metric, (display_name, format_str) in metrics_display.items():
                if metric in chatbot:
                    value = chatbot[metric]
                    formatted_value = format_str.format(value)
                    print(f"  {display_name:<25}: {formatted_value}")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate Neo4j knowledge graphs for philosopher chatbot quality')
    parser.add_argument('--databases', '-d', nargs='+', required=True, 
                       help='Database names to evaluate (space-separated)')
    parser.add_argument('--output', '-o', type=str, 
                       help='Output file for detailed report (JSON)')
    parser.add_argument('--text-report', '-t', action='store_true',
                       help='Generate comprehensive text report')
    parser.add_argument('--visual-report', '-v', action='store_true',
                       help='Generate visual charts and graphs (PDF)')
    parser.add_argument('--all-reports', '-a', action='store_true',
                       help='Generate all report types (JSON, text, visual)')
    parser.add_argument('--compare', '-c', action='store_true',
                       help='Compare multiple databases (default: evaluate individually)')
    
    args = parser.parse_args()
    
    try:
        evaluator = KnowledgeGraphEvaluator()
        
        if args.compare and len(args.databases) > 1:
            # Compare multiple databases
            print(f"Comparing knowledge graphs: {', '.join(args.databases)}")
            results = evaluator.compare_databases(args.databases)
            
            # Print summary to terminal (always shown)
            evaluator.print_evaluation_summary(results)
            
            # Generate reports based on arguments
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON report
            if args.output or args.all_reports:
                json_file = args.output if args.output else f"kg_comparison_report_{timestamp}.json"
                evaluator.save_evaluation_report(results, json_file)
            
            # Text report
            if args.text_report or args.all_reports:
                text_file = f"kg_comparison_text_report_{timestamp}.txt"
                evaluator.generate_text_report(results, text_file)
            
            # Visual report
            if args.visual_report or args.all_reports:
                visual_file = f"kg_comparison_visual_report_{timestamp}.pdf"
                evaluator.generate_visual_report(results, visual_file)
        
        else:
            # Evaluate databases individually
            for db_name in args.databases:
                print(f"\nEvaluating knowledge graph: {db_name}")
                results = evaluator.evaluate_database(db_name)
                
                # Print summary to terminal (always shown)
                evaluator.print_evaluation_summary(results)
                
                # Generate reports based on arguments
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                db_suffix = f"_{db_name}" if len(args.databases) > 1 else ""
                
                # JSON report
                if args.output or args.all_reports:
                    json_file = f"{db_name}_{args.output}" if args.output and len(args.databases) > 1 else (args.output if args.output else f"kg_evaluation_report{db_suffix}_{timestamp}.json")
                    evaluator.save_evaluation_report(results, json_file)
                
                # Text report
                if args.text_report or args.all_reports:
                    text_file = f"kg_evaluation_text_report{db_suffix}_{timestamp}.txt"
                    evaluator.generate_text_report(results, text_file)
                
                # Visual report
                if args.visual_report or args.all_reports:
                    visual_file = f"kg_evaluation_visual_report{db_suffix}_{timestamp}.pdf"
                    evaluator.generate_visual_report(results, visual_file)
        
        print(f"\n✅ Evaluation completed successfully!")
        
        # Summary of generated files
        if args.text_report or args.visual_report or args.all_reports or args.output:
            print(f"\n📄 Generated Reports:")
            if args.output or args.all_reports:
                print(f"  • JSON Report: Detailed evaluation data")
            if args.text_report or args.all_reports:
                print(f"  • Text Report: Comprehensive analysis with recommendations")
            if args.visual_report or args.all_reports:
                print(f"  • Visual Report: Charts and graphs (PDF)")
        
    except Exception as e:
        print(f"❌ Error during evaluation: {e}")
        raise


if __name__ == "__main__":
    main()
