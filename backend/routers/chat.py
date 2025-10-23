from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from typing import Dict, Any
import httpx
import asyncio

router = APIRouter()

@router.post("/chat")
async def handle_chat_query(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Main chat endpoint that routes queries to appropriate services.
    """
    try:
        query = request.get("query", "").strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        query_lower = query.lower().strip()
        
        # Check if it's a general greeting
        general_patterns = [
            "hi", "hello", "hey", "heyy", "heyyy", "heyyyy", "heyyyyy",
            "good morning", "good afternoon", "good evening",
            "how are you", "how do you do", "nice to meet you",
            "thanks", "thank you", "bye", "goodbye", "see you later",
            "can you help me", "what can you do", "help me", "assist me"
        ]
        
        is_general = any(pattern in query_lower for pattern in general_patterns)
        if len(query.split()) <= 2 and any(word in query_lower for word in ["hi", "hello", "hey", "thanks", "bye"]):
            is_general = True
        
        if is_general:
            if any(greeting in query_lower for greeting in ["hi", "hello", "hey", "heyy", "heyyy", "heyyyy", "heyyyyy", "good morning", "good afternoon", "good evening"]):
                response_text = "Hey there! 👋 Welcome to Triops Airline! I'm your AI assistant and I'm here to help with all your travel needs. What can I do for you today?"
            elif any(help_word in query_lower for help_word in ["help", "assist", "support"]):
                response_text = "I'm here to help you with all your airline needs! I can help with flight status, policies, bookings, and more. What would you like to know?"
            else:
                response_text = "Hello! I'm your Triops Airline assistant. How can I help you today?"
            
            return {
                "query": query,
                "type": "general",
                "response": response_text,
                "confidence": 0.9,
                "reasoning": "General conversational query detected"
            }
        
        # Check for cancellation confirmation
        if any(confirm_word in query_lower for confirm_word in ["yes, cancel my booking", "yes cancel", "confirm cancellation", "proceed with cancellation"]):
            return await handle_cancellation_confirmation(query, db)
        
        # Route to specific airline operations (order matters - more specific first)
        if any(keyword in query_lower for keyword in ["status", "flight status", "delay", "on time", "check flight"]):
            return await handle_flight_status_query(query, db)
        
        elif any(keyword in query_lower for keyword in ["seat", "seats", "availability", "available"]):
            return await handle_seat_availability_query(query, db)
        
        elif any(keyword in query_lower for keyword in ["policy", "policies", "rule", "rules", "baggage", "pet", "travel"]):
            return await handle_policy_query(query, db)
        
        elif any(keyword in query_lower for keyword in ["cancel", "cancellation", "refund"]) and not any(policy_word in query_lower for policy_word in ["policy", "policies", "rule", "rules"]):
            return await handle_cancellation_query(query, db)
        
        elif any(keyword in query_lower for keyword in ["book", "booking", "reserve"]):
            return await handle_booking_query(query, db)
        
        else:
            # Default to policy search for general questions
            return await handle_policy_query(query, db)
            
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return {
            "query": query,
            "type": "error",
            "response": "I apologize, but I encountered an error processing your request. Please try again or contact our support team.",
            "error": str(e)
        }

async def handle_booking_query(query: str, db: Session) -> Dict[str, Any]:
    """Handle flight booking queries."""
    try:
        # For now, return a helpful response about booking
        return {
            "query": query,
            "type": "booking",
            "response": "To book a flight, please provide:\n• Departure city\n• Destination city\n• Travel dates\n• Number of passengers\n• Class preference\n\nI can help you find available flights and make a reservation.",
            "confidence": 0.8,
            "reasoning": "Booking query detected"
        }
    except Exception as e:
        return {
            "query": query,
            "type": "booking_error",
            "response": "I apologize, but I couldn't process your booking request. Please contact our booking department at +1-800-TRIOPS.",
            "error": str(e)
        }

async def handle_cancellation_confirmation(query: str, db: Session) -> Dict[str, Any]:
    """Handle cancellation confirmation from user."""
    try:
        # For now, we'll simulate a successful cancellation
        # In a real system, you'd extract the PNR from context or session
        return {
            "query": query,
            "type": "cancellation_confirmed",
            "response": """✅ **Cancellation Confirmed!**

Your booking has been successfully cancelled.

📋 **Cancellation Summary:**
- Cancellation fee: $250
- Refund amount: $750 (will be processed within 5-7 business days)
- Confirmation email will be sent shortly

Thank you for choosing Triops Airline. We hope to serve you again soon! ✈️""",
            "confidence": 0.95,
            "reasoning": "User confirmed cancellation"
        }
    except Exception as e:
        return {
            "query": query,
            "type": "cancellation_error",
            "response": "I apologize, but there was an error processing your cancellation. Please contact our customer service at +1-800-TRIOPS.",
            "error": str(e)
        }

async def handle_cancellation_query(query: str, db: Session) -> Dict[str, Any]:
    """Handle cancellation queries."""
    try:
        # Extract PNR or booking reference if mentioned
        import re
        pnr_pattern = r'\b[A-Z0-9]{6,10}\b'
        pnr_matches = re.findall(pnr_pattern, query.upper())
        
        # Filter out common words that match the pattern
        filtered_pnr_matches = [pnr for pnr in pnr_matches if pnr not in ['CANCEL', 'BOOKING', 'FLIGHT', 'STATUS']]
        
        if filtered_pnr_matches:
            pnr = filtered_pnr_matches[0]
            # First, get booking details to show user
            async with httpx.AsyncClient() as client:
                booking_response = await client.post("http://localhost:8000/api/airline/booking-details", json={
                    "pnr": pnr
                })
                
                if booking_response.status_code == 200:
                    booking_data = booking_response.json()
                    # Show booking details and ask for confirmation
                    booking_info = f"""
📋 **Booking Details for PNR: {pnr}**

✈️ **Flight**: {booking_data.get('flight_number', 'N/A')}
🛫 **Route**: {booking_data.get('route', 'N/A')}
🕐 **Departure**: {booking_data.get('departure', 'N/A')}
🕑 **Arrival**: {booking_data.get('arrival', 'N/A')}
💺 **Seat**: {booking_data.get('seat', 'N/A')}
📊 **Status**: {booking_data.get('status', 'N/A')}

⚠️ **Cancellation Policy**: 
- Cancellation fees: $200-400 depending on fare type
- Refund will be processed within 5-7 business days
- 24-hour free cancellation rule applies

**To proceed with cancellation, please confirm by typing: "YES, CANCEL MY BOOKING"**
                    """
                    
                    return {
                        "query": query,
                        "type": "cancellation_details",
                        "response": booking_info,
                        "confidence": 0.9,
                        "reasoning": "Booking details retrieved, awaiting user confirmation",
                        "requires_confirmation": True,
                        "pnr": pnr
                    }
                else:
                    return {
                        "query": query,
                        "type": "cancellation_error",
                        "response": f"Sorry, I couldn't find a booking with PNR {pnr}. Please check your booking reference and try again.",
                        "confidence": 0.8,
                        "reasoning": "PNR not found in database"
                    }
        
        return {
            "query": query,
            "type": "cancellation",
            "response": "To cancel your flight, please provide your PNR (booking reference) number. You can find this in your booking confirmation email.",
            "confidence": 0.8,
            "reasoning": "Cancellation query detected"
        }
    except Exception as e:
        return {
            "query": query,
            "type": "cancellation_error",
            "response": "I apologize, but I couldn't process your cancellation request. Please contact our customer service at +1-800-TRIOPS.",
            "error": str(e)
        }

async def handle_flight_status_query(query: str, db: Session) -> Dict[str, Any]:
    """Handle flight status queries."""
    try:
        # Extract flight number or PNR
        import re
        flight_pattern = r'\b[A-Z]{2,3}\d{3,4}\b|\b[A-Z0-9]{6,10}\b'
        flight_matches = re.findall(flight_pattern, query.upper())
        
        if flight_matches:
            flight_id = flight_matches[0]
            # Map flight numbers to actual flight IDs
            flight_id_map = {
                "JB101": 1001,
                "JB102": 1002, 
                "JB103": 1003
            }
            actual_flight_id = flight_id_map.get(flight_id, 1001)  # Default to 1001
            
            # Call the actual flight status endpoint
            async with httpx.AsyncClient() as client:
                response = await client.post("http://localhost:8000/api/airline/flight-status", json={
                    "flight_id": actual_flight_id,
                    "pnr": flight_id if len(flight_id) > 6 else None
                })
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "query": query,
                        "type": "flight_status",
                        "response": f"Flight {flight_id} Status:\n{result.get('message', 'Information not available')}",
                        "confidence": 0.9,
                        "reasoning": "Flight status retrieved successfully"
                    }
        
        return {
            "query": query,
            "type": "flight_status",
            "response": "To check your flight status, please provide your flight number (e.g., AA123) or PNR (booking reference).",
            "confidence": 0.8,
            "reasoning": "Flight status query detected"
        }
    except Exception as e:
        return {
            "query": query,
            "type": "flight_status_error",
            "response": "I apologize, but I couldn't retrieve your flight status. Please contact our customer service at +1-800-TRIOPS.",
            "error": str(e)
        }

async def handle_seat_availability_query(query: str, db: Session) -> Dict[str, Any]:
    """Handle seat availability queries."""
    try:
        # Extract flight number
        import re
        flight_pattern = r'\b[A-Z]{2,3}\d{3,4}\b'
        flight_matches = re.findall(flight_pattern, query.upper())
        
        if flight_matches:
            flight_id = flight_matches[0]
            # Map flight numbers to actual flight IDs
            flight_id_map = {
                "JB101": 1001,
                "JB102": 1002, 
                "JB103": 1003
            }
            actual_flight_id = flight_id_map.get(flight_id, 1001)  # Default to 1001
            
            # Call the actual seat availability endpoint
            async with httpx.AsyncClient() as client:
                response = await client.post("http://localhost:8000/api/airline/seat-availability", json={
                    "flight_id": actual_flight_id,
                    "class_preference": "economy"
                })
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "query": query,
                        "type": "seat_availability",
                        "response": f"Seat availability for flight {flight_id}:\n{result.get('message', 'Information not available')}",
                        "confidence": 0.9,
                        "reasoning": "Seat availability retrieved successfully"
                    }
        
        return {
            "query": query,
            "type": "seat_availability",
            "response": "To check seat availability, please provide your flight number (e.g., AA123).",
            "confidence": 0.8,
            "reasoning": "Seat availability query detected"
        }
    except Exception as e:
        return {
            "query": query,
            "type": "seat_availability_error",
            "response": "I apologize, but I couldn't retrieve seat availability information. Please contact our customer service at +1-800-TRIOPS.",
            "error": str(e)
        }

async def handle_policy_query(query: str, db: Session) -> Dict[str, Any]:
    """Handle policy-related queries using the RAG system."""
    try:
        # Call the policy search endpoint
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/gemini/policy-search-classify",
                json={"query": query},
                timeout=30.0
            )
            if response.status_code == 200:
                result = response.json()
                return {
                    "query": query,
                    "type": "policy",
                    "response": result.get("results", {}).get("final_response", result.get("results", {}).get("response", "I found relevant policy information, but couldn't generate a complete response.")),
                    "confidence": result.get("confidence", 0.7),
                    "reasoning": result.get("reasoning", "Policy search performed"),
                    "search_type": result.get("search_type", "unknown")
                }
        
        # Fallback response
        return {
            "query": query,
            "type": "policy",
            "response": "I can help you with our airline policies including cancellation, refund, pet travel, and baggage policies. Please be more specific about what you'd like to know.",
            "confidence": 0.6,
            "reasoning": "Fallback policy response"
        }
    except Exception as e:
        return {
            "query": query,
            "type": "policy_error",
            "response": "I apologize, but I couldn't retrieve policy information. Please contact our customer service at +1-800-TRIOPS.",
            "error": str(e)
        }
