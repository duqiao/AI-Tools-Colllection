#!/usr/bin/env python3
"""
Pre-startup script to clean environment for PostgreSQL migration
"""

import os
import sys

def clean_environment():
    """Remove MongoDB-related environment variables that cause conflicts"""
    
    # List of environment variables to remove
    mongo_vars = [
        'mongodb_uri',
        'MONGODB_URI',
        'MONGO_URI',
        'MONGODB_URL',
        'MONGO_URL'
    ]
    
    removed_vars = []
    for var in mongo_vars:
        if var in os.environ:
            del os.environ[var]
            removed_vars.append(var)
    
    if removed_vars:
        print(f"Cleaned environment variables: {', '.join(removed_vars)}")
    
    # Set PostgreSQL environment variables if not set
    postgres_vars = {
        'POSTGRES_HOST': 'localhost',
        'POSTGRES_PORT': '5432',
        'POSTGRES_DB': 'ai_media_translation',
        'POSTGRES_USER': 'admin',
        'POSTGRES_PASSWORD': 'dev123456'
    }
    
    set_vars = []
    for var, value in postgres_vars.items():
        if var not in os.environ:
            os.environ[var] = value
            set_vars.append(var)
    
    if set_vars:
        print(f"Set PostgreSQL environment variables: {', '.join(set_vars)}")

if __name__ == "__main__":
    clean_environment()
    print("Environment prepared for PostgreSQL backend startup")