from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from app.core.config import settings
from app.core.database import get_collection
from app.core.redis import set_user_cache, get_user_cache
from app.models.schemas import User, UserCreate, TokenData, TokenResponse, GuestUserResponse

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# JWT Token dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        if not token:
            raise credentials_exception
        
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        token_data = TokenData(**payload)
        
        # Get user from cache or database
        user_data = await get_user_cache(token_data.user_id)
        if not user_data:
            collection = await get_collection("users")
            user = await collection.find_one({"_id": token_data.user_id})
            if not user:
                raise credentials_exception
            
            # Cache user data
            user_data = {
                "id": str(user["_id"]),
                "openid": user["openid"],
                "username": user["username"],
                "avatar_url": user["avatar_url"],
                "subscription_level": user["subscription_level"],
                "quota_used": user["quota_used"],
                "quota_limit": user["quota_limit"],
                "quota_reset_date": user["quota_reset_date"],
                "is_active": user["is_active"]
            }
            await set_user_cache(token_data.user_id, user_data)
        
        if not user_data.get("is_active", False):
            raise HTTPException(
                status_code=401,
                detail="User account is inactive"
            )
        
        return user_data
        
    except JWTError:
        raise credentials_exception
    except Exception as e:
        logger.error(f"Authentication error: {e}")
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

# Get user by ID helper
async def get_user_by_id(user_id: str):
    """Get user by ID"""
    try:
        user_data = await get_user_cache(user_id)
        if user_data:
            return user_data
        
        collection = await get_collection("users")
        user = await collection.find_one({"_id": user_id})
        if not user:
            return None
        
        return {
            "id": str(user["_id"]),
            "openid": user["openid"],
            "username": user["username"],
            "avatar_url": user["avatar_url"],
            "subscription_level": user["subscription_level"],
            "quota_used": user["quota_used"],
            "quota_limit": user["quota_limit"],
            "quota_reset_date": user["quota_reset_date"],
            "is_active": user["is_active"]
        }
        
    except Exception as e:
        logger.error(f"Get user by ID error: {e}")
        return None

@router.post("/guest", response_model=GuestUserResponse)
async def guest_login(user_data: UserCreate):
    """Create guest user session"""
    try:
        from app.core.redis import increment_user_quota
        
        # Generate guest user ID
        import time
        timestamp = int(time.time())
        guest_id = f"guest_{timestamp}"
        
        # Create guest user data
        guest_user = {
            "openid": guest_id,
            "username": user_data.username or "游客用户",
            "avatar_url": f"https://ui-avatars.com/api/?name=Guest&background=10B981&color=fff",
            "subscription_level": "free",
            "quota_used": 0,
            "quota_limit": settings.GUEST_DAILY_LIMIT,
            "quota_reset_date": datetime.utcnow() + timedelta(days=1),
            "is_active": True,
            "last_login_at": datetime.utcnow()
        }
        
        # Save to database
        collection = await get_collection("users")
        result = await collection.insert_one(guest_user)
        
        user_id = str(result.inserted_id)
        
        # Generate JWT tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = jwt.encode(
            {
                "user_id": user_id,
                "openid": guest_id,
                "subscription_level": guest_user["subscription_level"]
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
            expires_delta=access_token_expires
        )
        
        refresh_token = jwt.encode(
            {"user_id": user_id, "openid": guest_id},
            settings.JWT_REFRESH_SECRET,
            algorithm=settings.JWT_ALGORITHM,
            expires_delta=refresh_token_expires
        )
        
        logger.info(f"Guest user created: {guest_id}", extra={
            "user_id": user_id,
            "username": guest_user["username"],
            "quota_limit": guest_user["quota_limit"]
        })
        
        # Format user response
        user_response = {
            "id": user_id,
            "openid": guest_id,
            "username": guest_user["username"],
            "avatar_url": guest_user["avatar_url"],
            "subscription_level": guest_user["subscription_level"],
            "quota_used": guest_user["quota_used"],
            "quota_limit": guest_user["quota_limit"],
            "quota_reset_date": guest_user["quota_reset_date"],
            "is_active": guest_user["is_active"]
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

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    try:
        # Verify refresh token
        payload = jwt.decode(
            refresh_token,
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
        if not user or not user.get("is_active"):
            raise HTTPException(
                status_code=401,
                detail="Invalid user"
            )
        
        # Generate new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = jwt.encode(
            {
                "user_id": user["id"],
                "openid": user["openid"],
                "subscription_level": user["subscription_level"]
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
            expires_delta=access_token_expires
        )
        
        logger.info(f"Token refreshed for user: {user['openid']}")
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
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
        # In a real implementation, you might:
        # 1. Add token to blacklist
        # 2. Clear user cache
        # 3. Log the logout event
        
        logger.info(f"User logged out: {current_user['openid']}")
        
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