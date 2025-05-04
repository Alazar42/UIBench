from fastapi import APIRouter, HTTPException, Header, Depends
from ..services.auth_service import AuthService
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/users/register/")
def register_user(data: RegisterRequest):
    return AuthService.register_user(data.name, data.email, data.password, data.role)

@router.post("/users/login/")
def login_user(data: LoginRequest):
    return AuthService.login_user(data.email, data.password)

@router.get("/users/me")
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization token missing or invalid")
    
    token = authorization.split(" ")[1]
    return AuthService.get_current_user(token)
