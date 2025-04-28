"""
Tool Handler Module

This module provides functionality for registering, managing, and executing
tools that can be used by agents in the framework.
"""

import logging
import importlib
from typing import Dict, List, Any, Optional, Callable
import os
import yaml
import inspect

# Import ConfigLoader
from ultimate_ai_architect_framework.core_modules.config_loader import ConfigLoader

class ToolHandler:
    """
    Manages tools that can be used by agents in the framework.
    
    Handles:
    - Tool registration
    - Tool discovery
    - Tool execution
    - Tool permissions
    """
    
    def __init__(self, framework_root: str):
        """
        Initialize a new ToolHandler instance.
        
        Args:
            framework_root: Path to the framework root directory
        """
        self.framework_root = framework_root
        self.logger = logging.getLogger("core.tool_handler")
        
        # Dictionary of registered tools
        self.tools = {}
        
        # Initialize ConfigLoader
        self.config_loader = ConfigLoader(framework_root)
        
        # Load tool registry
        self._load_tool_registry()
        
        self.logger.info("Tool Handler initialized")
    
    def _load_tool_registry(self) -> None:
        """Load tools from the tool registry configuration."""
        try:
            # Use ConfigLoader to load the tool registry
            registry = self.config_loader.load_tool_registry()
            
            # Log the loaded registry data
            self.logger.info(f"Loaded tool registry: {registry}")
            
            # Register each tool from the registry
            if registry and 'tools' in registry:
                for tool_id, tool_config in registry['tools'].items():
                    self.logger.debug(f"Registering tool {tool_id} from registry")
                    implementation = tool_config.get('implementation', {})
                    # Create a config that matches what register_tool_from_config expects
                    config_for_registration = {
                        "module": implementation.get('module'),
                        "class": implementation.get('class'),
                        "name": tool_config.get('name', tool_id),
                        "description": tool_config.get('description', ''),
                        "config": tool_config.get('config', {})
                    }
                    self.register_tool_from_config(tool_id, config_for_registration)
            else:
                self.logger.warning("No tools found in registry or registry format is incorrect")
            
        except Exception as e:
            self.logger.error(f"Failed to load tool registry: {e}")
    
    def register_tool_from_config(self, tool_id: str, tool_config: Dict[str, Any]) -> bool:
        """
        Register a tool from configuration.
        
        Args:
            tool_id: Unique identifier for the tool
            tool_config: Tool configuration
            
        Returns:
            True if tool was registered successfully, False otherwise
        """
        try:
            # Extract module and class information
            module_path = tool_config.get("module")
            class_name = tool_config.get("class")
            
            if not module_path or not class_name:
                self.logger.error(f"Missing module or class for tool {tool_id}")
                return False
                
            # Import module
            module = importlib.import_module(module_path)
            
            # Get class
            tool_class = getattr(module, class_name)
            
            # Create instance
            tool_instance = tool_class()
            
            # Register tool
            self.tools[tool_id] = {
                "id": tool_id,
                "name": tool_config.get("name", tool_id),
                "description": tool_config.get("description", ""),
                "instance": tool_instance,
                "config": tool_config
            }
            
            self.logger.info(f"Registered tool: {tool_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register tool {tool_id}: {e}")
            return False
    
    def register_tool(self, tool_id: str, tool_instance: Any, name: str = "", description: str = "") -> bool:
        """
        Register a tool instance directly.
        
        Args:
            tool_id: Unique identifier for the tool
            tool_instance: Instance of the tool
            name: Display name for the tool
            description: Description of the tool
            
        Returns:
            True if tool was registered successfully, False otherwise
        """
        try:
            self.tools[tool_id] = {
                "id": tool_id,
                "name": name or tool_id,
                "description": description,
                "instance": tool_instance,
                "config": {}
            }
            
            self.logger.info(f"Registered tool: {tool_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register tool {tool_id}: {e}")
            return False
    
    def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a registered tool by ID.
        
        Args:
            tool_id: ID of the tool to get
            
        Returns:
            Tool information if found, None otherwise
        """
        return self.tools.get(tool_id)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools.
        
        Returns:
            List of tool information dictionaries
        """
        return [
            {
                "id": tool_id,
                "name": tool_info["name"],
                "description": tool_info["description"]
            }
            for tool_id, tool_info in self.tools.items()
        ]
    
    def execute_tool(self, tool_id: str, **kwargs) -> Any:
        """
        Execute a tool.
        
        Args:
            tool_id: ID of the tool to execute
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Result of tool execution
        """
        tool_info = self.get_tool(tool_id)
        
        if not tool_info:
            self.logger.error(f"Tool {tool_id} not found")
            raise ValueError(f"Tool {tool_id} not found")
            
        tool_instance = tool_info["instance"]
        
        # Check if tool has an execute method
        if hasattr(tool_instance, "execute") and callable(tool_instance.execute):
            self.logger.debug(f"Executing tool {tool_id}")
            return tool_instance.execute(**kwargs)
        else:
            # Try to call the instance directly
            self.logger.debug(f"Calling tool {tool_id} directly")
            return tool_instance(**kwargs)
    
    def get_tool_schema(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the schema for a tool.
        
        Args:
            tool_id: ID of the tool
            
        Returns:
            Tool schema if available, None otherwise
        """
        tool_info = self.get_tool(tool_id)
        
        if not tool_info:
            self.logger.error(f"Tool {tool_id} not found")
            return None
            
        tool_instance = tool_info["instance"]
        
        # Check if tool has a schema method or attribute
        if hasattr(tool_instance, "get_schema") and callable(tool_instance.get_schema):
            return tool_instance.get_schema()
        elif hasattr(tool_instance, "schema"):
            return tool_instance.schema
        else:
            # Try to infer schema from execute method signature
            if hasattr(tool_instance, "execute") and callable(tool_instance.execute):
                return self._infer_schema_from_function(tool_instance.execute)
            else:
                return self._infer_schema_from_function(tool_instance)
    
    def _infer_schema_from_function(self, func: Callable) -> Dict[str, Any]:
        """
        Infer a schema from a function's signature.
        
        Args:
            func: Function to infer schema from
            
        Returns:
            Inferred schema
        """
        sig = inspect.signature(func)
        
        parameters = {}
        for name, param in sig.parameters.items():
            # Skip self parameter
            if name == "self":
                continue
                
            param_info = {
                "type": "string"  # Default type
            }
            
            # Check for type annotations
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == str:
                    param_info["type"] = "string"
                elif param.annotation == int:
                    param_info["type"] = "integer"
                elif param.annotation == float:
                    param_info["type"] = "number"
                elif param.annotation == bool:
                    param_info["type"] = "boolean"
                elif param.annotation == list or param.annotation == List:
                    param_info["type"] = "array"
                elif param.annotation == dict or param.annotation == Dict:
                    param_info["type"] = "object"
            
            # Check for default value
            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default
            
            parameters[name] = param_info
        
        return {
            "parameters": parameters,
            "required": [
                name for name, param in sig.parameters.items()
                if param.default == inspect.Parameter.empty and name != "self"
            ]
        }
