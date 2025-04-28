"""
Configuration Loader Module

This module provides the ConfigLoader class for loading and managing YAML
configuration files throughout the framework.
"""

import logging
import os
import re
import yaml
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger("core.config_loader")

class ConfigLoader:
    """
    Loads and manages YAML configuration files for the framework and projects.

    Handles:
    - Global framework configuration (global_settings.yaml)
    - Base agent profiles (base_agent_profiles.yaml)
    - Tool registry (tool_registry.yaml)
    - Project-specific settings (projects/<project_name>/configs/project_settings.yaml)
    - Project-specific agent config (projects/<project_name>/configs/agent_config.yaml)
    - Caching loaded configurations
    - Environment variable expansion for values like ${VAR_NAME}
    - Converting relative paths to absolute paths
    - Saving configurations back to files
    - Merging global and project configurations
    """

    def __init__(self, framework_root: str):
        """
        Initialize a new ConfigLoader instance.

        Args:
            framework_root: Absolute path to the framework root directory.
        """
        self.framework_root = Path(os.path.expanduser(framework_root)).resolve()  # Ensure absolute path
        self.configs_dir = self.framework_root / "configs"
        self.projects_dir = self.framework_root / "projects"

        # Cache for loaded configurations
        self.config_cache: Dict[str, Dict[str, Any]] = {}

        logger.info(f"Config Loader initialized with root: {self.framework_root}")

    def _expand_env_vars(self, value: Any) -> Any:
        """
        Recursively expand environment variables in string values.
        
        Args:
            value: The value to process (can be a string, dict, list, or other type)
            
        Returns:
            The processed value with environment variables expanded
        """
        if isinstance(value, str):
            # Replace ${VAR_NAME} with the environment variable value
            return os.path.expandvars(value)
        elif isinstance(value, dict):
            return {k: self._expand_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._expand_env_vars(item) for item in value]
        else:
            return value

    def _absolutize_paths(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert relative paths in the 'paths' section to absolute paths.
        
        Args:
            config: The configuration dictionary containing a 'paths' key
            
        Returns:
            The configuration with absolute paths
        """
        if not isinstance(config, dict):
            return config
            
        paths_section = config.get("paths", {})
        if not paths_section or not isinstance(paths_section, dict):
            return config
            
        # Create a copy to avoid modifying the original
        result = config.copy()
        result["paths"] = paths_section.copy()
        
        # Convert relative paths to absolute
        for key, path in result["paths"].items():
            if isinstance(path, str) and not os.path.isabs(path):
                result["paths"][key] = str(self.framework_root / path)
                
        return result

    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Safely loads a single YAML file with environment variable expansion.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Dictionary containing the loaded YAML data, or empty dict if loading fails
        """
        if not file_path.is_file():
            logger.warning(f"Configuration file not found: {file_path}")
            return {}
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
                
            # Expand environment variables in the loaded data
            config_data = self._expand_env_vars(config_data)
            return config_data
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {file_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {}

    def _get_config(self, config_key: str, file_path: Path, process_global: bool = False) -> Dict[str, Any]:
        """
        Loads config from cache or file with optional global config processing.
        
        Args:
            config_key: Key for the config cache
            file_path: Path to the config file
            process_global: Whether to process global config (convert paths to absolute)
            
        Returns:
            The loaded configuration dictionary
        """
        if config_key in self.config_cache:
            return self.config_cache[config_key]

        config_data = self._load_yaml_file(file_path)
        
        # Process global config if needed (convert paths to absolute)
        if process_global:
            config_data = self._absolutize_paths(config_data)
            
        self.config_cache[config_key] = config_data
        return config_data

    def load_global_config(self) -> Dict[str, Any]:
        """
        Loads global_settings.yaml with path absolutization.
        
        Returns:
            The global configuration dictionary
        """
        file_path = self.configs_dir / "global_settings.yaml"
        return self._get_config("global_config", file_path, process_global=True)

    def load_agent_profiles(self) -> Dict[str, Any]:
        """
        Loads base_agent_profiles.yaml.
        
        Returns:
            The agent profiles configuration dictionary
        """
        file_path = self.configs_dir / "base_agent_profiles.yaml"
        return self._get_config("agent_profiles", file_path)

    def load_tool_registry(self) -> Dict[str, Any]:
        """
        Loads tool_registry.yaml.
        
        Returns:
            The tool registry configuration dictionary
        """
        file_path = self.configs_dir / "tool_registry.yaml"
        return self._get_config("tool_registry", file_path)

    def load_project_config(self, project_name: str) -> Dict[str, Any]:
        """
        Loads project_settings.yaml for a specific project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            The project configuration dictionary
        """
        if not project_name:
            logger.error("Invalid project name provided")
            return {}
            
        cache_key = f"project_config_{project_name}"
        file_path = self.projects_dir / project_name / "configs" / "project_settings.yaml"
        return self._get_config(cache_key, file_path)

    def load_project_agent_config(self, project_name: str) -> Dict[str, Any]:
        """
        Loads agent_config.yaml for a specific project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            The project agent configuration dictionary
        """
        if not project_name:
            logger.error("Invalid project name provided")
            return {}
            
        cache_key = f"project_agent_config_{project_name}"
        file_path = self.projects_dir / project_name / "configs" / "agent_config.yaml"
        return self._get_config(cache_key, file_path)

    def _get_config_path(self, config_type: str, project_name: Optional[str] = None) -> Optional[Path]:
        """
        Determines the file path for a given config type.
        
        Args:
            config_type: Type of configuration ('global', 'agent_profiles', 'tool_registry', 'project', 'project_agent')
            project_name: Required if config_type is 'project' or 'project_agent'
            
        Returns:
            Path to the configuration file, or None if invalid
        """
        if config_type == "global":
            return self.configs_dir / "global_settings.yaml"
        elif config_type == "agent_profiles":
            return self.configs_dir / "base_agent_profiles.yaml"
        elif config_type == "tool_registry":
            return self.configs_dir / "tool_registry.yaml"
        elif config_type == "project":
            if not project_name:
                logger.error("Project name is required for project configuration")
                return None
            return self.projects_dir / project_name / "configs" / "project_settings.yaml"
        elif config_type == "project_agent":
            if not project_name:
                logger.error("Project name is required for project agent configuration")
                return None
            return self.projects_dir / project_name / "configs" / "agent_config.yaml"
        else:
            logger.error(f"Unknown configuration type: {config_type}")
            return None

    def save_config(self, config_type: str, config_data: Dict[str, Any], project_name: Optional[str] = None) -> bool:
        """
        Save configuration data back to its corresponding YAML file.

        Args:
            config_type: Type of configuration ('global', 'agent_profiles', 'tool_registry', 'project', 'project_agent')
            config_data: The configuration dictionary to save
            project_name: Required if config_type is 'project' or 'project_agent'

        Returns:
            True if saving was successful, False otherwise
        """
        config_path = self._get_config_path(config_type, project_name)
        if not config_path:
            return False  # Error already logged by _get_config_path

        try:
            # Ensure the directory exists before writing
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

            # Update cache after successful save
            cache_key = config_type
            if project_name:
                cache_key = f"{config_type}_{project_name}" if config_type.startswith("project") else config_type

            # Special mapping for project types
            if config_type == "project": 
                cache_key = f"project_config_{project_name}"
            if config_type == "project_agent": 
                cache_key = f"project_agent_config_{project_name}"

            self.config_cache[cache_key] = config_data
            logger.info(f"Successfully saved {config_type} configuration to {config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save {config_type} configuration to {config_path}: {e}")
            return False

    def merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge two configurations, with override_config taking precedence.

        Args:
            base_config: Base configuration dictionary
            override_config: Configuration dictionary to override base with

        Returns:
            A new dictionary representing the merged configuration
        """
        merged = base_config.copy()  # Start with a copy of the base

        for key, value in override_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # If both key exist and are dicts, merge recursively
                merged[key] = self.merge_configs(merged[key], value)
            else:
                # Otherwise, override or add the key/value
                merged[key] = value
        return merged

    def get_effective_config(self, project_name: str) -> Dict[str, Any]:
        """
        Get the effective configuration for a project by merging all relevant configurations.
        
        This combines:
        1. Global settings
        2. Agent profiles
        3. Tool registry
        4. Project-specific settings
        5. Project-specific agent config
        
        The later configs override earlier ones in case of conflicts.

        Args:
            project_name: Name of the project

        Returns:
            The effective configuration dictionary for the project
        """
        # Load all configuration components
        global_config = self.load_global_config()
        agent_profiles = self.load_agent_profiles()
        tool_registry = self.load_tool_registry()
        project_config = self.load_project_config(project_name)
        project_agent_config = self.load_project_agent_config(project_name)
        
        # Merge global configurations
        global_merged = self.merge_configs(global_config, agent_profiles)
        global_merged = self.merge_configs(global_merged, tool_registry)
        
        # Merge project configurations
        project_merged = self.merge_configs(project_config, project_agent_config)
        
        # Merge global and project configurations
        effective_config = self.merge_configs(global_merged, project_merged)
        
        return effective_config

# Example usage (for testing purposes)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # Assume framework root is the parent directory of core_modules
    script_dir = os.path.dirname(os.path.abspath(__file__))
    framework_root_dir = os.path.dirname(script_dir)

    print(f"Testing ConfigLoader with framework root: {framework_root_dir}")

    # Ensure dummy files exist for testing
    configs_path = Path(framework_root_dir) / "configs"
    projects_path = Path(framework_root_dir) / "projects" / "test_project" / "configs"
    configs_path.mkdir(parents=True, exist_ok=True)
    projects_path.mkdir(parents=True, exist_ok=True)

    if not (configs_path / "global_settings.yaml").exists():
        print("Creating dummy global_settings.yaml")
        with open(configs_path / "global_settings.yaml", "w") as f:
            yaml.dump({
                "version": "1.0.0", 
                "logging": {"level": "INFO"}, 
                "paths": {"projects_dir": "projects/"},
                "services": {"openai": {"api_key": "${OPENAI_API_KEY}"}}
            }, f)

    if not (projects_path / "project_settings.yaml").exists():
        print("Creating dummy project_settings.yaml for test_project")
        with open(projects_path / "project_settings.yaml", "w") as f:
            yaml.dump({"name": "test_project", "version": "0.1.0", "logging": {"level": "DEBUG"}}, f)  # Override logging level

    loader = ConfigLoader(framework_root=str(framework_root_dir))

    print("\n--- Loading Tests ---")
    global_cfg = loader.load_global_config()
    print(f"Global Config Loaded: {'Yes' if global_cfg else 'No'}")
    print(f"Global Config Content: {global_cfg}")
    
    # Test environment variable expansion
    if "services" in global_cfg and "openai" in global_cfg["services"]:
        api_key = global_cfg["services"]["openai"]["api_key"]
        print(f"OpenAI API Key (should be expanded): {api_key}")
    
    # Test path absolutization
    if "paths" in global_cfg:
        projects_dir = global_cfg["paths"].get("projects_dir")
        print(f"Projects Directory (should be absolute): {projects_dir}")
        print(f"Is absolute path: {os.path.isabs(projects_dir)}")

    project_cfg = loader.load_project_config("test_project")
    print(f"Project Config (test_project) Loaded: {'Yes' if project_cfg else 'No'}")
    print(f"Project Config Content: {project_cfg}")

    print("\n--- Merging Test ---")
    effective_cfg = loader.get_effective_config("test_project")
    print(f"Effective Config (test_project) Generated: {'Yes' if effective_cfg else 'No'}")
    print(f"Effective Config Logging Level (should be DEBUG): {effective_cfg.get('logging', {}).get('level')}")
    print(f"Effective Config Global Version (should be 1.0.0): {effective_cfg.get('version')}")

    print("\n--- Saving Test ---")
    project_cfg_before_save = loader.load_project_config("test_project")
    project_cfg_before_save['description'] = 'Test description added by save test'
    save_success = loader.save_config("project", project_cfg_before_save, "test_project")
    print(f"Saving Project Config Succeeded: {save_success}")
    # Clear cache to force reload
    loader.config_cache.pop("project_config_test_project", None)
    project_cfg_after_save = loader.load_project_config("test_project")
    print(f"Description after save: {project_cfg_after_save.get('description')}")
