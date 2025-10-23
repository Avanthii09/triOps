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
    aircraft_type: Optional[str] = None
    total_seats: int
    available_seats: int

class FlightCreate(FlightBase):
    pass

class FlightUpdate(BaseModel):
    flight_number: Optional[str] = None
    airline_code: Optional[str] = None
    source_airport_code: Optional[str] = None
    destination_airport_code: Optional[str] = None
    scheduled_departure: Optional[datetime] = None
    scheduled_arrival: Optional[datetime] = None
    current_departure: Optional[datetime] = None
    current_arrival: Optional[datetime] = None
    current_status: Optional[str] = None
    aircraft_type: Optional[str] = None
    total_seats: Optional[int] = None
    available_seats: Optional[int] = None

class Flight(FlightBase):
    flight_id: int
    current_departure: Optional[datetime] = None
    current_arrival: Optional[datetime] = None
    current_status: str = "scheduled"
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
    current_departure: Optional[datetime] = None
    current_arrival: Optional[datetime] = None
    current_status: Optional[str] = None
    booking_status: Optional[str] = None
    cancellation_date: Optional[datetime] = None
    cancellation_charges: Optional[Decimal] = None
    refund_amount: Optional[Decimal] = None
    refund_date: Optional[datetime] = None

class Booking(BookingBase):
    booking_id: uuid.UUID
    current_departure: Optional[datetime] = None
    current_arrival: Optional[datetime] = None
    current_status: str = "on-time"
    booking_status: str = "confirmed"
    cancellation_date: Optional[datetime] = None
    cancellation_charges: Optional[Decimal] = None
    refund_amount: Optional[Decimal] = None
    refund_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Seat Schemas
class SeatBase(BaseModel):
    flight_id: int
    row_number: int
    column_letter: str
    class_type: str
    price: Decimal

class SeatCreate(SeatBase):
    pass

class SeatUpdate(BaseModel):
    is_available: Optional[bool] = None
    booking_id: Optional[uuid.UUID] = None

class Seat(SeatBase):
    seat_id: uuid.UUID
    is_available: bool = True
    booking_id: Optional[uuid.UUID] = None
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

class PolicyCreate(PolicyBase):
    pass

class PolicyUpdate(BaseModel):
    policy_type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class Policy(PolicyBase):
    policy_id: uuid.UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Request/Response Schemas
class FlightBookingRequest(BaseModel):
    customer_id: str
    flight_id: int
    seat_preference: Optional[str] = None
    class_preference: str = "economy"

class CancelTripRequest(BaseModel):
    pnr: str
    customer_id: str
    confirmation: bool = False

class FlightStatusRequest(BaseModel):
    flight_id: int
    pnr: Optional[str] = None

class SeatAvailabilityRequest(BaseModel):
    flight_id: int
    class_preference: Optional[str] = None

class BookingDetailsRequest(BaseModel):
    pnr: str

class PolicySearchRequest(BaseModel):
    search_term: str
    policy_type: Optional[str] = None

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    customer_id: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

# Response Schemas
class BookingResponse(BaseModel):
    booking_id: str
    pnr: str
    customer_id: str
    flight_id: int
    assigned_seat: Optional[str] = None
    status: str
    message: str

class CancellationResponse(BaseModel):
    booking_id: str
    pnr: str
    cancellation_status: str
    refund_amount: Optional[Decimal] = None
    cancellation_charges: Optional[Decimal] = None
    message: str

class FlightStatusResponse(BaseModel):
    flight_id: int
    flight_number: str
    current_status: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    current_departure: Optional[datetime] = None
    current_arrival: Optional[datetime] = None
    message: str

class SeatAvailabilityResponse(BaseModel):
    flight_id: int
    available_seats: List[dict]
    total_available: int
    message: str
