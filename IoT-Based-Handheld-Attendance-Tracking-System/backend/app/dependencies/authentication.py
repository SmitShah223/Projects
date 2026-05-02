"""
dependencies/authentication.py — Simple admin token authentication.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from app.config.settings import settings

security = HTTPBasic()

def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    correct_user = secrets.compare_digest(
        credentials.username, settings.admin_username
    )
    correct_pass = secrets.compare_digest(
        credentials.password, settings.admin_password
    )
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
