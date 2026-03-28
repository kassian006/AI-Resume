from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from my_site.database.db import get_db
from my_site.database.models import User, RefreshToken
from my_site.database.schema import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    MessageResponse,
    RefreshTokenRequest,
)
from my_site.core.security import (
    get_password_hash,
    create_access_token,
    create_refresh_token,
    authenticate_user,
    get_current_user,
    decode_token,
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    email_db = db.query(User).filter(User.email == user.email).first()
    if email_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    new_user = User(
        email=user.email,
        password_hash=get_password_hash(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@auth_router.post("/login/", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user_db = authenticate_user(db, user.email, user.password)
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token({"sub": str(user_db.id)})
    refresh_token = create_refresh_token({"sub": str(user_db.id)})

    refresh_db = RefreshToken(user_id=user_db.id, token=refresh_token)
    db.add(refresh_db)
    db.commit()

    return TokenResponse(
        token_type="bearer",
        access_token=access_token,
        refresh_token=refresh_token,
    )


@auth_router.post("/logout/", response_model=MessageResponse)
def logout(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> MessageResponse:
    stored_token = db.query(RefreshToken).filter(
        RefreshToken.token == payload.refresh_token
    ).first()

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    db.delete(stored_token)
    db.commit()

    return MessageResponse(message="Logged out successfully")


@auth_router.post("/refresh/", response_model=TokenResponse)
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> TokenResponse:
    stored_token = db.query(RefreshToken).filter(
        RefreshToken.token == payload.refresh_token
    ).first()

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    try:
        token_payload = decode_token(payload.refresh_token)

        if token_payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token type",
            )

        user_id_raw = token_payload.get("sub")
        if user_id_raw is None or int(user_id_raw) != stored_token.user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token user mismatch",
            )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    access_token = create_access_token({"sub": str(stored_token.user_id)})

    return TokenResponse(
        token_type="bearer",
        access_token=access_token,
        refresh_token=payload.refresh_token,
    )


@auth_router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return current_user