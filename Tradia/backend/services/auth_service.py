from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.auth import User, RefreshToken
import hashlib
import os
import secrets

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(user_id: str, db: Session):
        """Create and store refresh token"""
        # Generate random token
        token_data = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token_data.encode()).hexdigest()
        
        # Set expiration
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Store in database
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.add(refresh_token)
        db.commit()
        
        return token_data

    @staticmethod
    def verify_token(token: str, token_type: str = "access"):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            token_type_check: str = payload.get("type")
            
            if username is None or token_type_check != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return username
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        """Authenticate user credentials"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False
        if not AuthService.verify_password(password, user.hashed_password):
            return False
        return user

    @staticmethod
    def create_user(db: Session, username: str, email: str, password: str, full_name: Optional[str] = None):
        """Create new user"""
        # Check if user exists
        if db.query(User).filter(User.username == username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = AuthService.get_password_hash(password)
        
        # Create user
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str):
        """Create new access token using refresh token"""
        # Hash the provided token
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        # Find token in database
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        ).first()
        
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = db.query(User).filter(User.user_id == db_token.user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token = AuthService.create_access_token(data={"sub": user.username})
        
        return access_token

    @staticmethod
    def revoke_refresh_token(db: Session, refresh_token: str):
        """Revoke refresh token"""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()
        
        if db_token:
            db_token.is_revoked = True
            db.commit()

    @staticmethod
    def get_current_user(db: Session, token: str):
        """Get current user from token"""
        username = AuthService.verify_token(token)
        user = db.query(User).filter(User.username == username).first()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )
        
        return user

    @staticmethod
    def change_password(db: Session, user: User, current_password: str, new_password: str):
        """Change user password"""
        if not AuthService.verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        user.hashed_password = AuthService.get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        db.commit()
        
        # Revoke all refresh tokens for this user
        refresh_tokens = db.query(RefreshToken).filter(
            RefreshToken.user_id == user.user_id,
            RefreshToken.is_revoked == False
        ).all()
        
        for token in refresh_tokens:
            token.is_revoked = True
        
        db.commit()

    @staticmethod
    def update_profile(db: Session, user: User, full_name: Optional[str] = None, email: Optional[str] = None):
        """Update user profile"""
        if email and email != user.email:
            # Check if email is already taken
            if db.query(User).filter(User.email == email, User.user_id != user.user_id).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            user.email = email
        
        if full_name is not None:
            user.full_name = full_name
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        return user