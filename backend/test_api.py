#!/usr/bin/env python3
"""
Test script for Triops Airline Backend API
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"✅ {method} {endpoint} - Status: {response.status_code}")
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
            except:
                print(f"   Response: {response.text[:200]}...")
        else:
            print(f"   Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ {method} {endpoint} - Error: {e}")
        return False

def main():
    print("🧪 Testing Triops Airline Backend API\n")
    
    # Test basic endpoints
    print("Testing basic endpoints...")
    test_endpoint("/")
    test_endpoint("/health")
    
    print("\nTesting authentication endpoints...")
    # Test registration
    test_endpoint("/api/auth/register", "POST", {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpass",
        "phone": "+1234567890"
    })
    
    # Test login
    test_endpoint("/api/auth/login", "POST", {
        "email": "john.doe@email.com",
        "password": "pass"
    })
    
    print("\nTesting airline endpoints...")
    # Test flight status
    test_endpoint("/api/airline/flight-status", "POST", {
        "flight_id": 1001
    })
    
    # Test seat availability
    test_endpoint("/api/airline/seat-availability", "POST", {
        "flight_id": 1001
    })
    
    # Test booking details
    test_endpoint("/api/airline/booking-details", "POST", {
        "pnr": "PNR001"
    })
    
    print("\nTesting policy endpoints...")
    # Test policies
    test_endpoint("/api/policies/cancellation-policy")
    test_endpoint("/api/policies/pet-travel-policy")
    
    print("\nTesting admin endpoints...")
    # Test admin stats
    test_endpoint("/api/admin/stats")
    
    print("\n🎉 API testing completed!")
    print(f"\n📚 Full API documentation available at: {BASE_URL}/docs")
    print(f"🔍 Interactive API explorer: {BASE_URL}/redoc")

if __name__ == "__main__":
    main()
