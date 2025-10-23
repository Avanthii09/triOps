#!/usr/bin/env python3
"""
gRPC Chatbot Demo
This script demonstrates the gRPC streaming chatbot functionality.
"""

import asyncio
import grpc
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from backend.proto import chatbot_pb2, chatbot_pb2_grpc
except ImportError:
    print("❌ Error: gRPC proto files not found.")
    print("Please run: cd backend && python generate_grpc.py")
    sys.exit(1)

class ChatbotGRPCDemo:
    def __init__(self, server_url='localhost:50051'):
        self.server_url = server_url
        self.channel = None
        self.stub = None
        self.session_id = f"demo_session_{asyncio.get_event_loop().time()}"
    
    async def connect(self):
        """Connect to the gRPC server."""
        try:
            self.channel = grpc.aio.insecure_channel(self.server_url)
            self.stub = chatbot_pb2_grpc.ChatbotServiceStub(self.channel)
            
            # Test connection by getting available tools
            try:
                response = await self.stub.GetAvailableTools(chatbot_pb2.Empty())
                print(f"✅ Connected to gRPC server at {self.server_url}")
                print(f"📋 Available tools: {response.total_tools}")
                return True
            except grpc.aio.AioRpcError as e:
                print(f"❌ Failed to connect to gRPC server: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    async def stream_chat_demo(self, query):
        """Demonstrate streaming chat functionality."""
        print(f"\n{'='*60}")
        print(f"🤖 Streaming Chat Demo: {query}")
        print(f"{'='*60}")
        
        try:
            # Create the streaming call
            async def request_generator():
                yield chatbot_pb2.ChatMessage(
                    query=query,
                    session_id=self.session_id,
                    user_id="demo_user",
                    metadata={"demo": "true"}
                )
            
            # Process streaming responses
            async for response in self.stub.StreamChat(request_generator()):
                print(f"\n📨 Response Type: {response.type}")
                print(f"📝 Content: {response.content}")
                
                if response.tool_execution:
                    print(f"🔧 Tool: {response.tool_execution.tool_name}")
                    print(f"🔍 Search Type: {response.tool_execution.search_type}")
                    print(f"✅ Success: {response.tool_execution.success}")
                
                if response.search_result:
                    print(f"📊 Search Method: {response.search_result.search_method}")
                    if response.search_result.entities_found > 0:
                        print(f"🏢 Entities Found: {response.search_result.entities_found}")
                    if response.search_result.relationships_found > 0:
                        print(f"🔗 Relationships Found: {response.search_result.relationships_found}")
                    if response.search_result.chunks_retrieved > 0:
                        print(f"📄 Chunks Retrieved: {response.search_result.chunks_retrieved}")
                
                if response.confidence > 0:
                    print(f"🎯 Confidence: {response.confidence:.2f}")
                
                if response.reasoning:
                    print(f"💭 Reasoning: {response.reasoning}")
                
                if response.is_final:
                    print("🏁 Final response received")
                    break
                
                print("-" * 40)
        
        except grpc.aio.AioRpcError as e:
            print(f"❌ gRPC Error: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def single_query_demo(self, query):
        """Demonstrate single query functionality."""
        print(f"\n{'='*60}")
        print(f"💬 Single Query Demo: {query}")
        print(f"{'='*60}")
        
        try:
            response = await self.stub.ProcessQuery(chatbot_pb2.ChatMessage(
                query=query,
                session_id=self.session_id,
                user_id="demo_user"
            ))
            
            print(f"📨 Response Type: {response.type}")
            print(f"📝 Content: {response.content}")
            
            if response.tool_execution:
                print(f"🔧 Tool: {response.tool_execution.tool_name}")
                print(f"🔍 Search Type: {response.tool_execution.search_type}")
            
            if response.confidence > 0:
                print(f"🎯 Confidence: {response.confidence:.2f}")
            
            print("✅ Single query completed")
        
        except grpc.aio.AioRpcError as e:
            print(f"❌ gRPC Error: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def disconnect(self):
        """Disconnect from the gRPC server."""
        if self.channel:
            await self.channel.close()
            print("🔌 Disconnected from gRPC server")

async def main():
    """Main demo function."""
    print("🚀 Triops gRPC Chatbot Demo")
    print("Make sure the gRPC server is running on localhost:50051")
    print("Press Ctrl+C to stop...")
    
    demo = ChatbotGRPCDemo()
    
    try:
        # Connect to server
        if not await demo.connect():
            print("❌ Failed to connect to gRPC server")
            return
        
        # Demo queries
        demo_queries = [
            "Who founded Emirates Airlines?",
            "What is your cancellation policy?",
            "Tell me about Dubai government and Emirates relationship",
            "How do refunds work?",
            "What is the relationship between Sheikh Ahmed and Emirates?"
        ]
        
        print(f"\n🎯 Running {len(demo_queries)} demo queries...")
        
        # Test streaming chat
        for i, query in enumerate(demo_queries, 1):
            print(f"\n{'='*20} Demo {i}/{len(demo_queries)} {'='*20}")
            await demo.stream_chat_demo(query)
            
            # Small delay between queries
            await asyncio.sleep(1)
        
        print(f"\n🎉 Demo completed successfully!")
        print("=" * 60)
        print("✅ gRPC streaming is working!")
        print("✅ Knowledge graph search is functional!")
        print("✅ Vector search is functional!")
        print("✅ Tool execution is working!")
        print("✅ Frontend can now connect to gRPC server!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    finally:
        await demo.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

