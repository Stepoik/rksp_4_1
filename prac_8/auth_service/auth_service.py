from datetime import datetime, timedelta, timezone
import os
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi import Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy import Column, Integer, String, create_engine, select, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from starlette.responses import JSONResponse

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./auth.db")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

Base = declarative_base()
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("username", name="uq_username"),
                      UniqueConstraint("email", name="uq_email"))
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), nullable=False, index=True)
    email = Column(String(256), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

Base.metadata.create_all(bind=engine)

Username = constr(strip_whitespace=True, min_length=3, max_length=64)
Password = constr(min_length=8, max_length=128)

class RegisterIn(BaseModel):
    username: Username
    email: EmailStr
    password: Password

class RegisterOut(BaseModel):
    id: int
    username: str
    email: EmailStr

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime

class VerifyOut(BaseModel):
    active: bool
    sub: Optional[str] = None
    exp: Optional[datetime] = None

class MeOut(BaseModel):
    id: int
    username: str
    email: EmailStr

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> tuple[str, datetime]:
    expire = datetime.now(tz=timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": subject, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.execute(select(User).where(User.username == username)).scalar_one_or_none()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Невалидный токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user

# ===================== Приложение =====================
app = FastAPI(title="Auth Service", version="1.0.0")

@app.post("/register", response_model=RegisterOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if get_user_by_username(db, body.username):
        raise HTTPException(status_code=409, detail="Такой username уже занят")
    if get_user_by_email(db, body.email):
        raise HTTPException(status_code=409, detail="Такой email уже зарегистрирован")
    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return RegisterOut(id=user.id, username=user.username, email=user.email)

@app.post("/login", response_model=TokenOut)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверные учетные данные")
    token, expires_at = create_access_token(subject=str(user.id))
    return TokenOut(access_token=token, expires_at=expires_at)

@app.get("/verify")
def verify(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    sub = payload.get("sub")
    return JSONResponse(
        content={"active": True},
        headers={"X-User-Id": str(sub)},
        status_code=200,
    )

@app.get("/me", response_model=MeOut)
def me(current_user: User = Depends(get_current_user)):
    return MeOut(id=current_user.id, username=current_user.username, email=current_user.email)

