"""
FastAPI Dependencies
Authentication and authorization dependencies
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from .database import get_db
from .security import decode_access_token
from backend.app.models.user import User

security = HTTPBearer()

# Role-based permissions
ROLE_PERMISSIONS = {
    "admin": [
        "dashboard:view",
        "vehicles:view", "vehicles:create", "vehicles:edit", "vehicles:delete",
        "drivers:view", "drivers:create", "drivers:edit", "drivers:delete",
        "trips:view", "trips:create", "trips:edit", "trips:delete", "trips:dispatch",
        "maintenance:view", "maintenance:create", "maintenance:edit", "maintenance:delete",
        "fuel:view", "fuel:create", "fuel:edit", "fuel:delete",
        "expenses:view", "expenses:create", "expenses:edit", "expenses:delete", "expenses:approve",
        "analytics:view",
        "reports:view", "reports:export",
        "users:view", "users:create", "users:edit", "users:delete",
        "audit:view",
    ],
    "fleet_manager": [
        "dashboard:view",
        "vehicles:view", "vehicles:create", "vehicles:edit",
        "drivers:view", "drivers:create", "drivers:edit",
        "trips:view", "trips:create", "trips:edit", "trips:dispatch",
        "maintenance:view", "maintenance:create", "maintenance:edit",
        "fuel:view", "fuel:create", "fuel:edit",
        "expenses:view", "expenses:create", "expenses:edit",
        "analytics:view",
        "reports:view", "reports:export",
    ],
    "dispatcher": [
        "dashboard:view",
        "vehicles:view",
        "drivers:view",
        "trips:view", "trips:create", "trips:edit", "trips:dispatch",
        "fuel:view", "fuel:create",
        "expenses:view", "expenses:create",
    ],
    "safety_officer": [
        "dashboard:view",
        "vehicles:view",
        "drivers:view", "drivers:edit",
        "trips:view",
        "maintenance:view", "maintenance:create", "maintenance:edit",
        "analytics:view",
        "reports:view",
    ],
    "financial_analyst": [
        "dashboard:view",
        "vehicles:view",
        "trips:view",
        "fuel:view",
        "expenses:view", "expenses:approve",
        "analytics:view",
        "reports:view", "reports:export",
    ],
}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    return user


def require_permission(permission: str):
    """Dependency factory for permission checking"""
    async def permission_checker(current_user: User = Depends(get_current_user)):
        user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required"
            )
        return current_user
    return permission_checker


def require_any_permission(permissions: List[str]):
    """Dependency factory for checking any of multiple permissions"""
    async def permission_checker(current_user: User = Depends(get_current_user)):
        user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
        if not any(p in user_permissions for p in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        return current_user
    return permission_checker
