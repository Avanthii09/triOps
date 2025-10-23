from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import uuid

# Customer Schemas
class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: str = "user"

class CustomerCreate(CustomerBase):
    password: str

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[str] = None

class Customer(CustomerBase):
    customer_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Flight Schemas
class FlightBase(BaseModel):
    flight_number: str
    airline_code: str
    source_airport_code: str
    destination_airport_code: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    total_seats: int
    available_seats: int

class FlightCreate(FlightBase):
    current_departure: Optional[datetime] = None
    current_arrival: Optional[datetime] = None
    current_status: str = "scheduled"
    aircraft_type: Optional[str] = None

class FlightUpdate(BaseModel):
    current_departure: Optional[datetime] = None
    current_arrival: Optional[datetime] = None
    current_status: Optional[str] = None
    available_seats: Optional[int] = None

class Flight(FlightBase):
    flight_id: int
    current_departure: Optional[datetime]
    current_arrival: Optional[datetime]
    current_status: str
    aircraft_type: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Booking Schemas
class BookingBase(BaseModel):
    pnr: str
    customer_id: str
    flight_id: int
    source_airport_code: str
    destination_airport_code: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    assigned_seat: Optional[str] = None

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    assigned_seat: Optional[str] = None
    current_status: Optional[str] = None
    booking_status: Optional[str] = None
    cancellation_date: Optional[datetime] = None
    cancellation_charges: Optional[Decimal] = None
    refund_amount: Optional[Decimal] = None
    refund_date: Optional[datetime] = None

class Booking(BookingBase):
    booking_id: uuid.UUID
    current_departure: Optional[datetime]
    current_arrival: Optional[datetime]
    current_status: str
    booking_status: str
    cancellation_date: Optional[datetime]
    cancellation_charges: Optional[Decimal]
    refund_amount: Optional[Decimal]
    refund_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Seat Schemas
class SeatBase(BaseModel):
    flight_id: int
    row_number: int
    column_letter: str
    seat_class: str
    price: Decimal

class SeatCreate(SeatBase):
    pass

class SeatUpdate(BaseModel):
    is_available: Optional[bool] = None
    booking_id: Optional[uuid.UUID] = None

class Seat(SeatBase):
    seat_id: uuid.UUID
    is_available: bool
    booking_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Session Schemas
class SessionBase(BaseModel):
    customer_id: str
    intent_type: str
    current_step: Optional[str] = None
    collected_data: Optional[str] = None
    status: str = "active"

class SessionCreate(SessionBase):
    pass

class SessionUpdate(BaseModel):
    current_step: Optional[str] = None
    collected_data: Optional[str] = None
    status: Optional[str] = None

class Session(SessionBase):
    session_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Policy Schemas
class PolicyBase(BaseModel):
    policy_type: str
    title: str
    content: str
    effective_date: datetime
    expiry_date: Optional[datetime] = None
    is_active: bool = True

class PolicyCreate(PolicyBase):
    pass

class PolicyUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class Policy(PolicyBase):
    policy_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    customer_id: Optional[str] = None

# API Response Schemas
class BookingResponse(BaseModel):
    pnr: str
    seat: str
    class_type: str
    price: Decimal
    message: str

class CancellationResponse(BaseModel):
    pnr: str
    cancellation_charges: Decimal
    refund_amount: Decimal
    refund_date: datetime
    message: str

class FlightStatusResponse(BaseModel):
    flight_number: str
    route: str
    scheduled_departure: datetime
    current_status: str
    seat: Optional[str] = None
    available_seats: Optional[int] = None

class SeatAvailabilityResponse(BaseModel):
    flight_id: int
    available_seats: List[dict]
    total_available: int
