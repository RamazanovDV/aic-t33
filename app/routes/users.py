from typing import Optional
from fastapi import APIRouter, HTTPException
from app.models import User
from app import database

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[User])
def list_users():
    return database.load_users()


@router.get("/{user_id}", response_model=User)
def get_user(user_id: str):
    users = database.load_users()
    for user in users:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")


@router.get("/{user_id}/tickets")
def get_user_tickets(user_id: str):
    users = database.load_users()
    for user in users:
        if user.id == user_id:
            tickets = database.load_tickets()
            user_tickets = [t for t in tickets if t.user_id == user_id]
            return {
                "user": user,
                "tickets": user_tickets,
                "open_tickets": user.open_tickets,
            }
    raise HTTPException(status_code=404, detail="User not found")
