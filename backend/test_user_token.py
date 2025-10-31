"""
Generate Test User Token

This script creates a test user by calling the actual authentication endpoint
and returns a valid token that works with the authentication system.
"""

import sys
import os
import requests
import json

def create_test_user_via_api():
    """Create a test user via the actual API endpoint"""
    
    api_base_url = "http://127.0.0.1:8001/api/v1"
    
    # Test user data
    test_user_data = {
        "username": "test_user",
        "openid": "test_user_ai"
    }
    
    try:
        print("🔓 Creating test user via guest authentication...")
        
        # Call the guest authentication endpoint
        response = requests.post(
            f"{api_base_url}/auth/guest",
            json=test_user_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Test user created successfully!")
            return {
                "access_token": data.get("token", data.get("access_token")),
                "refresh_token": data.get("refresh_token"),
                "token_type": "bearer",
                "expires_in": 86400,  # 24 hours
                "user": data.get("user", {})
            }
        else:
            print(f"❌ Failed to create test user: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return None

if __name__ == "__main__":
    print("🎯 Generating Test User Token")
    print("=" * 50)
    
    try:
        result = create_test_user_via_api()
        
        if not result:
            print("❌ Failed to generate test user token")
            sys.exit(1)
        
        print("✅ Test user token generated successfully!")
        print(f"\n📋 Token Information:")
        if result.get('user'):
            print(f"   User ID: {result['user'].get('id', 'N/A')}")
            print(f"   Username: {result['user'].get('username', 'N/A')}")
            print(f"   Email: {result['user'].get('email', 'N/A')}")
            print(f"   Subscription: {result['user'].get('subscription_level', 'N/A')}")
        
        print(f"\n🔑 Access Token:")
        print(f"   {result['access_token']}")
        print(f"\n🔄 Refresh Token:")
        print(f"   {result['refresh_token']}")
        
        # Test the token by calling the profile endpoint
        print(f"\n🧪 Testing token with profile endpoint...")
        try:
            profile_response = requests.get(
                "http://127.0.0.1:8001/api/v1/users/profile",
                headers={"Authorization": f"Bearer {result['access_token']}"}
            )
            if profile_response.status_code == 200:
                print(f"✅ Profile endpoint test successful!")
                profile_data = profile_response.json()
                print(f"   Profile retrieved for: {profile_data.get('username', 'N/A')}")
            else:
                print(f"❌ Profile endpoint test failed: {profile_response.status_code}")
                print(f"   Response: {profile_response.text}")
        except Exception as e:
            print(f"❌ Profile endpoint test error: {e}")
        
        # Save tokens to file for easy use
        with open('test_user_credentials.txt', 'w') as f:
            f.write(f"ACCESS_TOKEN={result['access_token']}\n")
            f.write(f"REFRESH_TOKEN={result['refresh_token']}\n")
            if result.get('user'):
                f.write(f"USER_ID={result['user'].get('id', '')}\n")
                f.write(f"USERNAME={result['user'].get('username', '')}\n")
        
        print(f"\n💾 Credentials saved to: test_user_credentials.txt")
        print(f"\n🚀 Ready for testing! Use the access token in your Authorization header:")
        print(f"   Authorization: Bearer {result['access_token']}")
        
    except Exception as e:
        print(f"❌ Error generating token: {e}")
        sys.exit(1)