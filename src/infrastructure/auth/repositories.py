"""Repository implementations for authentication."""

from typing import Optional, List, Dict
from datetime import datetime
import uuid

from .models import User, UserRole, APIKey


class UserRepository:
    """In-memory user repository for demo purposes."""
    
    def __init__(self):
        """Initialize with demo users."""
        self._users: Dict[str, User] = {}
        self._username_index: Dict[str, str] = {}
        self._email_index: Dict[str, str] = {}
        
        # Create demo users
        self._create_demo_users()
    
    def _create_demo_users(self):
        """Create demo users for testing."""
        # Admin user
        admin = User(
            id="admin-001",
            username="admin",
            email="admin@mathtts.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGU1qpM4V2O",  # "admin123"
            is_active=True,
            is_verified=True,
            roles=[UserRole.ADMIN, UserRole.USER]
        )
        
        # Regular user
        user = User(
            id="user-001",
            username="testuser",
            email="user@example.com", 
            hashed_password="$2b$12$GhvMmNVjRW29ulnudl.LbuAnUtFWXbURnXpms1hC8tK0JnMA5E0di",  # "user123"
            is_active=True,
            is_verified=True,
            roles=[UserRole.USER]
        )
        
        # API user
        api_user = User(
            id="api-001",
            username="api_service",
            email="api@mathtts.com",
            hashed_password="$2b$12$rX2U3r0hGIuvwUwZBzVjVu4B5h9gL2CpMr4II0S7IhDq8HPBYkS0C",  # "api123"
            is_active=True,
            is_verified=True,
            roles=[UserRole.API_USER]
        )
        
        # Add to repository
        for user in [admin, user, api_user]:
            self._users[user.id] = user
            self._username_index[user.username] = user.id
            if user.email:
                self._email_index[user.email] = user.id
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self._users.get(user_id)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        user_id = self._username_index.get(username)
        return self._users.get(user_id) if user_id else None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        user_id = self._email_index.get(email.lower())
        return self._users.get(user_id) if user_id else None
    
    async def create(self, user: User) -> User:
        """Create new user."""
        if user.id in self._users:
            raise ValueError(f"User {user.id} already exists")
        
        if user.username in self._username_index:
            raise ValueError(f"Username {user.username} already taken")
        
        if user.email and user.email.lower() in self._email_index:
            raise ValueError(f"Email {user.email} already registered")
        
        self._users[user.id] = user
        self._username_index[user.username] = user.id
        if user.email:
            self._email_index[user.email.lower()] = user.id
        
        return user
    
    async def update(self, user: User) -> User:
        """Update user."""
        if user.id not in self._users:
            raise ValueError(f"User {user.id} not found")
        
        old_user = self._users[user.id]
        
        # Update indexes if username/email changed
        if old_user.username != user.username:
            del self._username_index[old_user.username]
            self._username_index[user.username] = user.id
        
        if old_user.email != user.email:
            if old_user.email:
                del self._email_index[old_user.email.lower()]
            if user.email:
                self._email_index[user.email.lower()] = user.id
        
        user.updated_at = datetime.utcnow()
        self._users[user.id] = user
        return user
    
    async def delete(self, user_id: str) -> bool:
        """Delete user."""
        user = self._users.get(user_id)
        if not user:
            return False
        
        del self._users[user_id]
        del self._username_index[user.username]
        if user.email:
            del self._email_index[user.email.lower()]
        
        return True
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users."""
        users = list(self._users.values())
        return users[offset:offset + limit]


class APIKeyRepository:
    """In-memory API key repository for demo purposes."""
    
    def __init__(self):
        """Initialize with demo API keys."""
        self._keys: Dict[str, APIKey] = {}
        self._prefix_index: Dict[str, str] = {}
        
        # Create demo API keys
        self._create_demo_keys()
    
    def _create_demo_keys(self):
        """Create demo API keys for testing."""
        # Full access key
        full_key = APIKey(
            id="key-001",
            key="$2b$12$abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJK",  # hashed version
            name="Full Access Key",
            description="Demo key with full access",
            scopes=["read", "write", "admin"],
            is_active=True
        )
        
        # Read-only key
        readonly_key = APIKey(
            id="key-002", 
            key="$2b$12$1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJK",  # hashed version
            name="Read Only Key",
            description="Demo key with read-only access",
            scopes=["read"],
            rate_limit=1000,
            is_active=True
        )
        
        # Add to repository with prefixes
        for key in [full_key, readonly_key]:
            self._keys[key.id] = key
            # Store first 10 chars as prefix for lookup
            self._prefix_index[f"mtts_demo{key.id[-3:]}"] = key.id
    
    async def get_by_id(self, key_id: str) -> Optional[APIKey]:
        """Get API key by ID."""
        return self._keys.get(key_id)
    
    async def get_by_prefix(self, prefix: str) -> Optional[APIKey]:
        """Get API key by prefix."""
        key_id = self._prefix_index.get(prefix)
        return self._keys.get(key_id) if key_id else None
    
    async def create(self, api_key: APIKey, key_prefix: str) -> APIKey:
        """Create new API key."""
        if api_key.id in self._keys:
            raise ValueError(f"API key {api_key.id} already exists")
        
        self._keys[api_key.id] = api_key
        self._prefix_index[key_prefix] = api_key.id
        
        return api_key
    
    async def update(self, api_key: APIKey) -> APIKey:
        """Update API key."""
        if api_key.id not in self._keys:
            raise ValueError(f"API key {api_key.id} not found")
        
        self._keys[api_key.id] = api_key
        return api_key
    
    async def update_last_used(self, key_id: str) -> None:
        """Update last used timestamp."""
        if key_id in self._keys:
            self._keys[key_id].last_used_at = datetime.utcnow()
    
    async def delete(self, key_id: str) -> bool:
        """Delete API key."""
        if key_id not in self._keys:
            return False
        
        # Find and remove prefix
        for prefix, kid in list(self._prefix_index.items()):
            if kid == key_id:
                del self._prefix_index[prefix]
        
        del self._keys[key_id]
        return True
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[APIKey]:
        """List all API keys."""
        keys = list(self._keys.values())
        return keys[offset:offset + limit]