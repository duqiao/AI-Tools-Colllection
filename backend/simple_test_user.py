import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from passlib.context import CryptContext

def generate_password_hash(password="test123456"):
    """Generate password hash for test user"""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)

if __name__ == "__main__":
    password = "test123456"
    password_hash = generate_password_hash(password)
    print(f"Password: {password}")
    print(f"Hash: {password_hash}")
    
    # Test verification
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    is_valid = pwd_context.verify(password, password_hash)
    print(f"Verification: {is_valid}")