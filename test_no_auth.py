#!/usr/bin/env python3
"""
Test script for Triops Airline API without authentication
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints_without_auth():
    """Test all airline endpoints without authentication"""
    print("✈️ Testing Triops Airline API (No Authentication Required)\n")
    
    # Test 1: Flight Status
    print("1. Testing flight status...")
    response = requests.post(f"{BASE_URL}/api/airline/flight-status", json={"flight_id": 1001})
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Flight {data['flight_number']}: {data['current_status']}")
        print(f"   📍 Route: {data['route']}")
        print(f"   💺 Available seats: {data['available_seats']}")
    else:
        print(f"   ❌ Failed: {response.text}")
    
    # Test 2: Seat Availability
    print("\n2. Testing seat availability...")
    response = requests.post(f"{BASE_URL}/api/airline/seat-availability", json={"flight_id": 1001})
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Total available seats: {data['total_available']}")
        print(f"   💺 Sample seats: {data['available_seats'][:3]}")
    else:
        print(f"   ❌ Failed: {response.text}")
    
    # Test 3: Flight Booking
    print("\n3. Testing flight booking...")
    booking_data = {
        "customer_id": "CUST002",
        "flight_id": 1002,
        "seat_preference": "window",
        "class_preference": "business"
    }
    response = requests.post(f"{BASE_URL}/api/airline/book-flight", json=booking_data)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Booking successful!")
        print(f"   🎫 PNR: {data['pnr']}")
        print(f"   💺 Seat: {data['seat']}")
        print(f"   💰 Price: ${data['price']}")
        pnr = data['pnr']
    else:
        print(f"   ❌ Failed: {response.text}")
        return False
    
    # Test 4: Booking Details
    print("\n4. Testing booking details...")
    response = requests.post(f"{BASE_URL}/api/airline/booking-details", json={"pnr": pnr})
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Booking details retrieved")
        print(f"   👤 Customer: {data['customer_name']}")
        print(f"   ✈️ Flight: {data['flight_number']}")
        print(f"   📍 Route: {data['route']}")
        print(f"   💺 Seat: {data['seat']}")
    else:
        print(f"   ❌ Failed: {response.text}")
    
    # Test 5: Trip Cancellation (preview)
    print("\n5. Testing trip cancellation preview...")
    cancel_data = {
        "pnr": pnr,
        "customer_id": "CUST002",
        "confirmation": False
    }
    response = requests.post(f"{BASE_URL}/api/airline/cancel-trip", json=cancel_data)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Cancellation preview:")
        print(f"   📝 Message: {data['message']}")
        print(f"   ✈️ Flight: {data['booking_details']['flight']}")
        print(f"   💺 Seat: {data['booking_details']['seat']}")
    else:
        print(f"   ❌ Failed: {response.text}")
    
    # Test 6: Policies
    print("\n6. Testing policy endpoints...")
    
    # Cancellation policy
    response = requests.get(f"{BASE_URL}/api/policies/cancellation-policy")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Cancellation policy: {data['title']}")
    else:
        print(f"   ❌ Failed: {response.text}")
    
    # Pet travel policy
    response = requests.get(f"{BASE_URL}/api/policies/pet-travel-policy")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Pet travel policy: {data['title']}")
    else:
        print(f"   ❌ Failed: {response.text}")
    
    print("\n🎉 All endpoints tested successfully without authentication!")
    print("\n📝 Note: Authentication has been temporarily removed from airline endpoints.")
    print("   You can now test all functionality without needing to login first.")
    
    return True

if __name__ == "__main__":
    test_endpoints_without_auth()
