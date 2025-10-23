from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime

from database.database import get_db
from database.models import Customer, Flight, Booking, Seat, Policy
from schemas import (
    CustomerCreate, CustomerUpdate, Customer as CustomerSchema,
    FlightCreate, FlightUpdate, Flight as FlightSchema,
    Booking as BookingSchema,
    PolicyCreate, PolicyUpdate, Policy as PolicySchema
)
from routers.auth import get_current_user

router = APIRouter()

def require_admin(current_user: Customer = Depends(get_current_user)):
    """Require admin role for access"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Customer CRUD Operations
@router.get("/customers", response_model=List[CustomerSchema])
async def get_customers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(require_admin)
):
    """Get all customers (admin only)"""
    customers = db.query(Customer).offset(skip).limit(limit).all()
    return customers

@router.get("/customers/{customer_id}", response_model=CustomerSchema)
async def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(require_admin)
):
    """Get customer by ID (admin only)"""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer

@router.post("/customers", response_model=CustomerSchema)
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(require_admin)
):
    """Create new customer (admin only)"""
    # Check if email already exists
    existing_customer = db.query(Customer).filter(Customer.email == customer_data.email).first()
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate customer ID
    import uuid
    customer_id = f"CUST{str(uuid.uuid4())[:8].upper()}"
    
    # Hash password
    from routers.auth import get_password_hash
    hashed_password = get_password_hash(customer_data.password)
    
    customer = Customer(
        customer_id=customer_id,
        name=customer_data.name,
        email=customer_data.email,
        phone=customer_data.phone,
        password_hash=hashed_password,
        role=customer_data.role
    )
    
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return customer

@router.put("/customers/{customer_id}", response_model=CustomerSchema)
async def update_customer(
    customer_id: str,
    customer_update: CustomerUpdate,
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(require_admin)
):
    """Update customer (admin only)"""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Update fields
    if customer_update.name is not None:
        customer.name = customer_update.name
    if customer_update.email is not None:
        customer.email = customer_update.email
    if customer_update.phone is not None:
        customer.phone = customer_update.phone
    if customer_update.role is not None:
        customer.role = customer_update.role
    
    customer.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(customer)
    
    return customer

@router.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(require_admin)
):
    """Delete customer (admin only)"""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Check if customer has active bookings
    active_bookings = db.query(Booking).filter(
        and_(Booking.customer_id == customer_id, Booking.booking_status == "confirmed")
    ).count()
    
    if active_bookings > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete customer with active bookings"
        )
    
    db.delete(customer)
    db.commit()
    
    return {"message": "Customer deleted successfully"}

# Flight CRUD Operations
@router.get("/flights", response_model=List[FlightSchema])
async def get_flights(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all flights (admin only)"""
    flights = db.query(Flight).offset(skip).limit(limit).all()
    return flights

@router.get("/flights/{flight_id}", response_model=FlightSchema)
async def get_flight(
    flight_id: int,
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(require_admin)
):
    """Get flight by ID (admin only)"""
    flight = db.query(Flight).filter(Flight.flight_id == flight_id).first()
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight not found"
        )
    return flight

@router.post("/flights", response_model=FlightSchema)
async def create_flight(
    flight_data: FlightCreate,
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(require_admin)
):
    """Create new flight (admin only)"""
    flight = Flight(**flight_data.dict())
    
    db.add(flight)
    db.commit()
    db.refresh(flight)
    
    return flight

@router.put("/flights/{flight_id}", response_model=FlightSchema)
async def update_flight(
    flight_id: int,
    flight_update: FlightUpdate,
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(require_admin)
):
    """Update flight (admin only)"""
    flight = db.query(Flight).filter(Flight.flight_id == flight_id).first()
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight not found"
        )
    
    # Update fields
    update_data = flight_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(flight, field, value)
    
    flight.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(flight)
    
    return flight

@router.delete("/flights/{flight_id}")
async def delete_flight(
    flight_id: int,
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(require_admin)
):
    """Delete flight (admin only)"""
    flight = db.query(Flight).filter(Flight.flight_id == flight_id).first()
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight not found"
        )
    
    # Check if flight has active bookings
    active_bookings = db.query(Booking).filter(
        and_(Booking.flight_id == flight_id, Booking.booking_status == "confirmed")
    ).count()
    
    if active_bookings > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete flight with active bookings"
        )
    
    db.delete(flight)
    db.commit()
    
    return {"message": "Flight deleted successfully"}

# Booking Management
@router.get("/bookings", response_model=List[BookingSchema])
async def get_bookings(
    skip: int = 0,
    limit: int = 100,
    booking_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all bookings (admin only)"""
    query = db.query(Booking)
    
    if booking_status:
        query = query.filter(Booking.booking_status == booking_status)
    
    bookings = query.offset(skip).limit(limit).all()
    return bookings

@router.get("/bookings/{booking_id}", response_model=BookingSchema)
async def get_booking(
    booking_id: str,
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(require_admin)
):
    """Get booking by ID (admin only)"""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    return booking

# Policy Management
@router.get("/policies", response_model=List[PolicySchema])
async def get_policies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(require_admin)
):
    """Get all policies (admin only)"""
    policies = db.query(Policy).offset(skip).limit(limit).all()
    return policies

@router.post("/policies", response_model=PolicySchema)
async def create_policy(
    policy_data: PolicyCreate,
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(require_admin)
):
    """Create new policy (admin only)"""
    policy = Policy(**policy_data.dict())
    
    db.add(policy)
    db.commit()
    db.refresh(policy)
    
    return policy

@router.put("/policies/{policy_id}", response_model=PolicySchema)
async def update_policy(
    policy_id: str,
    policy_update: PolicyUpdate,
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(require_admin)
):
    """Update policy (admin only)"""
    policy = db.query(Policy).filter(Policy.policy_id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    # Update fields
    update_data = policy_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)
    
    policy.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(policy)
    
    return policy

@router.delete("/policies/{policy_id}")
async def delete_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(require_admin)
):
    """Delete policy (admin only)"""
    policy = db.query(Policy).filter(Policy.policy_id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    db.delete(policy)
    db.commit()
    
    return {"message": "Policy deleted successfully"}

# System Statistics
@router.get("/stats")
async def get_system_stats(
    db: Session = Depends(get_db),
    admin_user: Customer = Depends(require_admin)
):
    """Get system statistics (admin only)"""
    total_customers = db.query(Customer).count()
    total_flights = db.query(Flight).count()
    total_bookings = db.query(Booking).count()
    active_bookings = db.query(Booking).filter(Booking.booking_status == "confirmed").count()
    cancelled_bookings = db.query(Booking).filter(Booking.booking_status == "cancelled").count()
    total_policies = db.query(Policy).filter(Policy.is_active == True).count()
    
    return {
        "total_customers": total_customers,
        "total_flights": total_flights,
        "total_bookings": total_bookings,
        "active_bookings": active_bookings,
        "cancelled_bookings": cancelled_bookings,
        "total_policies": total_policies
    }
