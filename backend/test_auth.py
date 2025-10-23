#!/usr/bin/env python3
"""
Comprehensive test for Triops Airline Authentication API
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_auth_endpoints():
    """Test all authentication endpoints"""
    print("🧪 Testing Triops Airline Authentication API\n")
    
    # Test 1: Register a new user
    print("1. Testing user registration...")
    register_data = {
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "testpass123",
        "phone": "+1234567890"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        user_data = response.json()
        print(f"   ✅ User registered: {user_data['name']} ({user_data['customer_id']})")
    else:
        print(f"   ❌ Registration failed: {response.text}")
        return False
    
    # Test 2: Login with new user
    print("\n2. Testing user login...")
    login_data = {
        "email": "testuser@example.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        print(f"   ✅ Login successful, token received")
    else:
        print(f"   ❌ Login failed: {response.text}")
        return False
    
    # Test 3: Get current user info
    print("\n3. Testing get current user...")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        user_info = response.json()
        print(f"   ✅ User info retrieved: {user_info['name']} ({user_info['role']})")
    else:
        print(f"   ❌ Get user info failed: {response.text}")
        return False
    
    # Test 4: Try to register with existing email
    print("\n4. Testing duplicate email registration...")
    duplicate_data = {
        "name": "Another User",
        "email": "testuser@example.com",  # Same email
        "password": "differentpass",
        "phone": "+1234567891"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=duplicate_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 400:
        print(f"   ✅ Duplicate email correctly rejected: {response.json()['detail']}")
    else:
        print(f"   ❌ Duplicate email should be rejected: {response.text}")
    
    # Test 5: Login with wrong password
    print("\n5. Testing wrong password login...")
    wrong_login = {
        "email": "testuser@example.com",
        "password": "wrongpassword"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=wrong_login)
    print(f"   Status: {response.status_code}")
    if response.status_code == 401:
        print(f"   ✅ Wrong password correctly rejected: {response.json()['detail']}")
    else:
        print(f"   ❌ Wrong password should be rejected: {response.text}")
    
    # Test 6: Test with existing users
    print("\n6. Testing with existing users...")
    
    # Test admin login
    admin_login = {
        "email": "admin@airline.com",
        "password": "admin"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=admin_login)
    if response.status_code == 200:
        admin_token = response.json()['access_token']
        print(f"   ✅ Admin login successful")
        
        # Test admin user info
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        if response.status_code == 200:
            admin_info = response.json()
            print(f"   ✅ Admin info: {admin_info['name']} ({admin_info['role']})")
    
    # Test regular user login
    user_login = {
        "email": "john.doe@email.com",
        "password": "pass"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=user_login)
    if response.status_code == 200:
        print(f"   ✅ Regular user login successful")
    
    print("\n🎉 Authentication API testing completed!")
    return True

if __name__ == "__main__":
    test_auth_endpoints()
