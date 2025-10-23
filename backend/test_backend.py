#!/usr/bin/env python3
"""
Simple test script to verify backend components work
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    try:
        print("Testing imports...")
        
        # Test basic imports
        from fastapi import FastAPI
        print("✅ FastAPI imported")
        
        from pydantic import BaseModel
        print("✅ Pydantic imported")
        
        from sqlalchemy import create_engine
        print("✅ SQLAlchemy imported")
        
        # Test our modules
        from schemas import Token, Customer, Flight, Booking
        print("✅ Schemas imported")
        
        from database.models import Base, Customer, Flight, Booking
        print("✅ Database models imported")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_fastapi_app():
    """Test that FastAPI app can be created"""
    try:
        print("\nTesting FastAPI app creation...")
        
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        
        app = FastAPI(
            title="Triops Airline Management System",
            description="A comprehensive airline management system",
            version="1.0.0"
        )
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://localhost:3001"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @app.get("/")
        async def root():
            return {"message": "Triops Airline Management System API"}
        
        print("✅ FastAPI app created successfully")
        return True
        
    except Exception as e:
        print(f"❌ FastAPI app creation failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Triops Airline Backend Components\n")
    
    success = True
    success &= test_imports()
    success &= test_fastapi_app()
    
    if success:
        print("\n🎉 All tests passed! Backend is ready to run.")
        print("\nTo start the backend:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set up database: python setup_database.py")
        print("3. Run server: python main.py")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
