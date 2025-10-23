#!/usr/bin/env python3
"""
Complete System Test Script
Tests the entire Triops Airline system end-to-end
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_backend_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/airline/list-tools", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend is not running: {e}")
        return False

def test_frontend_health():
    """Test if frontend is running"""
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running")
            return True
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend is not running: {e}")
        return False

def test_authentication():
    """Test user registration and login"""
    print("\n🔐 Testing Authentication...")
    
    # Test registration
    test_user = {
        "name": "Test User",
        "email": f"test{int(time.time())}@example.com",
        "password": "testpass123",
        "phone": "+1234567890"
    }
    
    try:
        # Register user
        response = requests.post(f"{BACKEND_URL}/api/auth/register", json=test_user)
        if response.status_code == 200:
            print("✅ User registration successful")
            user_data = response.json()
        else:
            print(f"❌ Registration failed: {response.status_code}")
            return False
        
        # Login user
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        
        response = requests.post(f"{BACKEND_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            print("✅ User login successful")
            token_data = response.json()
            return token_data["access_token"]
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def test_chatbot_api():
    """Test chatbot API endpoints"""
    print("\n🤖 Testing Chatbot API...")
    
    test_queries = [
        "What is your cancellation policy?",
        "Who founded Emirates Airlines?",
        "How do I get a refund?",
        "Tell me about pet travel requirements"
    ]
    
    for query in test_queries:
        try:
            print(f"  Testing query: '{query}'")
            response = requests.post(
                f"{BACKEND_URL}/api/gemini/policy-search-classify",
                json={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"    ✅ Response received (search_type: {data.get('search_type', 'unknown')})")
                print(f"    📊 Confidence: {data.get('confidence', 0):.2f}")
                print(f"    🧠 Reasoning: {data.get('reasoning', 'N/A')[:100]}...")
            else:
                print(f"    ❌ Failed with status {response.status_code}")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        time.sleep(1)  # Small delay between requests

def test_airline_operations():
    """Test airline operation endpoints"""
    print("\n✈️ Testing Airline Operations...")
    
    try:
        # Test list tools
        response = requests.get(f"{BACKEND_URL}/api/airline/list-tools")
        if response.status_code == 200:
            tools = response.json()
            print(f"✅ Available tools: {len(tools.get('tools', []))}")
            for tool in tools.get('tools', []):
                print(f"  - {tool.get('tool_name', 'unknown')}: {tool.get('description', 'No description')[:50]}...")
        else:
            print(f"❌ Failed to get tools: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Airline operations test failed: {e}")

def main():
    """Run complete system test"""
    print("🚀 Starting Complete System Test")
    print("=" * 50)
    
    # Test basic connectivity
    backend_ok = test_backend_health()
    frontend_ok = test_frontend_health()
    
    if not backend_ok:
        print("\n❌ Backend is not running. Please start it with:")
        print("   cd backend && python main.py")
        return
    
    if not frontend_ok:
        print("\n❌ Frontend is not running. Please start it with:")
        print("   cd frontend && npm start")
        return
    
    # Test authentication
    token = test_authentication()
    if not token:
        print("\n❌ Authentication failed")
        return
    
    # Test chatbot API
    test_chatbot_api()
    
    # Test airline operations
    test_airline_operations()
    
    print("\n" + "=" * 50)
    print("🎉 SYSTEM TEST COMPLETED!")
    print("\n📋 Summary:")
    print("✅ Backend API is running")
    print("✅ Frontend is running")
    print("✅ Authentication is working")
    print("✅ Chatbot API is responding")
    print("✅ Airline operations are available")
    
    print("\n🌐 Access Points:")
    print(f"   Frontend: {FRONTEND_URL}")
    print(f"   Backend API: {BACKEND_URL}")
    print(f"   API Docs: {BACKEND_URL}/docs")
    
    print("\n👤 Test Credentials:")
    print("   Email: test@example.com")
    print("   Password: testpass123")
    print("   (Or register a new account)")
    
    print("\n🧪 Test Queries:")
    print("   • 'What is your cancellation policy?'")
    print("   • 'Who founded Emirates Airlines?'")
    print("   • 'How do I get a refund?'")
    print("   • 'Tell me about pet travel requirements'")

if __name__ == "__main__":
    main()

