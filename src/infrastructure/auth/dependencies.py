"""Authentication dependencies for FastAPI."""

from typing import Optional, List, Annotated
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
import os

from .jwt_handler import JWTHandler, JWTSettings
from .models import User, TokenData, UserRole, APIKey
from .repositories import UserRepository, APIKeyRepository


# Security schemes
bearer_scheme = HTTPBearer(
    scheme_name="JWT Bearer Token",
    description="JWT access token obtained from /auth/login"
)

api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="API Key",
    description="API key for service-to-service authentication"
)


# Singleton instances
_jwt_handler: Optional[JWTHandler] = None
_user_repo: Optional[UserRepository] = None
_api_key_repo: Optional[APIKeyRepository] = None


def get_jwt_handler() -> JWTHandler:
    """Get JWT handler instance."""
    global _jwt_handler
    if _jwt_handler is None:
        settings = JWTSettings(
            secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key-here"),
            access_token_expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.getenv("JWT_REFRESH_DAYS", "7"))
        )
        _jwt_handler = JWTHandler(settings)
    return _jwt_handler


def get_user_repository() -> UserRepository:
    """Get user repository instance."""
    global _user_repo
    if _user_repo is None:
        _user_repo = UserRepository()
    return _user_repo


def get_api_key_repository() -> APIKeyRepository:
    """Get API key repository instance."""
    global _api_key_repo
    if _api_key_repo is None:
        _api_key_repo = APIKeyRepository()
    return _api_key_repo


async def get_current_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> TokenData:
    """Get current token data from JWT."""
    try:
        token_data = jwt_handler.decode_token(credentials.credentials)
        return token_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(
    token_data: TokenData = Depends(get_current_token),
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    """Get current authenticated user."""
    user = await user_repo.get_by_id(token_data.sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get verified user only."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get admin user only."""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_roles(allowed_roles: List[UserRole]):
    """Create a dependency that requires specific roles."""
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        user_roles = set(current_user.roles)
        if not any(role in allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(r.value for r in allowed_roles)}"
            )
        return current_user
    return role_checker


async def get_api_key(
    api_key: str = Security(api_key_header),
    api_key_repo: APIKeyRepository = Depends(get_api_key_repository),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> APIKey:
    """Validate API key."""
    # Find API key by prefix (first 10 chars)
    key_prefix = api_key[:10] if len(api_key) > 10 else api_key
    stored_key = await api_key_repo.get_by_prefix(key_prefix)
    
    if not stored_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Verify full key
    if not jwt_handler.verify_api_key(api_key, stored_key.key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    if not stored_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is disabled"
        )
    
    if stored_key.is_expired():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key has expired"
        )
    
    # Update last used timestamp
    await api_key_repo.update_last_used(stored_key.id)
    
    return stored_key


def require_api_scopes(required_scopes: List[str]):
    """Create a dependency that requires specific API scopes."""
    async def scope_checker(
        api_key: APIKey = Depends(get_api_key)
    ) -> APIKey:
        if not all(api_key.has_scope(scope) for scope in required_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required scopes: {', '.join(required_scopes)}"
            )
        return api_key
    return scope_checker


# Type aliases for cleaner function signatures
CurrentUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(get_admin_user)]
VerifiedUser = Annotated[User, Depends(get_verified_user)]
ValidAPIKey = Annotated[APIKey, Depends(get_api_key)]