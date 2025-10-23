#!/bin/bash

# Triops Airline Management System Setup Script

echo "🚀 Setting up Triops Airline Management System..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed. Please install Node.js 16+ and try again."
    exit 1
fi

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is required but not installed. Please install PostgreSQL and try again."
    exit 1
fi

echo "✅ Prerequisites check passed!"

# Create virtual environment for Python backend
echo "📦 Setting up Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd ../frontend
npm install

# Go back to root
cd ..

# Create environment file for backend
echo "⚙️ Creating environment configuration..."
cat > backend/.env << EOF
# Database Configuration
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=triops_airline

# JWT Configuration
SECRET_KEY=your-secret-key-change-this-in-production-$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Configuration
DEBUG=True
API_HOST=0.0.0.0
API_PORT=8000

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
EOF

echo "✅ Environment configuration created!"

# Database setup instructions
echo ""
echo "🗄️ Database Setup Instructions:"
echo "1. Make sure PostgreSQL is running"
echo "2. Create a database named 'triops_airline':"
echo "   sudo -u postgres createdb triops_airline"
echo "3. Update the database credentials in backend/.env if needed"
echo "4. Run the database setup script:"
echo "   cd backend && python setup_database.py"
echo ""

echo "🎉 Setup completed successfully!"
echo ""
echo "To start the application:"
echo "1. Start PostgreSQL service"
echo "2. Run: npm run dev"
echo ""
echo "The application will be available at:"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:8000"
echo "- API Documentation: http://localhost:8000/docs"
echo ""
echo "Default admin credentials:"
echo "- Email: admin@airline.com"
echo "- Password: admin123"
echo ""
echo "Default user credentials:"
echo "- Email: john.doe@email.com"
echo "- Password: password123"
