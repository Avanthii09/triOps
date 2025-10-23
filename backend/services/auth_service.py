from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database.models import Customer
from schemas import TokenData
import os

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Verify and decode JWT token."""
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
        token_data = TokenData(customer_id=customer_id)
    except JWTError:
        raise credentials_exception
    
    return token_data

def get_current_customer(token_data: TokenData = Depends(verify_token), db: Session = Depends(get_db)) -> Customer:
    """Get current authenticated customer."""
    customer = db.query(Customer).filter(Customer.customer_id == token_data.customer_id).first()
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer not found"
        )
    return customer

def get_current_admin_customer(current_customer: Customer = Depends(get_current_customer)) -> Customer:
    """Get current authenticated admin customer."""
    if current_customer.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_customer

def authenticate_customer(db: Session, email: str, password: str) -> Optional[Customer]:
    """Authenticate a customer with email and password."""
    customer = db.query(Customer).filter(Customer.email == email).first()
    if not customer:
        return None
    if not verify_password(password, customer.password_hash):
        return None
    return customer
