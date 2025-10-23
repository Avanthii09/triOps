
# **Triops Airline Chatbot**
### *AI-Powered Chatbot for Smarter Airline Operations*

---

## **Overview**

Triops is an **AI-driven airline chatbot** that streamlines operations through automation and chatbot-driven customer service.  
It combines a **React frontend**, **FastAPI backend**, and **PostgreSQL database** to deliver a responsive, reliable, and scalable airline management platform.

---

## 🧩 **Core Components**

| Layer | Technology | Description |
|-------|-------------|-------------|
| Frontend | **React.js** | Modern, responsive user interface |
| Backend | **FastAPI (Python)** | High-performance API server |
| Database | **PostgreSQL** | Relational data storage |
| Authentication | **JWT** | Secure token-based login system |
| AI | **Rule-based Chatbot** | Handles queries, policies, and bookings |

---

## ⚙️ **Setup Instructions**

### **1. Prerequisites**
Ensure the following are installed:
- Node.js v16+
- Python 3.9+
- PostgreSQL v12+
- Git (for cloning)

Check installations:
```bash
node -v
npm -v
python --version
psql --version
```

---

### **2. Clone the Repository**
```bash
git clone <repo-url>
cd triops-airline
```

---

### **3. Database Setup**
```bash
psql -U postgres
CREATE DATABASE triops_airline;
CREATE USER triops_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE triops_airline TO triops_user;
\q
```

Verify:
```bash
psql -U postgres -d triops_airline -c "SELECT version();"
```

---

### **4. Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate   # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
```

Create `.env`:
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/triops_airline
JWT_SECRET_KEY=secret
JWT_ALGORITHM=HS256
```

Initialize DB:
```bash
python -c "from database.models import Base, engine; Base.metadata.create_all(bind=engine)"
```

Run server:
```bash
uvicorn main_complete:app --reload --port 8000
```

Backend runs at → **http://localhost:8000**

---

### **5. Frontend Setup**
```bash
cd ../frontend
npm install
npm start
```

Frontend runs at → **http://localhost:3000**

---

### **6. Quick Run Command**
For both together:
```bash
npm run dev
```

---

## 💬 **Features Summary**

- **Chatbot Interface:** Real-time, conversational support  
- **Flight Management:** Bookings, cancellations, seat tracking  
- **Policy Queries:** Instant retrieval of policies (baggage, cancellation, etc.)  
- **Admin Dashboard:** Manage customers, flights, and analytics  
- **Security:** JWT auth, hashed passwords, role-based access  

---

## **System Workflow**

```
User → Chatbot UI → FastAPI → PostgreSQL
```

1. User query processed by chatbot  
2. API routes request to backend logic  
3. Database handles bookings, flights, and responses  
4. Chatbot returns structured reply instantly  

---





## 🔗 **Access Points**
- **Frontend:** http://localhost:3000  
- **Backend API:** http://localhost:8000  
- **Docs:** http://localhost:8000/docs  

---


