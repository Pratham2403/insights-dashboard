"""
Workflow utilities for agent management and lazy loading.
"""

import logging
from typing import Dict, Any, Optional, Callable, Type
from functools import cached_property

logger = logging.getLogger(__name__)

class LazyAgentManager:
    """
    Manages lazy initialization of agents with consistent patterns.
    """
    
    def __init__(self, llm_setup, rag_system=None):
        """
        Initialize the agent manager.
        
        Args:
            llm_setup: LLM setup instance
            rag_system: RAG system instance (optional)
        """
        self.llm_setup = llm_setup
        self.rag_system = rag_system
        self._agents: Dict[str, Any] = {}
        self._agent_configs: Dict[str, Dict[str, Any]] = {}
    
    def register_agent(self, name: str, agent_class: Type, 
                      requires_llm: bool = True, 
                      requires_rag: bool = False,
                      **agent_kwargs):
        """
        Register an agent for lazy initialization.
        
        Args:
            name: Agent name
            agent_class: Agent class to instantiate
            requires_llm: Whether agent needs LLM
            requires_rag: Whether agent needs RAG system
            **agent_kwargs: Additional agent parameters
        """
        self._agent_configs[name] = {
            'class': agent_class,
            'requires_llm': requires_llm,
            'requires_rag': requires_rag,
            'kwargs': agent_kwargs
        }
    
    def get_agent(self, name: str) -> Any:
        """
        Get agent instance, creating it if necessary.
        
        Args:
            name: Agent name
            
        Returns:
            Agent instance
        """
        if name not in self._agents:
            self._agents[name] = self._create_agent(name)
        return self._agents[name]
    
    def _create_agent(self, name: str) -> Any:
        """
        Create agent instance based on registered configuration.
        
        Args:
            name: Agent name
            
        Returns:
            Agent instance
        """
        if name not in self._agent_configs:
            raise ValueError(f"Agent '{name}' not registered")
        
        config = self._agent_configs[name]
        agent_class = config['class']
        kwargs = config['kwargs'].copy()
        
        # Add LLM if required
        if config['requires_llm']:
            llm = self.llm_setup.get_agent_llm(name)
            kwargs['llm'] = llm
        
        # Add RAG system if required
        if config['requires_rag'] and self.rag_system:
            kwargs['rag_system'] = self.rag_system
        
        logger.info(f"Creating agent: {name}")
        return agent_class(**kwargs)
    
    def clear_cache(self):
        """Clear all cached agent instances."""
        self._agents.clear()
        logger.info("Agent cache cleared")


def create_lazy_property(manager: LazyAgentManager, agent_name: str):
    """
    Create a lazy property for agent access.
    
    Args:
        manager: Agent manager instance
        agent_name: Name of the agent
        
    Returns:
        Property descriptor for lazy agent access
    """
    def getter(self):
        return manager.get_agent(agent_name)
    
    # Create a cached property to avoid repeated creation
    return cached_property(getter)


class WorkflowPropertyMixin:
    """
    Mixin class to add standardized lazy agent properties.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_agent_manager()
        self._register_agents()
    
    def _setup_agent_manager(self):
        """Setup the agent manager - should be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _setup_agent_manager")
    
    def _register_agents(self):
        """Register agents - should be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _register_agents")
    
    def get_all_agents(self) -> Dict[str, Any]:
        """
        Get all registered agents.
        
        Returns:
            Dictionary of agent name to instance
        """
        return {name: self.agent_manager.get_agent(name) 
                for name in self.agent_manager._agent_configs.keys()}
    
    def refresh_agents(self):
        """Refresh all agent instances."""
        self.agent_manager.clear_cache()
        logger.info("All agents refreshed")


def batch_create_properties(cls: Type, manager: LazyAgentManager, agent_names: list) -> Type:
    """
    Dynamically add lazy properties to a class for multiple agents.
    
    Args:
        cls: Class to add properties to
        manager: Agent manager instance
        agent_names: List of agent names to create properties for
        
    Returns:
        Modified class with lazy properties
    """
    for agent_name in agent_names:
        prop = create_lazy_property(manager, agent_name)
        setattr(cls, agent_name, prop)
    
    return cls
