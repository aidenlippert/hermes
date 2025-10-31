"""
Authentication Service

Handles user authentication, JWT tokens, and password hashing.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import secrets

from backend.database.models import User, APIKey, UserRole, SubscriptionTier
from backend.database.connection import get_db

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication and authorization service"""

    @staticmethod
    def validate_password(password: str) -> None:
        """Validate password meets requirements

        Raises:
            ValueError: If password is invalid
        """
        if not password:
            raise ValueError("Password cannot be empty")

        # Check byte length (bcrypt limit is 72 bytes)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            raise ValueError(
                f"Password is too long ({len(password_bytes)} bytes). "
                "Maximum is 72 bytes. Please use a shorter password."
            )

        # Minimum length
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password after validation

        Args:
            password: Plain text password

        Returns:
            Bcrypt hashed password

        Raises:
            ValueError: If password fails validation
        """
        # Validate before hashing
        AuthService.validate_password(password)
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash

        Args:
            plain_password: Password to verify
            hashed_password: Bcrypt hash to check against

        Returns:
            True if password matches, False otherwise
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            # If verification fails for any reason, return False
            return False

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.

        Args:
            data: Data to encode in token (user_id, email, etc.)
            expires_delta: Token expiration time

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "type": "access"})

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create a refresh token (longer expiration)"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token data or None if invalid
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

    @staticmethod
    def verify_refresh_token(token: str) -> Optional[str]:
        """
        Verify a refresh token and return the user's email.
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "refresh":
                return None
            return payload.get("sub")
        except JWTError:
            return None

    @staticmethod
    async def register_user(
        db: AsyncSession,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        username: Optional[str] = None
    ) -> User:
        """
        Register a new user.

        Args:
            db: Database session
            email: User email
            password: Plain text password (will be hashed)
            full_name: User's full name
            username: Unique username

        Returns:
            Created User object

        Raises:
            ValueError: If email already exists
        """
        # Check if email exists
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("Email already registered")

        # Check if username exists (if provided)
        if username:
            stmt = select(User).where(User.username == username)
            result = await db.execute(stmt)
            existing_username = result.scalar_one_or_none()

            if existing_username:
                raise ValueError("Username already taken")

        # Create user
        user = User(
            email=email,
            username=username,
            hashed_password=AuthService.hash_password(password),
            full_name=full_name,
            role=UserRole.USER,
            subscription_tier=SubscriptionTier.FREE
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate a user with email and password.

        Args:
            db: Database session
            email: User email
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        # Get user by email
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return None

        # Verify password
        if not AuthService.verify_password(password, user.hashed_password):
            return None

        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()

        return user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID"""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_api_key(
        db: AsyncSession,
        user_id: str,
        name: Optional[str] = None,
        rate_limit: int = 100
    ) -> APIKey:
        """
        Create an API key for a user.

        Args:
            db: Database session
            user_id: User ID
            name: Key name/description
            rate_limit: Requests per minute limit

        Returns:
            Created APIKey object
        """
        # Generate secure API key
        key = f"herm_{secrets.token_urlsafe(32)}"

        api_key = APIKey(
            user_id=user_id,
            key=key,
            name=name,
            rate_limit=rate_limit
        )

        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)

        return api_key

    @staticmethod
    async def validate_api_key(db: AsyncSession, key: str) -> Optional[User]:
        """
        Validate an API key and return associated user.

        Args:
            db: Database session
            key: API key string

        Returns:
            User object if key is valid, None otherwise
        """
        stmt = select(APIKey).where(APIKey.key == key, APIKey.is_active == True)
        result = await db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            return None

        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None

        # Update usage
        api_key.total_requests += 1
        api_key.last_used = datetime.utcnow()
        await db.commit()

        # Get user
        return await AuthService.get_user_by_id(db, api_key.user_id)

    @staticmethod
    async def get_api_key(db: AsyncSession, key: str) -> Optional[APIKey]:
        """Fetch APIKey record by key string"""
        stmt = select(APIKey).where(APIKey.key == key, APIKey.is_active == True)
        result = await db.execute(stmt)
        api_key = result.scalar_one_or_none()
        if not api_key:
            return None
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None
        return api_key

    @staticmethod
    def check_rate_limit(user: User) -> bool:
        """
        Check if user is within their rate limit.

        Args:
            user: User object

        Returns:
            True if within limit, False if exceeded
        """
        # TODO: Implement Redis-based rate limiting
        # For now, just check subscription tier limits

        limits = {
            SubscriptionTier.FREE: 100,      # 100 requests/month
            SubscriptionTier.PRO: 1000,      # 1000 requests/month
            SubscriptionTier.ENTERPRISE: -1   # Unlimited
        }

        limit = limits.get(user.subscription_tier, 100)

        if limit == -1:  # Unlimited
            return True

        return user.requests_this_month < limit


# FastAPI dependency for getting current user from JWT token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token from request header
        db: Database session

    Returns:
        User object if token is valid

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )

        # Get user from database
        user = await AuthService.get_user_by_id(db, user_id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return user

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )
