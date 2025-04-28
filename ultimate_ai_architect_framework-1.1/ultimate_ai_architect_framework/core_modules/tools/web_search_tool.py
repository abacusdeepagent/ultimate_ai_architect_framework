# ~/projects/ultimate_ai_architect_framework/core_modules/tools/web_search_tool.py
import logging
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS # Use updated import

class WebSearchTool:
    """
    A tool for performing web searches using DuckDuckGo.
    """
    def __init__(self, max_results: int = 5):
        """
        Initializes the WebSearchTool.

        Args:
            max_results (int): The default maximum number of search results to return.
        """
        self.logger = logging.getLogger(__name__)
        # Allow max_results to be configurable maybe via agent/project config later
        # For now, just using the init parameter or the default
        self.default_max_results = max_results
        self.logger.info(f"WebSearchTool initialized with default_max_results={self.default_max_results}")

    def execute(self, query: str, num_results: Optional[int] = None) -> Dict[str, Any]:
        """
        Executes a web search for the given query.

        Args:
            query (str): The search query.
            num_results (int, optional): Max number of results for this specific search.
                                         Defaults to self.default_max_results.

        Returns:
            Dict[str, Any]: A dictionary containing the status and a list of results.
                           Each result is a dictionary with 'title', 'href', and 'body'.
                           Returns status 'error' if search fails.
        """
        if not query:
             self.logger.warning("WebSearchTool execute called with empty query.")
             return {"status": "error", "message": "Query cannot be empty."}

        self.logger.info(f"Executing WebSearchTool with query: '{query}'")
        results_to_fetch = num_results if num_results is not None else self.default_max_results
        # Ensure num_results is positive if provided
        if isinstance(results_to_fetch, int) and results_to_fetch <= 0:
             self.logger.warning(f"Received non-positive num_results ({results_to_fetch}), using default: {self.default_max_results}")
             results_to_fetch = self.default_max_results
        # DDGS might have its own practical limit (~25-30), but we pass the requested number
        self.logger.debug(f"Attempting to fetch up to {results_to_fetch} results.")

        try:
            # Use context manager for DDGS object
            with DDGS() as ddgs:
                # Fetch text search results
                search_results = list(ddgs.text(
                    query,
                    region='wt-wt',  # Worldwide region
                    safesearch='moderate', # Moderate safesearch
                    max_results=results_to_fetch
                ))

            self.logger.info(f"Found {len(search_results)} results for query '{query}'")
            # Ensure results format is consistent if needed, DDGS usually returns list of dicts
            return {
                "status": "success",
                "result_count": len(search_results),
                "results": search_results # List of dicts: {'title': '...', 'href': '...', 'body': '...'}
            }
        except Exception as e:
            self.logger.error(f"Web search failed for query '{query}': {e}", exc_info=True) # Log traceback
            return {
                "status": "error",
                "message": f"An error occurred during web search: {str(e)}"
            }

    @property
    def schema(self) -> Dict[str, Any]:
        """
        Provides the schema for the tool, useful for agents.
        """
        return {
            "name": "web_search",
            "description": "Performs a web search using DuckDuckGo and returns a list of results including title, URL (href), and snippet (body).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query string to execute."
                    },
                    "num_results": {
                        "type": "integer",
                        "description": f"Optional. Maximum number of search results to return (default: {self.default_max_results}, practical limit around 25-30).",
                        "default": self.default_max_results
                    }
                },
                "required": ["query"]
            }
        }