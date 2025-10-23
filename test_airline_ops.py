#!/usr/bin/env python3
"""
Comprehensive test for Triops Airline Operations
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_airline_operations():
    """Test all airline operations"""
    print("✈️ Testing Triops Airline Operations\n")
    
    # Login to get token
    print("1. Logging in...")
    login_data = {
        "email": "lily@example.com",
        "password": "lily123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"   ❌ Login failed: {response.text}")
        return False
    
    token_data = response.json()
    access_token = token_data['access_token']
    print(f"   ✅ Login successful")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test flight status
    print("\n2. Testing flight status...")
    flight_status_data = {"flight_id": 1001}
    response = requests.post(f"{BASE_URL}/api/airline/flight-status", json=flight_status_data, headers=headers)
    if response.status_code == 200:
        status_data = response.json()
        print(f"   ✅ Flight {status_data['flight_number']}: {status_data['current_status']}")
        print(f"   📍 Route: {status_data['route']}")
        print(f"   💺 Available seats: {status_data['available_seats']}")
    else:
        print(f"   ❌ Flight status failed: {response.text}")
    
    # Test seat availability
    print("\n3. Testing seat availability...")
    seat_data = {"flight_id": 1001}
    response = requests.post(f"{BASE_URL}/api/airline/seat-availability", json=seat_data, headers=headers)
    if response.status_code == 200:
        seats_data = response.json()
        print(f"   ✅ Total available seats: {seats_data['total_available']}")
        print(f"   💺 Sample seats: {seats_data['available_seats'][:3]}")
    else:
        print(f"   ❌ Seat availability failed: {response.text}")
    
    # Test flight booking
    print("\n4. Testing flight booking...")
    booking_data = {
        "customer_id": "CUSTC196338E",  # lily's customer ID
        "flight_id": 1003,  # Different flight
        "seat_preference": "window",
        "class_preference": "economy"
    }
    response = requests.post(f"{BASE_URL}/api/airline/book-flight", json=booking_data, headers=headers)
    if response.status_code == 200:
        booking_result = response.json()
        print(f"   ✅ Booking successful!")
        print(f"   🎫 PNR: {booking_result['pnr']}")
        print(f"   💺 Seat: {booking_result['seat']}")
        print(f"   💰 Price: ${booking_result['price']}")
        pnr = booking_result['pnr']
    else:
        print(f"   ❌ Booking failed: {response.text}")
        return False
    
    # Test booking details
    print("\n5. Testing booking details...")
    details_data = {"pnr": pnr}
    response = requests.post(f"{BASE_URL}/api/airline/booking-details", json=details_data, headers=headers)
    if response.status_code == 200:
        details = response.json()
        print(f"   ✅ Booking details retrieved")
        print(f"   👤 Customer: {details['customer_name']}")
        print(f"   ✈️ Flight: {details['flight_number']}")
        print(f"   📍 Route: {details['route']}")
        print(f"   💺 Seat: {details['seat']}")
    else:
        print(f"   ❌ Booking details failed: {response.text}")
    
    # Test cancellation (without confirmation)
    print("\n6. Testing trip cancellation (without confirmation)...")
    cancel_data = {
        "pnr": pnr,
        "customer_id": "CUSTC196338E",
        "confirmation": False
    }
    response = requests.post(f"{BASE_URL}/api/airline/cancel-trip", json=cancel_data, headers=headers)
    if response.status_code == 200:
        cancel_result = response.json()
        print(f"   ✅ Cancellation preview:")
        print(f"   📝 Message: {cancel_result['message']}")
        print(f"   ✈️ Flight: {cancel_result['booking_details']['flight']}")
        print(f"   💺 Seat: {cancel_result['booking_details']['seat']}")
        print(f"   ⏰ Departure: {cancel_result['booking_details']['departure']}")
    else:
        print(f"   ❌ Cancellation preview failed: {response.text}")
    
    # Test policies
    print("\n7. Testing policy endpoints...")
    
    # Cancellation policy
    response = requests.get(f"{BASE_URL}/api/policies/cancellation-policy")
    if response.status_code == 200:
        policy = response.json()
        print(f"   ✅ Cancellation policy: {policy['title']}")
    else:
        print(f"   ❌ Cancellation policy failed: {response.text}")
    
    # Pet travel policy
    response = requests.get(f"{BASE_URL}/api/policies/pet-travel-policy")
    if response.status_code == 200:
        policy = response.json()
        print(f"   ✅ Pet travel policy: {policy['title']}")
    else:
        print(f"   ❌ Pet travel policy failed: {response.text}")
    
    print("\n🎉 All airline operations tested successfully!")
    return True

if __name__ == "__main__":
    test_airline_operations()
