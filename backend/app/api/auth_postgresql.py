"""
PostgreSQL-based Authentication Module

This module provides authentication functionality using PostgreSQL repositories
instead of MongoDB. It maintains backward compatibility with the existing API.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import time
import uuid
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.config import settings
from app.core.redis import set_user_cache, get_user_cache
from app.repositories.user_repository import UserRepository
from app.models.schemas import (
    User, UserCreate, UserRegistration, UserLogin, UserResponse,
    TokenData, TokenResponse, GuestUserResponse, UserProfile, UserProfileUpdate,
    SubscriptionLevel
)
from app.utils.postgres_errors import PostgresErrorHandler

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

@router.options("/guest")
async def auth_guest_options():
    """Handle CORS preflight requests for guest auth endpoint"""
    return JSONResponse(
        status_code=200,
        content={"message": "CORS preflight successful"}
    )

# JWT Token dependency using PostgreSQL
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token using PostgreSQL"""
    logger.info(f"🔐 Auth attempt - Credentials present: {bool(credentials)}")
    if credentials:
        logger.info(f"🔑 Token preview: {credentials.credentials[:30]}...")
    
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        if not token:
            raise credentials_exception
        
        logger.info(f"🔑 Decoding JWT token...")
        
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        logger.info(f"📋 JWT payload decoded successfully: {list(payload.keys())}")
        logger.info(f"📋 JWT payload data: {payload}")
        
        try:
            token_data = TokenData(**payload)
            logger.info(f"✅ TokenData created successfully")
        except Exception as validation_error:
            logger.error(f"❌ TokenData validation failed: {validation_error}")
            logger.error(f"❌ Expected fields: user_id, sub, subscription_level, exp, iat")
            raise credentials_exception
        
        # Get user from cache or PostgreSQL
        logger.info(f"🔍 Looking up user with ID: {token_data.user_id}")
        user_data = await get_user_cache(str(token_data.user_id))
        if not user_data:
            logger.info(f"📋 User not in cache, querying PostgreSQL...")
            
            async with UserRepository() as user_repo:
                user = await user_repo.get_by_id(token_data.user_id)
                logger.info(f"📋 Database query result: {user is not None}")
                if not user:
                    logger.error(f"❌ User not found in PostgreSQL with ID: {token_data.user_id}")
                    raise credentials_exception
            
            # Convert PostgreSQL user to expected format
            user_data = {
                "id": str(user["id"]),
                "username": user["username"],
                "email": user["email"],
                "subscription_level": user["subscription_level"],
                "profile": user.get("profile", {}),
                "usage_stats": user.get("usage_stats", {}),
                "last_login": user.get("last_login"),
                "created_at": user.get("created_at"),
                "updated_at": user.get("updated_at")
            }
            
            # Cache user data
            try:
                await set_user_cache(str(token_data.user_id), user_data)
                logger.info(f"✅ User data cached successfully for ID: {user['id']}")
            except Exception as cache_error:
                logger.error(f"Failed to cache user data: {cache_error}")
                # Continue without cache - not a fatal error
        
        return user_data
        
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        if "expired" in str(e).lower():
            raise HTTPException(
                status_code=401,
                detail="Token has expired. Please re-authenticate.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        raise credentials_exception
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        logger.error(f"Full exception details:", exc_info=True)
        raise credentials_exception

# Optional authentication (doesn't fail if no token)
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Optional authentication - doesn't fail if no token"""
    if not credentials or not credentials.credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except:
        return None

# Get user by ID helper using PostgreSQL
async def get_user_by_id(user_id: str):
    """Get user by ID using PostgreSQL"""
    try:
        user_data = await get_user_cache(user_id)
        if user_data:
            return user_data
        
        async with UserRepository() as user_repo:
            user = await user_repo.get_by_id(user_id)
            if not user:
                logger.info(f"User not found with ID: {user_id}")
                return None
        
        return {
            "id": str(user["id"]),
            "username": user["username"],
            "email": user["email"],
            "subscription_level": user["subscription_level"],
            "profile": user.get("profile", {}),
            "usage_stats": user.get("usage_stats", {}),
            "last_login": user.get("last_login"),
            "created_at": user.get("created_at"),
            "updated_at": user.get("updated_at")
        }
        
    except Exception as e:
        logger.error(f"Get user by ID error: {e}")
        return None

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserRegistration):
    """Register new user using PostgreSQL"""
    try:
        async with UserRepository() as user_repo:
            # Check if user already exists
            existing_user = await user_repo.get_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=409,
                    detail="User with this email already exists"
                )
            
            # Check username existence
            existing_username = await user_repo.get_by_username(user_data.username)
            if existing_username:
                raise HTTPException(
                    status_code=409,
                    detail="Username already exists"
                )
            
            # Hash password
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            password_hash = pwd_context.hash(user_data.password)
            
            # Create user record matching PostgreSQL schema
            user_record = {
                "username": user_data.username,
                "email": user_data.email,
                "password_hash": password_hash,
                "subscription_level": SubscriptionLevel.FREE,
                "profile": {
                    "first_name": user_data.firstName,
                    "last_name": user_data.lastName,
                    "avatar_url": None,
                    "preferences": {
                        "language": None,
                        "notifications": True
                    }
                },
                "usage_stats": {
                    "total_files_processed": 0,
                    "total_audio_duration": 0,
                    "api_calls_count": 0,
                    "storage_used_bytes": 0
                }
            }
            
            user_id = await user_repo.create(user_record)
            
            logger.info(f"User registered: {user_data.email}", extra={
                "user_id": user_id,
                "username": user_data.username
            })
            
            # Generate JWT tokens
            access_token_expires = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            refresh_token_expires = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            
            access_token = jwt.encode(
                {
                    "user_id": user_id,
                    "sub": user_data.email,
                    "subscription_level": SubscriptionLevel.FREE,
                    "exp": int(access_token_expires.timestamp()),
                    "iat": int(datetime.utcnow().timestamp())
                },
                settings.JWT_SECRET,
                algorithm=settings.JWT_ALGORITHM
            )
            
            refresh_token = jwt.encode(
                {
                    "user_id": user_id,
                    "sub": user_data.email,
                    "exp": int(refresh_token_expires.timestamp()),
                    "iat": int(datetime.utcnow().timestamp())
                },
                settings.JWT_REFRESH_SECRET,
                algorithm=settings.JWT_ALGORITHM
            )
            
            # Get created user for response
            created_user = await user_repo.get_by_id(user_id)
            
            user_response = {
                "id": user_id,
                "username": user_data.username,
                "email": user_data.email,
                "subscription_level": SubscriptionLevel.FREE,
                "profile": created_user.get("profile", {}),
                "usage_stats": created_user.get("usage_stats", {}),
                "created_at": created_user.get("created_at"),
                "updated_at": created_user.get("updated_at")
            }
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": user_response
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="User registration failed"
        )

@router.post("/login", response_model=dict)
async def login_user(user_data: UserLogin):
    """User login using PostgreSQL"""
    try:
        async with UserRepository() as user_repo:
            user = await user_repo.get_by_email(user_data.email)
            
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid credentials"
                )
            
            # Verify password
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            if not pwd_context.verify(user_data.password, user["password_hash"]):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid credentials"
                )
            
            # Update last login
            await user_repo.update_last_login(user["id"])
            
            # Generate JWT tokens
            access_token_expires = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            refresh_token_expires = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            
            access_token = jwt.encode(
                {
                    "user_id": str(user["id"]),
                    "sub": user["email"],
                    "subscription_level": user["subscription_level"],
                    "exp": int(access_token_expires.timestamp()),
                    "iat": int(datetime.utcnow().timestamp())
                },
                settings.JWT_SECRET,
                algorithm=settings.JWT_ALGORITHM
            )
            
            refresh_token = jwt.encode(
                {
                    "user_id": str(user["id"]),
                    "sub": user["email"],
                    "exp": int(refresh_token_expires.timestamp()),
                    "iat": int(datetime.utcnow().timestamp())
                },
                settings.JWT_REFRESH_SECRET,
                algorithm=settings.JWT_ALGORITHM
            )
            
            logger.info(f"User logged in: {user_data.email}")
            
            user_response = {
                "id": str(user["id"]),
                "username": user["username"],
                "email": user["email"],
                "subscription_level": user["subscription_level"],
                "profile": user.get("profile", {}),
                "usage_stats": user.get("usage_stats", {}),
                "created_at": user.get("created_at"),
                "updated_at": user.get("updated_at"),
                "last_login": datetime.utcnow()
            }
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": user_response
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Login failed"
        )

@router.post("/guest", response_model=GuestUserResponse)
async def guest_login(user_data: UserCreate):
    """Create guest user session using PostgreSQL"""
    try:
        logger.info(f"🔍 Creating PostgreSQL guest user...")
        
        # Generate guest user data
        timestamp = int(time.time())
        random_id = str(uuid.uuid4())[:8]
        guest_username = user_data.username or f"Guest_{random_id}"
        
        async with UserRepository() as user_repo:
            # Create guest user record
            guest_user_record = {
                "username": guest_username,
                "email": f"guest_{timestamp}_{random_id}@guest.local",  # Unique email for guests
                "password_hash": "guest_user_no_password",  # Guest users don't have passwords
                "subscription_level": SubscriptionLevel.FREE,
                "profile": {
                    "first_name": "Guest",
                    "last_name": "User",
                    "avatar_url": f"https://ui-avatars.com/api/?name=Guest&background=10B981&color=fff",
                    "is_guest": True,
                    "guest_created_at": timestamp
                },
                "usage_stats": {
                    "total_files_processed": 0,
                    "total_audio_duration": 0,
                    "api_calls_count": 0,
                    "storage_used_bytes": 0
                }
            }
            
            guest_user_id = await user_repo.create(guest_user_record)
            logger.info(f"✅ Guest user created with ID: {guest_user_id}")
            
            # Cache the guest user
            guest_user_data = {
                "id": guest_user_id,
                "username": guest_username,
                "email": guest_user_record["email"],
                "subscription_level": SubscriptionLevel.FREE,
                "profile": guest_user_record["profile"],
                "usage_stats": guest_user_record["usage_stats"],
                "last_login": datetime.utcnow(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            try:
                await set_user_cache(guest_user_id, guest_user_data)
                logger.info(f"✅ Guest user cached: {guest_user_id}")
            except Exception as cache_error:
                logger.error(f"Failed to cache guest user: {cache_error}")
        
        # Generate JWT tokens
        access_token_expires = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token_payload = {
            "user_id": uuid.UUID(guest_user_id),
            "sub": guest_user_record["email"],
            "subscription_level": SubscriptionLevel.FREE,
            "exp": int(access_token_expires.timestamp()),
            "iat": int(datetime.utcnow().timestamp())
        }
        
        refresh_token_payload = {
            "user_id": uuid.UUID(guest_user_id),
            "sub": guest_user_record["email"],
            "exp": int(refresh_token_expires.timestamp()),
            "iat": int(datetime.utcnow().timestamp())
        }
        
        access_token = jwt.encode(
            access_token_payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        
        refresh_token = jwt.encode(
            refresh_token_payload,
            settings.JWT_REFRESH_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        
        logger.info(f"Guest user created: {guest_username}", extra={
            "user_id": guest_user_id,
            "subscription_level": SubscriptionLevel.FREE
        })
        
        # Format user response to match UserResponse model
        user_response = {
            "id": guest_user_id,
            "username": guest_username,
            "email": None,  # Guest users don't have real emails
            "subscription_level": SubscriptionLevel.FREE,
            "profile": guest_user_record["profile"],
            "usage_stats": guest_user_record["usage_stats"],
            "created_at": guest_user_data["created_at"],
            "updated_at": guest_user_data["updated_at"],
            "last_login": guest_user_data["last_login"]
        }
        
        return GuestUserResponse(
            user=user_response,
            token=access_token,
            refresh_token=refresh_token
        )
        
    except Exception as e:
        logger.error(f"Guest login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Guest login failed"
        )

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using PostgreSQL"""
    try:
        # Verify refresh token
        payload = jwt.decode(
            request.refresh_token,
            settings.JWT_REFRESH_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid user"
            )
        
        # Generate new access token
        access_token_expires = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = jwt.encode(
            {
                "user_id": user["id"],
                "sub": user["email"],
                "subscription_level": user["subscription_level"],
                "exp": int(access_token_expires.timestamp()),
                "iat": int(datetime.utcnow().timestamp())
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        
        logger.info(f"Token refreshed for user: {user['username']}")
        
        return {
            "success": True,
            "data": {
                "token": new_access_token,
                "refreshToken": refresh_token,
                "tokenType": "bearer",
                "expiresIn": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        }
        
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        raise HTTPException(
            status_code=401,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Logout user"""
    try:
        # Clear user cache
        try:
            from app.core.redis import delete_user_cache
            await delete_user_cache(current_user["id"])
        except Exception:
            pass  # Cache clearing failure is not critical
        
        logger.info(f"User logged out: {current_user['username']}")
        
        return {
            "success": True,
            "message": "Logout successful"
        }
        
    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Logout failed"
        )