import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.models import Usuario
from app.schemas.schemas import UsuarioLogin, UsuarioOut
from app.scripts.create_user import pwd_context

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# NOTA: En un proyecto real esto debe estar en .env. Por facilidad se usa un valor por defecto.
SECRET_KEY = os.getenv("SESSION_SECRET", "super-secret-key-entrenamiento-futbol")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 semana

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
    
    return user

@router.post("/login")
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
        samesite="lax",
        secure=False  # en prod True si hay HTTPS
    )
    
    return {"message": "Sesión iniciada correctamente"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("session")
    return {"message": "Sesión cerrada correctamente"}

@router.get("/me", response_model=UsuarioOut)
def read_users_me(current_user: Usuario = Depends(get_current_user)):
    return current_user
