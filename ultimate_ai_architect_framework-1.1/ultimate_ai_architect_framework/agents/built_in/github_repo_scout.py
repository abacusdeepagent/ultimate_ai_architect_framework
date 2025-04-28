"""
GitHub Repo Scout Agent

This agent analyzes GitHub repositories to extract useful patterns, components,
and insights for AI architecture projects.
"""

import logging
from typing import Dict, List, Any, Optional
import sys
import os
import requests
from datetime import datetime

# Add parent directory to path to import base modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.base_agent import BaseAgent

class GitHubRepoScout(BaseAgent):
    """
    Agent that analyzes GitHub repositories for AI architecture insights.
    
    This agent can scan repositories, analyze code structure, identify patterns,
    and extract useful components that can be incorporated into AI projects.
    """
    
    def __init__(self, agent_id: str = "github_scout", config_path: Optional[str] = None):
        """
        Initialize a new GitHubRepoScout instance.
        
        Args:
            agent_id: Unique identifier for this agent instance
            config_path: Path to agent-specific configuration file
        """
        super().__init__(agent_id, config_path)
        
        # GitHub API configuration
        self.api_base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Add GitHub token if available
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"
        else:
            self.logger.warning("No GitHub token found. API rate limits will be restricted.")
        
        self.logger.info("GitHub Repo Scout agent initialized")
    
    def run(self, repo_url: str) -> Dict[str, Any]:
        """
        Analyze a GitHub repository and extract insights.
        
        Args:
            repo_url: URL of the GitHub repository to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        self.logger.info(f"Analyzing repository: {repo_url}")
        
        # Extract owner and repo name from URL
        repo_parts = repo_url.rstrip('/').split('/')
        owner = repo_parts[-2]
        repo = repo_parts[-1]
        
        # Gather repository information
        repo_info = self._get_repo_info(owner, repo)
        repo_structure = self._analyze_repo_structure(owner, repo)
        dependencies = self._analyze_dependencies(owner, repo)
        architecture_patterns = self._identify_architecture_patterns(repo_structure, dependencies)
        
        analysis_results = {
            "repo_info": repo_info,
            "structure": repo_structure,
            "dependencies": dependencies,
            "architecture_patterns": architecture_patterns,
            "reusable_components": self._identify_reusable_components(repo_structure, architecture_patterns),
            "insights": self._generate_insights(repo_info, architecture_patterns)
        }
        
        self.logger.info(f"Completed analysis of {repo_url}")
        return analysis_results
    
    def _get_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get basic information about a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary containing repository information
        """
        # In a real implementation, this would make an API call to GitHub
        # For this placeholder, we'll return mock data
        return {
            "name": repo,
            "owner": owner,
            "description": "A sample repository",
            "stars": 100,
            "forks": 20,
            "last_updated": datetime.now().isoformat(),
            "language": "Python"
        }
    
    def _analyze_repo_structure(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Analyze the structure of a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary containing repository structure analysis
        """
        # In a real implementation, this would analyze the file structure
        # For this placeholder, we'll return mock data
        return {
            "directories": [
                {"path": "/", "files": ["README.md", "requirements.txt", "setup.py"]},
                {"path": "/src", "files": ["main.py", "utils.py"]},
                {"path": "/src/models", "files": ["model.py", "embeddings.py"]},
                {"path": "/src/api", "files": ["api.py", "routes.py"]},
                {"path": "/tests", "files": ["test_main.py", "test_models.py"]}
            ],
            "file_types": {
                "Python": 6,
                "Markdown": 1,
                "Text": 1
            }
        }
    
    def _analyze_dependencies(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Analyze the dependencies of a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary containing dependency analysis
        """
        # In a real implementation, this would parse requirements.txt, setup.py, etc.
        # For this placeholder, we'll return mock data
        return {
            "python_dependencies": [
                {"name": "langchain", "version": "0.0.267"},
                {"name": "openai", "version": "0.27.8"},
                {"name": "fastapi", "version": "0.100.0"},
                {"name": "pydantic", "version": "2.0.3"},
                {"name": "chromadb", "version": "0.4.6"}
            ],
            "dependency_graph": {
                "langchain": ["openai", "chromadb"],
                "fastapi": ["pydantic"]
            }
        }
    
    def _identify_architecture_patterns(self, repo_structure: Dict[str, Any], dependencies: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify architecture patterns used in the repository.
        
        Args:
            repo_structure: Repository structure analysis
            dependencies: Dependency analysis
            
        Returns:
            List of identified architecture patterns
        """
        # In a real implementation, this would use more sophisticated analysis
        # For this placeholder, we'll return mock data
        patterns = []
        
        # Check for RAG pattern
        if any(dep["name"] == "chromadb" for dep in dependencies["python_dependencies"]):
            patterns.append({
                "name": "Retrieval-Augmented Generation",
                "confidence": 0.8,
                "components": ["vector database", "embeddings", "LLM integration"]
            })
        
        # Check for API pattern
        if any(dep["name"] == "fastapi" for dep in dependencies["python_dependencies"]):
            patterns.append({
                "name": "API Service",
                "confidence": 0.9,
                "components": ["REST API", "route handlers", "data models"]
            })
        
        return patterns
    
    def _identify_reusable_components(self, repo_structure: Dict[str, Any], patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify potentially reusable components in the repository.
        
        Args:
            repo_structure: Repository structure analysis
            patterns: Identified architecture patterns
            
        Returns:
            List of potentially reusable components
        """
        # In a real implementation, this would analyze code files
        # For this placeholder, we'll return mock data
        return [
            {
                "name": "Embedding Utility",
                "path": "/src/models/embeddings.py",
                "description": "Utility for creating and managing embeddings",
                "reuse_potential": "High"
            },
            {
                "name": "API Router",
                "path": "/src/api/routes.py",
                "description": "Modular API router setup",
                "reuse_potential": "Medium"
            }
        ]
    
    def _generate_insights(self, repo_info: Dict[str, Any], patterns: List[Dict[str, Any]]) -> List[str]:
        """
        Generate insights based on repository analysis.
        
        Args:
            repo_info: Repository information
            patterns: Identified architecture patterns
            
        Returns:
            List of insights
        """
        # In a real implementation, this would generate more meaningful insights
        # For this placeholder, we'll return mock data
        insights = [
            f"Repository uses {repo_info['language']} as its primary language",
            f"Project appears to implement {', '.join(p['name'] for p in patterns)} patterns",
            "Code structure follows a modular approach with clear separation of concerns",
            "Dependencies suggest a focus on AI and API development"
        ]
        
        return insights
