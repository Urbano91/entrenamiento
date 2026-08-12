import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.models import PerfilEntrenador, UserAccount, Usuario
from app.schemas.schemas import (
    OnboardingComplete, ProvisionalPasswordChange, UsuarioLogin, UsuarioOut,
)
from app.scripts.create_user import get_password_hash, pwd_context
from app.services.permissions import AccountType, account_type, get_account

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# NOTA: En un proyecto real esto debe estar en .env. Por facilidad se usa un valor por defecto.
SECRET_KEY = os.getenv("SESSION_SECRET")
if not SECRET_KEY:
    raise RuntimeError("SESSION_SECRET no está configurado")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 semana


class LoginResponse(BaseModel):
    message: str


def user_payload(db: Session, user: Usuario) -> dict:
    account = get_account(db, user.id)
    has_profile = db.query(PerfilEntrenador.id).filter(
        PerfilEntrenador.usuario_id == user.id
    ).first() is not None
    role = account_type(db, user.id).value
    return {
        "id": user.id,
        "usuario": user.usuario,
        "activo": user.activo,
        "account_type": role,
        "must_change_password": (
            account.must_change_password if account else not has_profile
        ),
        "onboarding_complete": (
            account.onboarding_complete if account else has_profile
        ),
    }

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    
    user = db.query(Usuario).filter(Usuario.usuario == username).first()
    if user is None or not user.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o inactivo")
    account = get_account(db, user.id)
    onboarding_paths = {
        "/api/perfil", "/api/temporadas",
    }
    if (
        account is not None
        and account.must_change_password
        and not request.url.path.startswith("/api/auth/")
        and not (request.method == "GET" and request.url.path in onboarding_paths)
    ):
        raise HTTPException(
            status_code=409,
            detail="Debes cambiar la contraseña provisional para continuar",
        )
    
    return user

@router.post("/login", response_model=LoginResponse)
def login(credentials: UsuarioLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.usuario == credentials.usuario).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos."
        )
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos."
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.usuario}, expires_delta=access_token_expires
    )
    
    response.set_cookie(
        key="session",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="none",
        secure=True
    )
    
    return LoginResponse(message="Sesión iniciada correctamente")


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("session")
    return {"message": "Sesión cerrada correctamente"}

@router.get("/me", response_model=UsuarioOut)
def read_users_me(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_payload(db, current_user)


@router.post("/change-provisional-password", response_model=UsuarioOut)
def change_provisional_password(
    data: ProvisionalPasswordChange,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = get_account(db, current_user.id)
    if account is None or not account.must_change_password:
        raise HTTPException(status_code=409, detail="La cuenta no tiene una contraseña provisional")
    if verify_password(data.password, current_user.password_hash):
        raise HTTPException(
            status_code=422,
            detail="La nueva contraseña debe ser distinta de la provisional",
        )
    current_user.password_hash = get_password_hash(data.password)
    account.must_change_password = False
    account.onboarding_complete = True
    db.commit()
    db.refresh(current_user)
    return user_payload(db, current_user)


@router.post("/complete-onboarding", response_model=UsuarioOut)
def complete_onboarding(
    data: OnboardingComplete,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if account_type(db, current_user.id) is not AccountType.TRAINER:
        raise HTTPException(status_code=403, detail="El Club no utiliza perfil de entrenador")
    if verify_password(data.password, current_user.password_hash):
        raise HTTPException(
            status_code=422,
            detail="La contraseña definitiva debe ser distinta de la provisional",
        )
    profile = db.query(PerfilEntrenador).filter(
        PerfilEntrenador.usuario_id == current_user.id
    ).one_or_none()
    if profile is None:
        profile = PerfilEntrenador(usuario_id=current_user.id)
        db.add(profile)
    profile.nombre = data.nombre.strip()
    profile.apellidos = data.apellidos.strip()
    current_user.password_hash = get_password_hash(data.password)
    account = get_account(db, current_user.id)
    if account is None:
        account = UserAccount(
            user_id=current_user.id, account_type=AccountType.TRAINER.value
        )
        db.add(account)
    account.must_change_password = False
    account.onboarding_complete = True
    db.commit()
    db.refresh(current_user)
    return user_payload(db, current_user)
