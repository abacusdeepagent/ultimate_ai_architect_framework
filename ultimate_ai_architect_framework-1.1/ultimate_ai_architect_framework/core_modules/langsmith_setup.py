"""
LangSmith Setup Module

This module provides functionality for setting up and configuring LangSmith
integration for tracing, evaluation, and monitoring of AI components.
"""

import logging
import os
from typing import Dict, Any, Optional, List

from ultimate_ai_architect_framework.core_modules.config_loader import ConfigLoader

class LangSmithSetup:
    """
    Sets up and configures LangSmith integration for the framework.
    
    Provides:
    - LangSmith client configuration
    - Tracing setup
    - Dataset management
    - Evaluation configuration
    """
    
    def __init__(self, framework_root: str):
        """
        Initialize a new LangSmithSetup instance.
        
        Args:
            framework_root: Path to the framework root directory
        """
        # Initialize logger
        self.logger = logging.getLogger("core.langsmith_setup")
        
        # Store framework root
        self.framework_root = framework_root
        
        # Load global configuration using ConfigLoader
        self.config_loader = ConfigLoader(framework_root)
        self.global_config = self.config_loader.load_global_config()
        
        # Initialize LangSmith client
        self.client = None
        self._initialize_client()
        
        self.logger.info("LangSmith Setup initialized")
    
    def _initialize_client(self) -> None:
        """
        Initialize LangSmith client if enabled and API key is available.
        
        This method:
        1. Checks if LangSmith is enabled in the config
        2. Gets the API key from the specified environment variable
        3. Sets up necessary environment variables for LangSmith
        4. Initializes the LangSmith client
        """
        try:
            # Get LangSmith configuration from global settings
            langsmith_config = self.global_config.get("langsmith", {})
            
            # Check if LangSmith is enabled
            if not langsmith_config.get("enabled", False):
                self.logger.info("LangSmith integration is disabled in configuration")
                return
            
            # Get the environment variable name for the API key
            api_key_env = langsmith_config.get("api_key_env", "LANGSMITH_API_KEY")
            
            # Get the API key from the environment
            api_key = os.environ.get(api_key_env)
            
            if not api_key:
                self.logger.warning(f"LangSmith API key not found in environment variable '{api_key_env}'. LangSmith integration disabled.")
                return
            
            # Set environment variables for LangSmith
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = api_key
            
            # Set project name from config or use fallback
            project_name = langsmith_config.get("project", "default-framework-project")
            os.environ["LANGCHAIN_PROJECT"] = project_name
            
            # Set endpoint if specified
            if "endpoint" in langsmith_config:
                os.environ["LANGCHAIN_ENDPOINT"] = langsmith_config["endpoint"]
            
            # Import and initialize LangSmith client
            try:
                from langsmith import Client
                self.client = Client()
                self.logger.info(f"LangSmith client initialized with project: {project_name}")
            except ImportError:
                self.logger.warning("LangSmith package not installed. Run 'pip install langsmith'.")
                return
            
        except Exception as e:
            self.logger.error(f"Failed to initialize LangSmith client: {e}")
            self.client = None
    
    def setup_tracing(self, project_name: Optional[str] = None) -> bool:
        """
        Set up LangSmith tracing for a project.
        
        Args:
            project_name: Name of the project to set up tracing for
            
        Returns:
            True if tracing was set up successfully, False otherwise
        """
        if not self.client:
            self.logger.warning("LangSmith client not initialized. Cannot set up tracing.")
            return False
        
        try:
            # Set project name for tracing if provided
            if project_name:
                os.environ["LANGCHAIN_PROJECT"] = project_name
                self.logger.info(f"LangSmith tracing enabled for project: {project_name}")
            else:
                self.logger.info("LangSmith tracing enabled with default project")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to set up LangSmith tracing: {e}")
            return False
    
    def create_dataset(self, dataset_name: str, description: str = None) -> Optional[dict]:
        """
        Create a new LangSmith dataset.
        
        Args:
            dataset_name: Name of the dataset to create
            description: Optional description of the dataset
            
        Returns:
            Dataset information dictionary if created successfully, None otherwise
        """
        if not self.client:
            self.logger.warning("LangSmith client not initialized. Cannot create dataset.")
            return None
        
        try:
            # Create dataset with the provided name and description
            dataset = self.client.create_dataset(
                dataset_name=dataset_name,
                description=description or ""
            )
            self.logger.info(f"Created LangSmith dataset: {dataset_name}")
            return dataset
        except Exception as e:
            if "already exists" in str(e).lower():
                self.logger.warning(f"Dataset '{dataset_name}' already exists")
                try:
                    # Try to get the existing dataset
                    datasets = self.client.list_datasets(dataset_name=dataset_name)
                    if datasets:
                        return datasets[0]
                except Exception as inner_e:
                    self.logger.error(f"Failed to retrieve existing dataset: {inner_e}")
            else:
                self.logger.error(f"Failed to create LangSmith dataset: {e}")
            return None
    
    def log_run(self, run_data: dict, dataset_name: str = None) -> Optional[str]:
        """
        Log a run to LangSmith and optionally add it to a dataset.
        
        Args:
            run_data: Dictionary containing run data
            dataset_name: Optional name of the dataset to add the run to
            
        Returns:
            Run ID if logged successfully, None otherwise
        """
        if not self.client:
            self.logger.warning("LangSmith client not initialized. Cannot log run.")
            return None
        
        try:
            # Create the run in LangSmith
            run = self.client.create_run(run_data)
            run_id = run.id
            
            # If dataset_name is provided, add the run to the dataset
            if dataset_name:
                # Get or create the dataset
                dataset = None
                try:
                    datasets = self.client.list_datasets(dataset_name=dataset_name)
                    if datasets:
                        dataset = datasets[0]
                    else:
                        dataset = self.create_dataset(dataset_name)
                except Exception as e:
                    self.logger.error(f"Failed to get or create dataset '{dataset_name}': {e}")
                
                # Add the run to the dataset if we have a valid dataset
                if dataset:
                    self.client.create_dataset_run(dataset_id=dataset.id, run_id=run_id)
                    self.logger.info(f"Added run {run_id} to dataset {dataset_name}")
            
            self.logger.info(f"Logged run with ID: {run_id}")
            return run_id
        except Exception as e:
            self.logger.error(f"Failed to log run to LangSmith: {e}")
            return None
    
    def get_runs(self, project_name: str = None, limit: int = 10) -> List[dict]:
        """
        Get runs from LangSmith for a specific project.
        
        Args:
            project_name: Optional name of the project to get runs for
            limit: Maximum number of runs to retrieve (default: 10)
            
        Returns:
            List of run dictionaries, empty list if no runs found or client not initialized
        """
        if not self.client:
            self.logger.warning("LangSmith client not initialized. Cannot get runs.")
            return []
        
        try:
            # Get runs for the specified project (or all projects if not specified)
            runs = self.client.list_runs(
                project_name=project_name,
                limit=limit
            )
            
            # Convert runs to dictionaries for easier handling
            run_list = [run.dict() for run in runs]
            
            self.logger.info(f"Retrieved {len(run_list)} runs" + 
                            (f" for project '{project_name}'" if project_name else ""))
            return run_list
        except Exception as e:
            self.logger.error(f"Failed to get runs from LangSmith: {e}")
            return []
