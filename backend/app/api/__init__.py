# API package initialization
from fastapi import APIRouter

from app.api import auth, upload, translation, users, health

__all__ = ["auth", "upload", "translation", "users", "health"]