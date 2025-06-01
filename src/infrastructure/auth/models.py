"""Authentication models."""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles."""
    ADMIN = "admin"
    USER = "user"
    API_USER = "api_user"


@dataclass
class User:
    """User model."""
    id: str
    username: str
    email: Optional[str] = None
    hashed_password: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    roles: List[UserRole] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        """Initialize defaults."""
        if self.roles is None:
            self.roles = [UserRole.USER]
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def has_role(self, role: UserRole) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return UserRole.ADMIN in self.roles


@dataclass
class Token:
    """JWT token response model."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 3600  # seconds


@dataclass
class TokenData:
    """Token payload data."""
    sub: str  # Subject (user ID)
    username: str
    roles: List[str] = None
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    jti: Optional[str] = None  # JWT ID for tracking
    
    def __post_init__(self):
        """Initialize defaults."""
        if self.roles is None:
            self.roles = []
        if self.iat is None:
            self.iat = datetime.utcnow()


@dataclass 
class APIKey:
    """API key model for service authentication."""
    id: str
    key: str  # Hashed key
    name: str
    description: Optional[str] = None
    scopes: List[str] = None
    rate_limit: Optional[int] = None  # Requests per hour
    is_active: bool = True
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize defaults."""
        if self.scopes is None:
            self.scopes = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def is_expired(self) -> bool:
        """Check if API key is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def has_scope(self, scope: str) -> bool:
        """Check if API key has a specific scope."""
        return scope in self.scopes