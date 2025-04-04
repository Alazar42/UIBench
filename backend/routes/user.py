from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from ..models.user import User  # Correct relative import
from ..schema.user import UserBase, UserCreate  # Correct relative import
from ..config.database import database  # Correct relative import

user_router = APIRouter(prefix="/users", tags=["users"])

@user_router.get("/", response_model=List[UserBase])
def get_users(db: Session = Depends(database.get_db)):
    users = db.query(User).all()
    return users

@user_router.get("/{user_id}", response_model=UserBase)
def get_user(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@user_router.post("/", response_model=UserBase, status_code=201)
def create_user(user_data: UserCreate, db: Session = Depends(database.get_db)):
    new_user = User(**user_data.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@user_router.put("/{user_id}", response_model=UserBase)
def update_user(user_id: int, user_data: UserCreate, db: Session = Depends(database.get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

@user_router.delete("/{user_id}", status_code=200)
def delete_user(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}
