"""
Pattern Repository interface.

Defines the contract for pattern storage and retrieval systems.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..entities import PatternEntity
from ..value_objects import MathematicalDomain, PatternPriority


class PatternRepository(ABC):
    """
    Abstract interface for pattern repositories.
    
    This interface defines the contract that all pattern repositories
    must implement, allowing for different storage backends while
    maintaining consistent access patterns.
    """
    
    @abstractmethod
    async def add(self, pattern: PatternEntity) -> None:
        """
        Add a pattern to the repository.
        
        Args:
            pattern: Pattern entity to add
            
        Raises:
            RepositoryError: If pattern cannot be added
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, pattern_id: str) -> Optional[PatternEntity]:
        """
        Retrieve a pattern by its ID.
        
        Args:
            pattern_id: Unique pattern identifier
            
        Returns:
            Pattern entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_all(self) -> List[PatternEntity]:
        """
        Retrieve all patterns from the repository.
        
        Returns:
            List of all pattern entities
        """
        pass
    
    @abstractmethod
    async def find_by_domain(self, domain: MathematicalDomain) -> List[PatternEntity]:
        """
        Find patterns by mathematical domain.
        
        Args:
            domain: Mathematical domain to filter by
            
        Returns:
            List of patterns in the specified domain
        """
        pass
    
    @abstractmethod
    async def find_by_priority_range(
        self,
        min_priority: PatternPriority,
        max_priority: PatternPriority
    ) -> List[PatternEntity]:
        """
        Find patterns within a priority range.
        
        Args:
            min_priority: Minimum priority (inclusive)
            max_priority: Maximum priority (inclusive)
            
        Returns:
            List of patterns within the priority range
        """
        pass
    
    @abstractmethod
    async def find_by_context(self, context: str) -> List[PatternEntity]:
        """
        Find patterns applicable to a specific context.
        
        Args:
            context: Context string (e.g., "inline", "display")
            
        Returns:
            List of patterns applicable to the context
        """
        pass
    
    @abstractmethod
    async def find_by_filters(self, filters: Dict[str, Any]) -> List[PatternEntity]:
        """
        Find patterns matching multiple filter criteria.
        
        Args:
            filters: Dictionary of filter criteria
                - domain: MathematicalDomain
                - contexts: List[str]
                - min_priority: PatternPriority
                - max_priority: PatternPriority
                - enabled: bool
                
        Returns:
            List of patterns matching all filter criteria
        """
        pass
    
    @abstractmethod
    async def update(self, pattern: PatternEntity) -> None:
        """
        Update an existing pattern.
        
        Args:
            pattern: Updated pattern entity
            
        Raises:
            RepositoryError: If pattern cannot be updated
        """
        pass
    
    @abstractmethod
    async def delete(self, pattern_id: str) -> bool:
        """
        Delete a pattern by its ID.
        
        Args:
            pattern_id: Unique pattern identifier
            
        Returns:
            True if pattern was deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """
        Get the total number of patterns.
        
        Returns:
            Total pattern count
        """
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get repository statistics.
        
        Returns:
            Dictionary containing:
            - total_patterns: int
            - domains: Dict[str, int] (domain -> count)
            - priorities: Dict[str, int] (priority range -> count)
            - contexts: Dict[str, int] (context -> count)
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """
        Remove all patterns from the repository.
        
        Raises:
            RepositoryError: If repository cannot be cleared
        """
        pass


class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class PatternNotFoundError(RepositoryError):
    """Raised when a requested pattern is not found."""
    pass


class DuplicatePatternError(RepositoryError):
    """Raised when attempting to add a pattern with duplicate ID."""
    pass


class InvalidPatternError(RepositoryError):
    """Raised when pattern data is invalid."""
    pass