import uuid
from database.connection import db_instance
from core.security import decode_access_token, hash_password, verify_password, create_access_token
from datetime import timedelta
from fastapi import HTTPException

users_collection = db_instance.db["users"]

class AuthService:
    @staticmethod
    def register_user(name: str, email: str, password: str, role: str):
        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_pw = hash_password(password)
        user_data = {
            "user_id": str(uuid.uuid4()),
            "name": name,
            "email": email,
            "hashed_password": hashed_pw,
            "role": role,
            "projects": []
        }
        users_collection.insert_one(user_data)
        return {"message": "User registered successfully"}

    @staticmethod
    def login_user(email: str, password: str):
        user = users_collection.find_one({"email": email})
        if not user or not verify_password(password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token({"user_id": user["user_id"], "email": user["email"], "role": user["role"]})
        return {"access_token": token, "token_type": "bearer"}
    @staticmethod
    def get_current_user(token: str):
        try:
            payload = decode_access_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")

            user = users_collection.find_one({"user_id": user_id}, {"_id": 0, "hashed_password": 0})
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            return user

        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired token")