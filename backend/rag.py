#!/usr/bin/env python3
"""
Complete RAG System Implementation with Pinecone
Implements semantic similarity with overlap chunking, multiple query generation,
cosine similarity retrieval, RRF ranking, and Gemini response generation using Pinecone
"""

import argparse
import os
import json
from pathlib import Path
import numpy as np
import pdfplumber
import logging
import uuid

from langchain_core.documents.base import Document
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.embeddings import Embeddings

from StatisticalChunker import StatisticalChunker
from kg_content_retrieval import KGContentRetriever

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------------- CONFIG ----------------------
from config import PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME, TOP_K, MAX_DOCS_FOR_CONTEXT, TARGET_DIM, GOOGLE_API_KEY

# Neo4j credentials for knowledge graph
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "avanthika123"


# ---------------------- EMBEDDING MODEL ----------------------
embedding_obj = FastEmbedEmbeddings(model_name="BAAI/bge-base-en-v1.5")  # 768-dim


# ---------------------- STATISTICAL CHUNKER ----------------------
class FastEmbedDenseEncoder:
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model

    def __call__(self, docs):
        return [self.embedding_model.embed_query(doc) for doc in docs]


encoder = FastEmbedDenseEncoder(embedding_obj)
chunker = StatisticalChunker(encoder=encoder, min_split_tokens=100, max_split_tokens=300, overlap_tokens=50)


# ---------------------- UTILITIES ----------------------
def read_pdf_files(directory: str):
    """Read PDF files and convert to Document objects"""
    documents = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        logger.error(f"Directory not found: {directory}")
        return documents
    
    for pdf_file in directory_path.glob("*.pdf"):
        try:
            text = ""
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if text.strip():
                documents.append(Document(
                    page_content=text, 
                    metadata={
                        "filename": pdf_file.stem, 
                        "file_type": "pdf",
                        "file_path": str(pdf_file)
                    }
                ))
                logger.info(f"Read PDF: {pdf_file.name}")
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_file}: {e}")
    
    return documents


def read_markdown_files(directory: str):
    """Read Markdown files and convert to Document objects"""
    documents = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        logger.error(f"Directory not found: {directory}")
        return documents
    
    for md_file in directory_path.glob("*.md"):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            if text.strip():
                documents.append(Document(
                    page_content=text, 
                    metadata={
                        "filename": md_file.stem, 
                        "file_type": "markdown",
                        "file_path": str(md_file)
                    }
                ))
                logger.info(f"Read Markdown: {md_file.name}")
        except Exception as e:
            logger.error(f"Error reading Markdown {md_file}: {e}")
    
    return documents


def read_documents(directory: str):
    """Read both PDF and Markdown files from the given directory."""
    pdf_docs = read_pdf_files(directory)
    md_docs = read_markdown_files(directory)
    all_docs = pdf_docs + md_docs
    logger.info(f"Found {len(pdf_docs)} PDF files and {len(md_docs)} Markdown files.")
    return all_docs


def create_pinecone_index():
    """Create Pinecone index with proper configuration"""
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Check if index exists
        if PINECONE_INDEX_NAME in pc.list_indexes().names():
            logger.info(f"Index '{PINECONE_INDEX_NAME}' already exists")
            return pc
        
        # Create new index
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=TARGET_DIM,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        
        logger.info(f"Pinecone index '{PINECONE_INDEX_NAME}' created.")
        return pc
        
    except Exception as e:
        logger.error(f"Error creating Pinecone index: {e}")
        return None


def upload_chunks_to_pinecone(docs):
    """Upload document chunks to Pinecone with embeddings"""
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
        
        vectors_to_upsert = []
        
        for doc in docs:
            try:
                chunks = chunker([doc.page_content])[0]
                for chunk in chunks:
                    text = " ".join(chunk.splits)
                    vector = embedding_obj.embed_query(text)
                    
                    # Create unique ID
                    vector_id = str(uuid.uuid4())
                    
                    vectors_to_upsert.append({
                        "id": vector_id,
                        "values": vector,
                        "metadata": {
                            "text": text,
                            "filename": doc.metadata.get("filename", "unknown"),
                            "file_type": doc.metadata.get("file_type", "unknown"),
                            "file_path": doc.metadata.get("file_path", ""),
                            "chunk_start": chunk.start,
                            "chunk_end": chunk.end
                        }
                    })
            except Exception as e:
                logger.error(f"Error processing document: {e}")
                continue

        if vectors_to_upsert:
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                index.upsert(vectors=batch)
            
            logger.info(f"Upload completed. Total chunks uploaded: {len(vectors_to_upsert)}")
        else:
            logger.warning("No vectors to upload")
            
    except Exception as e:
        logger.error(f"Error uploading to Pinecone: {e}")


# ---------------------- QUERY & RETRIEVAL ----------------------
def reciprocal_rank_fusion(results: list[list], k=60):
    """
    Reciprocal Rank Fusion: combines multiple query results using RRF
    """
    fused_scores = {}
    for docs in results:
        for rank, doc in enumerate(docs):
            # Convert Document to a serializable dict
            doc_dict = {
                "page_content": doc.page_content,
                "metadata": doc.metadata
            }
            doc_str = json.dumps(doc_dict, sort_keys=True)
            fused_scores[doc_str] = fused_scores.get(doc_str, 0) + 1 / (rank + k)
    
    reranked = [
        (json.loads(doc), score)
        for doc, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    ]
    
    # Convert back to Document objects
    result_docs = []
    for doc_dict, score in reranked[:MAX_DOCS_FOR_CONTEXT]:
        result_docs.append(Document(
            page_content=doc_dict["page_content"],
            metadata=doc_dict["metadata"]
        ))
    
    return result_docs


def generate_similar_queries(query_text: str) -> list[str]:
    """Generate semantically similar queries using Gemini"""
    print(f"📝 Generating similar queries for: '{query_text}'")
    
    try:
        # Set up Gemini
        if "GOOGLE_API_KEY" not in os.environ:
            os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
        
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
        
        prompt = f"""Generate 4 semantically similar queries to the following question about airline policies. 
        Make sure each query explores different aspects of the same topic and uses different wording.

        Original query: "{query_text}"

        Please provide exactly 4 different queries that would help retrieve relevant information about the same topic. 
        Format your response as a simple list, one query per line, without numbering or bullet points."""

        print("🤖 Calling Gemini to generate similar queries...")
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        
        # Parse the response
        queries = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Ensure we have the original query and limit to 4
        if query_text not in queries:
            queries.insert(0, query_text)
        
        queries = queries[:4]
        
        print(f"✅ Generated {len(queries)} queries:")
        for i, q in enumerate(queries, 1):
            print(f"   {i}. '{q}'")
        
        return queries
        
    except Exception as e:
        print(f"❌ Error generating queries with Gemini: {e}")
        print("🔄 Falling back to simple variations...")
        
        # Fallback to simple variations
        queries = [
            query_text,
            query_text.replace("?", ""),
            query_text.lower(),
            query_text.replace("What", "How").replace("?", "")
        ]
        
        # Remove duplicates and limit to 4
        unique_queries = []
        for q in queries:
            if q not in unique_queries and len(q) > 5:
                unique_queries.append(q)
        
        queries = unique_queries[:4]
        
        print(f"✅ Generated {len(queries)} fallback queries:")
        for i, q in enumerate(queries, 1):
            print(f"   {i}. '{q}'")
        
        return queries


def rrf_retriever(query: str):
    """Main RAG retrieval function with RRF using Pinecone"""
    logger.info(f"🔍 Processing query: '{query}'")
    
    # Generate similar queries
    queries = generate_similar_queries(query)
    logger.info(f"📝 Generated {len(queries)} queries:")
    for i, q in enumerate(queries, 1):
        logger.info(f"   {i}. '{q}'")
    
    # Connect to Pinecone
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
        
        # Retrieve top 3 chunks for each query using cosine similarity
        all_results = []
        for i, q in enumerate(queries, 1):
            logger.info(f"\n🔍 Query {i}: '{q}'")
            logger.info("-" * 40)
            
            try:
                # Generate embedding for query
                query_vector = embedding_obj.embed_query(q)
                
                # Search Pinecone
                search_response = index.query(
                    vector=query_vector,
                    top_k=TOP_K,
                    include_metadata=True
                )
                
                # Convert to Document objects
                retrieved_docs = []
                for j, match in enumerate(search_response.matches, 1):
                    doc_text = match.metadata.get("text", "")
                    doc_filename = match.metadata.get("filename", "unknown")
                    doc_score = match.score
                    
                    doc = Document(
                        page_content=doc_text,
                        metadata={
                            "filename": doc_filename,
                            "file_type": match.metadata.get("file_type", "unknown"),
                            "file_path": match.metadata.get("file_path", ""),
                            "score": doc_score
                        }
                    )
                    retrieved_docs.append(doc)
                    
                    logger.info(f"   Chunk {j}: {doc_filename} (score: {doc_score:.3f})")
                    logger.info(f"   Content: {doc_text[:100]}...")
                
                all_results.append(retrieved_docs)
                logger.info(f"   ✅ Retrieved {len(retrieved_docs)} chunks")
                
            except Exception as e:
                logger.error(f"   ❌ Error retrieving for query '{q}': {e}")
                continue
        
        # Apply Reciprocal Rank Fusion
        logger.info("\n" + "=" * 60)
        logger.info("🔄 Applying Reciprocal Rank Fusion (RRF)...")
        logger.info("=" * 60)
        
        final_results = reciprocal_rank_fusion(all_results)
        
        logger.info(f"\n📊 RRF Results - Top {len(final_results)} chunks:")
        for idx, document in enumerate(final_results[:TOP_K]):
            logger.info(f"🔹 Chunk {idx + 1}: {document.metadata.get('filename', 'N/A')}")
            logger.info(f"   Score: {document.metadata.get('score', 'N/A')}")
            logger.info(f"   Content: {document.page_content[:150]}...\n")
        
        return final_results
        
    except Exception as e:
        logger.error(f"Error in RRF retrieval: {e}")
        return []


def retrieve_knowledge_graph_content(query: str) -> dict:
    """Retrieve content from Neo4j knowledge graph"""
    print(f"🧠 Retrieving knowledge graph content for: '{query}'")
    
    try:
        kg_retriever = KGContentRetriever(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        
        if not kg_retriever.connect():
            print("❌ Failed to connect to Neo4j knowledge graph")
            return {"error": "Failed to connect to knowledge graph"}
        
        # Retrieve content from knowledge graph
        kg_content = kg_retriever.retrieve_content_for_query(query)
        
        kg_retriever.close()
        
        print(f"✅ Retrieved {len(kg_content.get('basic_search', []))} basic search results")
        print(f"✅ Retrieved {len(kg_content.get('center_searches', []))} center search results")
        print(f"✅ Retrieved {len(kg_content.get('multi_hop_searches', []))} multi-hop search results")
        print(f"✅ Retrieved {len(kg_content.get('relationship_searches', []))} relationship search results")
        print(f"✅ Retrieved {len(kg_content.get('entity_contexts', []))} entity contexts")
        
        return kg_content
        
    except Exception as e:
        print(f"❌ Error retrieving knowledge graph content: {e}")
        return {"error": f"Knowledge graph retrieval failed: {str(e)}"}


def generate_gemini_response(query: str, retrieved_chunks: list, kg_content: dict = None) -> str:
    """Generate response using Gemini with retrieved chunks"""
    try:
        print("🔑 Setting up Google API key...")
        if "GOOGLE_API_KEY" not in os.environ:
            os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
        
        print("🤖 Initializing Gemini model...")
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)
        
        print("📝 Preparing context from retrieved chunks...")
        # Prepare context from retrieved chunks
        pinecone_context = "\n\n".join([
            f"Document: {chunk.metadata.get('filename', 'unknown')}\nContent: {chunk.page_content}" 
            for chunk in retrieved_chunks[:3]
        ])
        
        print(f"📊 Pinecone context length: {len(pinecone_context)} characters")
        
        # Prepare knowledge graph context
        kg_context = ""
        if kg_content and "error" not in kg_content:
            print("📝 Preparing knowledge graph context...")
            
            # Format knowledge graph content
            kg_sections = []
            
            # Basic search results
            if kg_content.get('basic_search'):
                kg_sections.append("ENTITIES FOUND:")
                for item in kg_content['basic_search'][:5]:
                    kg_sections.append(f"- {item['name']} ({item['type']}) - confidence: {item.get('confidence', 'N/A')}")
            
            # Center search results
            if kg_content.get('center_searches'):
                kg_sections.append("\nRELATIONSHIPS:")
                for item in kg_content['center_searches'][:5]:
                    kg_sections.append(f"- {item['name']} ({item['type']}) - {item.get('relation', 'related')} - confidence: {item.get('confidence', 'N/A')}")
            
            # Multi-hop search results
            if kg_content.get('multi_hop_searches'):
                kg_sections.append("\nCONNECTION PATHS:")
                for item in kg_content['multi_hop_searches'][:3]:
                    path = " → ".join(item['entity_names'])
                    kg_sections.append(f"- Path: {path}")
                    kg_sections.append(f"  Relations: {' → '.join(item['relations'])}")
                    kg_sections.append(f"  Confidence: {item['path_confidence']:.3f}")
            
            # Entity contexts
            if kg_content.get('entity_contexts'):
                kg_sections.append("\nENTITY DETAILS:")
                for entity in kg_content['entity_contexts'][:2]:
                    kg_sections.append(f"- {entity['name']} ({entity['type']})")
                    if entity.get('outgoing_relationships'):
                        kg_sections.append("  Outgoing relationships:")
                        for rel in entity['outgoing_relationships'][:3]:
                            kg_sections.append(f"    → {rel['target_name']} ({rel['relation']})")
                    if entity.get('incoming_relationships'):
                        kg_sections.append("  Incoming relationships:")
                        for rel in entity['incoming_relationships'][:3]:
                            kg_sections.append(f"    ← {rel['source_name']} ({rel['relation']})")
            
            kg_context = "\n".join(kg_sections)
            print(f"📊 Knowledge graph context length: {len(kg_context)} characters")
        else:
            print("⚠️ No knowledge graph content available")
        
        print("📝 Context preview:")
        print("-" * 60)
        print("PINECONE CONTEXT:")
        print(pinecone_context[:300] + "..." if len(pinecone_context) > 300 else pinecone_context)
        if kg_context:
            print("\nKNOWLEDGE GRAPH CONTEXT:")
            print(kg_context[:300] + "..." if len(kg_context) > 300 else kg_context)
        print("-" * 60)
        
        # Create comprehensive prompt
        prompt_parts = [
            "You are a helpful airline customer service assistant. Based on the following context from Triops Airline policy documents and knowledge graph data, provide a comprehensive and accurate answer to the user's question.",
            "",
            "CONTEXT FROM POLICY DOCUMENTS:",
            pinecone_context
        ]
        
        if kg_context:
            prompt_parts.extend([
                "",
                "CONTEXT FROM KNOWLEDGE GRAPH:",
                kg_context
            ])
        
        prompt_parts.extend([
            "",
            f"USER QUESTION: {query}",
            "",
            "INSTRUCTIONS:",
            "1. Answer the question based on BOTH the policy documents and knowledge graph information",
            "2. Be specific and include relevant details like fees, timeframes, requirements, relationships, etc.",
            "3. If the context doesn't contain enough information to fully answer the question, clearly state what information is missing",
            "4. Use a helpful and professional tone",
            "5. Structure your response clearly with bullet points or numbered lists when appropriate",
            "6. Include contact information if mentioned in the context",
            "7. Use knowledge graph relationships to provide additional context and connections",
            "",
            "Please provide a detailed and helpful response:"
        ])
        
        prompt = "\n".join(prompt_parts)

        print(f"📝 Prompt length: {len(prompt)} characters")
        print("🚀 Calling Gemini API...")
        
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        
        print(f"✅ Gemini response received: {len(content)} characters")
        return content
        
    except Exception as e:
        print(f"❌ Error generating Gemini response: {e}")
        return f"I apologize, but I encountered an error while generating a response. Here's what I found in our policy documents:\n\n" + "\n\n".join([
            f"From {chunk.metadata.get('filename', 'unknown')}: {chunk.page_content[:200]}..."
            for chunk in retrieved_chunks[:2]
        ])


def complete_rag_pipeline(query: str) -> dict:
    """Complete RAG pipeline: query -> retrieval -> response generation"""
    print("\n" + "🚀" * 20)
    print("🚀 STARTING COMPLETE RAG PIPELINE")
    print("🚀" * 20)
    print(f"📝 Query: '{query}'")
    print("=" * 80)
    
    # Step 1: Retrieve relevant chunks using RRF
    print("\n🔍 STEP 1: RETRIEVING CHUNKS WITH RRF")
    print("=" * 80)
    retrieved_chunks = rrf_retriever(query)
    
    if not retrieved_chunks:
        print("\n❌ No chunks retrieved!")
        return {
            "query": query,
            "retrieved_chunks": [],
            "response": "No relevant information found.",
            "status": "no_results"
        }
    
    # Print detailed chunk information before Gemini
    print("\n" + "📄" * 20)
    print("📄 DETAILED CHUNK INFORMATION FOR GEMINI")
    print("📄" * 20)
    print(f"📊 Total chunks retrieved: {len(retrieved_chunks)}")
    print(f"📊 Top chunks to send to Gemini: {min(3, len(retrieved_chunks))}")
    print("\n" + "-" * 80)
    
    for i, chunk in enumerate(retrieved_chunks[:3], 1):
        print(f"\n🔹 CHUNK {i}:")
        print(f"   📁 Filename: {chunk.metadata.get('filename', 'unknown')}")
        print(f"   📊 Score: {chunk.metadata.get('score', 'N/A')}")
        print(f"   📏 Length: {len(chunk.page_content)} characters")
        print(f"   📝 Content Preview: {chunk.page_content[:200]}...")
        print(f"   📝 Full Content:")
        print("   " + "-" * 60)
        print(f"   {chunk.page_content}")
        print("   " + "-" * 60)
    
    print("\n" + "🧠" * 20)
    print("🧠 STEP 2: RETRIEVING KNOWLEDGE GRAPH CONTENT")
    print("🧠" * 20)
    
    # Step 2: Retrieve knowledge graph content
    kg_content = retrieve_knowledge_graph_content(query)
    
    print("\n" + "🤖" * 20)
    print("🤖 STEP 3: GENERATING RESPONSE WITH GEMINI")
    print("🤖" * 20)
    
    # Step 3: Generate response using Gemini with both Pinecone and KG content
    response = generate_gemini_response(query, retrieved_chunks, kg_content)
    
    print("\n" + "✅" * 20)
    print("✅ GEMINI RESPONSE GENERATION COMPLETED")
    print("✅" * 20)
    
    # Prepare result
    result = {
        "query": query,
        "retrieved_chunks": [
            {
                "content": chunk.page_content,
                "metadata": chunk.metadata,
                "preview": chunk.page_content[:200] + "..." if len(chunk.page_content) > 200 else chunk.page_content
            }
            for chunk in retrieved_chunks[:3]
        ],
        "knowledge_graph_content": kg_content if kg_content and "error" not in kg_content else None,
        "response": response,
        "status": "success"
    }
    
    print("🎯 RAG Pipeline completed successfully!")
    return result


# ---------------------- MAIN ----------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Complete RAG System with Pinecone")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("create", help="Create the Pinecone index")

    upload_parser = subparsers.add_parser("upload", help="Upload PDFs and Markdown files to Pinecone")
    upload_parser.add_argument("--dir", required=True, help="Directory containing PDF and/or Markdown files")

    query_parser = subparsers.add_parser("query", help="Query the vector DB")
    query_parser.add_argument("--text", required=True, help="User query text")

    rag_parser = subparsers.add_parser("rag", help="Complete RAG pipeline")
    rag_parser.add_argument("--text", required=True, help="User query text")

    enhanced_rag_parser = subparsers.add_parser("enhanced-rag", help="Enhanced RAG pipeline with knowledge graph")
    enhanced_rag_parser.add_argument("--text", required=True, help="User query text")

    retrieval_parser = subparsers.add_parser("retrieval", help="Test retrieval only (no Gemini)")
    retrieval_parser.add_argument("--text", required=True, help="User query text")

    args = parser.parse_args()

    if args.command == "create":
        create_pinecone_index()
    elif args.command == "upload":
        documents = read_documents(args.dir)
        upload_chunks_to_pinecone(documents)
    elif args.command == "query":
        rrf_retriever(args.text)
    elif args.command == "rag":
        result = complete_rag_pipeline(args.text)
        print("\n" + "="*60)
        print("🎯 FINAL RESPONSE:")
        print("="*60)
        print(result["response"])
        print("\n" + "="*60)
        print("📄 RETRIEVED CHUNKS:")
        print("="*60)
        for i, chunk in enumerate(result["retrieved_chunks"], 1):
            print(f"\nChunk {i}: {chunk['metadata'].get('filename', 'unknown')}")
            print(f"Content: {chunk['preview']}")
    elif args.command == "enhanced-rag":
        result = complete_rag_pipeline(args.text)
        print("\n" + "="*60)
        print("🎯 FINAL RESPONSE:")
        print("="*60)
        print(result["response"])
        print("\n" + "="*60)
        print("📄 RETRIEVED CHUNKS:")
        print("="*60)
        for i, chunk in enumerate(result["retrieved_chunks"], 1):
            print(f"\nChunk {i}: {chunk['metadata'].get('filename', 'unknown')}")
            print(f"Content: {chunk['preview']}")
        if result.get("knowledge_graph_content"):
            print("\n" + "="*60)
            print("🧠 KNOWLEDGE GRAPH CONTENT:")
            print("="*60)
            kg_content = result["knowledge_graph_content"]
            if kg_content.get('basic_search'):
                print(f"Basic Search Results: {len(kg_content['basic_search'])}")
            if kg_content.get('center_searches'):
                print(f"Center Search Results: {len(kg_content['center_searches'])}")
            if kg_content.get('multi_hop_searches'):
                print(f"Multi-hop Search Results: {len(kg_content['multi_hop_searches'])}")
            if kg_content.get('entity_contexts'):
                print(f"Entity Contexts: {len(kg_content['entity_contexts'])}")
    elif args.command == "retrieval":
        print(f"\n🔍 Testing retrieval for: '{args.text}'")
        print("="*60)
        results = rrf_retriever(args.text)
        print(f"\n✅ Retrieved {len(results)} chunks total")
    else:
        parser.print_help()