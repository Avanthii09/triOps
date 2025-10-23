from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uvicorn
import os
from dotenv import load_dotenv

from database.database import get_db, engine
from database import models
from routers import airline, policies, auth
from schemas import Token

load_dotenv()

# Create database tables
models.Base.metadata.create_all(bind=engine)

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

# Security
security = HTTPBearer()

# Include essential routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(airline.router, prefix="/api/airline", tags=["Airline Operations"])
app.include_router(policies.router, prefix="/api/policies", tags=["Policies"])

@app.get("/")
async def root():
    return {"message": "Triops Airline Management System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "triops-airline-api"}

# Add the gemini policy search endpoint that client.py needs
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
        "main_complete:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
