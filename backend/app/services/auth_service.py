"""
Authentication Service Module

This module handles authentication-related logic:
- Password hashing and verification
- JWT token creation and validation
- Current user extraction from token

Uses bcrypt for password hashing and python-jose for JWT.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import TokenData


# Password hashing context
# bcrypt is a secure, slow-by-design hashing algorithm
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"  # Auto-upgrade old hashes
)

# OAuth2 scheme for extracting token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_password_hash(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Args:
        password (str): Plain text password to hash
    
    Returns:
        str: Bcrypt hashed password
    
    Example:
        hashed = get_password_hash("mypassword123")
        # Returns something like: $2b$12$LQv3c1yqBWVHxk...
    """
    return pwd_context.hash(secret=password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password (str): The password to check
        hashed_password (str): The stored hashed password
    
    Returns:
        bool: True if password matches, False otherwise
    
    Example:
        if verify_password("mypassword123", stored_hash):
            print("Password correct!")
    """
    return pwd_context.verify(secret=plain_password, hash=hashed_password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    The token contains the user's email and expiration time.
    It's signed with the secret key to prevent tampering.
    
    Args:
        data (dict): Data to encode in the token (usually {"sub": email})
        expires_delta (timedelta): Optional custom expiration time
    
    Returns:
        str: Encoded JWT token
    
    Example:
        token = create_access_token(
            data={"sub": "user@example.com"},
            expires_delta=timedelta(hours=1)
        )
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    
    # Encode the JWT
    encoded_jwt = jwt.encode(
        claims=to_encode,
        key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Extract and validate current user from JWT token.
    
    This is a FastAPI dependency that:
    1. Extracts the token from Authorization header
    2. Decodes and validates the JWT
    3. Looks up the user in the database
    4. Returns the user object
    
    Args:
        token (str): JWT token from Authorization header
        db (AsyncSession): Database session
    
    Returns:
        User: The authenticated user object
    
    Raises:
        HTTPException 401: If token is invalid or user not found
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"message": f"Hello, {user.username}!"}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token=token,
            key=settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Extract email from token
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        
        token_data = TokenData(email=email)
        
    except JWTError:
        raise credentials_exception
    
    # Look up user in database
    result = await db.execute(
        select(User).where(User.email == token_data.email)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    return user
