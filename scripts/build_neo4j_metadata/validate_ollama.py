#!/usr/bin/env python3
"""
Ollama Validation Script for Daemonium System

This script validates that Ollama is running, loads each configured model,
and tests that modeling functionality is working properly.

Uses centralized configuration from config/ollama_models.yaml

Author: Daemonium System
Version: 2.0.0
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# Add project root to Python path for imports
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))

from config.ollama_config import OllamaConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class OllamaValidator:
    """Comprehensive Ollama validation system"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the validator with configuration
        
        Args:
            config_path: Optional path to config file. If None, uses default.
        """
        self.config_loader = OllamaConfigLoader(config_path)
        self.server_url = self.config_loader.get_server_url()
        self.retry_config = self.config_loader.get_retry_config()
        self.model_loading_config = self.config_loader.get_model_loading_config()
        
        # Results tracking
        self.validation_results = {
            'server_status': False,
            'models_available': [],
            'models_missing': [],
            'models_functional': [],
            'models_failed': [],
            'test_results': {},
            'start_time': datetime.now(),
            'config_info': {
                'server_url': self.server_url,
                'config_path': str(self.config_loader.config_path)
            }
        }
    
    def check_ollama_server(self) -> bool:
        """Check if Ollama server is running and accessible
        
        Returns:
            bool: True if server is accessible, False otherwise
        """
        logger.info("Checking Ollama server status...")
        logger.info(f"  Server URL: {self.server_url}")
        logger.info(f"  Connection timeout: 10 seconds")
        
        start_time = time.time()
        try:
            tags_url = self.config_loader.get_endpoint_url('tags')
            logger.info(f"  Testing endpoint: {tags_url}")
            
            response = requests.get(
                tags_url, 
                timeout=10  # Use default connection timeout
            )
            
            response_time = time.time() - start_time
            logger.info(f"  Response time: {response_time:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get('models', []))
                logger.info(f"✓ Ollama server is running and accessible")
                logger.info(f"  Available models: {model_count}")
                self.validation_results['server_status'] = True
                self.validation_results['server_response_time'] = response_time
                return True
            else:
                logger.error(f"✗ Ollama server returned status code: {response.status_code}")
                logger.error(f"  Response: {response.text[:200]}...")
                return False
                
        except requests.exceptions.ConnectionError:
            logger.error(f"✗ Cannot connect to Ollama server at {self.server_url}")
            logger.error(f"  Connection time: {time.time() - start_time:.2f}s")
            return False
        except requests.exceptions.Timeout:
            logger.error(f"✗ Timeout connecting to Ollama server (10s)")
            return False
        except Exception as e:
            logger.error(f"✗ Error checking Ollama server: {e}")
            logger.error(f"  Connection time: {time.time() - start_time:.2f}s")
            return False
    
    def wait_for_model_loading(self, model_name: str, is_first_model: bool = False) -> bool:
        """Wait for model to load with progressive intervals."""
        if is_first_model:
            wait_time = self.model_loading_config.get('warmup_timeout', 120)
            logger.info(f"  Waiting for initial model warmup: {wait_time}s")
        else:
            wait_time = self.model_loading_config.get('max_wait', 90)
            logger.info(f"  Waiting for model loading: {wait_time}s")
        
        test_timeout = self.model_loading_config.get('test_timeout', 5)
        intervals = [5, 10, 15, 20, 30]  # Progressive wait intervals
        total_waited = 0
        
        for interval in intervals:
            if total_waited >= wait_time:
                break
                
            actual_wait = min(interval, wait_time - total_waited)
            logger.info(f"    Waiting {actual_wait}s for model to load...")
            time.sleep(actual_wait)
            total_waited += actual_wait
            
            # Quick test to see if model is responsive
            try:
                generate_url = self.config_loader.get_endpoint_url('generate')
                test_payload = {
                    "model": model_name,
                    "prompt": "test",
                    "stream": False,
                    "options": {"num_predict": 1}
                }
                
                response = requests.post(
                    generate_url,
                    json=test_payload,
                    timeout=test_timeout
                )
                
                if response.status_code == 200:
                    logger.info(f"    ✓ Model {model_name} is responsive after {total_waited}s")
                    return True
                    
            except Exception:
                # Model not ready yet, continue waiting
                pass
        
        logger.warning(f"  Model {model_name} may not be fully loaded after {total_waited}s")
        return True  # Continue with validation anyway
    
    def get_available_models(self) -> List[str]:
        """Get list of currently available Ollama models
        
        Returns:
            List[str]: List of available model names
        """
        try:
            tags_url = self.config_loader.get_endpoint_url('tags')
            response = requests.get(
                tags_url,
                timeout=10  # Use default connection timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                logger.info(f"Found {len(models)} available models")
                return models
            else:
                logger.error(f"Failed to get model list: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a model using ollama CLI
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Pulling model: {model_name}")
        
        try:
            # Get timeout for this model
            timeout = self.config_loader.get_timeout_for_model(model_name, 'general_kg')
            pull_timeout = max(timeout * 3, 300)  # At least 5 minutes for pulling
            
            logger.info(f"  Model timeout (config): {timeout}s")
            logger.info(f"  Pull timeout (calculated): {pull_timeout}s")
            logger.info(f"  Command: ollama pull {model_name}")
            
            start_time = time.time()
            result = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True,
                timeout=pull_timeout
            )
            
            pull_time = time.time() - start_time
            logger.info(f"  Pull time: {pull_time:.2f}s")
            
            if result.returncode == 0:
                logger.info(f"✓ Successfully pulled {model_name}")
                if result.stdout:
                    logger.info(f"  Output: {result.stdout.strip()[:200]}...")
                return True
            else:
                logger.error(f"✗ Failed to pull {model_name}: {result.stderr}")
                logger.error(f"  Return code: {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"✗ Timeout pulling {model_name} ({pull_timeout}s)")
            return False
        except FileNotFoundError:
            logger.error("✗ Ollama CLI not found. Please install Ollama first.")
            logger.error("  Make sure Ollama is installed and in your PATH")
            return False
        except Exception as e:
            logger.error(f"✗ Error pulling {model_name}: {e}")
            return False
    
    def test_model_generation(self, model_name: str) -> Tuple[bool, str]:
        """Test if a model can generate text
        
        Args:
            model_name: Name of the model to test
            
        Returns:
            Tuple[bool, str]: (success, response_text or error_message)
        """
        test_prompt = "What is philosophy? Answer in one sentence."
        
        try:
            timeout = self.config_loader.get_timeout_for_model(model_name, 'general_kg')
            generate_url = self.config_loader.get_endpoint_url('generate')
            
            logger.info(f"    Testing text generation...")
            logger.info(f"    Timeout: {timeout}s")
            logger.info(f"    Endpoint: {generate_url}")
            logger.info(f"    Prompt: {test_prompt[:50]}...")
            
            payload = {
                "model": model_name,
                "prompt": test_prompt,
                "stream": False
            }
            
            start_time = time.time()
            response = requests.post(
                generate_url,
                json=payload,
                timeout=timeout
            )
            
            response_time = time.time() - start_time
            logger.info(f"    Response time: {response_time:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '').strip()
                
                if response_text:
                    logger.info(f"    ✓ Generation successful")
                    logger.info(f"    Response length: {len(response_text)} characters")
                    logger.info(f"    Response preview: {response_text[:100]}...")
                    return True, response_text[:100] + "..." if len(response_text) > 100 else response_text
                else:
                    logger.error(f"    ✗ Empty response received")
                    return False, "Empty response"
            else:
                logger.error(f"    ✗ HTTP error: {response.status_code}")
                logger.error(f"    Response: {response.text[:200]}...")
                return False, f"HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            logger.error(f"    ✗ Request timeout after {timeout}s")
            return False, "Timeout"
        except Exception as e:
            logger.error(f"    ✗ Generation error: {e}")
            return False, str(e)
    
    def test_model_embeddings(self, model_name: str) -> Tuple[bool, str]:
        """Test if a model can generate embeddings
        
        Args:
            model_name: Name of the model to test
            
        Returns:
            Tuple[bool, str]: (success, embedding_info or error_message)
        """
        test_text = "Philosophy is the study of fundamental questions."
        
        try:
            timeout = self.config_loader.get_timeout_for_model(model_name, 'semantic_similarity')
            embeddings_url = self.config_loader.get_endpoint_url('embeddings')
            
            logger.info(f"    Testing embeddings generation...")
            logger.info(f"    Timeout: {timeout}s")
            logger.info(f"    Endpoint: {embeddings_url}")
            logger.info(f"    Text: {test_text[:50]}...")
            
            payload = {
                "model": model_name,
                "prompt": test_text
            }
            
            start_time = time.time()
            response = requests.post(
                embeddings_url,
                json=payload,
                timeout=timeout
            )
            
            response_time = time.time() - start_time
            logger.info(f"    Response time: {response_time:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                embedding = data.get('embedding', [])
                
                if embedding and len(embedding) > 0:
                    logger.info(f"    ✓ Embeddings successful")
                    logger.info(f"    Embedding dimension: {len(embedding)}")
                    logger.info(f"    Sample values: {embedding[:3]}...")
                    return True, f"Embedding dimension: {len(embedding)}"
                else:
                    logger.error(f"    ✗ Empty embedding received")
                    return False, "Empty embedding"
            else:
                logger.error(f"    ✗ HTTP error: {response.status_code}")
                logger.error(f"    Response: {response.text[:200]}...")
                return False, f"HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            logger.error(f"    ✗ Request timeout after {timeout}s")
            return False, "Timeout"
        except Exception as e:
            logger.error(f"    ✗ Embeddings error: {e}")
            return False, str(e)
    
    def validate_model(self, model_name: str, model_type: str) -> Dict:
        """Validate a single model comprehensively
        
        Args:
            model_name: Name of the model to validate
            model_type: Type of model (general_kg, semantic_similarity, concept_clustering)
            
        Returns:
            Dict: Validation results for the model
        """
        logger.info(f"\nValidating {model_name} ({model_type})...")
        
        result = {
            'model': model_name,
            'type': model_type,
            'available': False,
            'generation_test': {'success': False, 'result': ''},
            'embeddings_test': {'success': False, 'result': ''},
            'overall_status': 'FAILED'
        }
        
        # Check if model is available
        available_models = self.get_available_models()
        model_was_pulled = False
        
        if model_name in available_models:
            result['available'] = True
            logger.info(f"  ✓ {model_name} is available")
        else:
            logger.warning(f"  ⚠ {model_name} not found, attempting to pull...")
            if self.pull_model(model_name):
                result['available'] = True
                model_was_pulled = True
            else:
                logger.error(f"  ✗ Failed to pull {model_name}")
                return result
        
        # Wait for model loading after pulling or for first model
        is_first_model = not hasattr(self, '_models_tested')
        if not hasattr(self, '_models_tested'):
            self._models_tested = set()
        
        if model_was_pulled or model_name not in self._models_tested:
            logger.info(f"  Waiting for model {model_name} to load...")
            self.wait_for_model_loading(model_name, is_first_model and len(self._models_tested) == 0)
            self._models_tested.add(model_name)
        
        # Test generation capability
        gen_success, gen_result = self.test_model_generation(model_name)
        result['generation_test'] = {'success': gen_success, 'result': gen_result}
        
        # Test embeddings capability (for embedding models)
        if 'embed' in model_name.lower() or model_type == 'semantic_similarity':
            emb_success, emb_result = self.test_model_embeddings(model_name)
            result['embeddings_test'] = {'success': emb_success, 'result': emb_result}
        
        # Determine overall status
        if result['available'] and result['generation_test']['success']:
            if 'embed' in model_name.lower() or model_type == 'semantic_similarity':
                if result['embeddings_test']['success']:
                    result['overall_status'] = 'PASSED'
                else:
                    result['overall_status'] = 'PARTIAL'
            else:
                result['overall_status'] = 'PASSED'
        
        return result
    
    def run_validation(self) -> Dict:
        """Run comprehensive validation of all configured models
        
        Returns:
            Dict: Complete validation results
        """
        logger.info("Starting Ollama Validation for Daemonium System")
        logger.info("=" * 60)
        
        # Step 1: Check server status
        if not self.check_ollama_server():
            logger.error("Cannot proceed without Ollama server running")
            logger.info("\nTo start Ollama:")
            logger.info("  - Windows: Start Ollama from Start menu or run 'ollama serve'")
            logger.info("  - macOS/Linux: Run 'ollama serve' in terminal")
            return self.validation_results
        
        # Step 2: Validate models by task type with fallback logic
        task_types = ['general_kg', 'semantic_similarity', 'concept_clustering']
        validation_results = []
        task_results = {}  # Track which model passed for each task
        
        logger.info(f"\nValidating models for {len(task_types)} task types...")
        
        # Step 3: Validate each task type with fallback logic
        for task_idx, task_type in enumerate(task_types, 1):
            logger.info(f"\n[{task_idx}/{len(task_types)}] Validating {task_type} models...")
            
            # Get default model and alternatives
            default_model = self.config_loader.get_model_for_task(task_type)
            alternatives = self.config_loader.get_alternatives_for_task(task_type)
            
            # Create ordered list: default first, then alternatives
            models_to_test = [default_model] + alternatives
            task_passed = False
            
            logger.info(f"  Default: {default_model}")
            if alternatives:
                logger.info(f"  Alternatives: {', '.join(alternatives)}")
            
            # Test models in order until one passes
            for model_idx, model_name in enumerate(models_to_test):
                is_default = (model_idx == 0)
                model_label = "Default" if is_default else f"Alternative {model_idx}"
                
                logger.info(f"\n  Testing {model_label}: {model_name}")
                
                result = self.validate_model(model_name, task_type)
                validation_results.append(result)
                
                # Update tracking
                if result['overall_status'] == 'PASSED':
                    self.validation_results['models_functional'].append(model_name)
                    task_results[task_type] = model_name
                    task_passed = True
                    
                    if is_default:
                        logger.info(f"  ✓ Default model {model_name} passed - skipping alternatives")
                    else:
                        logger.info(f"  ✓ Alternative {model_name} passed - skipping remaining alternatives")
                    break  # Stop testing alternatives once one passes
                    
                elif result['overall_status'] == 'PARTIAL':
                    self.validation_results['models_functional'].append(model_name)
                    task_results[task_type] = model_name
                    task_passed = True
                    
                    if is_default:
                        logger.info(f"  ⚠ Default model {model_name} partially functional - skipping alternatives")
                    else:
                        logger.info(f"  ⚠ Alternative {model_name} partially functional - skipping remaining alternatives")
                    break  # Stop testing alternatives once one passes
                    
                else:
                    self.validation_results['models_failed'].append(model_name)
                    
                    if is_default:
                        logger.info(f"  ✗ Default model {model_name} failed - testing alternatives")
                    else:
                        logger.info(f"  ✗ Alternative {model_name} failed - trying next alternative")
                
                # Small delay between tests
                time.sleep(1)
            
            # Summary for this task type
            if task_passed:
                logger.info(f"\n  Task {task_type}: ✓ VALIDATED with {task_results[task_type]}")
            else:
                logger.info(f"\n  Task {task_type}: ✗ FAILED - no functional models found")
                task_results[task_type] = None
        
        # Step 4: Generate summary
        self.validation_results['test_results'] = validation_results
        self.validation_results['task_results'] = task_results
        self.validation_results['end_time'] = datetime.now()
        self.validation_results['total_duration'] = (self.validation_results['end_time'] - self.validation_results['start_time']).total_seconds()
        
        self._print_summary()
        self._generate_report()
        
        return self.validation_results
    
    def _print_summary(self):
        """Print validation summary"""
        logger.info("\n" + "=" * 60)
        logger.info("OLLAMA VALIDATION SUMMARY")
        logger.info("=" * 60)
        
        # Server status
        server_status = "✓ RUNNING" if self.validation_results['server_status'] else "✗ NOT RUNNING"
        logger.info(f"Server Status: {server_status}")
        
        # Model results
        passed_models = [r for r in self.validation_results['test_results'] if r['overall_status'] == 'PASSED']
        partial_models = [r for r in self.validation_results['test_results'] if r['overall_status'] == 'PARTIAL']
        failed_models = [r for r in self.validation_results['test_results'] if r['overall_status'] == 'FAILED']
        
        logger.info(f"\nModel Validation Results:")
        logger.info(f"  ✓ Fully Functional: {len(passed_models)} models")
        for model in passed_models:
            logger.info(f"    - {model['model']} ({model['type']})")
        
        if partial_models:
            logger.info(f"  ⚠ Partially Functional: {len(partial_models)} models")
            for model in partial_models:
                logger.info(f"    - {model['model']} ({model['type']}) - Generation only")
        
        if failed_models:
            logger.info(f"  ✗ Failed: {len(failed_models)} models")
            for model in failed_models:
                logger.info(f"    - {model['model']} ({model['type']})")
        
        # Task type assignments
        logger.info(f"\nTask Type Assignments:")
        task_results = self.validation_results.get('task_results', {})
        for task_type in ['general_kg', 'semantic_similarity', 'concept_clustering']:
            validated_model = task_results.get(task_type)
            if validated_model:
                logger.info(f"  ✓ {task_type}: {validated_model}")
            else:
                default_model = self.config_loader.get_model_for_task(task_type)
                logger.info(f"  ✗ {task_type}: {default_model} (FAILED - no functional model found)")
        
        # Overall status
        total_models = len(self.validation_results['test_results'])
        functional_models = len(passed_models) + len(partial_models)
        
        if functional_models == total_models:
            logger.info(f"\n🎉 ALL MODELS VALIDATED SUCCESSFULLY!")
        elif functional_models > 0:
            logger.info(f"\n⚠ PARTIAL SUCCESS: {functional_models}/{total_models} models functional")
        else:
            logger.info(f"\n❌ VALIDATION FAILED: No models are functional")
        
        logger.info(f"\nValidation complete. Ready for knowledge graph operations.")
    
    def _generate_report(self):
        """Generate comprehensive validation report"""
        try:
            # Create reports directory if it doesn't exist
            reports_dir = script_dir / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            # Generate timestamp for report filename
            timestamp = self.validation_results['start_time'].strftime('%Y%m%d_%H%M%S')
            report_filename = f"ollama_validation_{timestamp}.txt"
            report_path = reports_dir / report_filename
            
            logger.info(f"\nGenerating detailed report: {report_path}")
            
            with open(report_path, 'w', encoding='utf-8') as f:
                # Header
                f.write("=" * 80 + "\n")
                f.write("OLLAMA VALIDATION REPORT\n")
                f.write("=" * 80 + "\n\n")
                
                # Execution details
                f.write("EXECUTION DETAILS\n")
                f.write("-" * 40 + "\n")
                f.write(f"Start Time: {self.validation_results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"End Time: {self.validation_results['end_time'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Duration: {self.validation_results['total_duration']:.2f} seconds\n")
                f.write(f"Config Path: {self.validation_results['config_info']['config_path']}\n")
                f.write(f"Server URL: {self.validation_results['config_info']['server_url']}\n")
                
                # Server status
                f.write("\nSERVER STATUS\n")
                f.write("-" * 40 + "\n")
                server_status = "RUNNING" if self.validation_results['server_status'] else "NOT RUNNING"
                f.write(f"Ollama Server: {server_status}\n")
                if 'server_response_time' in self.validation_results:
                    f.write(f"Server Response Time: {self.validation_results['server_response_time']:.2f}s\n")
                
                # Task results summary
                f.write("\nTASK VALIDATION SUMMARY\n")
                f.write("-" * 40 + "\n")
                task_results = self.validation_results.get('task_results', {})
                for task_type in ['general_kg', 'semantic_similarity', 'concept_clustering']:
                    validated_model = task_results.get(task_type)
                    if validated_model:
                        f.write(f"✓ {task_type}: {validated_model}\n")
                    else:
                        default_model = self.config_loader.get_model_for_task(task_type)
                        f.write(f"✗ {task_type}: {default_model} (FAILED)\n")
                
                # Detailed model results
                f.write("\nDETAILED MODEL RESULTS\n")
                f.write("-" * 40 + "\n")
                
                passed_models = [r for r in self.validation_results['test_results'] if r['overall_status'] == 'PASSED']
                partial_models = [r for r in self.validation_results['test_results'] if r['overall_status'] == 'PARTIAL']
                failed_models = [r for r in self.validation_results['test_results'] if r['overall_status'] == 'FAILED']
                
                f.write(f"Fully Functional Models: {len(passed_models)}\n")
                for model in passed_models:
                    f.write(f"  ✓ {model['model']} ({model['type']})\n")
                    f.write(f"    - Generation: {model['generation_test']['result']}\n")
                    if model['embeddings_test']['success']:
                        f.write(f"    - Embeddings: {model['embeddings_test']['result']}\n")
                
                if partial_models:
                    f.write(f"\nPartially Functional Models: {len(partial_models)}\n")
                    for model in partial_models:
                        f.write(f"  ⚠ {model['model']} ({model['type']}) - Generation only\n")
                        f.write(f"    - Generation: {model['generation_test']['result']}\n")
                        f.write(f"    - Embeddings: {model['embeddings_test']['result']}\n")
                
                if failed_models:
                    f.write(f"\nFailed Models: {len(failed_models)}\n")
                    for model in failed_models:
                        f.write(f"  ✗ {model['model']} ({model['type']})\n")
                        f.write(f"    - Generation: {model['generation_test']['result']}\n")
                        if model['embeddings_test']['result']:
                            f.write(f"    - Embeddings: {model['embeddings_test']['result']}\n")
                
                # Configuration details
                f.write("\nCONFIGURATION DETAILS\n")
                f.write("-" * 40 + "\n")
                for task_type in ['general_kg', 'semantic_similarity', 'concept_clustering']:
                    default_model = self.config_loader.get_model_for_task(task_type)
                    alternatives = self.config_loader.get_alternatives_for_task(task_type)
                    timeout = self.config_loader.get_timeout_for_model(default_model, task_type)
                    
                    f.write(f"\n{task_type.upper()}:\n")
                    f.write(f"  Default Model: {default_model}\n")
                    f.write(f"  Timeout: {timeout}s\n")
                    if alternatives:
                        f.write(f"  Alternatives: {', '.join(alternatives)}\n")
                
                # Overall status
                f.write("\nOVERALL STATUS\n")
                f.write("-" * 40 + "\n")
                total_models = len(self.validation_results['test_results'])
                functional_models = len(passed_models) + len(partial_models)
                
                if functional_models == total_models:
                    f.write("🎉 ALL MODELS VALIDATED SUCCESSFULLY!\n")
                elif functional_models > 0:
                    f.write(f"⚠ PARTIAL SUCCESS: {functional_models}/{total_models} models functional\n")
                else:
                    f.write("❌ VALIDATION FAILED: No models are functional\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("Report generated by Ollama Validation Script v2.0.0\n")
                f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n")
            
            logger.info(f"✓ Report saved to: {report_path}")
            
            # Also generate JSON report for programmatic access
            json_filename = f"ollama_validation_{timestamp}.json"
            json_path = reports_dir / json_filename
            
            # Prepare JSON-serializable results
            json_results = {
                'start_time': self.validation_results['start_time'].isoformat(),
                'end_time': self.validation_results['end_time'].isoformat(),
                'total_duration': self.validation_results['total_duration'],
                'server_status': self.validation_results['server_status'],
                'config_info': self.validation_results['config_info'],
                'task_results': self.validation_results['task_results'],
                'test_results': self.validation_results['test_results'],
                'summary': {
                    'total_models_tested': len(self.validation_results['test_results']),
                    'functional_models': len(self.validation_results['models_functional']),
                    'failed_models': len(self.validation_results['models_failed']),
                    'success_rate': len(self.validation_results['models_functional']) / len(self.validation_results['test_results']) * 100 if self.validation_results['test_results'] else 0
                }
            }
            
            if 'server_response_time' in self.validation_results:
                json_results['server_response_time'] = self.validation_results['server_response_time']
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ JSON report saved to: {json_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")

def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate Ollama installation and configured models"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to ollama_models.yaml config file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        validator = OllamaValidator(args.config)
        results = validator.run_validation()
        
        # Exit with appropriate code
        functional_count = len([r for r in results['test_results'] if r['overall_status'] in ['PASSED', 'PARTIAL']])
        total_count = len(results['test_results'])
        
        if functional_count == total_count and results['server_status']:
            sys.exit(0)  # Success
        elif functional_count > 0:
            sys.exit(1)  # Partial success
        else:
            sys.exit(2)  # Failure
            
    except KeyboardInterrupt:
        logger.info("\nValidation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()
