"""
API package initialization

This module provides the API package structure and common imports.
"""

from fastapi import APIRouter

# Create API router for v1
api_router = APIRouter()

__all__ = ["api_router"]