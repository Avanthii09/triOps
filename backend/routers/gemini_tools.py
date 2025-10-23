#!/usr/bin/env python3
"""
Gemini Tool Calling Router
This module implements LLM tool calling using Gemini for intelligent policy search routing.
"""

import os
import json
import httpx
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from database.database import get_db

router = APIRouter(tags=["Gemini Tools"])

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyDe1C_D8eLAC8d3ESLqUpZ5OGcAlxR2igs")

class PolicyQueryRequest(BaseModel):
    query: str
    user_context: Optional[Dict[str, Any]] = None

class PolicySearchResponse(BaseModel):
    search_type: str  # "knowledge_graph" or "vector_search"
    query: str
    results: Dict[str, Any]
    confidence: float
    reasoning: str

class GeminiToolCallRequest(BaseModel):
    query: str
    available_tools: List[Dict[str, Any]]

class GeminiToolCallResponse(BaseModel):
    selected_tool: str
    tool_parameters: Dict[str, Any]
    confidence: float
    reasoning: str

def call_gemini_tool_calling(prompt: str) -> Dict[str, Any]:
    """Call Gemini API for tool calling with structured output."""
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
            "maxOutputTokens": 1000,
            "topP": 0.8,
            "topK": 10
        }
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result["candidates"][0]["content"]["parts"][0]["text"]
            
            # Clean the response - remove markdown code blocks if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.startswith("```"):
                content = content[3:]   # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove trailing ```
            
            content = content.strip()
            tool_call_result = json.loads(content)
            return tool_call_result
            
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return {
            "selected_tool": "vector_search",
            "tool_parameters": {"query": "fallback search"},
            "confidence": 0.3,
            "reasoning": f"Fallback due to error: {str(e)}"
        }

@router.post("/policy-search-classify", response_model=PolicySearchResponse)
async def classify_policy_search(
    request: PolicyQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Classify whether a policy query needs knowledge graph search or vector search.
    Uses Gemini to intelligently determine the best search method.
    """
    try:
        # First check if this is a general/conversational query
        query_lower = request.query.lower().strip()
        general_patterns = [
            "hi", "hello", "hey", "heyy", "heyyy", "heyyyy", "heyyyyy",
            "good morning", "good afternoon", "good evening",
            "how are you", "how do you do", "nice to meet you",
            "thanks", "thank you", "bye", "goodbye", "see you later",
            "can you help me", "what can you do", "help me", "assist me"
        ]
        
        # Check if query matches general patterns
        is_general = any(pattern in query_lower for pattern in general_patterns)
        
        # If it's a very short query (1-2 words), likely general
        if len(request.query.split()) <= 2 and any(word in query_lower for word in ["hi", "hello", "hey", "thanks", "bye"]):
            is_general = True
        
        if is_general:
            # Handle as general query
            if any(greeting in query_lower for greeting in ["hi", "hello", "hey", "heyy", "heyyy", "heyyyy", "heyyyyy", "good morning", "good afternoon", "good evening"]):
                response_text = "Hey there! 👋 Welcome to Triops Airline! I'm your AI assistant and I'm here to help with all your travel needs. What can I do for you today?"
            elif any(help_word in query_lower for help_word in ["help", "assist", "support"]):
                response_text = "I'm here to help you with all your airline needs! I can help with flight status, policies, bookings, and more. What would you like to know?"
            else:
                response_text = "Hello! I'm your Triops Airline assistant. How can I help you today?"
            
            return PolicySearchResponse(
                search_type="general",
                query=request.query,
                results={"response": response_text},
                confidence=0.9,
                reasoning="General conversational query detected"
            )
        
        # Create prompt for Gemini to classify the search type
        prompt = f"""
You are an AI assistant for Triops Airline that needs to classify policy queries for optimal search.

You have access to two search methods:
1. **Knowledge Graph Search**: Best for queries about relationships, entities, specific facts, and connections between concepts
2. **Vector Search**: Best for queries about general policies, procedures, detailed explanations, and comprehensive information

CLASSIFICATION GUIDELINES:
- Use **Knowledge Graph Search** for:
  * Questions about specific entities (e.g., "Who founded Emirates Airlines?", "What companies are related to Dubai?")
  * Relationship queries (e.g., "What is the relationship between X and Y?", "How is company A connected to company B?")
  * Factual lookups about specific people, organizations, or events
  * Questions requiring entity connections and relationships

- Use **Vector Search** for:
  * General policy questions (e.g., "What is the cancellation policy?", "How do refunds work?")
  * Procedural queries (e.g., "How to book a flight?", "What are the check-in procedures?")
  * Comprehensive explanations (e.g., "Tell me about baggage rules", "Explain pet travel requirements")
  * Questions requiring detailed policy information

USER QUERY: "{request.query}"

Respond with a JSON object:
{{
    "search_type": "knowledge_graph" or "vector_search",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why this search type was chosen"
}}
"""
        
        # Call Gemini for classification
        classification_result = call_gemini_tool_calling(prompt)
        
        search_type = classification_result.get("search_type", "vector_search")
        confidence = classification_result.get("confidence", 0.5)
        reasoning = classification_result.get("reasoning", "Default classification")
        
        # Execute the appropriate search based on classification
        if search_type == "knowledge_graph":
            results = await execute_knowledge_graph_search(request.query, db)
        else:
            results = await execute_vector_search(request.query, db)
        
        return PolicySearchResponse(
            search_type=search_type,
            query=request.query,
            results=results,
            confidence=confidence,
            reasoning=reasoning
        )
        
    except Exception as e:
        print(f"Error in policy search classification: {e}")
        # Fallback to vector search
        results = await execute_vector_search(request.query, db)
        return PolicySearchResponse(
            search_type="vector_search",
            query=request.query,
            results=results,
            confidence=0.3,
            reasoning=f"Fallback due to error: {str(e)}"
        )

async def execute_knowledge_graph_search(query: str, db: Session) -> Dict[str, Any]:
    """Execute knowledge graph search using Neo4j."""
    try:
        # Import the KG content retriever
        from kg_content_retrieval import KGContentRetriever
        
        # Neo4j connection details
        NEO4J_URI = "bolt://localhost:7687"
        NEO4J_USER = "neo4j"
        NEO4J_PASSWORD = "avanthika123"
        
        kg_retriever = KGContentRetriever(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        
        if not kg_retriever.connect():
            return {"error": "Failed to connect to Neo4j knowledge graph"}
        
        # Retrieve content from knowledge graph
        kg_content = kg_retriever.retrieve_content_for_query(query)
        
        kg_retriever.close()
        
        # Format the results for the client
        formatted_results = {
            "search_method": "knowledge_graph",
            "query": query,
            "entities_found": len(kg_content.get('basic_search', [])),
            "relationships_found": len(kg_content.get('center_searches', [])),
            "connection_paths": len(kg_content.get('multi_hop_searches', [])),
            "entity_contexts": len(kg_content.get('entity_contexts', [])),
            "raw_data": kg_content
        }
        
        return formatted_results
        
    except Exception as e:
        print(f"Error in knowledge graph search: {e}")
        return {
            "error": f"Knowledge graph search failed: {str(e)}",
            "search_method": "knowledge_graph",
            "query": query
        }

async def execute_vector_search(query: str, db: Session) -> Dict[str, Any]:
    """Execute vector search using Pinecone and RAG system."""
    try:
        # Import the RAG system
        from rag import complete_rag_pipeline
        
        # Execute the RAG pipeline
        rag_result = complete_rag_pipeline(query)
        
        # Format the results for the client
        formatted_results = {
            "search_method": "vector_search",
            "query": query,
            "retrieved_chunks": len(rag_result.get('retrieved_chunks', [])),
            "similar_queries": len(rag_result.get('similar_queries', [])),
            "knowledge_graph_content": rag_result.get('knowledge_graph_content', {}),
            "final_response": rag_result.get('final_response', ''),
            "raw_data": rag_result
        }
        
        return formatted_results
        
    except Exception as e:
        print(f"Error in vector search: {e}")
        return {
            "error": f"Vector search failed: {str(e)}",
            "search_method": "vector_search",
            "query": query
        }

@router.post("/gemini-tool-call", response_model=GeminiToolCallResponse)
async def gemini_tool_call(request: GeminiToolCallRequest):
    """
    Generic Gemini tool calling endpoint for any tool selection.
    """
    try:
        # Create tools description for Gemini
        tools_description = []
        for tool in request.available_tools:
            tools_description.append(f"""
Tool: {tool.get('tool_name', 'unknown')}
Description: {tool.get('description', 'No description')}
Parameters: {json.dumps(tool.get('parameters', {}), indent=2)}
Examples: {', '.join(tool.get('examples', []))}
""")
        
        tools_text = "\n".join(tools_description)
        
        # Create prompt for Gemini tool calling
        prompt = f"""
You are an AI assistant for Triops Airline. You need to select the most appropriate tool for the user's query.

AVAILABLE TOOLS:
{tools_text}

USER QUERY: "{request.query}"

INSTRUCTIONS:
1. Analyze the user query carefully
2. Select the most appropriate tool from the available tools
3. Extract relevant parameters from the query
4. Provide confidence score and reasoning

Respond with a JSON object:
{{
    "selected_tool": "tool_name",
    "tool_parameters": {{"param1": "value1", "param2": "value2"}},
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of tool selection and parameter extraction"
}}
"""
        
        # Call Gemini for tool selection
        tool_call_result = call_gemini_tool_calling(prompt)
        
        return GeminiToolCallResponse(
            selected_tool=tool_call_result.get("selected_tool", "policy_info"),
            tool_parameters=tool_call_result.get("tool_parameters", {}),
            confidence=tool_call_result.get("confidence", 0.5),
            reasoning=tool_call_result.get("reasoning", "Default tool selection")
        )
        
    except Exception as e:
        print(f"Error in Gemini tool calling: {e}")
        return GeminiToolCallResponse(
            selected_tool="policy_info",
            tool_parameters={"query": request.query},
            confidence=0.3,
            reasoning=f"Fallback due to error: {str(e)}"
        )

@router.get("/available-search-methods")
async def get_available_search_methods():
    """Get information about available search methods."""
    return {
        "search_methods": [
            {
                "name": "knowledge_graph",
                "description": "Searches Neo4j knowledge graph for entity relationships and connections",
                "best_for": [
                    "Questions about specific entities",
                    "Relationship queries",
                    "Factual lookups about people/organizations",
                    "Entity connections and relationships"
                ],
                "example_queries": [
                    "Who founded Emirates Airlines?",
                    "What is the relationship between Dubai and Emirates?",
                    "Which companies are related to aviation?"
                ]
            },
            {
                "name": "vector_search",
                "description": "Searches document embeddings using Pinecone for comprehensive policy information",
                "best_for": [
                    "General policy questions",
                    "Procedural queries",
                    "Comprehensive explanations",
                    "Detailed policy information"
                ],
                "example_queries": [
                    "What is the cancellation policy?",
                    "How do refunds work?",
                    "Tell me about baggage rules",
                    "Explain pet travel requirements"
                ]
            }
        ]
    }

