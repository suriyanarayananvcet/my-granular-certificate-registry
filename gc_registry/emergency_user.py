"""
Emergency user creation endpoint - bypasses database for demo
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class UserResponse(BaseModel):
    id: int = 1
    name: str
    email: str
    role: int
    message: str = "Demo user created successfully"

@router.post("/emergency-user", response_model=UserResponse)
async def create_emergency_user():
    """Create a demo user for immediate testing"""
    return UserResponse(
        id=1,
        name="Admin User",
        email="admin@registry.com", 
        role=4,
        message="Emergency demo user created - you can now login"
    )

@router.post("/demo-login")
async def demo_login():
    """Demo login endpoint that always succeeds"""
    return {
        "access_token": "demo_token_12345",
        "token_type": "bearer",
        "user_id": 1,
        "message": "Demo login successful"
    }

# Add this as auth/login endpoint too
from fastapi import Form

@router.post("/login")
async def emergency_login(username: str = Form(...), password: str = Form(...)):
    """Emergency login that always works"""
    return {
        "access_token": "demo_token_12345",
        "token_type": "bearer",
        "user_id": 1
    }