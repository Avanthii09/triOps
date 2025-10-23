from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import uuid
import re

from database.database import get_db
from database.models import Customer
from schemas import UserLogin, UserRegister, Token, Customer as CustomerSchema

router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password, hashed_password):
    # For now, use simple string comparison since we're using simple hashes
    return plain_password == hashed_password.replace("simple_hash_", "")

def get_password_hash(password):
    # For now, use simple hash prefix since we're using simple verification
    return f"simple_hash_{password}"

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(Customer).filter(Customer.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        customer_id: str = payload.get("sub")
        if customer_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if user is None:
        raise credentials_exception
    return user

def generate_customer_id():
    return f"CUST{str(uuid.uuid4())[:8].upper()}"

@router.post("/register", response_model=CustomerSchema)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(Customer).filter(Customer.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new customer
    customer_id = generate_customer_id()
    hashed_password = get_password_hash(user_data.password)
    
    customer = Customer(
        customer_id=customer_id,
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=hashed_password,
        role="user"
    )
    
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return customer

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.customer_id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=CustomerSchema)
async def read_users_me(current_user: Customer = Depends(get_current_user)):
    return current_user

@router.get("/verify-token")
async def verify_token(current_user: Customer = Depends(get_current_user)):
    return {"valid": True, "user": current_user}