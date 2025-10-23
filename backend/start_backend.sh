#!/bin/bash

# Triops Airline Backend Startup Script

echo "🚀 Starting Triops Airline Backend..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cat > .env << EOF
# Database Configuration
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=triops_airline

# JWT Configuration
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Configuration
DEBUG=True
API_HOST=0.0.0.0
API_PORT=8000

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
EOF
    echo "✅ .env file created. Please update database credentials if needed."
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📦 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🗄️ Setting up database..."
python setup_database.py

echo "🚀 Starting FastAPI server..."
echo "   API will be available at: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""

python main.py
