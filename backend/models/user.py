from pydantic import BaseModel, EmailStr
import uuid
from typing import List, Optional

class UserModel(BaseModel):
    user_id: str = str(uuid.uuid4())
    name: str
    email: EmailStr
    hashed_password: str  # Store hashed password securely
    role: str  # e.g., "admin", "designer"

class UserInDB(UserModel):
    projects: List[str] = []
