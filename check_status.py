#!/usr/bin/env python3
"""
Status check for Triops Airline System
"""

import requests
import time

def check_servers():
    """Check if both frontend and backend are running"""
    print("🔍 Checking Triops Airline System Status\n")
    
    # Check Backend
    print("Backend (FastAPI) - http://localhost:8000")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Status: {health_data['status']}")
            print(f"   📊 Version: {health_data['version']}")
        else:
            print(f"   ❌ Status: Error {response.status_code}")
    except Exception as e:
        print(f"   ❌ Status: Not reachable - {e}")
    
    # Check Frontend
    print("\nFrontend (React) - http://localhost:3000")
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            if "Triops Airline" in response.text:
                print("   ✅ Status: Running")
                print("   📱 Title: Triops Airline")
            else:
                print("   ⚠️  Status: Running but title not updated")
        else:
            print(f"   ❌ Status: Error {response.status_code}")
    except Exception as e:
        print(f"   ❌ Status: Not reachable - {e}")
    
    # Test API Communication
    print("\nAPI Communication Test")
    try:
        # Test login
        login_data = {
            "email": "john.doe@email.com",
            "password": "pass"
        }
        response = requests.post("http://localhost:8000/api/auth/login", json=login_data, timeout=5)
        if response.status_code == 200:
            print("   ✅ Authentication API: Working")
            
            # Test flight status
            flight_data = {"flight_id": 1001}
            response = requests.post("http://localhost:8000/api/airline/flight-status", json=flight_data, timeout=5)
            if response.status_code == 200:
                print("   ✅ Airline API: Working")
            else:
                print("   ❌ Airline API: Error")
        else:
            print("   ❌ Authentication API: Error")
    except Exception as e:
        print(f"   ❌ API Communication: Failed - {e}")
    
    print("\n🌐 Access Points:")
    print("   Frontend: http://localhost:3000")
    print("   Backend API: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("   Admin Dashboard: http://localhost:3000/admin")
    
    print("\n👤 Test Credentials:")
    print("   Admin: admin@airline.com / admin")
    print("   User: john.doe@email.com / pass")

if __name__ == "__main__":
    check_servers()
