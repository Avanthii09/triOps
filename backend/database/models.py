from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, DECIMAL, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql://postgres:avanthika123@localhost:5432/triops_airline"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"
    
    customer_id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    password_hash = Column(String(255))
    role = Column(String(20), default="user")  # 'user' or 'admin'
    oauth_provider = Column(String(50))  # 'google', 'facebook', 'local', etc.
    oauth_id = Column(String(255))  # External OAuth ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = relationship("Booking", back_populates="customer")

class Flight(Base):
    __tablename__ = "flights"
    
    flight_id = Column(Integer, primary_key=True)
    flight_number = Column(String(20), nullable=False)
    airline_code = Column(String(10), nullable=False)
    source_airport_code = Column(String(10), nullable=False)
    destination_airport_code = Column(String(10), nullable=False)
    scheduled_departure = Column(DateTime, nullable=False)
    scheduled_arrival = Column(DateTime, nullable=False)
    current_departure = Column(DateTime)
    current_arrival = Column(DateTime)
    current_status = Column(String(50), default="scheduled")  # on-time, delayed, cancelled, departed, arrived, scheduled
    aircraft_type = Column(String(50))
    total_seats = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = relationship("Booking", back_populates="flight")
    seats = relationship("Seat", back_populates="flight")

class Booking(Base):
    __tablename__ = "bookings"
    
    booking_id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pnr = Column(String(20), unique=True, nullable=False)
    customer_id = Column(String(100), ForeignKey("customers.customer_id"))
    flight_id = Column(Integer, ForeignKey("flights.flight_id"))
    source_airport_code = Column(String(10), nullable=False)
    destination_airport_code = Column(String(10), nullable=False)
    scheduled_departure = Column(DateTime, nullable=False)
    scheduled_arrival = Column(DateTime, nullable=False)
    assigned_seat = Column(String(10))
    current_departure = Column(DateTime)
    current_arrival = Column(DateTime)
    current_status = Column(String(50), default="on-time")  # on-time, delayed, cancelled, departed, arrived
    booking_status = Column(String(20), default="confirmed")  # confirmed, cancelled, completed
    
    # Cancellation details
    cancellation_date = Column(DateTime)
    cancellation_charges = Column(DECIMAL(10, 2))
    refund_amount = Column(DECIMAL(10, 2))
    refund_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="bookings")
    flight = relationship("Flight", back_populates="bookings")
    seats = relationship("Seat", back_populates="booking")

class Session(Base):
    __tablename__ = "sessions"
    
    session_id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(100), ForeignKey("customers.customer_id"))
    intent_type = Column(String(50))  # cancel_trip, flight_status, seat_availability, cancellation_policy, pet_travel, book_flight
    current_step = Column(String(100))  # get_pnr, confirm_details, process_cancellation, etc.
    collected_data = Column(Text)  # JSON string
    status = Column(String(20), default="active")  # active, completed, failed, waiting_input
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Seat(Base):
    __tablename__ = "seats"
    
    seat_id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flight_id = Column(Integer, ForeignKey("flights.flight_id"))
    row_number = Column(Integer, nullable=False)
    column_letter = Column(String(2), nullable=False)
    class_type = Column(String(20), nullable=False)  # economy, business, first
    price = Column(DECIMAL(10, 2), nullable=False)
    is_available = Column(Boolean, default=True)
    booking_id = Column(PostgresUUID(as_uuid=True), ForeignKey("bookings.booking_id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    flight = relationship("Flight", back_populates="seats")
    booking = relationship("Booking", back_populates="seats")

class Policy(Base):
    __tablename__ = "policies"
    
    policy_id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_type = Column(String(50), nullable=False)  # cancellation, pet_travel, baggage, etc.
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    effective_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()