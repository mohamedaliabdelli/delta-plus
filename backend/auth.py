from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_session
from models_sql import User
from security import ALGORITHM, create_token, hash_password, verify_password

router = APIRouter(tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

ROLES = {"admin", "technicien", "client"}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(401, "Token invalide ou expiré")
    user = await session.scalar(select(User).where(User.email == email))
    if not user or not user.is_active:
        raise HTTPException(401, "Utilisateur introuvable")
    return user


def require_role(*roles: str):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Accès refusé")
        return user

    return checker


class RegisterIn(BaseModel):
    email: str
    password: str
    role: str = "technicien"


@router.post("/register")
async def register(
    data: RegisterIn,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_role("admin")),
):
    if data.role not in ROLES:
        raise HTTPException(400, f"Rôle invalide. Choix : {', '.join(sorted(ROLES))}")
    exists = await session.scalar(select(User).where(User.email == data.email))
    if exists:
        raise HTTPException(400, "Email déjà utilisé")
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role,
    )
    session.add(user)
    await session.commit()
    return {"id": user.id, "email": user.email, "role": user.role}


@router.post("/login")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    user = await session.scalar(select(User).where(User.email == form.username))
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Identifiants incorrects")
    return {"access_token": create_token(user.email, user.role), "token_type": "bearer"}