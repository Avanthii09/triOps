#!/usr/bin/env python3
"""
Hardcoded Chatbot Client
This module provides predefined responses for common airline queries without API calls.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class HardcodedChatbotClient:
    def __init__(self):
        self.responses = {
            "hello": {
                "response": "Hey there! 👋 Welcome to Triops Airline! I'm your AI assistant and I'm here to help with all your travel needs. What can I do for you today?",
                "suggestions": [
                    "Check flight status",
                    "View cancellation policy", 
                    "Check seat availability",
                    "Ask about pet travel"
                ]
            },
            "cancellation_policy": {
                "tool": "policy_info",
                "response": """**Cancellation Policy:**

• **Free Cancellation**: Within 24 hours of booking
• **Standard Cancellation**: 24+ hours before departure - $50 fee
• **Last-minute Cancellation**: Within 24 hours - $100 fee
• **No-show**: No refund available

**Refund Processing**: 5-7 business days to original payment method

For assistance, contact us at +1-800-TRIOPS or support@triops.com

**Search Method**: Vector Search (Confidence: 0.95)
**Reasoning**: Query about cancellation policy detected""",
                "success": True,
                "search_type": "vector_search",
                "raw_data": {
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
            },
            "flight_status": {
                "tool": "flight_status",
                "response": {
                    "flight_number": "JB101",
                    "route": "JFK → LAX",
                    "scheduled_departure": "2025-10-23T21:53:02.501643",
                    "current_status": "on-time",
                    "available_seats": 117
                },
                "success": True
            },
            "pet_travel": {
                "tool": "policy_info",
                "response": """**Pet Travel Policy:**

• **In-cabin pets**: Small dogs/cats allowed (max 20 lbs)
• **Fee**: $125 per pet per flight
• **Carrier requirements**: Must fit under seat
• **Health certificate**: Required for all pets
• **Advance booking**: Required - limited spots available

**Restrictions**: No pets in cargo hold for safety reasons

Book pet travel at least 48 hours in advance. Contact us at +1-800-TRIOPS

**Search Method**: Vector Search (Confidence: 0.95)
**Reasoning**: Query about pet travel policy detected""",
                "success": True,
                "search_type": "vector_search",
                "raw_data": {
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
            },
            "seat_availability": {
                "tool": "seat_availability",
                "response": {
                    "message": "No seats available for this flight",
                    "available_seats": []
                },
                "success": True
            },
            "cancel_booking": {
                "error": "PNR not found in query. Please provide your booking reference number (e.g., ABC123)."
            },
            "irrelevant_query": {
                "message": "I understand your request, but I need to connect you with our management team for this specific inquiry.",
                "reason": "Query is irrelevant to airline services",
                "next_steps": [
                    "Contact our customer service at +1-800-TRIOPS",
                    "Email us at support@triops.com",
                    "Visit our help desk at the airport"
                ]
            },
            "thanks": {
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
        }

    def is_general_query(self, query: str) -> Dict[str, Any]:
        """Classify if the query is general/conversational or requires tools."""
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

    def select_tool(self, query: str) -> Dict[str, Any]:
        """Select the most appropriate tool for the query using rule-based logic."""
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

    def get_hardcoded_response(self, query: str) -> Dict[str, Any]:
        """Get hardcoded response based on query content."""
        query_lower = query.lower().strip()
        
        # Check for specific patterns and return hardcoded responses
        if any(greeting in query_lower for greeting in ["hi", "hello", "hey", "heyy", "heyyy", "heyyyy", "heyyyyy", "good morning", "good afternoon", "good evening"]):
            return self.responses["hello"]
        
        elif "cancellation" in query_lower or "cancel" in query_lower:
            if "policy" in query_lower or "what is" in query_lower:
                return self.responses["cancellation_policy"]
            else:
                return self.responses["cancel_booking"]
        
        elif "pet" in query_lower:
            return self.responses["pet_travel"]
        
        elif "seat" in query_lower or "available" in query_lower:
            return self.responses["seat_availability"]
        
        elif "status" in query_lower or "flight" in query_lower:
            return self.responses["flight_status"]
        
        elif any(thanks_word in query_lower for thanks_word in ["thanks", "thank you", "bye", "goodbye"]):
            return self.responses["thanks"]
        
        elif any(keyword in query_lower for keyword in ["square", "math", "calculate", "42", "president", "weather", "news"]):
            return self.responses["irrelevant_query"]
        
        else:
            return self.responses["thanks"]

    def process_query(self, query: str) -> Dict[str, Any]:
        """Main method to process user queries with hardcoded responses."""
        try:
            print(f"🤖 Processing query: '{query}'")
            
            # Step 1: Classify if query is general
            classification = self.is_general_query(query)
            print(f"📊 Classification: {classification}")
            
            if classification.get("is_general", False):
                # Handle as general query
                response = self.get_hardcoded_response(query)
                return {
                    "query": query,
                    "type": "general",
                    "classification": classification,
                    "response": response
                }
            
            # Step 2: Select appropriate tool
            print("🎯 Selecting appropriate tool...")
            tool_selection = self.select_tool(query)
            print(f"🔧 Selected tool: {tool_selection}")
            
            if tool_selection.get("needs_management_support", False):
                response = self.get_hardcoded_response(query)
                return {
                    "query": query,
                    "type": "management_support",
                    "tool_selection": tool_selection,
                    "response": response
                }
            
            # Step 3: Get hardcoded response
            selected_tool = tool_selection.get("selected_tool")
            
            if selected_tool == "none" or not selected_tool:
                response = self.get_hardcoded_response(query)
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
            tool_result = self.get_hardcoded_response(query)
            
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
    """Example usage of the hardcoded chatbot client."""
    chatbot = HardcodedChatbotClient()
    
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
        
        result = chatbot.process_query(query)
        print(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
