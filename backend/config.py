# Configuration file for the RAG system
import os
from dotenv import load_dotenv

load_dotenv()

# Pinecone Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "pcsk_4twLmW_Ac9bdp6nF34ME5C1d2Jg4sfTmDTixEev9YQc8D8U17ZU9hSabfKsQqkmZYjWFo")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "airline-policies")
TOP_K = int(os.getenv("TOP_K", "3"))
MAX_DOCS_FOR_CONTEXT = int(os.getenv("MAX_DOCS_FOR_CONTEXT", "10"))
TARGET_DIM = int(os.getenv("TARGET_DIM", "768"))

# Google API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyDe1C_D8eLAC8d3ESLqUpZ5OGcAlxR2igs")

# File paths
DOCUMENTS_FOLDER = os.getenv("DOCUMENTS_FOLDER", "./documents")