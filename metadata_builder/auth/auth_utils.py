"""
Authentication utilities for user management and security.
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from passlib.context import CryptContext
import jwt
from cryptography.fernet import Fernet
import base64
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

# Session encryption key (should be stored securely in production)
ENCRYPTION_KEY = os.getenv("SESSION_ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Generate a key for development - in production, this should be a fixed secure key
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    logger.warning("Using generated encryption key for development. Set SESSION_ENCRYPTION_KEY in production!")

fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

# Database connection for auth schema
AUTH_DATABASE_URL = os.getenv("DATABASE_URL")
AUTH_SCHEMA = os.getenv("AUTH_SCHEMA", "metadata_builder")

# Create engine for auth database
auth_engine = None
AuthSessionLocal = None

if AUTH_DATABASE_URL:
    auth_engine = create_engine(
        AUTH_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )
    AuthSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=auth_engine)


def get_database_session() -> Session:
    """Get a database session for auth operations."""
    if not AuthSessionLocal:
        raise ValueError("Database not configured. Set DATABASE_URL environment variable.")
    
    db = AuthSessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_user_token(user_id: str, username: str, role: str = "user") -> str:
    """Create a JWT token for a user."""
    token_data = {
        "sub": user_id,  # Subject (user ID)
        "username": username,
        "role": role,
        "iat": datetime.utcnow(),  # Issued at
        "type": "access"
    }
    return JWTUtils.create_access_token(token_data)


def verify_token(token: str) -> str:
    """Verify JWT token and return user_id."""
    payload = JWTUtils.verify_token(token)
    if not payload:
        raise ValueError("Invalid or expired token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Token missing user ID")
    
    return user_id


class PasswordUtils:
    """Utilities for password hashing and verification."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)


class JWTUtils:
    """Utilities for JWT token management."""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT verification failed: Token has expired")
            return None
        except jwt.InvalidSignatureError:
            logger.warning("JWT verification failed: Invalid signature")
            return None
        except jwt.DecodeError:
            logger.warning("JWT verification failed: Invalid token format")
            return None
        except Exception as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            return None
    
    @staticmethod
    def extract_user_id_from_token(token: str) -> Optional[str]:
        """Extract user ID from JWT token."""
        payload = JWTUtils.verify_token(token)
        if payload:
            return payload.get("sub")  # 'sub' is the standard JWT claim for user ID
        return None


class SessionUtils:
    """Utilities for session management and credential encryption."""
    
    @staticmethod
    def encrypt_credentials(credentials: Dict[str, str]) -> str:
        """Encrypt connection credentials for session storage."""
        try:
            json_string = json.dumps(credentials)
            encrypted_data = fernet.encrypt(json_string.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt credentials: {str(e)}")
            raise ValueError("Failed to encrypt credentials")
    
    @staticmethod
    def decrypt_credentials(encrypted_credentials: str) -> Dict[str, str]:
        """Decrypt connection credentials from session storage."""
        try:
            encrypted_data = base64.b64decode(encrypted_credentials.encode())
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {str(e)}")
            raise ValueError("Failed to decrypt credentials")
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())
    
    @staticmethod
    def is_session_expired(expires_at: datetime) -> bool:
        """Check if a session has expired."""
        return datetime.utcnow() > expires_at
    
    @staticmethod
    def get_session_expiry(hours: int = 24) -> datetime:
        """Get session expiry time."""
        return datetime.utcnow() + timedelta(hours=hours)


class AuthValidator:
    """Utilities for authentication validation."""
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """Validate password strength."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            return False, "Password must contain uppercase, lowercase, and numeric characters"
        
        return True, "Password is valid"
    
    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        """Validate username format."""
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 50:
            return False, "Username must be no more than 50 characters long"
        
        if not username.replace('_', '').replace('-', '').isalnum():
            return False, "Username can only contain letters, numbers, hyphens, and underscores"
        
        return True, "Username is valid"
    
    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """Basic email validation."""
        import re
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return True, "Email is valid"
        return False, "Invalid email format"


class SecurityUtils:
    """Additional security utilities."""
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data for logging/auditing (non-reversible)."""
        import hashlib
        return hashlib.sha256(data.encode()).hexdigest()[:16]  # First 16 chars for logging
    
    @staticmethod
    def sanitize_for_logging(data: str) -> str:
        """Sanitize sensitive data for logging."""
        if len(data) <= 4:
            return "***"
        return data[:2] + "*" * (len(data) - 4) + data[-2:]
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key."""
        return base64.b64encode(os.urandom(32)).decode()


# Example usage and testing functions
def test_auth_utils():
    """Test the authentication utilities."""
    # Test password hashing
    password = "test123"
    hashed = PasswordUtils.hash_password(password)
    assert PasswordUtils.verify_password(password, hashed)
    assert not PasswordUtils.verify_password("wrong", hashed)
    
    # Test JWT tokens
    user_data = {"sub": "user123", "username": "testuser"}
    token = JWTUtils.create_access_token(user_data)
    decoded = JWTUtils.verify_token(token)
    assert decoded["sub"] == "user123"
    
    # Test credential encryption
    credentials = {"password": "secret123", "host": "db.example.com"}
    encrypted = SessionUtils.encrypt_credentials(credentials)
    decrypted = SessionUtils.decrypt_credentials(encrypted)
    assert decrypted == credentials
    
    print("All authentication utilities tests passed!")


if __name__ == "__main__":
    test_auth_utils() 