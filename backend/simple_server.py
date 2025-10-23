#!/usr/bin/env python3
"""
Simple FastAPI server startup script
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create a simple FastAPI app for testing
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

@app.get("/")
async def root():
    return {"message": "Triops Airline Management System API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "triops-airline-api"}

@app.get("/api/test")
async def test_endpoint():
    return {
        "message": "Backend is working!",
        "features": [
            "Flight booking",
            "Trip cancellation", 
            "Flight status checking",
            "Seat availability",
            "Policy management",
            "Admin dashboard"
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting Triops Airline Backend...")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("🧪 Test Endpoint: http://localhost:8000/api/test")
    print("")
    
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
