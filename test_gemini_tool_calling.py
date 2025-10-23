#!/usr/bin/env python3
"""
Test script for Gemini Tool Calling System
This script demonstrates the new intelligent policy search routing.
"""

import asyncio
import json
from client import ChatbotClient

async def test_gemini_tool_calling():
    """Test the new Gemini tool calling system with various policy queries."""
    chatbot = ChatbotClient()
    
    # Test queries that should trigger different search methods
    test_queries = [
        # Knowledge Graph queries (entity/relationship focused)
        "Who founded Emirates Airlines?",
        "What is the relationship between Dubai and Emirates Airlines?",
        "Which companies are related to aviation in the UAE?",
        "Tell me about Sheikh Ahmed bin Saeed Al Maktoum",
        
        # Vector Search queries (policy/procedure focused)
        "What is your cancellation policy?",
        "How do refunds work?",
        "Tell me about baggage rules",
        "Can I bring my pet on the flight?",
        "What are the check-in procedures?",
        
        # General queries
        "Hello!",
        "Help me with airline information",
        "What services do you offer?",
        
        # Irrelevant queries
        "What is the square of 42?",
        "Who is the president of France?"
    ]
    
    print("🤖 Testing Gemini Tool Calling System")
    print("=" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*20} Test {i}: {query} {'='*20}")
        
        try:
            result = await chatbot.process_query(query)
            
            # Print a clean summary based on result type
            if result['type'] == 'general':
                print(f"✅ General Response:")
                print(f"   {result['response']['response']}")
                
            elif result['type'] == 'tool_execution':
                tool_name = result['tool_selection']['selected_tool']
                print(f"✅ Tool Executed: {tool_name}")
                
                if tool_name == 'policy_info':
                    tool_result = result['tool_result']
                    search_type = tool_result.get('search_type', 'unknown')
                    print(f"   Search Method: {search_type}")
                    print(f"   Success: {tool_result.get('success', False)}")
                    
                    # Show response preview
                    response = tool_result.get('response', '')
                    if len(response) > 200:
                        print(f"   Response: {response[:200]}...")
                    else:
                        print(f"   Response: {response}")
                        
                else:
                    print(f"   Response: {result['tool_result'].get('response', 'No response')}")
                    
            elif result['type'] == 'management_support':
                print(f"⚠️ Management Support Required:")
                print(f"   {result['response']['message']}")
                
            elif result['type'] == 'no_tool_found':
                print(f"❌ No Tool Found:")
                print(f"   {result['response']['message']}")
                
            else:
                print(f"❓ Unknown Result Type: {result['type']}")
                
        except Exception as e:
            print(f"❌ Error processing query: {e}")
        
        print("-" * 80)

async def test_policy_search_classification():
    """Test the policy search classification endpoint directly."""
    import httpx
    
    print("\n🔬 Testing Policy Search Classification Directly")
    print("=" * 60)
    
    test_queries = [
        "Who founded Emirates Airlines?",  # Should be knowledge graph
        "What is your cancellation policy?",  # Should be vector search
        "Tell me about Dubai government and Emirates",  # Should be knowledge graph
        "How do I get a refund?",  # Should be vector search
    ]
    
    async with httpx.AsyncClient() as client:
        for query in test_queries:
            print(f"\nQuery: {query}")
            try:
                response = await client.post(
                    "http://localhost:8000/api/gemini/policy-search-classify",
                    json={"query": query}
                )
                response.raise_for_status()
                
                result = response.json()
                print(f"✅ Search Type: {result['search_type']}")
                print(f"   Confidence: {result['confidence']:.2f}")
                print(f"   Reasoning: {result['reasoning']}")
                
                # Show some results preview
                results = result.get('results', {})
                if result['search_type'] == 'knowledge_graph':
                    raw_data = results.get('raw_data', {})
                    entities = len(raw_data.get('basic_search', []))
                    relationships = len(raw_data.get('center_searches', []))
                    print(f"   Entities Found: {entities}")
                    print(f"   Relationships Found: {relationships}")
                else:
                    retrieved_chunks = results.get('retrieved_chunks', 0)
                    print(f"   Retrieved Chunks: {retrieved_chunks}")
                
            except Exception as e:
                print(f"❌ Error: {e}")

async def main():
    """Main test function."""
    print("🚀 Starting Gemini Tool Calling Tests")
    print("Make sure the backend server is running on http://localhost:8000")
    print("Press Ctrl+C to stop...")
    
    try:
        # Test the full chatbot workflow
        await test_gemini_tool_calling()
        
        # Test the policy classification directly
        await test_policy_search_classification()
        
        print("\n✅ All tests completed!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

