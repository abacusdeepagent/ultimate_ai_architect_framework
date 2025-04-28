"""
Framework Strategy Advisor Agent

This agent analyzes project requirements and provides strategic advice on
architectural decisions, component selection, and implementation approaches.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Union
import yaml
import sys
import os

# Add parent directory to path to import base modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ultimate_ai_architect_framework.agents.modules.base_agent import BaseAgent

class FrameworkStrategyAdvisor(BaseAgent):
    """
    Agent that provides strategic advice for AI architecture decisions.
    
    This agent analyzes project requirements, constraints, and goals to recommend
    the most appropriate architectural patterns, tools, and implementation approaches.
    """
    
    def __init__(self, 
                 framework_root: str,
                 agent_id: str = "strategy_advisor", 
                 config_path: Optional[str] = None):
        """
        Initialize a new FrameworkStrategyAdvisor instance.
        
        Args:
            framework_root: Path to the framework root directory
            agent_id: Unique identifier for this agent instance
            config_path: Path to agent-specific configuration file
        """
        super().__init__(framework_root=framework_root, agent_id=agent_id)
        
        # Strategy advisor specific initialization
        self.patterns_library = self._load_patterns_library()
        self.logger.info("Strategy Advisor agent initialized")
    
    def _load_patterns_library(self) -> Dict[str, Any]:
        """
        Load the library of architectural patterns and approaches.
        
        Returns:
            Dictionary of patterns and their details
        """
        # In a real implementation, this would load from a file or database
        return {
            "rag": {
                "name": "Retrieval-Augmented Generation",
                "description": "Enhances LLM responses with retrieved knowledge",
                "use_cases": ["question answering", "knowledge base", "documentation"],
                "components": ["vector database", "embedding model", "LLM"]
            },
            "agent": {
                "name": "Autonomous Agent",
                "description": "Self-directed AI that can plan and execute tasks",
                "use_cases": ["automation", "research", "problem solving"],
                "components": ["planning module", "tool use", "memory", "LLM"]
            },
            "multi_agent": {
                "name": "Multi-Agent System",
                "description": "Multiple specialized agents collaborating on tasks",
                "use_cases": ["complex workflows", "specialized domains"],
                "components": ["orchestrator", "specialized agents", "communication protocol"]
            }
        }
        
    def _get_llm_client(self, task_type: str) -> Optional[Any]:
        """
        Get an LLM client based on the task type.
        
        Args:
            task_type: The type of task to perform (e.g., 'reasoning', 'generation', 'summarization')
            
        Returns:
            An LLM client instance or None if initialization fails.
        """
        # Map task types to model names
        task_to_model = {
            'reasoning': 'openrouter.anthropic/claude-3-opus',
            'generation': 'openrouter.anthropic/claude-3-sonnet',
            'summarization': 'google_gemini.gemini-pro',
            'default': 'openrouter.anthropic/claude-3-haiku'
        }
        
        # Get the model name for the task type
        model_name = task_to_model.get(task_type, task_to_model['default'])
        
        # Call the parent class's _get_llm_client method with the model name
        return super()._get_llm_client(model_name)
    
    def run(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze requirements and provide strategic recommendations.
        
        Args:
            requirements: Dictionary containing project requirements, constraints, and goals
            
        Returns:
            Dictionary containing strategic recommendations or error information
        """
        try:
            # Log the incoming requirements
            self.logger.info(f"Analyzing requirements: {requirements}")
            
            # Get an LLM client for reasoning tasks
            llm_client = self._get_llm_client(task_type='reasoning')
            if not llm_client:
                error_msg = "Failed to obtain LLM client for reasoning task"
                self.logger.error(error_msg)
                return {"error": True, "message": error_msg, "details": "LLM client initialization failed"}
            
            # Construct the prompt for the LLM
            prompt = self._construct_strategy_prompt(requirements)
            
            # Call the LLM with the prompt
            response_text = self._call_llm(llm_client, prompt)
            
            # Parse the response into a structured format
            structured_response = self._parse_llm_response(response_text)
            
            # Log the run to LangSmith
            self._log_run_to_langsmith(run_data={
                "inputs": requirements,
                "outputs": structured_response
            })
            
            self.logger.info(f"Generated recommendations: {structured_response}")
            return structured_response
            
        except Exception as e:
            error_msg = f"Error in strategy advisor: {str(e)}"
            self.logger.error(error_msg)
            return {
                "error": True,
                "message": "Failed to generate strategic recommendations",
                "details": str(e)
            }
    
    def _construct_strategy_prompt(self, requirements: Dict[str, Any]) -> str:
        """
        Construct a detailed prompt for the LLM to generate strategic recommendations.
        
        Args:
            requirements: Dictionary containing project requirements
            
        Returns:
            Formatted prompt string
        """
        # Format the patterns library for inclusion in the prompt
        patterns_str = yaml.dump(self.patterns_library, default_flow_style=False)
        
        # Format the requirements for inclusion in the prompt
        requirements_str = yaml.dump(requirements, default_flow_style=False)
        
        prompt = f"""
You are an AI Strategy Advisor specializing in AI architecture and implementation strategies.
Your task is to analyze the provided project requirements and recommend the most appropriate
architectural patterns, implementation approaches, and technology stack.

# Project Requirements
```yaml
{requirements_str}
```

# Available Architectural Patterns
```yaml
{patterns_str}
```

Based on the project requirements, provide comprehensive strategic recommendations.
Your response should be structured with the following markdown headings:

## Recommended Patterns
List the architectural patterns from the provided library that best match the project requirements.
Explain why each pattern is appropriate for this project.

## Architecture Overview
Provide a high-level overview of the recommended architecture, explaining how the components
will work together to fulfill the project requirements.

## Implementation Approach
Outline a phased implementation approach, including key considerations, potential challenges,
and recommended development practices.

## Technology Stack
Recommend specific technologies, frameworks, models, and tools for implementing the architecture.
Organize recommendations by category (e.g., frameworks, models, databases, infrastructure).

Your recommendations should be practical, well-justified, and tailored to the specific project requirements.
"""
        
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the LLM response text into a structured dictionary based on markdown headings.
        
        Args:
            response_text: The raw text response from the LLM
            
        Returns:
            Structured dictionary containing the parsed recommendations
        """
        # Initialize the structured response
        structured_response = {
            "recommended_patterns": [],
            "architecture_overview": "",
            "implementation_approach": {},
            "technology_stack": {}
        }
        
        # Extract sections based on markdown headings
        sections = {}
        current_section = None
        
        for line in response_text.split('\n'):
            if line.startswith('## '):
                current_section = line[3:].strip().lower().replace(' ', '_')
                sections[current_section] = []
            elif current_section:
                sections[current_section].append(line)
        
        # Process recommended patterns section
        if 'recommended_patterns' in sections:
            pattern_text = '\n'.join(sections['recommended_patterns'])
            # Extract pattern names (assuming they are mentioned in the text)
            for pattern in self.patterns_library.keys():
                if pattern.lower() in pattern_text.lower() or self.patterns_library[pattern]['name'].lower() in pattern_text.lower():
                    structured_response['recommended_patterns'].append(pattern)
        
        # Process architecture overview section
        if 'architecture_overview' in sections:
            structured_response['architecture_overview'] = '\n'.join(sections['architecture_overview']).strip()
        
        # Process implementation approach section
        if 'implementation_approach' in sections:
            approach_text = '\n'.join(sections['implementation_approach'])
            
            # Extract phases (assuming they are listed with bullet points or numbers)
            phases = re.findall(r'[*-]\s*(.*?)(?=\n[*-]|\n\n|$)', approach_text)
            considerations = re.findall(r'consideration[s]?:?\s*(.*?)(?=\n\n|$)', approach_text, re.IGNORECASE)
            
            structured_response['implementation_approach'] = {
                "development_phases": phases if phases else [],
                "key_considerations": considerations if considerations else []
            }
        
        # Process technology stack section
        if 'technology_stack' in sections:
            tech_text = '\n'.join(sections['technology_stack'])
            
            # Initialize categories
            tech_stack = {
                "frameworks": [],
                "models": [],
                "databases": [],
                "infrastructure": []
            }
            
            # Extract technologies by category
            current_category = None
            for line in tech_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Check if this line is a category header
                category_match = re.match(r'[*-]?\s*(?:frameworks|models|databases|infrastructure)[:]?', line, re.IGNORECASE)
                if category_match:
                    category_word = re.search(r'(frameworks|models|databases|infrastructure)', line, re.IGNORECASE).group(1).lower()
                    current_category = category_word
                    continue
                
                # If we have a current category and this line contains a technology (bullet point)
                if current_category and re.match(r'[*-]\s*(.*)', line):
                    tech = re.match(r'[*-]\s*(.*)', line).group(1).strip()
                    tech_stack[current_category].append(tech)
            
            structured_response['technology_stack'] = tech_stack
        
        return structured_response
