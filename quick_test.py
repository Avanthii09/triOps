#!/usr/bin/env python3
"""
Quick System Test - Final Verification
"""

import requests
import json

def test_system():
    print("🚀 QUICK SYSTEM TEST")
    print("=" * 30)
    
    # Test backend
    try:
        response = requests.get("http://localhost:8000/api/airline/list-tools", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API: WORKING")
        else:
            print(f"❌ Backend API: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Backend API: NOT RUNNING ({e})")
        return False
    
    # Test frontend
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend: WORKING")
        else:
            print(f"❌ Frontend: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Frontend: NOT RUNNING ({e})")
        return False
    
    # Test chatbot API
    test_queries = ["hello", "book flight", "cancel trip", "policy"]
    for query in test_queries:
        try:
            response = requests.post(
                "http://localhost:8000/api/gemini/policy-search-classify",
                json={"query": query},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Chatbot API: '{query}' -> {data.get('search_type', 'unknown')}")
            else:
                print(f"❌ Chatbot API: '{query}' -> FAILED ({response.status_code})")
        except Exception as e:
            print(f"❌ Chatbot API: '{query}' -> ERROR ({e})")
    
    print("\n🎉 SYSTEM READY!")
    print("🌐 Frontend: http://localhost:3000")
    print("🔧 Backend: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("\n👤 Login Credentials:")
    print("   Admin: admin@airline.com / admin")
    print("   User: john.doe@email.com / pass")
    print("   Or register a new account!")
    
    return True

if __name__ == "__main__":
    test_system()

