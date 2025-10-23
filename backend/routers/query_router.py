#!/usr/bin/env python3
"""
Query Router Middleware
This module handles user queries and routes them to appropriate endpoints
using Gemini AI for intelligent routing and quality control.
"""

import asyncio
import os
import json
import httpx
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database.database import get_db
# Policy and airline functions will be imported as needed

router = APIRouter(tags=["Query Router"])

# Gemini API configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyDe1C_D8eLAC8d3ESLqUpZ5OGcAlxR2igs")

class UserQuery(BaseModel):
    query: str
    customer_id: Optional[str] = None
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    category: str
    endpoint: str
    response: Any
    confidence: float
    reasoning: str

class AvailableEndpoints(BaseModel):
    general_endpoints: List[Dict[str, str]]
    policy_endpoints: List[Dict[str, str]]
    airline_endpoints: List[Dict[str, str]]

def get_available_endpoints() -> AvailableEndpoints:
    """Get all available endpoints for Gemini to choose from"""
    return AvailableEndpoints(
        general_endpoints=[
            {
                "endpoint": "general_greeting",
                "description": "Handle greetings, farewells, and general conversation",
                "example": "Hi, Hello, Goodbye, How are you?"
            },
            {
                "endpoint": "general_help",
                "description": "Provide general help and information about the airline",
                "example": "What services do you offer? How can I help you?"
            }
        ],
        policy_endpoints=[
            {
                "endpoint": "cancellation_policy",
                "description": "Get cancellation policy information",
                "example": "What is your cancellation policy? Can I cancel my flight?"
            },
            {
                "endpoint": "pet_travel_policy",
                "description": "Get pet travel policy information",
                "example": "Can I bring my pet? What are the pet travel rules?"
            },
            {
                "endpoint": "search_policies",
                "description": "Search for specific policy information",
                "example": "What are the baggage rules? Tell me about refunds"
            }
        ],
        airline_endpoints=[
            {
                "endpoint": "book_flight",
                "description": "Book a flight with seat selection",
                "example": "I want to book a flight, Book me a seat, Reserve a flight"
            },
            {
                "endpoint": "cancel_trip",
                "description": "Cancel an existing booking",
                "example": "Cancel my flight, I want to cancel my booking"
            },
            {
                "endpoint": "flight_status",
                "description": "Check flight status and information",
                "example": "What is the status of my flight? Is my flight on time?"
            },
            {
                "endpoint": "seat_availability",
                "description": "Check seat availability on flights",
                "example": "What seats are available? Show me available seats"
            },
            {
                "endpoint": "booking_details",
                "description": "Get details of existing bookings",
                "example": "Show my booking details, What is my booking information?"
            }
        ]
    )

def create_quality_control_prompt() -> str:
    """Create quality control prompt to prevent irrelevant responses"""
    return """
QUALITY CONTROL RULES:
1. ONLY respond to airline-related queries (flights, bookings, policies, travel)
2. DO NOT answer mathematical questions (like "what is the square of 42")
3. DO NOT answer general knowledge questions unrelated to airlines
4. DO NOT answer personal questions or inappropriate content
5. If query is irrelevant, respond with category: "rejected" and endpoint: "none"
6. If query is unclear, ask for clarification
7. Focus ONLY on airline operations, policies, and travel services
"""

def call_gemini_for_routing(query: str, endpoints: AvailableEndpoints) -> Dict[str, Any]:
    """Use Gemini to determine the appropriate endpoint for the user query"""
    try:
        # Create the routing prompt
        prompt = f"""
You are an intelligent airline customer service router. Your job is to analyze user queries and determine the most appropriate endpoint to handle them.

{create_quality_control_prompt()}

AVAILABLE ENDPOINTS:

GENERAL ENDPOINTS:
{json.dumps(endpoints.general_endpoints, indent=2)}

POLICY ENDPOINTS:
{json.dumps(endpoints.policy_endpoints, indent=2)}

AIRLINE ENDPOINTS:
{json.dumps(endpoints.airline_endpoints, indent=2)}

USER QUERY: "{query}"

INSTRUCTIONS:
1. Analyze the user query carefully
2. Determine the most appropriate category (general, policy, airline, or rejected)
3. Select the best matching endpoint
4. Provide confidence score (0.0 to 1.0)
5. Explain your reasoning

RESPOND WITH EXACTLY THIS JSON FORMAT:
{{
    "category": "general|policy|airline|rejected",
    "endpoint": "endpoint_name",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this endpoint was chosen"
}}

IMPORTANT: Only respond with valid JSON, no additional text.
"""

        # Call Gemini API
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GOOGLE_API_KEY
        }
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 500,
                "topP": 0.8,
                "topK": 10
            }
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result["candidates"][0]["content"]["parts"][0]["text"]
            
            # Parse JSON response
            try:
                # Clean the response - remove markdown code blocks if present
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]  # Remove ```json
                if content.startswith("```"):
                    content = content[3:]   # Remove ```
                if content.endswith("```"):
                    content = content[:-3]  # Remove trailing ```
                
                content = content.strip()
                routing_result = json.loads(content)
                return routing_result
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "category": "general",
                    "endpoint": "general_help",
                    "confidence": 0.5,
                    "reasoning": "Failed to parse Gemini response, using fallback"
                }
                
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return {
            "category": "general",
            "endpoint": "general_help",
            "confidence": 0.3,
            "reasoning": f"Error occurred: {str(e)}"
        }

def handle_general_query(endpoint: str, query: str) -> Dict[str, Any]:
    """Handle general queries"""
    if endpoint == "general_greeting":
        return {
            "message": "Hello! Welcome to Triops Airline. How can I assist you with your travel needs today?",
            "suggestions": [
                "Book a flight",
                "Check flight status", 
                "View cancellation policy",
                "Ask about pet travel"
            ]
        }
    elif endpoint == "general_help":
        return {
            "message": "I'm here to help you with all your airline needs! Here's what I can do:",
            "services": [
                "Book flights with seat selection",
                "Cancel existing bookings",
                "Check flight status",
                "View seat availability",
                "Get policy information (cancellation, pet travel)",
                "Answer questions about our services"
            ],
            "suggestions": [
                "Try asking: 'I want to book a flight'",
                "Try asking: 'What is your cancellation policy?'",
                "Try asking: 'Can I bring my pet on the flight?'"
            ]
        }
    else:
        return {
            "message": "I'm not sure how to help with that. Could you please rephrase your question?",
            "suggestions": ["Book a flight", "Check policies", "Get help"]
        }

async def handle_policy_query(endpoint: str, query: str, db: Session) -> Dict[str, Any]:
    """Handle policy-related queries"""
    try:
        if endpoint == "cancellation_policy":
            # Call the cancellation policy logic directly
            from database.models import Policy
            from sqlalchemy import and_
            
            policy = db.query(Policy).filter(
                and_(Policy.policy_type == "cancellation", Policy.is_active == True)
            ).order_by(Policy.effective_date.desc()).first()
            
            if not policy:
                return {"policy_type": "cancellation", "content": {"message": "Cancellation policy not found"}}
            
            return {
                "policy_type": "cancellation", 
                "content": {
                    "title": policy.title,
                    "content": policy.content,
                    "effective_date": policy.effective_date,
                    "policy_id": policy.policy_id
                }
            }
        elif endpoint == "pet_travel_policy":
            # Call the pet travel policy logic directly
            from database.models import Policy
            from sqlalchemy import and_
            
            policy = db.query(Policy).filter(
                and_(Policy.policy_type == "pet_travel", Policy.is_active == True)
            ).order_by(Policy.effective_date.desc()).first()
            
            if not policy:
                return {"policy_type": "pet_travel", "content": {"message": "Pet travel policy not found"}}
            
            return {
                "policy_type": "pet_travel", 
                "content": {
                    "title": policy.title,
                    "content": policy.content,
                    "effective_date": policy.effective_date,
                    "policy_id": policy.policy_id
                }
            }
        elif endpoint == "search_policies":
            # Search policies logic
            from database.models import Policy
            from sqlalchemy import and_, or_
            
            policies = db.query(Policy).filter(
                and_(
                    Policy.is_active == True,
                    or_(
                        Policy.title.ilike(f"%{query}%"),
                        Policy.content.ilike(f"%{query}%"),
                        Policy.policy_type.ilike(f"%{query}%")
                    )
                )
            ).order_by(Policy.effective_date.desc()).limit(10).all()
            
            return {
                "policy_type": "search", 
                "content": {
                    "query": query,
                    "results": [
                        {
                            "title": policy.title,
                            "content": policy.content,
                            "policy_type": policy.policy_type,
                            "effective_date": policy.effective_date,
                            "policy_id": policy.policy_id
                        } for policy in policies
                    ],
                    "count": len(policies)
                }
            }
        else:
            return {"error": "Unknown policy endpoint"}
    except Exception as e:
        return {"error": f"Error handling policy query: {str(e)}"}

def handle_airline_query(endpoint: str, query: str, customer_id: str, db: Session) -> Dict[str, Any]:
    """Handle airline operation queries"""
    try:
        if endpoint == "book_flight":
            # This would need flight details from the query - for now return guidance
            return {
                "message": "To book a flight, I need more details. Please provide:",
                "required_info": [
                    "Flight ID or route",
                    "Travel dates",
                    "Seat preference (aisle/window)",
                    "Class preference (economy/business/first)"
                ],
                "example": "Book flight 1001 for tomorrow, aisle seat, economy class"
            }
        elif endpoint == "cancel_trip":
            return {
                "message": "To cancel your trip, I need your booking details.",
                "required_info": ["Booking ID or customer ID"],
                "example": "Cancel booking for customer CUST001"
            }
        elif endpoint == "flight_status":
            return {
                "message": "To check flight status, I need the flight number.",
                "required_info": ["Flight ID"],
                "example": "Check status of flight 1001"
            }
        elif endpoint == "seat_availability":
            return {
                "message": "To check seat availability, I need flight details.",
                "required_info": ["Flight ID"],
                "example": "Show available seats for flight 1001"
            }
        elif endpoint == "booking_details":
            return {
                "message": "To get booking details, I need your customer information.",
                "required_info": ["Customer ID"],
                "example": "Show booking details for customer CUST001"
            }
        else:
            return {"error": "Unknown airline endpoint"}
    except Exception as e:
        return {"error": f"Error handling airline query: {str(e)}"}

@router.get("/endpoints", response_model=AvailableEndpoints)
async def get_all_endpoints():
    """Get all available endpoints for routing"""
    return get_available_endpoints()

@router.post("/route", response_model=QueryResponse)
async def route_query(
    user_query: UserQuery,
    db: Session = Depends(get_db)
):
    """
    Route user query to appropriate endpoint using Gemini AI
    """
    try:
        # Get available endpoints
        endpoints = get_available_endpoints()
        
        # Use Gemini to determine routing
        routing_result = call_gemini_for_routing(user_query.query, endpoints)
        
        category = routing_result.get("category", "general")
        endpoint = routing_result.get("endpoint", "general_help")
        confidence = routing_result.get("confidence", 0.5)
        reasoning = routing_result.get("reasoning", "No reasoning provided")
        
        # Handle the query based on category
        if category == "rejected":
            response_data = {
                "message": "I can only help with airline-related questions. Please ask about flights, bookings, policies, or travel services.",
                "suggestions": [
                    "Book a flight",
                    "Check flight status",
                    "View cancellation policy",
                    "Ask about pet travel"
                ]
            }
        elif category == "general":
            response_data = handle_general_query(endpoint, user_query.query)
        elif category == "policy":
            response_data = await handle_policy_query(endpoint, user_query.query, db)
        elif category == "airline":
            if not user_query.customer_id:
                response_data = {
                    "message": "For airline operations, I need your customer ID. Please provide it.",
                    "required": "customer_id"
                }
            else:
                response_data = handle_airline_query(endpoint, user_query.query, user_query.customer_id, db)
        else:
            response_data = {
                "message": "I'm not sure how to help with that. Could you please rephrase your question?",
                "suggestions": ["Book a flight", "Check policies", "Get help"]
            }
        
        return QueryResponse(
            category=category,
            endpoint=endpoint,
            response=response_data,
            confidence=confidence,
            reasoning=reasoning
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error routing query: {str(e)}"
        )

@router.post("/test-routing")
async def test_routing(query: str):
    """Test endpoint for routing without database dependency"""
    try:
        endpoints = get_available_endpoints()
        routing_result = call_gemini_for_routing(query, endpoints)
        
        return {
            "query": query,
            "routing_result": routing_result,
            "available_endpoints": endpoints
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing routing: {str(e)}"
        )
