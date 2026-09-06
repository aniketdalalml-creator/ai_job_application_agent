from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.core.dependencies import get_current_user
from backend.app.models import User
from backend.app.schemas import UserOut
from backend.app.services.auth_service import user_out

router = APIRouter(prefix="/api/auth", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user_out(user)
