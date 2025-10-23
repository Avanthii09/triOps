from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uvicorn
import os
from dotenv import load_dotenv

from database.database import get_db, engine
from database import models
from routers import auth, airline, policies, admin, query_router, gemini_tools, chat
from schemas import Token

load_dotenv()

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Triops Airline Management System",
    description="A comprehensive airline management system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(airline.router, prefix="/api/airline", tags=["Airline Operations"])
app.include_router(policies.router, prefix="/api/policies", tags=["Policies"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin Operations"])
app.include_router(query_router.router, prefix="/api/query", tags=["Query Router"])
app.include_router(gemini_tools.router, prefix="/api/gemini", tags=["Gemini Tools"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])

@app.get("/")
async def root():
    return {"message": "Triops Airline Management System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "triops-airline-api"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )