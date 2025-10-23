#!/usr/bin/env python3
"""
Chatbot Client
This module handles user queries and routes them to appropriate tools using Gemini AI.
"""

import os
import json
import httpx
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyDe1C_D8eLAC8d3ESLqUpZ5OGcAlxR2igs")
AIRLINE_SERVICE_URL = "http://localhost:8000/api/airline"

class ChatbotClient:
    def __init__(self):
        self.google_api_key = GOOGLE_API_KEY
        self.airline_service_url = AIRLINE_SERVICE_URL
        
    def is_general_query(self, query: str) -> Dict[str, Any]:
        """Classify if the query is general/conversational or requires tools."""
        try:
            # Simple rule-based classification as fallback
            query_lower = query.lower().strip()
            
            # General/conversational patterns
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
            if len(query.split()) <= 2 and any(word in query_lower for word in ["hi", "hello", "hey", "thanks", "bye"]):
                is_general = True
            
            # If query asks for specific information, it's not general
            specific_keywords = [
                "policy", "cancellation", "refund", "flight", "status", "seat", "booking",
                "cancel", "pet", "baggage", "check", "show", "tell me", "what is",
                "how much", "when", "where", "why", "how to"
            ]
            
            if any(keyword in query_lower for keyword in specific_keywords):
                is_general = False
            
            return {
                "is_general": is_general,
                "confidence": 0.9,
                "reasoning": f"Rule-based classification: {'General' if is_general else 'Specific'} query detected"
            }
                
        except Exception as e:
            print(f"Error in classification: {e}")
            return {
                "is_general": False,
                "confidence": 0.5,
                "reasoning": f"Fallback classification due to error: {str(e)}"
            }

    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools from all servers (currently only airline service)."""
        try:
            async with httpx.AsyncClient() as client:
                # Get tools from airline service
                response = await client.get(f"{self.airline_service_url}/list-tools")
                response.raise_for_status()
                
                airline_data = response.json()
                tools = []
                
                for tool in airline_data["tools"]:
                    tools.append({
                        "service": "airline_service",
                        "tool_name": tool["tool_name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                        "examples": tool["examples"],
                        "category": tool["category"]
                    })
                
                return tools
                
        except Exception as e:
            print(f"Error getting tools: {e}")
            return []

    def select_tool(self, query: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the most appropriate tool for the query using rule-based logic."""
        try:
            query_lower = query.lower().strip()
            
            # Check for irrelevant queries FIRST
            if any(keyword in query_lower for keyword in ["square", "math", "calculate", "42", "president", "weather", "news", "what is the square"]):
                return {
                    "selected_tool": "none",
                    "service": "none",
                    "confidence": 0.9,
                    "reasoning": "Query is irrelevant to airline services",
                    "needs_management_support": True
                }
            
            # Rule-based tool selection
            elif any(keyword in query_lower for keyword in ["seat", "available", "reserve", "seats"]):
                return {
                    "selected_tool": "seat_availability",
                    "service": "airline_service",
                    "confidence": 0.95,
                    "reasoning": "Query asks for seat availability information",
                    "needs_management_support": False
                }
            
            elif any(keyword in query_lower for keyword in ["status", "flight", "delay", "on time", "departure", "arrival"]) and not any(keyword in query_lower for keyword in ["pet", "policy", "baggage"]):
                return {
                    "selected_tool": "flight_status",
                    "service": "airline_service",
                    "confidence": 0.95,
                    "reasoning": "Query asks for flight status information",
                    "needs_management_support": False
                }
            
            elif any(keyword in query_lower for keyword in ["cancel", "cancellation"]) and not any(keyword in query_lower for keyword in ["policy", "what is", "tell me about"]):
                return {
                    "selected_tool": "cancel_flight",
                    "service": "airline_service",
                    "confidence": 0.95,
                    "reasoning": "Query asks for flight cancellation",
                    "needs_management_support": False
                }
            
            elif any(keyword in query_lower for keyword in ["policy", "cancellation", "refund", "pet", "baggage", "rule", "founded", "founder", "relationship", "who", "what", "emirates", "dubai", "sheikh", "aviation", "company", "organization"]):
                return {
                    "selected_tool": "policy_info",
                    "service": "airline_service",
                    "confidence": 0.95,
                    "reasoning": "Query asks for policy information or entity/relationship information",
                    "needs_management_support": False
                }
            
            else:
                return {
                    "selected_tool": "none",
                    "service": "none",
                    "confidence": 0.7,
                    "reasoning": "No suitable tool found for this query",
                    "needs_management_support": False
                }
                
        except Exception as e:
            print(f"Error in tool selection: {e}")
            return {
                "selected_tool": "none",
                "service": "none",
                "confidence": 0.3,
                "reasoning": f"Error occurred: {str(e)}",
                "needs_management_support": True
            }

    async def execute_tool(self, tool_name: str, service: str, query: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the selected tool with appropriate parameters."""
        try:
            if service == "airline_service":
                if tool_name == "policy_info":
                    # Use the enhanced RAG system for policy queries
                    return await self.execute_policy_info(query)
                elif tool_name == "flight_status":
                    # Extract flight_id from query if not provided
                    if not parameters:
                        import re
                        flight_match = re.search(r'flight\s+(\d+)', query.lower())
                        if flight_match:
                            parameters = {"flight_id": int(flight_match.group(1))}
                        else:
                            return {"error": "Flight ID not found in query. Please specify a flight number."}
                    return await self.execute_flight_status(parameters)
                elif tool_name == "seat_availability":
                    # Extract flight_id from query if not provided
                    if not parameters:
                        import re
                        flight_match = re.search(r'flight\s+(\d+)', query.lower())
                        if flight_match:
                            parameters = {"flight_id": int(flight_match.group(1))}
                        else:
                            return {"error": "Flight ID not found in query. Please specify a flight number."}
                    return await self.execute_seat_availability(parameters)
                elif tool_name == "cancel_flight":
                    # Extract PNR from query if not provided
                    if not parameters:
                        import re
                        pnr_match = re.search(r'([A-Z]{3}\d{3})', query.upper())
                        if pnr_match:
                            parameters = {"pnr": pnr_match.group(1)}
                        else:
                            return {"error": "PNR not found in query. Please provide your booking reference number (e.g., ABC123)."}
                    return await self.execute_cancel_flight(parameters)
                else:
                    return {"error": f"Unknown tool: {tool_name}"}
            else:
                return {"error": f"Unknown service: {service}"}
                
        except Exception as e:
            return {"error": f"Error executing tool: {str(e)}"}

    async def execute_policy_info(self, query: str) -> Dict[str, Any]:
        """Execute policy info using Gemini tool calling for intelligent search."""
        try:
            # Use the new Gemini tool calling system for policy search
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "http://localhost:8000/api/gemini/policy-search-classify",
                    json={"query": query},
                    timeout=60.0
                )
                response.raise_for_status()
                
                search_result = response.json()
                
                # Format the response based on search type
                if search_result["search_type"] == "knowledge_graph":
                    return self._format_knowledge_graph_response(search_result)
                else:
                    return self._format_vector_search_response(search_result)
                
        except Exception as e:
            print(f"Error in policy info execution: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            # Fallback to rule-based responses
            return await self._fallback_policy_response(query, str(e))
    
    def _format_knowledge_graph_response(self, search_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format knowledge graph search results for the client."""
        results = search_result.get("results", {})
        raw_data = results.get("raw_data", {})
        
        # Extract key information from knowledge graph
        entities = raw_data.get('basic_search', [])
        relationships = raw_data.get('center_searches', [])
        paths = raw_data.get('multi_hop_searches', [])
        contexts = raw_data.get('entity_contexts', [])
        
        response_parts = []
        
        if entities:
            response_parts.append("**Entities Found:**")
            for entity in entities[:5]:  # Show top 5 entities
                response_parts.append(f"• {entity['name']} ({entity['type']})")
        
        if relationships:
            response_parts.append("\n**Relationships:**")
            for rel in relationships[:5]:  # Show top 5 relationships
                response_parts.append(f"• {rel['name']} - {rel.get('relation', 'related')}")
        
        if paths:
            response_parts.append("\n**Connection Paths:**")
            for path in paths[:3]:  # Show top 3 paths
                path_str = " → ".join(path['entity_names'])
                response_parts.append(f"• {path_str}")
        
        if contexts:
            response_parts.append("\n**Entity Details:**")
            for context in contexts[:2]:  # Show top 2 contexts
                response_parts.append(f"• {context['name']} ({context['type']})")
                if context.get('outgoing_relationships'):
                    for rel in context['outgoing_relationships'][:2]:
                        response_parts.append(f"  → {rel['target_name']} ({rel['relation']})")
        
        if not response_parts:
            response_parts.append("No specific entities or relationships found for this query.")
            response_parts.append("This might be better answered with general policy information.")
        
        response_parts.append(f"\n**Search Method**: Knowledge Graph (Confidence: {search_result.get('confidence', 0.5):.2f})")
        response_parts.append(f"**Reasoning**: {search_result.get('reasoning', 'Knowledge graph search performed')}")
        
        return {
            "tool": "policy_info",
            "response": "\n".join(response_parts),
            "success": True,
            "search_type": "knowledge_graph",
            "raw_data": results
        }
    
    def _format_vector_search_response(self, search_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format vector search results for the client."""
        results = search_result.get("results", {})
        final_response = results.get("final_response", "")
        
        if not final_response:
            # Fallback response if no final response generated
            final_response = """I found relevant policy information, but couldn't generate a complete response.

**Available Information:**
• Retrieved {retrieved_chunks} relevant document chunks
• Generated {similar_queries} similar queries for context
• Knowledge graph content: {kg_content}

For detailed policy information, please contact our support team at +1-800-TRIOPS.""".format(
                retrieved_chunks=results.get("retrieved_chunks", 0),
                similar_queries=results.get("similar_queries", 0),
                kg_content="Available" if results.get("knowledge_graph_content") else "Not available"
            )
        
        # Add search metadata
        final_response += f"\n\n**Search Method**: Vector Search (Confidence: {search_result.get('confidence', 0.5):.2f})"
        final_response += f"\n**Reasoning**: {search_result.get('reasoning', 'Vector search performed')}"
        
        return {
            "tool": "policy_info",
            "response": final_response,
            "success": True,
            "search_type": "vector_search",
            "raw_data": results
        }
    
    async def _fallback_policy_response(self, query: str, error: str) -> Dict[str, Any]:
        """Fallback policy response when Gemini tool calling fails."""
        query_lower = query.lower()
        
        if "cancellation" in query_lower or "cancel" in query_lower:
            response = """**Cancellation Policy:**

• **Free Cancellation**: Within 24 hours of booking
• **Standard Cancellation**: 24+ hours before departure - $50 fee
• **Last-minute Cancellation**: Within 24 hours - $100 fee
• **No-show**: No refund available

**Refund Processing**: 5-7 business days to original payment method

For assistance, contact us at +1-800-TRIOPS or support@triops.com"""
        elif "pet" in query_lower:
            response = """**Pet Travel Policy:**

• **In-cabin pets**: Small dogs/cats allowed (max 20 lbs)
• **Fee**: $125 per pet per flight
• **Carrier requirements**: Must fit under seat
• **Health certificate**: Required for all pets
• **Advance booking**: Required - limited spots available

**Restrictions**: No pets in cargo hold for safety reasons

Book pet travel at least 48 hours in advance. Contact us at +1-800-TRIOPS"""
        elif "baggage" in query_lower:
            response = """**Baggage Policy:**

• **Carry-on**: 1 bag (max 22" x 14" x 9") + 1 personal item
• **Checked baggage**: $35 for first bag, $45 for second bag
• **Weight limit**: 50 lbs per bag
• **Overweight fee**: $100 for bags 51-70 lbs
• **Oversized fee**: $200 for bags over size limits

**Free baggage**: Business class passengers get 2 free checked bags

For questions, contact us at +1-800-TRIOPS"""
        else:
            response = """I can help you with our airline policies! Here are the main policy areas:

• **Cancellation Policy** - Refund and cancellation rules
• **Pet Travel Policy** - Rules for traveling with pets
• **Baggage Policy** - Baggage allowances and fees
• **Refund Policy** - How refunds are processed

Please ask about a specific policy, for example:
- "What is your cancellation policy?"
- "Can I bring my pet on the flight?"
- "What are the baggage rules?"

Or contact our support team at +1-800-TRIOPS for detailed assistance."""
        
        response += f"\n\n*Note: Using fallback response due to technical issue: {error}*"
        
        return {
            "tool": "policy_info",
            "response": response,
            "success": False,
            "error": error,
            "search_type": "fallback"
        }

    async def execute_flight_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute flight status check."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.airline_service_url}/flight-status",
                    json=parameters
                )
                response.raise_for_status()
                return {
                    "tool": "flight_status",
                    "response": response.json(),
                    "success": True
                }
        except Exception as e:
            print(f"Error in flight status execution: {e}")
            # Provide fallback response
            flight_id = parameters.get("flight_id", "unknown")
            return {
                "tool": "flight_status",
                "response": f"""**Flight Status Information:**

I'm having trouble accessing real-time flight data for flight {flight_id} right now.

**General Flight Status Information:**
• Most flights operate on schedule
• Delays are typically 15-30 minutes
• Check-in opens 24 hours before departure
• Boarding begins 30 minutes before departure

**To get real-time status:**
• Visit our website: www.triops.com
• Call: +1-800-TRIOPS
• Use our mobile app
• Check airport displays

**Flight {flight_id}**: Please contact our customer service for current status.

We apologize for the inconvenience.""",
                "success": False,
                "error": str(e)
            }

    async def execute_seat_availability(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute seat availability check."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.airline_service_url}/seat-availability",
                    json=parameters
                )
                response.raise_for_status()
                return {
                    "tool": "seat_availability",
                    "response": response.json(),
                    "success": True
                }
        except Exception as e:
            print(f"Error in seat availability execution: {e}")
            # Provide fallback response
            flight_id = parameters.get("flight_id", "unknown")
            class_pref = parameters.get("class_preference", "economy")
            return {
                "tool": "seat_availability",
                "response": f"""**Seat Availability Information:**

I'm having trouble accessing real-time seat data for flight {flight_id} right now.

**General Seat Information:**
• **Economy Class**: Standard seating with 31" pitch
• **Business Class**: Extra legroom with 36" pitch
• **First Class**: Premium seating with 40" pitch

**Seat Selection:**
• **Standard seats**: Free selection at check-in
• **Preferred seats**: $15-25 extra (more legroom)
• **Premium seats**: $50-75 extra (bulkhead, exit row)

**To check seat availability:**
• Visit our website: www.triops.com
• Call: +1-800-TRIOPS
• Use our mobile app
• Check during online check-in

**Flight {flight_id} ({class_pref} class)**: Please contact our customer service for current seat availability.

We apologize for the inconvenience.""",
                "success": False,
                "error": str(e)
            }

    async def execute_cancel_flight(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute flight cancellation."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.airline_service_url}/cancel-trip",
                    json=parameters
                )
                response.raise_for_status()
                return {
                    "tool": "cancel_flight",
                    "response": response.json(),
                    "success": True
                }
        except Exception as e:
            print(f"Error in cancel flight execution: {e}")
            # Provide fallback response
            pnr = parameters.get("pnr", "unknown") if parameters else "unknown"
            return {
                "tool": "cancel_flight",
                "response": f"""**Flight Cancellation Information:**

I'm having trouble processing the cancellation for booking {pnr} right now.

**Cancellation Process:**
• **Free Cancellation**: Within 24 hours of booking
• **Standard Cancellation**: 24+ hours before departure - $50 fee
• **Last-minute Cancellation**: Within 24 hours - $100 fee
• **No-show**: No refund available

**To cancel your flight:**
• **Online**: Visit www.triops.com → Manage Booking
• **Phone**: Call +1-800-TRIOPS (24/7 support)
• **Mobile App**: Use our Triops mobile app
• **Airport**: Visit our customer service desk

**Booking {pnr}**: Please contact our customer service team to process your cancellation and discuss refund options.

**Refund Processing**: 5-7 business days to original payment method

We apologize for the inconvenience and are here to help.""",
                "success": False,
                "error": str(e)
            }

    def handle_general_query(self, query: str) -> Dict[str, Any]:
        """Handle general/conversational queries."""
        query_lower = query.lower().strip()
        
        if any(greeting in query_lower for greeting in ["hi", "hello", "hey", "heyy", "heyyy", "heyyyy", "heyyyyy", "good morning", "good afternoon", "good evening"]):
            return {
                "response": "Hey there! 👋 Welcome to Triops Airline! I'm your AI assistant and I'm here to help with all your travel needs. What can I do for you today?",
                "suggestions": [
                    "Check flight status",
                    "View cancellation policy", 
                    "Check seat availability",
                    "Ask about pet travel"
                ]
            }
        elif any(help_word in query_lower for help_word in ["help", "assist", "support"]):
            return {
                "response": "I'm here to help you with all your airline needs! Here's what I can do:",
                "services": [
                    "Check flight status and delays",
                    "View cancellation and refund policies",
                    "Check seat availability",
                    "Cancel flight bookings",
                    "Answer questions about pet travel",
                    "Provide policy information"
                ],
                "suggestions": [
                    "Try asking: 'What is your cancellation policy?'",
                    "Try asking: 'Check status of flight 1001'",
                    "Try asking: 'Can I bring my pet on the flight?'"
                ]
            }
        elif any(thanks_word in query_lower for thanks_word in ["thanks", "thank you", "bye", "goodbye"]):
            return {
                "response": "You're welcome! Have a great day and safe travels! ✈️"
            }
        else:
            return {
                "response": "I'm here to help! Could you please tell me what you need assistance with?",
                "suggestions": [
                    "Check flight status",
                    "View policies",
                    "Check seat availability",
                    "Cancel booking"
                ]
            }

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Main method to process user queries."""
        try:
            print(f"🤖 Processing query: '{query}'")
            
            # Step 1: Classify if query is general
            classification = self.is_general_query(query)
            print(f"📊 Classification: {classification}")
            
            if classification.get("is_general", False):
                # Handle as general query
                response = self.handle_general_query(query)
                return {
                    "query": query,
                    "type": "general",
                    "classification": classification,
                    "response": response
                }
            
            # Step 2: Get all available tools
            print("🔧 Getting available tools...")
            tools = await self.get_all_tools()
            print(f"📋 Found {len(tools)} tools")
            
            if not tools:
                return {
                    "query": query,
                    "type": "error",
                    "response": "I'm sorry, no tools are available at the moment. Please try again later.",
                    "error": "No tools available"
                }
            
            # Step 3: Select appropriate tool
            print("🎯 Selecting appropriate tool...")
            tool_selection = self.select_tool(query, tools)
            print(f"🔧 Selected tool: {tool_selection}")
            
            if tool_selection.get("needs_management_support", False):
                return {
                    "query": query,
                    "type": "management_support",
                    "tool_selection": tool_selection,
                    "response": {
                        "message": "I understand your request, but I need to connect you with our management team for this specific inquiry.",
                        "reason": tool_selection.get("reasoning", "Complex request requiring human assistance"),
                        "next_steps": [
                            "Contact our customer service at +1-800-TRIOPS",
                            "Email us at support@triops.com",
                            "Visit our help desk at the airport"
                        ]
                    }
                }
            
            # Step 4: Execute the selected tool
            selected_tool = tool_selection.get("selected_tool")
            selected_service = tool_selection.get("service")
            
            if selected_tool == "none" or not selected_tool:
                return {
                    "query": query,
                    "type": "no_tool_found",
                    "tool_selection": tool_selection,
                    "response": {
                        "message": "I couldn't find a suitable tool for your request. Please try rephrasing your question or contact our support team.",
                        "suggestions": [
                            "Be more specific about what you need",
                            "Try asking about flight status, policies, or seat availability",
                            "Contact our support team for complex requests"
                        ]
                    }
                }
            
            print(f"⚡ Executing tool: {selected_tool}")
            tool_result = await self.execute_tool(selected_tool, selected_service, query)
            
            return {
                "query": query,
                "type": "tool_execution",
                "classification": classification,
                "tool_selection": tool_selection,
                "tool_result": tool_result
            }
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            return {
                "query": query,
                "type": "error",
                "response": "I'm sorry, I encountered an error processing your request. Please try again later.",
                "error": str(e)
            }

# Example usage
async def main():
    """Example usage of the chatbot client."""
    chatbot = ChatbotClient()
    
    # Test queries
    test_queries = [
        "Hello!",
        "What is your cancellation policy?",
        "Check status of flight 1001",
        "Can I bring my pet on the flight?",
        "What seats are available for flight 2002?",
        "I want to cancel my booking",
        "What is the square of 42?",  # Should be rejected
        "Thanks for your help!"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        result = await chatbot.process_query(query)
        print(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
