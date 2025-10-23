#!/usr/bin/env python3
"""
gRPC Chatbot Server
This module implements a gRPC server with streaming support for the chatbot.
"""

import asyncio
import grpc
from concurrent import futures
import logging
from typing import AsyncIterator, Dict, Any
import uuid
import json
from datetime import datetime

# Import generated gRPC code
try:
    import chatbot_pb2
    import chatbot_pb2_grpc
except ImportError:
    print("gRPC proto files not generated yet. Run: python -m grpc_tools.protoc --python_out=. --grpc_python_out=. proto/chatbot.proto")
    exit(1)

# Import our existing chatbot client
import sys
import os

# Add the triops directory (where client.py is located) to the path
sys.path.insert(0, '/Users/avanthikarammohan/Downloads/triops')

from client import ChatbotClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatbotServicer(chatbot_pb2_grpc.ChatbotServiceServicer):
    """gRPC servicer for chatbot operations with streaming support."""
    
    def __init__(self):
        self.chatbot_client = ChatbotClient()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def StreamChat(self, request_iterator: AsyncIterator[chatbot_pb2.ChatMessage], context) -> AsyncIterator[chatbot_pb2.ChatResponse]:
        """Stream chat messages for real-time conversation."""
        session_id = None
        
        try:
            async for message in request_iterator:
                if not session_id:
                    session_id = message.session_id or str(uuid.uuid4())
                    self.active_sessions[session_id] = {
                        'created_at': datetime.now(),
                        'message_count': 0
                    }
                
                self.active_sessions[session_id]['message_count'] += 1
                
                # Process the query
                query = message.query
                logger.info(f"Processing streaming query: {query}")
                
                # Send initial acknowledgment
                yield chatbot_pb2.ChatResponse(
                    response_id=str(uuid.uuid4()),
                    session_id=session_id,
                    type=chatbot_pb2.STREAMING_CHUNK,
                    content=f"Processing: {query}",
                    is_final=False
                )
                
                # Process the query using our existing chatbot
                try:
                    result = await self.chatbot_client.process_query(query)
                    
                    # Stream the response based on type
                    if result['type'] == 'general':
                        yield chatbot_pb2.ChatResponse(
                            response_id=str(uuid.uuid4()),
                            session_id=session_id,
                            type=chatbot_pb2.GENERAL_RESPONSE,
                            content=result['response']['response'],
                            is_final=True
                        )
                    
                    elif result['type'] == 'tool_execution':
                        tool_result = result['tool_result']
                        
                        # Send tool execution info
                        tool_execution = chatbot_pb2.ToolExecution(
                            tool_name=result['tool_selection']['selected_tool'],
                            service=result['tool_selection']['service'],
                            search_type=tool_result.get('search_type', 'unknown'),
                            success=tool_result.get('success', False)
                        )
                        
                        # Send search result info if available
                        search_result = None
                        if tool_result.get('search_type') == 'knowledge_graph':
                            raw_data = tool_result.get('raw_data', {})
                            entities = raw_data.get('basic_search', [])
                            relationships = raw_data.get('center_searches', [])
                            
                            search_result = chatbot_pb2.SearchResult(
                                search_method="knowledge_graph",
                                entities_found=len(entities),
                                relationships_found=len(relationships),
                                entities=[e.get('name', '') for e in entities[:5]],
                                relationships=[f"{r.get('name', '')} - {r.get('relation', '')}" for r in relationships[:5]]
                            )
                        elif tool_result.get('search_type') == 'vector_search':
                            raw_data = tool_result.get('raw_data', {})
                            chunks = raw_data.get('retrieved_chunks', 0)
                            
                            search_result = chatbot_pb2.SearchResult(
                                search_method="vector_search",
                                chunks_retrieved=chunks
                            )
                        
                        # Stream the response content
                        response_content = tool_result.get('response', '')
                        
                        # Split response into chunks for streaming
                        chunk_size = 200
                        chunks = [response_content[i:i+chunk_size] for i in range(0, len(response_content), chunk_size)]
                        
                        for i, chunk in enumerate(chunks):
                            is_final = (i == len(chunks) - 1)
                            
                            yield chatbot_pb2.ChatResponse(
                                response_id=str(uuid.uuid4()),
                                session_id=session_id,
                                type=chatbot_pb2.TOOL_EXECUTION,
                                content=chunk,
                                tool_execution=tool_execution,
                                search_result=search_result,
                                is_final=is_final,
                                confidence=result['tool_selection'].get('confidence', 0.5),
                                reasoning=result['tool_selection'].get('reasoning', '')
                            )
                    
                    elif result['type'] == 'management_support':
                        yield chatbot_pb2.ChatResponse(
                            response_id=str(uuid.uuid4()),
                            session_id=session_id,
                            type=chatbot_pb2.MANAGEMENT_SUPPORT,
                            content=result['response']['message'],
                            is_final=True
                        )
                    
                    elif result['type'] == 'no_tool_found':
                        yield chatbot_pb2.ChatResponse(
                            response_id=str(uuid.uuid4()),
                            session_id=session_id,
                            type=chatbot_pb2.NO_TOOL_FOUND,
                            content=result['response']['message'],
                            is_final=True
                        )
                    
                    else:
                        yield chatbot_pb2.ChatResponse(
                            response_id=str(uuid.uuid4()),
                            session_id=session_id,
                            type=chatbot_pb2.ERROR,
                            content="Unknown response type",
                            is_final=True
                        )
                
                except Exception as e:
                    logger.error(f"Error processing query: {e}")
                    yield chatbot_pb2.ChatResponse(
                        response_id=str(uuid.uuid4()),
                        session_id=session_id,
                        type=chatbot_pb2.ERROR,
                        content=f"Error processing query: {str(e)}",
                        error_info=chatbot_pb2.ErrorInfo(
                            error_code="PROCESSING_ERROR",
                            error_message=str(e)
                        ),
                        is_final=True
                    )
                
                # Send completion signal
                yield chatbot_pb2.ChatResponse(
                    response_id=str(uuid.uuid4()),
                    session_id=session_id,
                    type=chatbot_pb2.STREAMING_COMPLETE,
                    content="",
                    is_final=True
                )
        
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}")
            yield chatbot_pb2.ChatResponse(
                response_id=str(uuid.uuid4()),
                session_id=session_id or "unknown",
                type=chatbot_pb2.ERROR,
                content=f"Streaming error: {str(e)}",
                error_info=chatbot_pb2.ErrorInfo(
                    error_code="STREAMING_ERROR",
                    error_message=str(e)
                ),
                is_final=True
            )
    
    async def ProcessQuery(self, request: chatbot_pb2.ChatMessage, context) -> chatbot_pb2.ChatResponse:
        """Process a single query without streaming."""
        try:
            session_id = request.session_id or str(uuid.uuid4())
            query = request.query
            
            logger.info(f"Processing single query: {query}")
            
            result = await self.chatbot_client.process_query(query)
            
            if result['type'] == 'general':
                return chatbot_pb2.ChatResponse(
                    response_id=str(uuid.uuid4()),
                    session_id=session_id,
                    type=chatbot_pb2.GENERAL_RESPONSE,
                    content=result['response']['response'],
                    is_final=True
                )
            
            elif result['type'] == 'tool_execution':
                tool_result = result['tool_result']
                
                tool_execution = chatbot_pb2.ToolExecution(
                    tool_name=result['tool_selection']['selected_tool'],
                    service=result['tool_selection']['service'],
                    search_type=tool_result.get('search_type', 'unknown'),
                    success=tool_result.get('success', False)
                )
                
                return chatbot_pb2.ChatResponse(
                    response_id=str(uuid.uuid4()),
                    session_id=session_id,
                    type=chatbot_pb2.TOOL_EXECUTION,
                    content=tool_result.get('response', ''),
                    tool_execution=tool_execution,
                    is_final=True,
                    confidence=result['tool_selection'].get('confidence', 0.5),
                    reasoning=result['tool_selection'].get('reasoning', '')
                )
            
            else:
                return chatbot_pb2.ChatResponse(
                    response_id=str(uuid.uuid4()),
                    session_id=session_id,
                    type=chatbot_pb2.ERROR,
                    content="Unknown response type",
                    is_final=True
                )
        
        except Exception as e:
            logger.error(f"Error processing single query: {e}")
            return chatbot_pb2.ChatResponse(
                response_id=str(uuid.uuid4()),
                session_id=request.session_id or "unknown",
                type=chatbot_pb2.ERROR,
                content=f"Error: {str(e)}",
                error_info=chatbot_pb2.ErrorInfo(
                    error_code="PROCESSING_ERROR",
                    error_message=str(e)
                ),
                is_final=True
            )
    
    async def GetAvailableTools(self, request: chatbot_pb2.Empty, context) -> chatbot_pb2.ToolsResponse:
        """Get available tools."""
        try:
            tools = await self.chatbot_client.get_all_tools()
            
            tool_messages = []
            for tool in tools:
                parameters = {}
                for param_name, param_info in tool.get('parameters', {}).items():
                    parameters[param_name] = chatbot_pb2.ParameterInfo(
                        type=param_info.get('type', 'string'),
                        description=param_info.get('description', ''),
                        required=param_info.get('required', False)
                    )
                
                tool_messages.append(chatbot_pb2.Tool(
                    tool_name=tool.get('tool_name', ''),
                    description=tool.get('description', ''),
                    category=tool.get('category', ''),
                    examples=tool.get('examples', []),
                    parameters=parameters
                ))
            
            return chatbot_pb2.ToolsResponse(
                tools=tool_messages,
                total_tools=len(tool_messages)
            )
        
        except Exception as e:
            logger.error(f"Error getting tools: {e}")
            return chatbot_pb2.ToolsResponse(
                tools=[],
                total_tools=0
            )

async def serve():
    """Start the gRPC server."""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add the servicer
    chatbot_pb2_grpc.add_ChatbotServiceServicer_to_server(ChatbotServicer(), server)
    
    # Configure server
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting gRPC server on {listen_addr}")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
        await server.stop(5)

if __name__ == '__main__':
    asyncio.run(serve())
