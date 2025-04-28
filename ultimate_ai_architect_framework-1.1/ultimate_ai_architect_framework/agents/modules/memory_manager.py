"""
Memory Manager Module

This module provides memory management capabilities for agents in the framework,
allowing them to store, retrieve, and manage information across interactions.
"""

import logging
from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime

class MemoryManager:
    """
    Manages memory for agents, providing short-term and long-term storage capabilities.
    
    Features:
    - Short-term working memory for current session
    - Long-term persistent storage
    - Memory segmentation for different types of information
    - Memory search and retrieval
    """
    
    def __init__(self, agent_id: str, memory_config: Optional[Dict[str, Any]] = None):
        """
        Initialize a new MemoryManager instance.
        
        Args:
            agent_id: ID of the agent this memory manager belongs to
            memory_config: Configuration for memory behavior
        """
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"memory.{agent_id}")
        
        # Default configuration
        self.config = {
            'max_short_term_items': 100,
            'persistence_enabled': True,
            'persistence_path': f"memory/{agent_id}/",
            'segments': ['conversation', 'knowledge', 'task']
        }
        
        # Override with provided config
        if memory_config:
            self.config.update(memory_config)
            
        # Initialize memory segments
        self.short_term = {segment: [] for segment in self.config['segments']}
        self.long_term = {segment: [] for segment in self.config['segments']}
        
        # Load persistent memory if enabled
        if self.config['persistence_enabled']:
            self._load_persistent_memory()
            
        self.logger.debug(f"Memory manager initialized for agent {agent_id}")
    
    def add(self, segment: str, data: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add an item to memory.
        
        Args:
            segment: Memory segment to store in (e.g., 'conversation', 'knowledge')
            data: The data to store
            metadata: Additional metadata about this memory item
            
        Returns:
            ID of the stored memory item
        """
        if segment not in self.config['segments']:
            self.logger.error(f"Invalid memory segment: {segment}")
            raise ValueError(f"Invalid memory segment: {segment}")
            
        # Create memory item
        timestamp = datetime.now().isoformat()
        memory_id = f"{segment}_{timestamp}"
        
        memory_item = {
            'id': memory_id,
            'timestamp': timestamp,
            'data': data,
            'metadata': metadata or {}
        }
        
        # Add to short-term memory
        self.short_term[segment].append(memory_item)
        
        # Trim if exceeding max size
        if len(self.short_term[segment]) > self.config['max_short_term_items']:
            oldest = self.short_term[segment].pop(0)
            self.logger.debug(f"Removed oldest item from short-term {segment} memory: {oldest['id']}")
            
            # Move to long-term if persistence enabled
            if self.config['persistence_enabled']:
                self.long_term[segment].append(oldest)
                self._save_persistent_memory()
        
        self.logger.debug(f"Added item {memory_id} to {segment} memory")
        return memory_id
    
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific memory item by ID.
        
        Args:
            memory_id: ID of the memory item to retrieve
            
        Returns:
            Memory item if found, None otherwise
        """
        # Check short-term memory first
        for segment in self.short_term:
            for item in self.short_term[segment]:
                if item['id'] == memory_id:
                    return item
        
        # Check long-term memory if not found
        for segment in self.long_term:
            for item in self.long_term[segment]:
                if item['id'] == memory_id:
                    return item
                    
        self.logger.debug(f"Memory item {memory_id} not found")
        return None
    
    def search(self, segment: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for memory items matching the query.
        
        Args:
            segment: Memory segment to search in
            query: Dictionary of field-value pairs to match
            
        Returns:
            List of matching memory items
        """
        if segment not in self.config['segments']:
            self.logger.error(f"Invalid memory segment: {segment}")
            raise ValueError(f"Invalid memory segment: {segment}")
            
        results = []
        
        # Search in short-term memory
        for item in self.short_term[segment]:
            if self._matches_query(item, query):
                results.append(item)
                
        # Search in long-term memory
        for item in self.long_term[segment]:
            if self._matches_query(item, query):
                results.append(item)
                
        self.logger.debug(f"Found {len(results)} items matching query in {segment}")
        return results
    
    def _matches_query(self, item: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """
        Check if a memory item matches the query.
        
        Args:
            item: Memory item to check
            query: Query to match against
            
        Returns:
            True if item matches query, False otherwise
        """
        for key, value in query.items():
            # Handle nested keys with dot notation
            if '.' in key:
                parts = key.split('.')
                current = item
                for part in parts:
                    if part not in current:
                        return False
                    current = current[part]
                if current != value:
                    return False
            # Handle direct keys
            elif key not in item or item[key] != value:
                return False
                
        return True
    
    def _load_persistent_memory(self) -> None:
        """Load persistent memory from disk."""
        try:
            base_path = self.config['persistence_path']
            os.makedirs(base_path, exist_ok=True)
            
            for segment in self.config['segments']:
                file_path = os.path.join(base_path, f"{segment}.json")
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        self.long_term[segment] = json.load(f)
                    self.logger.debug(f"Loaded {len(self.long_term[segment])} items from {segment} persistent memory")
        except Exception as e:
            self.logger.error(f"Failed to load persistent memory: {e}")
    
    def _save_persistent_memory(self) -> None:
        """Save persistent memory to disk."""
        try:
            base_path = self.config['persistence_path']
            os.makedirs(base_path, exist_ok=True)
            
            for segment in self.config['segments']:
                file_path = os.path.join(base_path, f"{segment}.json")
                with open(file_path, 'w') as f:
                    json.dump(self.long_term[segment], f)
                self.logger.debug(f"Saved {len(self.long_term[segment])} items to {segment} persistent memory")
        except Exception as e:
            self.logger.error(f"Failed to save persistent memory: {e}")
