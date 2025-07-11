"""
Authentication router for user management.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..dependencies import get_database_session
from ...auth.auth_utils import (
    PasswordUtils, create_user_token, verify_token
)
from ...auth.models import User, UserSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


class RegisterRequest(BaseModel):
    """Registration request model."""
    username: str
    email: str
    password: str
    first_name: str = None
    last_name: str = None


class UserResponse(BaseModel):
    """User information response model."""
    user_id: str
    username: str
    email: str
    first_name: str = None
    last_name: str = None
    role: str
    is_active: bool
    created_at: datetime
    last_login: datetime = None


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_database_session)
) -> LoginResponse:
    """
    User login endpoint.
    """
    try:
        # Find user by username or email
        user = db.query(User).filter(
            (User.username == request.username) | (User.email == request.username),
            User.is_active == True
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Verify password
        if not PasswordUtils.verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create access token
        access_token = create_user_token(
            user_id=str(user.user_id),
            username=user.username,
            role=user.role
        )
        
        # Update last login
        user.last_login = datetime.now()
        db.commit()
        
        # Log successful login
        logger.info(f"User {user.username} logged in successfully")
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1440 * 60,  # 24 hours in seconds
            user=user.to_dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_database_session)
) -> UserResponse:
    """
    User registration endpoint (if registration is enabled).
    """
    try:
        # Check if username already exists
        existing_user = db.query(User).filter(
            (User.username == request.username) | (User.email == request.email)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists"
            )
        
        # Create new user
        user = User(
            username=request.username,
            email=request.email,
            password_hash=PasswordUtils.hash_password(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
            role="user"  # Default role
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"New user registered: {user.username}")
        
        return UserResponse(**user.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/logout")
async def logout(
    token: str = Depends(security),
    db: Session = Depends(get_database_session)
) -> Dict[str, str]:
    """
    User logout endpoint.
    """
    try:
        # Verify token and get user
        user_id = verify_token(token.credentials)
        
        # Note: In a full implementation, you might want to blacklist the token
        # or remove it from active sessions table
        
        logger.info(f"User {user_id} logged out")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    token: str = Depends(security),
    db: Session = Depends(get_database_session)
) -> UserResponse:
    """
    Get current user information.
    """
    try:
        # Verify token and get user
        user_id = verify_token(token.credentials)
        
        user = db.query(User).filter(
            User.user_id == user_id,
            User.is_active == True
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(**user.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@router.get("/validate")
async def validate_token(
    token: str = Depends(security),
    db: Session = Depends(get_database_session)
) -> Dict[str, Any]:
    """
    Validate JWT token and return user info.
    """
    try:
        # Verify token
        user_id = verify_token(token.credentials)
        
        user = db.query(User).filter(
            User.user_id == user_id,
            User.is_active == True
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return {
            "valid": True,
            "user_id": str(user.user_id),
            "username": user.username,
            "role": user.role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        ) 