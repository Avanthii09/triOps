from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
import uuid
import random
import string
import re

from database.database import get_db
from database.models import Customer, Flight, Booking, Seat, Session as SessionModel
from schemas import (
    FlightBookingRequest, CancelTripRequest, FlightStatusRequest, 
    SeatAvailabilityRequest, BookingDetailsRequest, SessionCreate, SessionUpdate
)
# Authentication removed temporarily

router = APIRouter()

def generate_pnr():
    """Generate a 6-character PNR"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_hours_until_departure(departure_time):
    """Calculate hours until departure"""
    now = datetime.utcnow()
    return (departure_time - now).total_seconds() / 3600

@router.post("/book-flight")
async def book_flight(
    booking_request: FlightBookingRequest,
    db: Session = Depends(get_db)
):
    """Book a flight for a customer with seat selection"""
    try:
        # Verify customer exists
        customer = db.query(Customer).filter(Customer.customer_id == booking_request.customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Check if flight exists and has available seats
        flight = db.query(Flight).filter(
            and_(Flight.flight_id == booking_request.flight_id, Flight.available_seats > 0)
        ).first()
        
        if not flight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flight not found or no seats available"
            )
        
        # Generate PNR
        pnr = generate_pnr()
        
        # Find available seat
        seat_query = db.query(Seat).filter(
            and_(Seat.flight_id == booking_request.flight_id, Seat.is_available == True)
        )
        
        if booking_request.seat_preference:
            # Parse seat preference (e.g., "12A")
            seat_match = re.match(r'(\d+)([A-Z]+)', booking_request.seat_preference)
            if seat_match:
                row_num = int(seat_match.group(1))
                col_letter = seat_match.group(2)
                seat_query = seat_query.filter(
                    and_(Seat.row_number == row_num, Seat.column_letter == col_letter)
                )
        
        if booking_request.class_preference:
            seat_query = seat_query.filter(Seat.class_type == booking_request.class_preference)
        
        available_seat = seat_query.first()
        
        if not available_seat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No seats available matching your preferences"
            )
        
        # Create booking
        booking = Booking(
            pnr=pnr,
            customer_id=booking_request.customer_id,
            flight_id=booking_request.flight_id,
            source_airport_code=flight.source_airport_code,
            destination_airport_code=flight.destination_airport_code,
            scheduled_departure=flight.scheduled_departure,
            scheduled_arrival=flight.scheduled_arrival,
            assigned_seat=f"{available_seat.row_number}{available_seat.column_letter}",
            current_status=flight.current_status
        )
        
        db.add(booking)
        db.flush()  # Get the booking_id
        
        # Update seat availability
        available_seat.is_available = False
        available_seat.booking_id = booking.booking_id
        
        # Update flight available seats count
        flight.available_seats -= 1
        
        db.commit()
        
        return {
            "message": "Flight booked successfully",
            "pnr": pnr,
            "seat": f"{available_seat.row_number}{available_seat.column_letter}",
            "class": available_seat.class_type,
            "price": float(available_seat.price),
            "booking_id": str(booking.booking_id)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error booking flight: {str(e)}"
        )

@router.post("/cancel-trip")
async def cancel_trip(
    cancel_request: CancelTripRequest,
    db: Session = Depends(get_db)
):
    """Cancel a customer trip with confirmation workflow"""
    try:
        # Verify customer exists
        customer = db.query(Customer).filter(Customer.customer_id == cancel_request.customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Get booking details
        booking = db.query(Booking).filter(
            and_(
                Booking.pnr == cancel_request.pnr,
                Booking.customer_id == cancel_request.customer_id,
                Booking.booking_status == "confirmed"
            )
        ).first()
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found or already cancelled"
            )
        
        if not cancel_request.confirmation:
            return {
                "message": "Please confirm cancellation",
                "booking_details": {
                    "pnr": booking.pnr,
                    "flight": f"{booking.source_airport_code} to {booking.destination_airport_code}",
                    "departure": booking.scheduled_departure.isoformat(),
                    "seat": booking.assigned_seat
                },
                "confirmation_required": True
            }
        
        # Calculate refund based on cancellation policy
        hours_until_departure = get_hours_until_departure(booking.scheduled_departure)
        refund_amount = 0
        cancellation_charges = 0
        
        if hours_until_departure > 24:
            refund_amount = 100  # Full refund minus processing fee
            cancellation_charges = 25
        elif hours_until_departure > 0:
            refund_amount = 50  # 50% refund
            cancellation_charges = 50
        
        # Process cancellation
        booking.booking_status = "cancelled"
        booking.cancellation_date = datetime.utcnow()
        booking.cancellation_charges = cancellation_charges
        booking.refund_amount = refund_amount
        booking.refund_date = datetime.utcnow() + timedelta(days=7)
        
        # Free up the seat
        seat = db.query(Seat).filter(Seat.booking_id == booking.booking_id).first()
        if seat:
            seat.is_available = True
            seat.booking_id = None
        
        # Update flight available seats count
        flight = db.query(Flight).filter(Flight.flight_id == booking.flight_id).first()
        if flight:
            flight.available_seats += 1
        
        db.commit()
        
        return {
            "message": "Trip cancelled successfully",
            "pnr": booking.pnr,
            "cancellation_charges": cancellation_charges,
            "refund_amount": refund_amount,
            "refund_date": booking.refund_date.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling trip: {str(e)}"
        )

@router.post("/flight-status")
async def get_flight_status(
    status_request: FlightStatusRequest,
    db: Session = Depends(get_db)
):
    """Get current status of a flight"""
    try:
        if status_request.pnr:
            # Get flight status for specific booking
            booking = db.query(Booking).join(Flight).filter(
                and_(Booking.pnr == status_request.pnr, Flight.flight_id == status_request.flight_id)
            ).first()
            
            if not booking:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Booking not found"
                )
            
            return {
                "pnr": booking.pnr,
                "flight_number": booking.flight.flight_number,
                "route": f"{booking.source_airport_code} → {booking.destination_airport_code}",
                "scheduled_departure": booking.scheduled_departure.isoformat(),
                "current_status": booking.current_status,
                "assigned_seat": booking.assigned_seat,
                "booking_status": booking.booking_status
            }
        else:
            # Get general flight status
            flight = db.query(Flight).filter(Flight.flight_id == status_request.flight_id).first()
            
            if not flight:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Flight not found"
                )
            
            return {
                "flight_number": flight.flight_number,
                "route": f"{flight.source_airport_code} → {flight.destination_airport_code}",
                "scheduled_departure": flight.scheduled_departure.isoformat(),
                "current_status": flight.current_status,
                "available_seats": flight.available_seats
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting flight status: {str(e)}"
        )

@router.post("/seat-availability")
async def get_seat_availability(
    availability_request: SeatAvailabilityRequest,
    db: Session = Depends(get_db)
):
    """Get available seats for a flight"""
    try:
        query = db.query(Seat).filter(
            and_(Seat.flight_id == availability_request.flight_id, Seat.is_available == True)
        )
        
        if availability_request.class_preference:
            query = query.filter(Seat.class_type == availability_request.class_preference)
        
        seats = query.all()
        
        if not seats:
            return {
                "message": "No seats available for this flight",
                "available_seats": []
            }
        
        seat_list = [
            {
                "seat": f"{seat.row_number}{seat.column_letter}",
                "class": seat.class_type,
                "price": float(seat.price)
            }
            for seat in seats
        ]
        
        return {
            "flight_id": availability_request.flight_id,
            "available_seats": seat_list,
            "total_available": len(seat_list)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting seat availability: {str(e)}"
        )

@router.post("/booking-details")
async def get_booking_details(
    details_request: BookingDetailsRequest,
    db: Session = Depends(get_db)
):
    """Get booking details by PNR"""
    try:
        booking = db.query(Booking).join(Flight).join(Customer).filter(
            Booking.pnr == details_request.pnr
        ).first()
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        return {
            "pnr": booking.pnr,
            "customer_name": booking.customer.name,
            "flight_number": booking.flight.flight_number,
            "airline_code": booking.flight.airline_code,
            "route": f"{booking.source_airport_code} → {booking.destination_airport_code}",
            "departure": booking.scheduled_departure.isoformat(),
            "arrival": booking.scheduled_arrival.isoformat(),
            "seat": booking.assigned_seat,
            "status": booking.booking_status
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting booking details: {str(e)}"
        )

@router.post("/create-session")
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """Create a new conversation session for workflow management"""
    try:
        # Verify customer exists
        customer = db.query(Customer).filter(Customer.customer_id == session_data.customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        session = SessionModel(
            customer_id=session_data.customer_id,
            intent_type=session_data.intent_type,
            current_step=session_data.current_step or "start",
            collected_data=session_data.collected_data,
            status=session_data.status
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return {
            "session_id": str(session.session_id),
            "status": "created"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating session: {str(e)}"
        )

@router.put("/update-session/{session_id}")
async def update_session(
    session_id: str,
    session_update: SessionUpdate,
    db: Session = Depends(get_db)
):
    """Update session with collected data and current step"""
    try:
        session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        if session_update.current_step:
            session.current_step = session_update.current_step
        if session_update.collected_data:
            session.collected_data = session_update.collected_data
        if session_update.status:
            session.status = session_update.status
        
        session.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Session updated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating session: {str(e)}"
        )

@router.get("/list-tools")
async def list_tools(db: Session = Depends(get_db)):
    """Get all available tools for the airline service"""
    tools = [
        {
            "tool_name": "policy_info",
            "description": "Search and retrieve airline policy information using vector search and knowledge graph. This tool can answer questions about cancellation policies, refund procedures, pet travel requirements, baggage rules, and other airline policies.",
            "category": "information",
            "examples": ["What is your cancellation policy?", "Tell me about pet travel requirements", "What are the baggage rules?"],
            "parameters": {
                "query": "string - The policy question to search for"
            }
        },
        {
            "tool_name": "flight_status",
            "description": "Check the current status of a flight including departure/arrival times, delays, cancellations, and gate information.",
            "category": "flight_operations",
            "examples": ["What is the status of flight AA123?", "Is my flight delayed?", "What gate is my flight departing from?"],
            "parameters": {
                "flight_id": "integer - The flight ID to check",
                "pnr": "string (optional) - Passenger name record for specific booking"
            }
        },
        {
            "tool_name": "seat_availability",
            "description": "Check available seats on a specific flight, including seat types, pricing, and availability by class.",
            "category": "booking",
            "examples": ["What seats are available on flight AA123?", "Show me economy seats", "Are there any window seats available?"],
            "parameters": {
                "flight_id": "integer - The flight ID to check",
                "class_preference": "string (optional) - Preferred class (economy, business, first)"
            }
        },
        {
            "tool_name": "cancel_flight",
            "description": "Cancel an existing flight booking with confirmation and refund information.",
            "category": "booking",
            "examples": ["I want to cancel my flight", "Cancel booking ABC123", "What is the cancellation fee?"],
            "parameters": {
                "pnr": "string - Passenger name record",
                "customer_id": "string - Customer ID",
                "confirmation": "boolean - Confirmation of cancellation"
            }
        }
    ]
    
    return {
        "service_name": "airline_service",
        "tools": tools,
        "total_tools": len(tools)
    }