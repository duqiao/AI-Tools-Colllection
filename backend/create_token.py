#!/usr/bin/env python3
"""
Create a new JWT token for MySelectedUser
"""

import asyncio
import sys
import time
import uuid
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

async def create_token():
    from app.core.config import settings
    from jose import jwt
    
    # MySelectedUser information
    user_id = "68fc5af3d27a3e281b1e8b68"
    openid = "my_selected_user_permanent"
    
    # Create JWT payload
    payload = {
        "user_id": user_id,
        "openid": openid,
        "subscription_level": "premium",
        "exp": int(time.time()) + 86400,  # 24 hours
        "iat": int(time.time())
    }
    
    # Create token
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    
    print("New JWT Token for MySelectedUser:")
    print(f"Token: {token}")
    print(f"User ID: {user_id}")
    print(f"OpenID: {openid}")
    
    return token

if __name__ == "__main__":
    token = asyncio.run(create_token())
    
    # Test with curl command
    print(f"\nTest command:")
    print(f'curl -s -H "Authorization: Bearer {token}" "http://127.0.0.1:8001/api/v1/upload/jobs?limit=3"')