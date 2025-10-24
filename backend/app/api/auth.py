from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import time
import uuid
from bson import ObjectId
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import get_collection
from app.core.redis import set_user_cache, get_user_cache
from app.models.schemas import (
    User, UserCreate, UserRegistration, UserLogin, UserResponse,
    TokenData, TokenResponse, GuestUserResponse, UserProfile, UserProfileUpdate
)

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

# JWT Token dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
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
            logger.error(f"❌ Expected fields: user_id, openid, subscription_level, exp, iat")
            raise credentials_exception
        
        # Get user from cache or database
        logger.info(f"🔍 Looking up user with ID: {token_data.user_id}")
        user_data = await get_user_cache(token_data.user_id)
        if not user_data:
            logger.info(f"📋 User not in cache, querying database...")
            collection = await get_collection("users")
            
            # Convert string ID to MongoDB ObjectId
            try:
                object_id = ObjectId(token_data.user_id)
                user = await collection.find_one({"_id": object_id})
                logger.info(f"📋 Database query result: {user is not None}")
                if not user:
                    logger.error(f"❌ User not found in database with ID: {token_data.user_id}")
                    raise credentials_exception
            except (TypeError, ValueError) as id_error:
                logger.error(f"❌ Invalid ObjectId format: {token_data.user_id}")
                logger.error(f"❌ Error details: {id_error}")
                raise credentials_exception
            
            # Cache user data
            try:
                user_id_str = str(user["_id"])
                if not ObjectId.is_valid(user_id_str):
                    logger.error(f"Invalid MongoDB ObjectId: {user_id_str}")
                    raise credentials_exception
                
                user_data = {
                    "id": user_id_str,
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
                logger.info(f"✅ User data cached successfully for ID: {user_id_str}")
            except Exception as cache_error:
                logger.error(f"Failed to cache user data: {cache_error}")
                # Continue without cache - not a fatal error
        
        if not user_data.get("is_active", False):
            raise HTTPException(
                status_code=401,
                detail="User account is inactive"
            )
        
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
        
        # Log more details for debugging
        if hasattr(e, 'detail'):
            logger.error(f"Error detail: {e.detail}")
        if hasattr(e, 'status_code'):
            logger.error(f"Error status code: {e.status_code}")
            
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
        try:
            object_id = ObjectId(user_id)
            user = await collection.find_one({"_id": object_id})
            if not user:
                logger.info(f"User not found with ID: {user_id}")
                return None
        except (TypeError, ValueError) as id_error:
            logger.error(f"Invalid ObjectId format in get_user_by_id: {user_id}")
            logger.error(f"Error details: {id_error}")
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

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserRegistration):
    """Register new user"""
    try:
        # Check if user already exists
        collection = await get_collection("users")
        
        # Check email existence
        existing_user = await collection.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="User with this email already exists"
            )
        
        # Check username existence
        existing_username = await collection.find_one({"username": user_data.username})
        if existing_username:
            raise HTTPException(
                status_code=409,
                detail="Username already exists"
            )
        
        # Hash password
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password_hash = pwd_context.hash(user_data.password)
        
        # Create user record
        user_record = {
            "email": user_data.email,
            "username": user_data.username,
            "password_hash": password_hash,
            "profile": {
                "firstName": user_data.firstName,
                "lastName": user_data.lastName,
                "organization": None,
                "avatar": None
            },
            "subscription": {
                "plan": "free",
                "limits": {
                    "maxFileSize": 50 * 1024 * 1024,  # 50MB
                    "maxStorage": 1024 * 1024 * 1024,  # 1GB
                    "monthlyMinutes": 120
                },
                "usage": {
                    "currentStorage": 0,
                    "monthlyMinutesUsed": 0,
                    "lastReset": datetime.utcnow()
                }
            },
            "preferences": {
                "defaultLanguage": None,
                "autoDeleteDays": 30,
                "notificationSettings": {
                    "email": True,
                    "push": False
                }
            },
            "isActive": True,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
            "lastLoginAt": None
        }
        
        result = await collection.insert_one(user_record)
        user_id = str(result.inserted_id)
        
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
                "email": user_data.email,
                "username": user_data.username,
                "subscription_level": "free",
                "exp": int(access_token_expires.timestamp()),  # Convert to Unix timestamp
                "iat": int(datetime.utcnow().timestamp())       # Add issued at time
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        
        refresh_token = jwt.encode(
            {
                "user_id": user_id,
                "email": user_data.email,
                "exp": int(refresh_token_expires.timestamp()),  # Convert to Unix timestamp
                "iat": int(datetime.utcnow().timestamp())       # Add issued at time
            },
            settings.JWT_REFRESH_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        
        user_response = {
            "id": user_id,
            "email": user_data.email,
            "username": user_data.username,
            "profile": {
                "firstName": user_data.firstName,
                "lastName": user_data.lastName,
                "organization": None,
                "avatar": None
            },
            "createdAt": user_record["createdAt"]
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
    """User login"""
    try:
        collection = await get_collection("users")
        user = await collection.find_one({"email": user_data.email})
        
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
        
        if not user.get("isActive", True):
            raise HTTPException(
                status_code=401,
                detail="Account is inactive"
            )
        
        # Update last login
        await collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"lastLoginAt": datetime.utcnow()}}
        )
        
        # Generate JWT tokens
        access_token_expires = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = jwt.encode(
            {
                "user_id": str(user["_id"]),
                "email": user["email"],
                "username": user["username"],
                "subscription_level": user.get("subscription", {}).get("plan", "free"),
                "exp": int(access_token_expires.timestamp()),  # Convert to Unix timestamp
                "iat": int(datetime.utcnow().timestamp())       # Add issued at time
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        
        refresh_token = jwt.encode(
            {
                "user_id": str(user["_id"]),
                "email": user["email"],
                "exp": int(refresh_token_expires.timestamp()),  # Convert to Unix timestamp
                "iat": int(datetime.utcnow().timestamp())       # Add issued at time
            },
            settings.JWT_REFRESH_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        
        logger.info(f"User logged in: {user_data.email}")
        
        user_response = {
            "id": str(user["_id"]),
            "email": user["email"],
            "username": user["username"],
            "profile": user.get("profile", {}),
            "createdAt": user.get("createdAt")
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
    """Create guest user session"""
    try:
        from app.core.redis import increment_user_quota
        
        # Test database connection first
        logger.info(f"🔍 Testing database connection...")
        test_collection = await get_collection("users")
        test_count = await test_collection.count_documents({})
        logger.info(f"✅ Database connection OK, current user count: {test_count}")
        
        # Generate guest user ID with random component to avoid collisions
        import time
        import random
        import uuid
        
        timestamp = int(time.time())
        random_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID for uniqueness
        guest_id = f"guest_{timestamp}_{random_id}"
        
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
            "last_login_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),  # Use snake_case to match BaseDocument
            "updated_at": datetime.utcnow()
        }
        
        # Save to database with verification
        logger.info(f"💾 Saving guest user to database...")
        collection = await get_collection("users")
        
        try:
            # First check if user already exists
            existing_user = await collection.find_one({"openid": guest_id})
            if existing_user:
                logger.info(f"Found existing guest user: {guest_id}")
                try:
                    user_id = str(existing_user["_id"])
                    if not ObjectId.is_valid(user_id):
                        raise ValueError(f"Invalid ObjectId in existing user: {user_id}")
                    guest_user = existing_user  # Use existing user data
                except (KeyError, ValueError) as id_error:
                    logger.error(f"Invalid user data structure: {id_error}")
                    raise HTTPException(
                        status_code=500,
                        detail="Invalid user data in database"
                    )
            else:
                # Create new user
                result = await collection.insert_one(guest_user)
                inserted_id = result.inserted_id
                
                # Validate the inserted ID
                if not isinstance(inserted_id, ObjectId):
                    logger.error(f"Invalid ObjectId type: {type(inserted_id)}")
                    raise HTTPException(
                        status_code=500,
                        detail="Invalid database ID generated"
                    )
                
                user_id = str(inserted_id)
                logger.info(f"Created new guest user with ID: {user_id}")
                
                # Important: Verify the user was created by reading it back
                created_user = await collection.find_one({"_id": inserted_id})
                if not created_user:
                    logger.error("User document not found after creation")
                    # Try to clean up the failed insertion
                    try:
                        await collection.delete_one({"_id": inserted_id})
                    except Exception as cleanup_error:
                        logger.error(f"Failed to clean up invalid user: {cleanup_error}")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to verify guest user creation"
                    )
                guest_user = created_user  # Use verified user data
                
                # Cache the new user immediately
                try:
                    await set_user_cache(user_id, {
                        "id": user_id,
                        "openid": guest_id,
                        "username": guest_user["username"],
                        "avatar_url": guest_user["avatar_url"],
                        "subscription_level": guest_user["subscription_level"],
                        "quota_used": guest_user["quota_used"],
                        "quota_limit": guest_user["quota_limit"],
                        "quota_reset_date": guest_user["quota_reset_date"],
                        "is_active": guest_user["is_active"]
                    })
                    logger.info(f"✅ New user cached successfully: {user_id}")
                except Exception as cache_error:
                    logger.error(f"Failed to cache new user: {cache_error}")
                    # Continue without cache - not a fatal error
                
            logger.info(f"✅ Guest user confirmed in database with ID: {user_id}")
            logger.info(f"📋 Guest openid: {guest_id}")
            
        except Exception as db_error:
            logger.error(f"❌ Database operation failed: {db_error}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Failed to create guest user in database"
            )
        
        # Generate JWT tokens
        access_token_expires = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token_payload = {
            "user_id": user_id,
            "openid": guest_id,
            "subscription_level": guest_user["subscription_level"],
            "exp": int(access_token_expires.timestamp()),  # Convert to Unix timestamp
            "iat": int(datetime.utcnow().timestamp())       # Add issued at time
        }
        
        refresh_token_payload = {
            "user_id": user_id,
            "openid": guest_id,
            "exp": int(refresh_token_expires.timestamp()),  # Convert to Unix timestamp
            "iat": int(datetime.utcnow().timestamp())       # Add issued at time
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
        
        logger.info(f"Guest user created: {guest_id}", extra={
            "user_id": user_id,
            "username": guest_user["username"],
            "quota_limit": guest_user["quota_limit"]
        })
        
        # Format user response to match UserResponse model
        user_response = {
            "id": user_id,
            "email": None,  # Guest users don't have email
            "openid": guest_id,
            "username": guest_user["username"],
            "avatar_url": guest_user["avatar_url"],
            "subscription_level": guest_user["subscription_level"],
            "quota_used": guest_user["quota_used"],
            "quota_limit": guest_user["quota_limit"],
            "quota_reset_date": guest_user["quota_reset_date"],
            "is_active": guest_user["is_active"],
            "last_login_at": guest_user["last_login_at"],
            "profile": None,  # Guest users don't have detailed profile
            "createdAt": guest_user.get("created_at", datetime.utcnow())
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
        access_token_expires = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = jwt.encode(
            {
                "user_id": user["id"],
                "openid": user["openid"],
                "subscription_level": user["subscription_level"],
                "exp": int(access_token_expires.timestamp()),  # Convert to Unix timestamp
                "iat": int(datetime.utcnow().timestamp())       # Add issued at time
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
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