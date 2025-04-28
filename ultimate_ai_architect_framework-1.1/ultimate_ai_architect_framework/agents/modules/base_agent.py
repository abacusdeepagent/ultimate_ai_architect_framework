"""
Base Agent Module

This module defines the BaseAgent class that serves as the foundation for all agents
in the Ultimate AI Architect Framework. It provides common functionality and interfaces
that all specialized agents will inherit.
"""

import logging
import json
import os
import requests
from typing import Dict, List, Any, Optional, Union, Tuple

# Import core modules
from ultimate_ai_architect_framework.core_modules.config_loader import ConfigLoader
from ultimate_ai_architect_framework.core_modules.llm_router import LLMRouter
from ultimate_ai_architect_framework.core_modules.tool_handler import ToolHandler
from ultimate_ai_architect_framework.core_modules.flowise_client import FlowiseClient
from ultimate_ai_architect_framework.core_modules.langsmith_setup import LangSmithSetup

# Import agent modules
from ultimate_ai_architect_framework.agents.modules.memory_manager import MemoryManager

# Import LangChain components for LLM clients
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.llms import BaseLLM

class BaseAgent:
    """
    Base class for all agents in the framework.
    
    Provides common functionality such as configuration loading, memory management,
    tool access, and execution patterns.
    """
    
    def __init__(self, 
                 framework_root: str,
                 agent_id: str,
                 config_loader=None,
                 llm_router=None,
                 tool_handler=None,
                 memory_manager=None,
                 flowise_client=None,
                 langsmith_setup=None):
        """
        Initialize a new BaseAgent instance.
        
        Args:
            framework_root: Path to the framework root directory
            agent_id: Unique identifier for this agent instance
            config_loader: Optional ConfigLoader instance
            llm_router: Optional LLMRouter instance
            tool_handler: Optional ToolHandler instance
            memory_manager: Optional MemoryManager instance
            flowise_client: Optional FlowiseClient instance
            langsmith_setup: Optional LangSmithSetup instance
        """
        self.framework_root = framework_root
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"agent.{agent_id}")
        
        # Initialize or use provided framework components
        self.config_loader = config_loader or ConfigLoader(framework_root)
        self.llm_router = llm_router or LLMRouter()
        self.tool_handler = tool_handler or ToolHandler(framework_root)
        self.flowise_client = flowise_client or FlowiseClient(framework_root)
        self.langsmith_setup = langsmith_setup or LangSmithSetup(framework_root)
        
        # Load agent profile configuration
        agent_profiles = self.config_loader.load_agent_profiles()
        self.profile_config = agent_profiles.get('agents', {}).get(agent_id, {})
        if not self.profile_config:
            self.logger.warning(f"No profile configuration found for agent {agent_id}")
        
        # Initialize memory manager
        memory_config = self.profile_config.get('memory', {})
        self.memory_manager = memory_manager or MemoryManager(agent_id, memory_config)
        
        # Initialize tools dictionary
        self.tools = {}
        
        self.logger.info(f"Agent {agent_id} initialized with framework components")
    
    def run(self, input_data: Any) -> Any:
        """
        Execute the agent's primary function.
        
        Args:
            input_data: The input data for the agent to process
            
        Returns:
            The result of the agent's processing
        """
        self.logger.info(f"Agent {self.agent_id} running with input: {input_data}")
        # This method should be overridden by subclasses
        raise NotImplementedError("Subclasses must implement run()")
    
    def add_tool(self, tool_name: str, tool_instance: Any) -> None:
        """
        Add a tool to this agent's available tools.
        
        Args:
            tool_name: Name of the tool
            tool_instance: Instance of the tool
        """
        self.tools[tool_name] = tool_instance
        self.logger.debug(f"Tool {tool_name} added to agent {self.agent_id}")
    
    def use_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Use one of the agent's available tools.
        
        Args:
            tool_name: Name of the tool to use
            **kwargs: Arguments to pass to the tool
            
        Returns:
            The result of the tool execution
        """
        if tool_name not in self.tools:
            self.logger.error(f"Tool {tool_name} not available to agent {self.agent_id}")
            raise ValueError(f"Tool {tool_name} not available")
            
        self.logger.debug(f"Agent {self.agent_id} using tool {tool_name}")
        return self.tools[tool_name].execute(**kwargs)
    
    def _get_llm_client(self, model_name: str) -> Optional[Any]:
        """
        Get an LLM client based on the model name prefix.
        
        Args:
            model_name: The name of the model to use, with prefix indicating the provider.
                        Supported prefixes: 'openrouter.', 'google_gemini.'
        
        Returns:
            An LLM client instance or None if initialization fails.
        """
        try:
            # Handle OpenRouter models (using ChatOpenAI)
            if model_name.startswith("openrouter."):
                try:
                    from langchain_openai import ChatOpenAI
                except ImportError:
                    self.logger.error("Failed to import ChatOpenAI. Please install langchain-openai package.")
                    return None
                
                try:
                    # Get the actual model name (remove the prefix)
                    actual_model = model_name.replace("openrouter.", "")
                    
                    # Get API key and base URL from environment variables
                    api_key = os.environ.get("OPENROUTER_API_KEY")
                    api_base = os.environ.get("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
                    
                    if not api_key:
                        self.logger.error("OPENROUTER_API_KEY environment variable not set")
                        return None
                    
                    # Create and return the ChatOpenAI client with correct parameters
                    # Note: No headers parameter as per requirements
                    return ChatOpenAI(
                        model=actual_model,
                        openai_api_key=api_key,
                        openai_api_base=api_base,
                        temperature=0.7,  # Default temperature, can be adjusted as needed
                        max_tokens=1024   # Default max_tokens, can be adjusted as needed
                    )
                except Exception as e:
                    self.logger.error(f"Failed to initialize OpenRouter client: {str(e)}")
                    return None
            
            # Handle Google Gemini models
            elif model_name.startswith("google_gemini."):
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                except ImportError:
                    self.logger.error("Failed to import ChatGoogleGenerativeAI. Please install langchain-google-genai package.")
                    return None
                
                try:
                    # Get the actual model name (remove the prefix)
                    actual_model = model_name.replace("google_gemini.", "")
                    
                    # Get API key from environment variables
                    api_key = os.environ.get("GOOGLE_API_KEY")
                    
                    if not api_key:
                        self.logger.error("GOOGLE_API_KEY environment variable not set")
                        return None
                    
                    # Create and return the ChatGoogleGenerativeAI client
                    return ChatGoogleGenerativeAI(
                        model=actual_model,
                        google_api_key=api_key,
                        temperature=0.7,  # Default temperature, can be adjusted as needed
                        max_tokens=1024   # Default max_tokens, can be adjusted as needed
                    )
                except Exception as e:
                    self.logger.error(f"Failed to initialize Google Gemini client: {str(e)}")
                    return None
            
            # Unsupported model prefix
            else:
                self.logger.error(f"Unsupported model prefix in '{model_name}'. Supported prefixes: 'openrouter.', 'google_gemini.'")
                return None
                
        except Exception as e:
            self.logger.error(f"Unexpected error in _get_llm_client: {str(e)}")
            return None
    
    def _call_llm(self, llm_client: Union[BaseChatModel, BaseLLM], prompt: Union[str, List]) -> str:
        """
        Execute a call to the initialized LLM client.
        
        Handles both string prompts and structured message lists.
        Adds LangSmith logging if available.
        
        Args:
            llm_client: The initialized LangChain LLM client
            prompt: Either a string prompt or a list of message dictionaries
            
        Returns:
            The LLM response as a string
            
        Raises:
            RuntimeError: If the LLM call fails
        """
        try:
            self.logger.debug(f"Calling LLM with prompt: {prompt[:100]}...")
            
            # Create a run in LangSmith if available
            run_id = None
            if self.langsmith_setup and self.langsmith_setup.client:
                run_name = f"{self.agent_id}_llm_call"
                run_id = self.langsmith_setup.start_run(
                    run_name=run_name,
                    inputs={"prompt": prompt}
                )
            
            # Execute the LLM call
            if isinstance(prompt, str):
                response = llm_client.invoke(prompt).content
            else:
                # Assume it's a list of message dictionaries
                response = llm_client.invoke(prompt).content
            
            # Log the run completion in LangSmith
            if run_id and self.langsmith_setup and self.langsmith_setup.client:
                self.langsmith_setup.end_run(
                    run_id=run_id,
                    outputs={"response": response}
                )
            
            self.logger.debug(f"LLM response: {response[:100]}...")
            return response
            
        except Exception as e:
            error_msg = f"LLM call failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Log the run failure in LangSmith
            if run_id and self.langsmith_setup and self.langsmith_setup.client:
                self.langsmith_setup.end_run(
                    run_id=run_id,
                    error=error_msg
                )
                
            raise RuntimeError(error_msg)
    
    def _use_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool through the tool handler with agent-specific context.
        
        Checks if the tool is allowed based on the agent's configuration
        before executing it.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Arguments to pass to the tool
            
        Returns:
            The result of the tool execution
            
        Raises:
            ValueError: If the tool is not allowed for this agent
            RuntimeError: If tool execution fails
        """
        try:
            # Check if tool is allowed for this agent
            allowed_tools = self.profile_config.get('allowed_tools', [])
            if allowed_tools and tool_name not in allowed_tools:
                error_msg = f"Tool {tool_name} is not allowed for agent {self.agent_id}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            self.logger.info(f"Agent {self.agent_id} executing tool: {tool_name}")
            
            # Create a run in LangSmith if available
            run_id = None
            if self.langsmith_setup and self.langsmith_setup.client:
                run_name = f"{self.agent_id}_tool_{tool_name}"
                run_id = self.langsmith_setup.start_run(
                    run_name=run_name,
                    inputs={"tool": tool_name, "args": kwargs}
                )
            
            # Execute the tool
            result = self.tool_handler.execute_tool(tool_name, **kwargs)
            
            # Log the run completion in LangSmith
            if run_id and self.langsmith_setup and self.langsmith_setup.client:
                self.langsmith_setup.end_run(
                    run_id=run_id,
                    outputs={"result": result}
                )
            
            return result
            
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Log the run failure in LangSmith
            if run_id and self.langsmith_setup and self.langsmith_setup.client:
                self.langsmith_setup.end_run(
                    run_id=run_id,
                    error=error_msg
                )
                
            raise RuntimeError(error_msg)
    
    def _call_flowise(self, flow_endpoint_url: str, input_data: dict) -> dict:
        """
        Execute a Flowise flow with the given input data.
        
        Args:
            flow_endpoint_url: The URL endpoint of the Flowise flow
            input_data: Dictionary of input data to send to the flow
            
        Returns:
            The response from the Flowise flow as a dictionary
            
        Raises:
            RuntimeError: If the Flowise call fails
        """
        try:
            self.logger.info(f"Calling Flowise flow: {flow_endpoint_url}")
            self.logger.debug(f"Flowise input data: {input_data}")
            
            # Create a run in LangSmith if available
            run_id = None
            if self.langsmith_setup and self.langsmith_setup.client:
                run_name = f"{self.agent_id}_flowise_call"
                run_id = self.langsmith_setup.start_run(
                    run_name=run_name,
                    inputs={"flow_url": flow_endpoint_url, "input_data": input_data}
                )
            
            # Execute the Flowise flow
            response = self.flowise_client.run_flow(flow_endpoint_url, input_data)
            
            # Log the run completion in LangSmith
            if run_id and self.langsmith_setup and self.langsmith_setup.client:
                self.langsmith_setup.end_run(
                    run_id=run_id,
                    outputs={"response": response}
                )
            
            self.logger.debug(f"Flowise response: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Flowise call failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Log the run failure in LangSmith
            if run_id and self.langsmith_setup and self.langsmith_setup.client:
                self.langsmith_setup.end_run(
                    run_id=run_id,
                    error=error_msg
                )
                
            raise RuntimeError(error_msg)
    
    def _log_run_to_langsmith(self, run_data: dict, dataset_name: Optional[str] = None) -> Optional[str]:
        """
        Log a run to LangSmith for tracking and evaluation.
        
        Args:
            run_data: Dictionary containing run data (inputs, outputs, etc.)
            dataset_name: Optional name of the dataset to associate with this run
            
        Returns:
            The run ID if successful, None otherwise
        """
        try:
            if not self.langsmith_setup or not self.langsmith_setup.client:
                self.logger.warning("LangSmith client not available, skipping run logging")
                return None
            
            self.logger.info(f"Logging run to LangSmith{' in dataset ' + dataset_name if dataset_name else ''}")
            
            # Add agent context to run data
            run_data['agent_id'] = self.agent_id
            
            # Log the run
            run_id = self.langsmith_setup.log_run(run_data, dataset_name)
            
            self.logger.debug(f"Run logged to LangSmith with ID: {run_id}")
            return run_id
            
        except Exception as e:
            self.logger.error(f"Failed to log run to LangSmith: {str(e)}")
            return None
