#!/usr/bin/env python3
"""
Ollama Configuration Loader for Daemonium System

This module provides centralized configuration loading for Ollama models and timeouts
across all scripts in the Daemonium system.

Author: Daemonium System
Version: 1.0.0
"""

import yaml
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class ModelConfig:
    """Configuration for a specific model type"""
    default: str
    alternatives: List[str]
    description: str

@dataclass
class TimeoutConfig:
    """Timeout configuration for models and operations"""
    model_specific: Dict[str, int]
    task_defaults: Dict[str, int]
    retry: Dict[str, Any]
    model_loading: Dict[str, int]

@dataclass
class ServerConfig:
    """Ollama server configuration"""
    url: str
    endpoints: Dict[str, str]
    connection_timeout: int
    read_timeout: int

class OllamaConfigLoader:
    """Centralized configuration loader for Ollama models and settings"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration loader
        
        Args:
            config_path: Optional path to config file. If None, uses default location.
        """
        self.logger = logging.getLogger(__name__)
        
        # Determine config file path
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default to config/ollama_models.yaml relative to this file
            script_dir = Path(__file__).parent
            self.config_path = script_dir / "ollama_models.yaml"
        
        # Load configuration
        self.config = self._load_config()
        
        # Parse configuration sections
        self.models = self._parse_models()
        self.timeouts = self._parse_timeouts()
        self.server = self._parse_server()
        self.fallbacks = self.config.get('fallbacks', {})
        self.performance = self.config.get('performance', {})
        
    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.logger.info(f"Loaded Ollama configuration from: {self.config_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load config from {self.config_path}: {e}")
            return self._get_default_config()
    
    def _parse_models(self) -> Dict[str, ModelConfig]:
        """Parse model configurations"""
        models_config = self.config.get('models', {})
        models = {}
        
        for task_type, config in models_config.items():
            models[task_type] = ModelConfig(
                default=config.get('default', ''),
                alternatives=config.get('alternatives', []),
                description=config.get('description', '')
            )
        
        return models
    
    def _parse_timeouts(self) -> TimeoutConfig:
        """Parse timeout configurations"""
        timeout_config = self.config.get('timeouts', {})
        
        return TimeoutConfig(
            model_specific=timeout_config.get('model_specific', {}),
            task_defaults=timeout_config.get('task_defaults', {}),
            retry=timeout_config.get('retry', {}),
            model_loading=timeout_config.get('model_loading', {})
        )
    
    def _parse_server(self) -> ServerConfig:
        """Parse server configurations"""
        server_config = self.config.get('server', {})
        
        return ServerConfig(
            url=server_config.get('url', 'http://localhost:11434'),
            endpoints=server_config.get('endpoints', {}),
            connection_timeout=server_config.get('connection_timeout', 10),
            read_timeout=server_config.get('read_timeout', 300)
        )
    
    def get_model_for_task(self, task_type: str, override: Optional[str] = None) -> str:
        """Get the model to use for a specific task type
        
        Args:
            task_type: Type of task (general_kg, semantic_similarity, concept_clustering)
            override: Optional model override from CLI or environment
            
        Returns:
            Model name to use
        """
        # Check for override first
        if override:
            return override
        
        # Check environment variables
        if self.config.get('environment_overrides', {}).get('enabled', True):
            env_var = f"{self.config['environment_overrides']['prefix']}{task_type.upper()}"
            env_model = os.getenv(env_var)
            if env_model:
                self.logger.info(f"Using environment override for {task_type}: {env_model}")
                return env_model
        
        # Use configured default
        if task_type in self.models:
            return self.models[task_type].default
        
        # Fallback
        self.logger.warning(f"No model configured for task type: {task_type}")
        return "llama3.2:latest"  # Safe fallback
    
    def get_alternatives_for_task(self, task_type: str) -> List[str]:
        """Get alternative models for a specific task type
        
        Args:
            task_type: Type of task (general_kg, semantic_similarity, concept_clustering)
            
        Returns:
            List of alternative model names
        """
        if task_type in self.models:
            return self.models[task_type].alternatives
        
        # Fallback
        self.logger.warning(f"No alternatives configured for task type: {task_type}")
        return []
    
    def get_timeout_for_model(self, model_name: str, task_type: Optional[str] = None) -> int:
        """Get timeout for a specific model
        
        Args:
            model_name: Name of the model
            task_type: Optional task type for fallback timeout
            
        Returns:
            Timeout in seconds
        """
        # Check model-specific timeout first
        if model_name in self.timeouts.model_specific:
            return self.timeouts.model_specific[model_name]
        
        # Check task-type default
        if task_type and task_type in self.timeouts.task_defaults:
            return self.timeouts.task_defaults[task_type]
        
        # Global fallback
        return 60
    
    def get_retry_config(self) -> Dict[str, Any]:
        """Get retry configuration"""
        return self.timeouts.retry
    
    def get_model_loading_config(self) -> Dict[str, int]:
        """Get model loading configuration"""
        return self.timeouts.model_loading
    
    def get_fallback_models(self, task_type: str) -> List[str]:
        """Get fallback models for a task type
        
        Args:
            task_type: Type of task
            
        Returns:
            List of fallback model names
        """
        fallback_key = f"{task_type}_fallbacks"
        return self.fallbacks.get(fallback_key, [])
    
    def get_server_url(self) -> str:
        """Get Ollama server URL"""
        return self.server.url
    
    def get_endpoint_url(self, endpoint_name: str) -> str:
        """Get full URL for a specific endpoint
        
        Args:
            endpoint_name: Name of endpoint (generate, embeddings, tags)
            
        Returns:
            Full URL for the endpoint
        """
        endpoint_path = self.server.endpoints.get(endpoint_name, f"/api/{endpoint_name}")
        return f"{self.server.url}{endpoint_path}"
    
    def should_warmup_on_startup(self) -> bool:
        """Check if models should be warmed up on startup"""
        return self.performance.get('warmup_on_startup', True)
    
    def should_warmup_all_models(self) -> bool:
        """Check if all models should be warmed up (vs just assigned models)"""
        return self.performance.get('warmup_all_models', False)
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get caching configuration"""
        return {
            'enabled': self.performance.get('enable_embedding_cache', True),
            'max_size': self.performance.get('max_cache_size', 10000),
            'clear_threshold': self.performance.get('clear_cache_threshold', 8000)
        }
    
    def get_batch_config(self) -> Dict[str, Any]:
        """Get batch processing configuration"""
        return {
            'max_size': self.performance.get('max_batch_size', 10),
            'delay': self.performance.get('batch_delay', 1)
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file loading fails"""
        self.logger.warning("Using default configuration due to config file loading failure")
        
        return {
            'models': {
                'general_kg': {
                    'default': 'deepseek-r1:latest',
                    'alternatives': ['llama3.1:latest', 'mistral:latest'],
                    'description': 'General knowledge graph tasks'
                },
                'semantic_similarity': {
                    'default': 'granite-embedding:278m',
                    'alternatives': ['all-minilm:latest', 'nomic-embed-text:latest'],
                    'description': 'Semantic similarity tasks'
                },
                'concept_clustering': {
                    'default': 'llama3.2:latest',
                    'alternatives': ['llama3.1:latest', 'mistral:latest'],
                    'description': 'Concept clustering tasks'
                }
            },
            'timeouts': {
                'model_specific': {
                    'deepseek-r1:latest': 120,
                    'llama3.2:latest': 60,
                    'granite-embedding:278m': 60
                },
                'task_defaults': {
                    'general_kg': 90,
                    'semantic_similarity': 45,
                    'concept_clustering': 60
                },
                'retry': {
                    'max_attempts': 3,
                    'base_delay': 2,
                    'backoff_multiplier': 2
                },
                'model_loading': {
                    'max_wait': 90,
                    'test_timeout': 5,
                    'warmup_timeout': 120
                }
            },
            'server': {
                'url': 'http://localhost:11434',
                'endpoints': {
                    'generate': '/api/generate',
                    'embeddings': '/api/embeddings',
                    'tags': '/api/tags'
                },
                'connection_timeout': 10,
                'read_timeout': 300
            },
            'performance': {
                'warmup_on_startup': True,
                'warmup_all_models': False,
                'enable_embedding_cache': True,
                'max_cache_size': 10000
            }
        }

# Global configuration instance
_config_instance = None

def get_ollama_config(config_path: Optional[str] = None) -> OllamaConfigLoader:
    """Get the global Ollama configuration instance
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        OllamaConfigLoader instance
    """
    global _config_instance
    
    if _config_instance is None or config_path:
        _config_instance = OllamaConfigLoader(config_path)
    
    return _config_instance
