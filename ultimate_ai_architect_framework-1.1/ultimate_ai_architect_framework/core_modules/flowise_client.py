"""
Flowise Client Module

This module provides the FlowiseClient class for interacting with the FlowiseAI API,
allowing the framework to execute flows designed in FlowiseAI.
"""

import logging
import os
import requests
from typing import Dict, Any, Optional, Union, Generator
from pathlib import Path
from os import PathLike

from .config_loader import ConfigLoader

# Set up module logger
logger = logging.getLogger("core.flowise_client")


class FlowiseConnectionError(Exception):
    """Exception raised for connection issues with the FlowiseAI API."""
    pass


class FlowiseTimeoutError(Exception):
    """Exception raised for timeout issues with the FlowiseAI API."""
    pass


class FlowiseAPIError(Exception):
    """Exception raised for API errors from the FlowiseAI API."""
    pass


class FlowiseClient:
    """
    Client for interacting with the FlowiseAI API.
    
    This class handles communication with FlowiseAI, allowing the framework to
    execute flows designed in the FlowiseAI visual editor. It manages authentication,
    connection pooling, error handling, and request formatting.
    """

    def __init__(self, framework_root: Union[str, PathLike]):
        """
        Initialize a new FlowiseClient instance.

        Args:
            framework_root: Absolute path to the framework root directory.
        """
        self.framework_root = Path(os.path.expanduser(framework_root)).resolve()
        self.logger = logging.getLogger("core.flowise_client")
        
        # Load configuration
        config_loader = ConfigLoader(framework_root)
        global_config = config_loader._load_yaml_file(
            config_loader.configs_dir / "global_settings.yaml"
        )
        
        # Extract Flowise configuration
        flowise_config = global_config.get("flowise", {})
        self.enabled = flowise_config.get("enabled", False)
        self.base_url = flowise_config.get("base_url", "http://localhost:3000")
        self.default_timeout = flowise_config.get("default_timeout", 60)
        
        # Set up API key if configured
        self.api_key = None
        api_key_env = flowise_config.get("api_key_env")
        if api_key_env:
            self.api_key = os.environ.get(api_key_env)
            if not self.api_key:
                self.logger.warning(
                    f"Flowise API key environment variable '{api_key_env}' is configured but not set. "
                    "Proceeding without authentication."
                )
        
        # Initialize session for connection pooling
        self.session = requests.Session()
        
        self.logger.info(f"FlowiseClient initialized with base URL: {self.base_url}")
        if not self.enabled:
            self.logger.warning("Flowise integration is disabled in configuration")

    def run_flow(self, flow_endpoint_url: str, input_data: Dict[str, Any], stream: bool = False) -> Union[Dict[str, Any], Generator]:
        """
        Execute a flow in FlowiseAI.

        Args:
            flow_endpoint_url: The endpoint URL for the flow to execute.
                This should be the full URL including the base URL.
            input_data: Dictionary containing the input data for the flow.
            stream: Whether to stream the response. If True, returns a generator
                that yields chunks of the response as they arrive.

        Returns:
            If stream=False: Dictionary containing the flow execution results.
            If stream=True: Generator yielding chunks of the response.

        Raises:
            FlowiseConnectionError: If there's an issue connecting to the FlowiseAI API.
            FlowiseTimeoutError: If the request times out.
            FlowiseAPIError: If the FlowiseAI API returns an error.
        """
        if not self.enabled:
            self.logger.warning("Attempting to run a flow while Flowise integration is disabled")
        
        # Prepare headers
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        if stream:
            headers["Accept"] = "text/event-stream"
        
        # Ensure the URL is properly formatted
        if not flow_endpoint_url.startswith(("http://", "https://")):
            # Assume it's a relative path to the base URL
            if flow_endpoint_url.startswith("/"):
                flow_endpoint_url = f"{self.base_url}{flow_endpoint_url}"
            else:
                flow_endpoint_url = f"{self.base_url}/{flow_endpoint_url}"
        
        self.logger.debug(f"Making request to FlowiseAI flow: {flow_endpoint_url}")
        
        try:
            response = self.session.post(
                flow_endpoint_url,
                json=input_data,
                headers=headers,
                timeout=self.default_timeout,
                stream=stream
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            if stream:
                # Return a generator that yields chunks of the response
                def response_generator():
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            yield chunk.decode('utf-8')
                
                return response_generator()
            else:
                # Parse and return the JSON response
                try:
                    return response.json()
                except ValueError:
                    error_msg = f"Failed to parse JSON response from FlowiseAI: {response.text}"
                    self.logger.error(error_msg)
                    raise FlowiseAPIError(error_msg)
                
        except requests.ConnectionError as e:
            error_msg = f"Failed to connect to FlowiseAI API: {str(e)}"
            self.logger.error(error_msg)
            raise FlowiseConnectionError(error_msg) from e
            
        except requests.Timeout as e:
            error_msg = f"Request to FlowiseAI API timed out after {self.default_timeout} seconds"
            self.logger.error(error_msg)
            raise FlowiseTimeoutError(error_msg) from e
            
        except requests.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') else "unknown"
            error_msg = f"FlowiseAI API returned error (status {status_code}): {str(e)}"
            self.logger.error(error_msg)
            
            # Try to extract more detailed error information from the response
            try:
                error_details = e.response.json() if hasattr(e, 'response') else {}
                error_msg += f" Details: {error_details}"
            except (ValueError, AttributeError):
                pass
                
            raise FlowiseAPIError(error_msg) from e
