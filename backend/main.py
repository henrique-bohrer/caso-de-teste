import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from backend.database import Base, engine, get_db
from backend.models import User
from backend.schemas import UserLogin, GoogleAuthSchema, TokenResponse, UserResponse
from backend import auth

load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dual Auth API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = auth.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@app.on_event("startup")
def startup_db_seed():
    db = next(get_db())
    # Create default user if not exists
    default_user = db.query(User).filter(User.email == "user@example.com").first()
    if not default_user:
        hashed_pwd = auth.get_password_hash("password123")
        user = User(
            email="user@example.com",
            name="Usuário de Teste",
            hashed_password=hashed_pwd
        )
        db.add(user)
        db.commit()


@app.post("/api/auth/login", response_model=TokenResponse)
def login_classic(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas. E-mail ou senha incorretos."
        )
    if not auth.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas. E-mail ou senha incorretos."
        )

    access_token = auth.create_access_token(
        data={"sub": str(user.id), "email": user.email, "name": user.name}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@app.post("/api/auth/google", response_model=TokenResponse)
def login_google(auth_data: GoogleAuthSchema, db: Session = Depends(get_db)):
    id_info = auth.verify_google_token(auth_data.credential_token)
    if not id_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token do Google inválido ou expirado."
        )

    email = id_info.get("email")
    google_id = id_info.get("sub")
    name = id_info.get("name", "")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token do Google não contém e-mail válido."
        )

    # Check if user exists by email or google_id
    user = db.query(User).filter((User.email == email) | (User.google_id == google_id)).first()

    if not user:
        # Register new user authenticated via Google
        user = User(
            email=email,
            name=name,
            google_id=google_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Link google_id if not linked yet
        if not user.google_id:
            user.google_id = google_id
            db.commit()
            db.refresh(user)

    access_token = auth.create_access_token(
        data={"sub": str(user.id), "email": user.email, "name": user.name}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@app.get("/api/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
