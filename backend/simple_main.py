from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime

app = FastAPI(
    title="Triops Airline Management System",
    description="A comprehensive airline management system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Triops Airline Management System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "triops-airline-api"}

# Mock airline service endpoints
@app.get("/api/airline/list-tools")
async def list_tools():
    return {
        "tools": [
            {
                "tool_name": "policy_info",
                "description": "Get information about airline policies including cancellation, pet travel, and baggage policies",
                "parameters": {"query": "string"},
                "examples": ["What is your cancellation policy?", "Can I bring my pet?", "What are the baggage rules?"],
                "category": "policy"
            },
            {
                "tool_name": "flight_status",
                "description": "Check the current status of a flight",
                "parameters": {"flight_id": "integer"},
                "examples": ["Check status of flight 1001", "Is flight 2002 on time?"],
                "category": "flight"
            },
            {
                "tool_name": "seat_availability",
                "description": "Check available seats for a flight",
                "parameters": {"flight_id": "integer", "class_preference": "string"},
                "examples": ["What seats are available for flight 1001?", "Show me business class seats for flight 2002"],
                "category": "booking"
            },
            {
                "tool_name": "cancel_flight",
                "description": "Cancel a flight booking",
                "parameters": {"pnr": "string"},
                "examples": ["Cancel my booking", "I want to cancel flight ABC123"],
                "category": "booking"
            }
        ]
    }

@app.post("/api/airline/flight-status")
async def flight_status(data: dict):
    flight_id = data.get("flight_id", 1001)
    return {
        "flight_id": flight_id,
        "flight_number": f"TR{flight_id}",
        "status": "on-time",
        "departure_time": "2024-01-15T10:30:00Z",
        "arrival_time": "2024-01-15T14:45:00Z",
        "gate": "A12",
        "terminal": "1"
    }

@app.post("/api/airline/seat-availability")
async def seat_availability(data: dict):
    flight_id = data.get("flight_id", 1001)
    class_pref = data.get("class_preference", "economy")
    return {
        "flight_id": flight_id,
        "class_preference": class_pref,
        "available_seats": [
            {"seat": "12A", "price": 50},
            {"seat": "12B", "price": 50},
            {"seat": "15C", "price": 75},
            {"seat": "15D", "price": 75}
        ],
        "total_available": 4
    }

@app.post("/api/airline/cancel-trip")
async def cancel_trip(data: dict):
    pnr = data.get("pnr", "ABC123")
    return {
        "pnr": pnr,
        "status": "cancelled",
        "refund_amount": 150.00,
        "cancellation_fee": 25.00,
        "refund_date": "2024-01-20T00:00:00Z"
    }

@app.post("/api/gemini/policy-search-classify")
async def policy_search_classify(data: dict):
    query = data.get("query", "")
    query_lower = query.lower()
    
    # Mock response based on query type
    if "cancellation" in query_lower or "cancel" in query_lower:
        return {
            "search_type": "vector_search",
            "confidence": 0.95,
            "reasoning": "Query about cancellation policy detected",
            "results": {
                "final_response": """**Cancellation Policy:**

• **Free Cancellation**: Within 24 hours of booking
• **Standard Cancellation**: 24+ hours before departure - $50 fee
• **Last-minute Cancellation**: Within 24 hours - $100 fee
• **No-show**: No refund available

**Refund Processing**: 5-7 business days to original payment method

For assistance, contact us at +1-800-TRIOPS or support@triops.com""",
                "retrieved_chunks": 3,
                "similar_queries": 2,
                "knowledge_graph_content": True
            }
        }
    elif "pet" in query_lower:
        return {
            "search_type": "vector_search",
            "confidence": 0.95,
            "reasoning": "Query about pet travel policy detected",
            "results": {
                "final_response": """**Pet Travel Policy:**

• **In-cabin pets**: Small dogs/cats allowed (max 20 lbs)
• **Fee**: $125 per pet per flight
• **Carrier requirements**: Must fit under seat
• **Health certificate**: Required for all pets
• **Advance booking**: Required - limited spots available

**Restrictions**: No pets in cargo hold for safety reasons

Book pet travel at least 48 hours in advance. Contact us at +1-800-TRIOPS""",
                "retrieved_chunks": 2,
                "similar_queries": 1,
                "knowledge_graph_content": True
            }
        }
    elif "baggage" in query_lower:
        return {
            "search_type": "vector_search",
            "confidence": 0.95,
            "reasoning": "Query about baggage policy detected",
            "results": {
                "final_response": """**Baggage Policy:**

• **Carry-on**: 1 bag (max 22" x 14" x 9") + 1 personal item
• **Checked baggage**: $35 for first bag, $45 for second bag
• **Weight limit**: 50 lbs per bag
• **Overweight fee**: $100 for bags 51-70 lbs
• **Oversized fee**: $200 for bags over size limits

**Free baggage**: Business class passengers get 2 free checked bags

For questions, contact us at +1-800-TRIOPS""",
                "retrieved_chunks": 4,
                "similar_queries": 3,
                "knowledge_graph_content": True
            }
        }
    else:
        return {
            "search_type": "knowledge_graph",
            "confidence": 0.7,
            "reasoning": "General policy query detected",
            "results": {
                "raw_data": {
                    "basic_search": [
                        {"name": "Airline Policy", "type": "policy"},
                        {"name": "Customer Service", "type": "service"}
                    ],
                    "center_searches": [
                        {"name": "Cancellation Policy", "relation": "related"},
                        {"name": "Pet Travel Policy", "relation": "related"}
                    ],
                    "multi_hop_searches": [
                        {"entity_names": ["Airline Policy", "Cancellation Policy", "Refund Policy"]}
                    ],
                    "entity_contexts": [
                        {
                            "name": "Airline Policy",
                            "type": "policy",
                            "outgoing_relationships": [
                                {"target_name": "Cancellation Policy", "relation": "includes"},
                                {"target_name": "Pet Travel Policy", "relation": "includes"}
                            ]
                        }
                    ]
                }
            }
        }

if __name__ == "__main__":
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )







