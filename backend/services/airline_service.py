from sqlalchemy.orm import Session
from database.models import Customer, Flight, Booking, Seat, Session as ChatSession
# from schemas import BookingResponse, CancellationResponse, FlightStatusResponse, SeatAvailabilityResponse
from typing import List, Optional, Dict, Any
import uuid
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal

class AirlineService:
    def __init__(self, db: Session):
        self.db = db

    def generate_pnr(self) -> str:
        """Generate a unique PNR."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(6))

    def book_flight(self, customer_id: str, flight_id: int, seat_preference: str = None, class_preference: str = "economy") -> BookingResponse:
        """Book a flight for a customer."""
        # Check if flight exists and has available seats
        flight = self.db.query(Flight).filter(Flight.flight_id == flight_id).first()
        if not flight:
            raise ValueError("Flight not found")
        
        if flight.available_seats <= 0:
            raise ValueError("No seats available")

        # Find available seat
        seat_query = self.db.query(Seat).filter(
            Seat.flight_id == flight_id,
            Seat.is_available == True
        )

        if seat_preference:
            # Parse seat preference (e.g., "12A")
            import re
            match = re.match(r'(\d+)([A-Z]+)', seat_preference)
            if match:
                row_num = int(match.group(1))
                col_letter = match.group(2)
                seat_query = seat_query.filter(
                    Seat.row_number == row_num,
                    Seat.column_letter == col_letter
                )

        if class_preference:
            seat_query = seat_query.filter(Seat.seat_class == class_preference)

        available_seat = seat_query.first()
        if not available_seat:
            raise ValueError("No seats available matching your preferences")

        # Generate PNR
        pnr = self.generate_pnr()
        
        # Ensure PNR is unique
        while self.db.query(Booking).filter(Booking.pnr == pnr).first():
            pnr = self.generate_pnr()

        # Create booking
        booking = Booking(
            pnr=pnr,
            customer_id=customer_id,
            flight_id=flight_id,
            source_airport_code=flight.source_airport_code,
            destination_airport_code=flight.destination_airport_code,
            scheduled_departure=flight.scheduled_departure,
            scheduled_arrival=flight.scheduled_arrival,
            assigned_seat=f"{available_seat.row_number}{available_seat.column_letter}",
            current_status=flight.current_status
        )

        self.db.add(booking)
        self.db.flush()  # Get booking_id

        # Update seat availability
        available_seat.is_available = False
        available_seat.booking_id = booking.booking_id

        # Update flight available seats count
        flight.available_seats -= 1

        self.db.commit()

        return BookingResponse(
            pnr=pnr,
            seat=f"{available_seat.row_number}{available_seat.column_letter}",
            class_type=available_seat.seat_class,
            price=available_seat.price,
            message=f"Flight booked successfully! PNR: {pnr}"
        )

    def cancel_trip(self, pnr: str, customer_id: str, confirmation: bool = False) -> CancellationResponse:
        """Cancel a customer trip."""
        booking = self.db.query(Booking).filter(
            Booking.pnr == pnr,
            Booking.customer_id == customer_id,
            Booking.booking_status == "confirmed"
        ).first()

        if not booking:
            raise ValueError("Booking not found or already cancelled")

        if not confirmation:
            return CancellationResponse(
                pnr=pnr,
                cancellation_charges=Decimal("0"),
                refund_amount=Decimal("0"),
                refund_date=datetime.utcnow(),
                message=f"Please confirm cancellation for booking {pnr}. Type 'confirm' to proceed."
            )

        # Calculate refund based on cancellation policy
        hours_until_departure = self.get_hours_until_departure(booking.scheduled_departure)
        
        if hours_until_departure > 24:
            refund_amount = Decimal("100")  # Full refund minus processing fee
            cancellation_charges = Decimal("25")
        elif hours_until_departure > 0:
            refund_amount = Decimal("50")  # 50% refund
            cancellation_charges = Decimal("50")
        else:
            refund_amount = Decimal("0")  # No refund for no-shows
            cancellation_charges = Decimal("100")

        refund_date = datetime.utcnow() + timedelta(days=7)

        # Update booking status
        booking.booking_status = "cancelled"
        booking.cancellation_date = datetime.utcnow()
        booking.cancellation_charges = cancellation_charges
        booking.refund_amount = refund_amount
        booking.refund_date = refund_date

        # Free up the seat
        seat = self.db.query(Seat).filter(Seat.booking_id == booking.booking_id).first()
        if seat:
            seat.is_available = True
            seat.booking_id = None

        # Update flight available seats count
        flight = self.db.query(Flight).filter(Flight.flight_id == booking.flight_id).first()
        if flight:
            flight.available_seats += 1

        self.db.commit()

        return CancellationResponse(
            pnr=pnr,
            cancellation_charges=cancellation_charges,
            refund_amount=refund_amount,
            refund_date=refund_date,
            message=f"Trip cancelled successfully! Refund: ${refund_amount}"
        )

    def get_flight_status(self, flight_id: int, pnr: str = None) -> FlightStatusResponse:
        """Get flight status."""
        if pnr:
            # Get booking-specific flight status
            booking = self.db.query(Booking).filter(Booking.pnr == pnr).first()
            if not booking:
                raise ValueError("Booking not found")
            
            flight = booking.flight
            return FlightStatusResponse(
                flight_number=flight.flight_number,
                route=f"{flight.source_airport_code} → {flight.destination_airport_code}",
                scheduled_departure=flight.scheduled_departure,
                current_status=flight.current_status,
                seat=booking.assigned_seat
            )
        else:
            # Get general flight status
            flight = self.db.query(Flight).filter(Flight.flight_id == flight_id).first()
            if not flight:
                raise ValueError("Flight not found")
            
            return FlightStatusResponse(
                flight_number=flight.flight_number,
                route=f"{flight.source_airport_code} → {flight.destination_airport_code}",
                scheduled_departure=flight.scheduled_departure,
                current_status=flight.current_status,
                available_seats=flight.available_seats
            )

    def get_seat_availability(self, flight_id: int, class_preference: str = None) -> SeatAvailabilityResponse:
        """Get available seats for a flight."""
        query = self.db.query(Seat).filter(
            Seat.flight_id == flight_id,
            Seat.is_available == True
        )

        if class_preference:
            query = query.filter(Seat.seat_class == class_preference)

        available_seats = query.all()

        seat_list = []
        for seat in available_seats:
            seat_list.append({
                "row_number": seat.row_number,
                "column_letter": seat.column_letter,
                "price": float(seat.price),
                "class": seat.seat_class
            })

        return SeatAvailabilityResponse(
            flight_id=flight_id,
            available_seats=seat_list,
            total_available=len(seat_list)
        )

    def get_booking_details(self, pnr: str) -> dict:
        """Get booking details by PNR."""
        booking = self.db.query(Booking).filter(Booking.pnr == pnr).first()
        if not booking:
            raise ValueError("Booking not found")

        return {
            "pnr": booking.pnr,
            "customer_name": booking.customer.name,
            "flight_number": booking.flight.flight_number,
            "airline_code": booking.flight.airline_code,
            "route": f"{booking.source_airport_code} → {booking.destination_airport_code}",
            "departure": booking.scheduled_departure,
            "arrival": booking.scheduled_arrival,
            "seat": booking.assigned_seat,
            "status": booking.booking_status
        }

    def create_session(self, customer_id: str, intent_type: str, initial_data: dict = None) -> str:
        """Create a new conversation session."""
        session = ChatSession(
            customer_id=customer_id,
            intent_type=intent_type,
            collected_data=str(initial_data) if initial_data else None,
            current_step="start",
            status="active"
        )
        
        self.db.add(session)
        self.db.commit()
        
        return str(session.session_id)

    def update_session(self, session_id: str, current_step: str = None, collected_data: dict = None, status: str = None):
        """Update session with collected data."""
        session = self.db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            raise ValueError("Session not found")

        if current_step:
            session.current_step = current_step
        if collected_data:
            session.collected_data = str(collected_data)
        if status:
            session.status = status

        self.db.commit()

    def get_hours_until_departure(self, departure_time: datetime) -> int:
        """Calculate hours until departure."""
        now = datetime.utcnow()
        return int((departure_time - now).total_seconds() / 3600)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools with descriptions for the airline service."""
        return [
            {
                "tool_name": "policy_info",
                "description": "Search and retrieve airline policy information using vector search and knowledge graph. This tool can answer questions about cancellation policies, pet travel policies, baggage rules, refund policies, and other airline-specific policies. It combines document search with knowledge graph relationships to provide comprehensive policy information.",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "The policy question or search term (e.g., 'cancellation policy', 'pet travel rules', 'baggage allowance')",
                        "required": True
                    }
                },
                "examples": [
                    "What is your cancellation policy?",
                    "Can I bring my pet on the flight?",
                    "What are the baggage rules?",
                    "Tell me about refund policies"
                ],
                "category": "policy"
            },
            {
                "tool_name": "flight_status",
                "description": "Check the current status of a flight including departure/arrival times, delays, cancellations, and gate information. This tool provides real-time flight status updates and can help passengers track their flights.",
                "parameters": {
                    "flight_id": {
                        "type": "integer",
                        "description": "The unique flight identifier",
                        "required": True
                    },
                    "pnr": {
                        "type": "string",
                        "description": "Optional Passenger Name Record for personalized flight status",
                        "required": False
                    }
                },
                "examples": [
                    "Check status of flight 1001",
                    "Is flight 2002 on time?",
                    "What's the status of my flight?"
                ],
                "category": "flight_operations"
            },
            {
                "tool_name": "seat_availability",
                "description": "Check available seats on a specific flight, including seat classes (economy, business, first), seat preferences (aisle, window), and seat numbers. This tool helps passengers find and select their preferred seats.",
                "parameters": {
                    "flight_id": {
                        "type": "integer",
                        "description": "The unique flight identifier",
                        "required": True
                    },
                    "class_preference": {
                        "type": "string",
                        "description": "Preferred seat class: economy, business, or first",
                        "required": False
                    }
                },
                "examples": [
                    "Show available seats for flight 1001",
                    "What seats are available in business class?",
                    "Check seat availability for flight 2002"
                ],
                "category": "flight_operations"
            },
            {
                "tool_name": "cancel_flight",
                "description": "Cancel an existing flight booking with confirmation workflow. This tool handles the complete cancellation process including refund calculations, cancellation fees, and confirmation steps. It provides detailed information about refund amounts and policies.",
                "parameters": {
                    "pnr": {
                        "type": "string",
                        "description": "Passenger Name Record of the booking to cancel",
                        "required": True
                    },
                    "customer_id": {
                        "type": "string",
                        "description": "Customer ID for verification",
                        "required": True
                    },
                    "confirmation": {
                        "type": "boolean",
                        "description": "Confirmation to proceed with cancellation",
                        "required": False
                    }
                },
                "examples": [
                    "Cancel my flight booking",
                    "I want to cancel flight PNR ABC123",
                    "Cancel booking for customer CUST001"
                ],
                "category": "booking_management"
            }
        ]
