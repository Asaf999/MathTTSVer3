"""Authentication router."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, EmailStr

from src.infrastructure.auth import (
    JWTHandler, User, Token, UserRole,
    get_jwt_handler, get_user_repository,
    CurrentUser, AdminUser
)
from src.infrastructure.auth.repositories import UserRepository


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    }
)


class LoginRequest(BaseModel):
    """Login request model."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class RegisterRequest(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    
    
class UserResponse(BaseModel):
    """User response model."""
    id: str
    username: str
    email: Optional[str]
    is_active: bool
    is_verified: bool
    roles: list[str]
    
    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        """Create from User model."""
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_verified=user.is_verified,
            roles=[role.value for role in user.roles]
        )


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str = Field(..., min_length=6)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    user_repo: UserRepository = Depends(get_user_repository)
) -> Token:
    """
    Login with username/email and password.
    
    Returns JWT access and refresh tokens.
    """
    # Try to find user by username or email
    user = await user_repo.get_by_username(form_data.username)
    if not user:
        user = await user_repo.get_by_email(form_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verify password
    if not jwt_handler.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Create token pair
    return jwt_handler.create_token_pair(user)


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    request: RegisterRequest,
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserResponse:
    """
    Register a new user.
    
    Note: In production, this would send a verification email.
    """
    # Check if username/email already exists
    if await user_repo.get_by_username(request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if await user_repo.get_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    import uuid
    user = User(
        id=str(uuid.uuid4()),
        username=request.username,
        email=request.email,
        hashed_password=jwt_handler.hash_password(request.password),
        is_active=True,
        is_verified=False,  # Would require email verification in production
        roles=[UserRole.USER]
    )
    
    created_user = await user_repo.create(user)
    return UserResponse.from_user(created_user)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str = Field(..., description="Refresh token"),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    user_repo: UserRepository = Depends(get_user_repository)
) -> Token:
    """
    Refresh access token using refresh token.
    """
    try:
        # Decode refresh token
        token_data = jwt_handler.decode_token(refresh_token)
        
        # Verify it's a refresh token
        # In production, would check token type in payload
        
        # Get user
        user = await user_repo.get_by_id(token_data.sub)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new token pair
        return jwt_handler.create_token_pair(user)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: CurrentUser
) -> UserResponse:
    """
    Get current authenticated user.
    """
    return UserResponse.from_user(current_user)


@router.post("/change-password", status_code=204)
async def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser,
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Change current user's password.
    """
    # Verify current password
    if not jwt_handler.verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = jwt_handler.hash_password(request.new_password)
    await user_repo.update(current_user)
    
    return Response(status_code=204)


@router.post("/logout", status_code=204)
async def logout(
    current_user: CurrentUser
):
    """
    Logout current user.
    
    Note: With JWT, logout is typically handled client-side by removing the token.
    In production, might invalidate the token server-side.
    """
    # In production, would add token to blacklist
    return Response(status_code=204)


# Admin endpoints

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    admin_user: AdminUser,
    user_repo: UserRepository = Depends(get_user_repository),
    limit: int = 100,
    offset: int = 0
) -> list[UserResponse]:
    """
    List all users (admin only).
    """
    users = await user_repo.list_all(limit=limit, offset=offset)
    return [UserResponse.from_user(user) for user in users]


@router.put("/users/{user_id}/activate", status_code=204)
async def activate_user(
    user_id: str,
    admin_user: AdminUser,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Activate a user account (admin only).
    """
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    await user_repo.update(user)
    
    return Response(status_code=204)


@router.put("/users/{user_id}/deactivate", status_code=204)
async def deactivate_user(
    user_id: str,
    admin_user: AdminUser,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Deactivate a user account (admin only).
    """
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deactivating self
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user.is_active = False
    await user_repo.update(user)
    
    return Response(status_code=204)