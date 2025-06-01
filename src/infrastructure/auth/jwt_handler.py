"""JWT token handler."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from dataclasses import dataclass
import secrets

from .models import User, Token, TokenData


@dataclass
class JWTSettings:
    """JWT configuration settings."""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    issuer: Optional[str] = "mathtts-api"
    audience: Optional[str] = "mathtts-users"


class JWTHandler:
    """Handle JWT token operations."""
    
    def __init__(self, settings: JWTSettings):
        """Initialize JWT handler."""
        self.settings = settings
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_access_token(
        self, 
        user: User,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.settings.access_token_expire_minutes
            )
        
        payload = {
            "sub": user.id,
            "username": user.username,
            "roles": [role.value for role in user.roles],
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "iss": self.settings.issuer,
            "aud": self.settings.audience,
            "jti": secrets.token_urlsafe(16)  # Unique token ID
        }
        
        return jwt.encode(
            payload, 
            self.settings.secret_key, 
            algorithm=self.settings.algorithm
        )
    
    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token."""
        expire = datetime.now(timezone.utc) + timedelta(
            days=self.settings.refresh_token_expire_days
        )
        
        payload = {
            "sub": user.id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(16)
        }
        
        return jwt.encode(
            payload,
            self.settings.secret_key,
            algorithm=self.settings.algorithm
        )
    
    def create_token_pair(self, user: User) -> Token:
        """Create access and refresh token pair."""
        access_token = self.create_access_token(user)
        refresh_token = self.create_refresh_token(user)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.settings.access_token_expire_minutes * 60
        )
    
    def decode_token(self, token: str) -> TokenData:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm],
                audience=self.settings.audience,
                issuer=self.settings.issuer
            )
            
            return TokenData(
                sub=payload["sub"],
                username=payload.get("username", ""),
                roles=payload.get("roles", []),
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
                iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
                jti=payload.get("jti")
            )
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        """Hash password."""
        return self.pwd_context.hash(password)
    
    def generate_api_key(self) -> str:
        """Generate a secure API key."""
        return f"mtts_{secrets.token_urlsafe(32)}"
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage."""
        return self.pwd_context.hash(api_key)
    
    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """Verify API key against hash."""
        return self.pwd_context.verify(api_key, hashed_key)