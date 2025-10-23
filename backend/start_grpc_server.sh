#!/bin/bash
# Start gRPC Chatbot Server

echo "🚀 Starting Triops gRPC Chatbot Server"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "grpc_server.py" ]; then
    echo "❌ Error: grpc_server.py not found. Please run this script from the backend directory."
    exit 1
fi

# Check if gRPC files exist
if [ ! -f "chatbot_pb2.py" ] || [ ! -f "chatbot_pb2_grpc.py" ]; then
    echo "📦 Generating gRPC Python files..."
    python generate_grpc.py
    if [ $? -ne 0 ]; then
        echo "❌ Failed to generate gRPC files"
        exit 1
    fi
fi

# Check if required dependencies are installed
echo "🔍 Checking dependencies..."
python -c "import grpc" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing gRPC dependencies..."
    pip install grpcio grpcio-tools grpcio-status
fi

# Check if backend server is running
echo "🔍 Checking if backend server is running..."
curl -s http://localhost:8000/api/airline/list-tools > /dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Backend server not running on port 8000"
    echo "   The gRPC server will work, but some features may not be available"
fi

# Start the gRPC server
echo "🚀 Starting gRPC server on port 50051..."
echo "   Frontend will connect to: localhost:50051"
echo "   Press Ctrl+C to stop the server"
echo ""

python grpc_server.py

