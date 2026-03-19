from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from my_site.database.db import get_db
from my_site.database.schema import LoginRequest, LoginResponse
from my_site.database import models

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Быстрый вход/регистрация по email"""

    # Ищем или создаём пользователя
    user = db.query(models.UserProfile).filter(models.UserProfile.email == request.email).first()

    if not user:
        user = models.UserProfile(email=request.email, location_preference=request.location)

        db.add(user)
        db.commit()
        db.refresh(user)

    # Для демо: простой "токен" (в реальном проекте — JWT)
    demo_token = f"demo_{user.id}_{request.location}"

    return LoginResponse(
        user_id=user.id,
        email=user.email,
        location=request.location or user.location_preference,
        token=demo_token
    )