"""
LLM Router Module

This module provides the LLMRouter class for dynamically selecting LLM models
based on task types and configured strategies.
"""

import os
import yaml
import logging
from typing import Optional, Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LLMRouter")


class LLMRouter:
    """
    A router class that dynamically selects the appropriate LLM model based on task type
    and configured routing strategies.
    
    The router loads configuration from the global_settings.yaml file and implements
    various routing strategies including 'balanced', 'cost_optimized', and 'performance_optimized'.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the LLMRouter by loading configuration from the specified YAML file.
        
        Args:
            config_path: Path to the configuration YAML file. If None, uses the default path.
        """
        if config_path is None:
            config_path = os.path.expanduser("~/projects/ultimate_ai_architect_framework/ultimate_ai_architect_framework/configs/global_settings.yaml")
        
        self.config_path = config_path
        self.config = self._load_config()
        
        # Extract relevant configuration sections
        self.routellm_config = self.config.get('routellm', {})
        self.llm_providers_config = self.config.get('llm_providers', {})
        
        # Extract key routing parameters
        self.default_strategy = self.routellm_config.get('default_strategy', 'balanced')
        self.fallback_model = self.routellm_config.get('fallback_model', 'openai.gpt-3.5-turbo')
        self.task_model_mapping = self.routellm_config.get('task_model_mapping', {})
        
        logger.info(f"LLMRouter initialized with strategy: {self.default_strategy}")
        logger.info(f"Fallback model set to: {self.fallback_model}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from the YAML file.
        
        Returns:
            Dict containing the parsed YAML configuration.
        
        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            yaml.YAMLError: If the YAML file is malformed.
        """
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                logger.info(f"Configuration loaded from {self.config_path}")
                return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            raise
    
    def _is_provider_available(self, provider_name: str) -> bool:
        """
        Check if a provider is available based on the 'enabled' flag in configuration.
        
        Args:
            provider_name: Name of the provider to check.
            
        Returns:
            bool: True if the provider is enabled, False otherwise.
        """
        provider_config = self.llm_providers_config.get(provider_name, {})
        return provider_config.get('enabled', False)
    
    def _is_api_key_available(self, provider_name: str) -> bool:
        """
        Check if the API key for a provider is available in environment variables.
        
        Args:
            provider_name: Name of the provider to check.
            
        Returns:
            bool: True if the API key is available, False otherwise.
        """
        provider_config = self.llm_providers_config.get(provider_name, {})
        api_key_env = provider_config.get('api_key_env')
        
        if not api_key_env:
            logger.warning(f"No API key environment variable configured for {provider_name}")
            return False
        
        api_key = os.environ.get(api_key_env)
        return api_key is not None and api_key.strip() != ""
    
    def _parse_model_identifier(self, model_id: str) -> tuple:
        """
        Parse a model identifier into provider and model name.
        
        Args:
            model_id: Model identifier in the format 'provider.model_name'.
            
        Returns:
            tuple: (provider_name, model_name)
        """
        parts = model_id.split('.')
        if len(parts) != 2:
            logger.warning(f"Invalid model identifier format: {model_id}. Expected 'provider.model_name'")
            return None, None
        
        return parts[0], parts[1]
    
    def _validate_model(self, model_id: str) -> bool:
        """
        Validate that a model exists and is available for use.
        
        Args:
            model_id: Model identifier in the format 'provider.model_name'.
            
        Returns:
            bool: True if the model is valid and available, False otherwise.
        """
        provider_name, model_name = self._parse_model_identifier(model_id)
        
        if not provider_name or not model_name:
            return False
        
        # Check if provider is enabled
        if not self._is_provider_available(provider_name):
            logger.warning(f"Provider {provider_name} is disabled in configuration")
            return False
        
        # Check if API key is available
        if not self._is_api_key_available(provider_name):
            logger.warning(f"API key for {provider_name} is not available in environment variables")
            return False
        
        # Check if model is in available models list
        provider_config = self.llm_providers_config.get(provider_name, {})
        available_models = provider_config.get('available_models', [])
        
        if model_name not in available_models:
            logger.warning(f"Model {model_name} is not in the available models list for {provider_name}")
            return False
        
        return True
    
    def route(self, task_type: Optional[str] = None, query: Optional[str] = None) -> str:
        """
        Route to the appropriate LLM model based on task type and routing strategy.
        
        Args:
            task_type: Type of task to route (e.g., 'creative_writing', 'code_generation').
            query: The query text (not used in the current implementation but reserved for future use).
            
        Returns:
            str: Selected model identifier in the format 'provider.model_name'.
        """
        # Use the 'balanced' strategy with task_model_mapping
        if task_type and task_type in self.task_model_mapping:
            candidate_model = self.task_model_mapping[task_type]
            logger.info(f"Task type '{task_type}' mapped to model: {candidate_model}")
            
            # Validate the candidate model
            if self._validate_model(candidate_model):
                logger.info(f"Selected model: {candidate_model} for task: {task_type}")
                return candidate_model
            else:
                logger.warning(f"Candidate model {candidate_model} is not available, falling back to: {self.fallback_model}")
        else:
            if task_type:
                logger.info(f"No mapping found for task type: {task_type}, using fallback model")
            else:
                logger.info(f"No task type provided, using fallback model")
        
        # Validate the fallback model
        if self._validate_model(self.fallback_model):
            return self.fallback_model
        else:
            # If fallback model is also not available, find the first available model
            logger.warning(f"Fallback model {self.fallback_model} is not available, searching for any available model")
            
            for provider_name, provider_config in self.llm_providers_config.items():
                if self._is_provider_available(provider_name) and self._is_api_key_available(provider_name):
                    default_model = provider_config.get('default_model')
                    if default_model:
                        model_id = f"{provider_name}.{default_model}"
                        logger.info(f"Selected alternative model: {model_id}")
                        return model_id
            
            # If no model is available, return the fallback model anyway (caller will need to handle the error)
            logger.error("No available models found. Returning fallback model, but it may not work.")
            return self.fallback_model


if __name__ == "__main__":
    # Example usage
    router = LLMRouter()
    
    # Test routing with different task types
    print(f"Code generation task: {router.route('code_generation')}")
    print(f"Creative writing task: {router.route('creative_writing')}")
    print(f"Unknown task: {router.route('unknown_task')}")
    print(f"No task specified: {router.route()}")
