import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from database.models import Base
from database.database import engine
from datetime import datetime, timedelta
from decimal import Decimal

load_dotenv()

def setup_database():
    """Set up the database with tables and sample data"""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
        
        # Insert sample data
        insert_sample_data()
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        sys.exit(1)

def insert_sample_data():
    """Insert sample data into the database"""
    from sqlalchemy.orm import sessionmaker
    from database.models import Customer, Flight, Seat, Policy
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Inserting sample data...")
        
        # Insert sample customers with simple password hash
        customers_data = [
            {
                "customer_id": "CUST001",
                "name": "John Doe",
                "email": "john.doe@email.com",
                "phone": "+1234567890",
                "password_hash": "simple_hash_pass",  # Simple hash for now
                "role": "user"
            },
            {
                "customer_id": "CUST002", 
                "name": "Jane Smith",
                "email": "jane.smith@email.com",
                "phone": "+1234567891",
                "password_hash": "simple_hash_pass",
                "role": "user"
            },
            {
                "customer_id": "ADMIN001",
                "name": "Admin User",
                "email": "admin@airline.com",
                "phone": "+1234567892",
                "password_hash": "simple_hash_admin",
                "role": "admin"
            }
        ]
        
        for customer_data in customers_data:
            existing_customer = db.query(Customer).filter(Customer.customer_id == customer_data["customer_id"]).first()
            if not existing_customer:
                customer = Customer(**customer_data)
                db.add(customer)
        
        # Insert sample flights
        flights_data = [
            {
                "flight_id": 1001,
                "flight_number": "JB101",
                "airline_code": "JB",
                "source_airport_code": "JFK",
                "destination_airport_code": "LAX",
                "scheduled_departure": datetime.utcnow() + timedelta(days=1, hours=8),
                "scheduled_arrival": datetime.utcnow() + timedelta(days=1, hours=11, minutes=30),
                "current_status": "on-time",
                "total_seats": 150,
                "available_seats": 120
            },
            {
                "flight_id": 1002,
                "flight_number": "JB102",
                "airline_code": "JB",
                "source_airport_code": "LAX",
                "destination_airport_code": "JFK",
                "scheduled_departure": datetime.utcnow() + timedelta(days=1, hours=14),
                "scheduled_arrival": datetime.utcnow() + timedelta(days=1, hours=22, minutes=30),
                "current_status": "on-time",
                "total_seats": 150,
                "available_seats": 140
            },
            {
                "flight_id": 1003,
                "flight_number": "JB103",
                "airline_code": "JB",
                "source_airport_code": "JFK",
                "destination_airport_code": "SFO",
                "scheduled_departure": datetime.utcnow() + timedelta(days=2, hours=9),
                "scheduled_arrival": datetime.utcnow() + timedelta(days=2, hours=12),
                "current_status": "delayed",
                "total_seats": 200,
                "available_seats": 180
            }
        ]
        
        for flight_data in flights_data:
            existing_flight = db.query(Flight).filter(Flight.flight_id == flight_data["flight_id"]).first()
            if not existing_flight:
                flight = Flight(**flight_data)
                db.add(flight)
        
        db.commit()
        
        # Insert sample seats (reduced number for faster setup)
        seats_data = []
        for flight_id in [1001, 1002, 1003]:
            # Economy seats (rows 1-5 only for faster setup)
            for row in range(1, 6):
                for col in ['A', 'B', 'C', 'D', 'E', 'F']:
                    seats_data.append({
                        "flight_id": flight_id,
                        "row_number": row,
                        "column_letter": col,
                        "class_type": "economy",
                        "price": Decimal("299.99"),
                        "is_available": True
                    })
            
            # Business seats (rows 6-8)
            for row in range(6, 9):
                for col in ['A', 'B', 'C', 'D']:
                    seats_data.append({
                        "flight_id": flight_id,
                        "row_number": row,
                        "column_letter": col,
                        "class_type": "business",
                        "price": Decimal("599.99"),
                        "is_available": True
                    })
            
            # First class seats (rows 9-10)
            for row in range(9, 11):
                for col in ['A', 'B']:
                    seats_data.append({
                        "flight_id": flight_id,
                        "row_number": row,
                        "column_letter": col,
                        "class_type": "first",
                        "price": Decimal("999.99"),
                        "is_available": True
                    })
        
        for seat_data in seats_data:
            existing_seat = db.query(Seat).filter(
                Seat.flight_id == seat_data["flight_id"],
                Seat.row_number == seat_data["row_number"],
                Seat.column_letter == seat_data["column_letter"]
            ).first()
            if not existing_seat:
                seat = Seat(**seat_data)
                db.add(seat)
        
        # Insert sample policies
        policies_data = [
            {
                "policy_type": "cancellation",
                "title": "Standard Cancellation Policy",
                "content": "Cancellations made more than 24 hours before departure: Full refund minus $25 processing fee. Cancellations made within 24 hours: 50% refund. No refunds for no-shows.",
                "effective_date": datetime.utcnow(),
                "is_active": True
            },
            {
                "policy_type": "pet_travel",
                "title": "Pet Travel Policy",
                "content": "Small pets (under 20 lbs) are allowed in the cabin for a fee of $125. Pets must be in an approved carrier that fits under the seat. Larger pets must travel as cargo. Service animals are always welcome at no additional charge.",
                "effective_date": datetime.utcnow(),
                "is_active": True
            },
            {
                "policy_type": "baggage",
                "title": "Baggage Policy",
                "content": "Each passenger is allowed one carry-on bag and one personal item. Checked baggage fees apply: $35 for first bag, $45 for second bag. Weight limit: 50 lbs per bag.",
                "effective_date": datetime.utcnow(),
                "is_active": True
            }
        ]
        
        for policy_data in policies_data:
            existing_policy = db.query(Policy).filter(
                Policy.policy_type == policy_data["policy_type"],
                Policy.title == policy_data["title"]
            ).first()
            if not existing_policy:
                policy = Policy(**policy_data)
                db.add(policy)
        
        db.commit()
        print("Sample data inserted successfully!")
        
    except Exception as e:
        print(f"Error inserting sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_database()