#!/usr/bin/env python3
"""
Fixed LightRAG Implementation with Corrected Entity-Relationship Logic
This fixes the entity-to-entity relationship implementation issues
"""

import os
import json
import asyncio
import pdfplumber
import requests
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Neo4j imports
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

# Neo4j credentials
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "avanthika123"

# ----------------------------
# LOCAL OLLAMA CLIENT
# ----------------------------
class LocalOllamaClient:
    def __init__(self, model_name="llama3.2", use_dummy_responses=False, base_url="http://localhost:11434"):
        self.model_name = model_name
        self.use_dummy_responses = use_dummy_responses
        self.base_url = base_url

    async def _generate_response(self, prompt):
        if self.use_dummy_responses:
            return {"extracted_entities": [], "edges": []}

        loop = asyncio.get_event_loop()

        def query():
            prompt_text = prompt if isinstance(prompt, str) else " ".join(prompt)
            json_instruction = (
                "\nRespond ONLY in valid JSON with keys 'extracted_entities' and 'edges'."
            )
            try:
                url = f"{self.base_url}/api/generate"
                payload = {
                    "model": self.model_name,
                    "prompt": prompt_text + json_instruction,
                    "stream": False
                }
                
                response = requests.post(url, json=payload, timeout=120)
                response.raise_for_status()
                
                result = response.json()
                content = result.get("response", "")
                return content
                
            except requests.exceptions.ConnectionError:
                print(f"❌ Cannot connect to Ollama at {self.base_url}")
                print("   Make sure Ollama is running: ollama serve")
                return '{"extracted_entities": [], "edges": []}'
            except requests.exceptions.Timeout:
                print(f"⏱️  Request timed out")
                return '{"extracted_entities": [], "edges": []}'
            except Exception as e:
                print(f"Ollama error: {e}")
                return '{"extracted_entities": [], "edges": []}'

        result_str = await loop.run_in_executor(None, query)

        try:
            if "```json" in result_str:
                result_str = result_str.split("```json")[1].split("```")[0].strip()
            elif "```" in result_str:
                result_str = result_str.split("```")[1].split("```")[0].strip()
            
            return json.loads(result_str)
        except json.JSONDecodeError:
            print(f"⚠️  Failed to parse JSON response")
            print(f"   First 300 chars: {result_str[:300]}")
            return {"extracted_entities": [], "edges": []}

    async def generate_response(self, prompt):
        return await self._generate_response(prompt)


def test_ollama_connection(base_url="http://localhost:11434"):
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama is running")
            print(f"   Available models: {[m['name'] for m in models]}")
            return True
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Ollama at {base_url}")
        print(f"   Please start Ollama with: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error testing Ollama: {e}")
        return False


def read_document(file_path):
    """Read document based on file extension"""
    if file_path.lower().endswith('.pdf'):
        return read_pdf(file_path)
    elif file_path.lower().endswith('.md'):
        return read_markdown(file_path)
    else:
        print(f"Unsupported file type: {file_path}")
        return ""


def read_pdf(file_path):
    """Read text from PDF file"""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""
    return text.strip()


def read_markdown(file_path):
    """Read text from Markdown file"""
    text = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"Error reading Markdown {file_path}: {e}")
        return ""
    return text.strip()


# ----------------------------
# FIXED LIGHTRAG-INSPIRED KNOWLEDGE GRAPH
# ----------------------------
class FixedLightRAGGraph:
    def __init__(self, uri, user, password):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
    
    def connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            print("✅ Connected to Neo4j")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            return False
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            print("🔌 Neo4j connection closed")
    
    def clean_database(self):
        """Clean existing Neo4j database"""
        print("\n" + "="*60)
        print("🧹 CLEANING EXISTING NEO4J DATABASE")
        print("="*60)
        
        if not self.connect():
            return False
        
        try:
            with self.driver.session() as session:
                # Clear all existing data
                result = session.run("MATCH (n) DETACH DELETE n")
                print("✅ Cleared all existing nodes and relationships")
                
                # Drop all constraints and indexes
                try:
                    session.run("DROP CONSTRAINT entity_name IF EXISTS")
                    session.run("DROP INDEX entity_type IF EXISTS")
                    session.run("DROP INDEX document_name IF EXISTS")
                    print("✅ Dropped existing constraints and indexes")
                except Exception as e:
                    print(f"ℹ️  No existing constraints/indexes to drop: {e}")
                
                print("✅ Database cleaning completed successfully!")
                return True
                
        except Exception as e:
            print(f"❌ Error cleaning database: {e}")
            return False
    
    def create_knowledge_graph(self, extracted_data):
        """Create LightRAG-inspired knowledge graph with FIXED entity-relationship logic"""
        print("\n" + "="*60)
        print("Creating FIXED LightRAG-inspired Knowledge Graph")
        print("="*60)
        
        if not self.connect():
            return False
        
        try:
            with self.driver.session() as session:
                # Create constraints and indexes
                try:
                    session.run("CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE")
                    session.run("CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)")
                    session.run("CREATE INDEX document_name IF NOT EXISTS FOR (d:Document) ON (d.name)")
                    print("📊 Created constraints and indexes")
                except Exception as e:
                    print(f"ℹ️  Constraints/indexes may already exist: {e}")
                
                # FIRST PASS: Create all entities from all documents
                print("\n🔄 FIRST PASS: Creating all entities...")
                all_entities = set()  # Use set to avoid duplicates
                
                for doc_name, data in extracted_data.items():
                    entities = data["entities"]
                    for entity in entities:
                        all_entities.add((entity["name"], entity["type"]))
                
                # Create all unique entities
                for entity_name, entity_type in all_entities:
                    session.run("""
                        MERGE (e:Entity {name: $name})
                        SET e.type = $type
                        SET e.created_at = datetime()
                        SET e.confidence = 0.8
                        SET e.source_documents = []
                    """, name=entity_name, type=entity_type)
                
                print(f"✅ Created {len(all_entities)} unique entities")
                
                # SECOND PASS: Create documents and connect to entities
                print("\n🔄 SECOND PASS: Creating documents and connections...")
                for doc_name, data in extracted_data.items():
                    entities = data["entities"]
                    relationships = data["relationships"]
                    
                    print(f"\n📄 Processing: {doc_name}")
                    print(f"   Entities: {len(entities)}")
                    print(f"   Relationships: {len(relationships)}")
                    
                    # Create document node
                    session.run("""
                        MERGE (d:Document {name: $name})
                        SET d.processed_at = datetime()
                        SET d.entity_count = $entity_count
                        SET d.relationship_count = $relationship_count
                    """, name=doc_name, entity_count=len(entities), relationship_count=len(relationships))
                    
                    # Connect entities to document
                    for entity in entities:
                        session.run("""
                            MATCH (d:Document {name: $doc})
                            MATCH (e:Entity {name: $entity_name})
                            MERGE (d)-[:CONTAINS]->(e)
                            
                            // Add document to entity's source_documents list
                            SET e.source_documents = CASE 
                                WHEN $doc IN e.source_documents THEN e.source_documents
                                ELSE e.source_documents + [$doc]
                            END
                        """, doc=doc_name, entity_name=entity["name"])
                
                # THIRD PASS: Create relationships (FIXED LOGIC)
                print("\n🔄 THIRD PASS: Creating relationships...")
                relationship_count = 0
                skipped_count = 0
                
                for doc_name, data in extracted_data.items():
                    relationships = data["relationships"]
                    
                    for rel in relationships:
                        try:
                            # FIXED: Use MERGE to create relationship without checking existence first
                            result = session.run("""
                                MATCH (source:Entity {name: $source_name})
                                MATCH (target:Entity {name: $target_name})
                                MERGE (source)-[r:RELATIONSHIP {relation: $relation}]->(target)
                                SET r.source_document = $doc
                                SET r.created_at = datetime()
                                SET r.confidence = 0.7
                                SET r.id = randomUUID()
                                RETURN r.id as relationship_id
                            """, source_name=rel["source"], target_name=rel["target"], 
                                   relation=rel["relation"], doc=doc_name)
                            
                            relationship_id = result.single()
                            if relationship_id:
                                relationship_count += 1
                                print(f"     ✅ Created: {rel['source']} --[{rel['relation']}]--> {rel['target']}")
                            else:
                                skipped_count += 1
                                print(f"     ⚠️  Skipped: {rel['source']} --[{rel['relation']}]--> {rel['target']} (entities not found)")
                                
                        except Exception as e:
                            skipped_count += 1
                            print(f"     ❌ Error creating relationship: {e}")
                
                print(f"\n📊 Relationship Creation Summary:")
                print(f"   ✅ Created: {relationship_count}")
                print(f"   ⚠️  Skipped: {skipped_count}")
                
                print("\n✅ FIXED LightRAG-inspired knowledge graph created successfully!")
                return True
                
        except Exception as e:
            print(f"❌ Error creating knowledge graph: {e}")
            return False
    
    def verify_relationships(self):
        """Verify that relationships were created correctly"""
        print("\n🔍 Verifying relationships...")
        try:
            with self.driver.session() as session:
                # Count total relationships
                total_rels = session.run("MATCH ()-[r:RELATIONSHIP]->() RETURN count(r) as total").single()["total"]
                print(f"   Total relationships: {total_rels}")
                
                # Count relationships by type
                rel_types = session.run("""
                    MATCH ()-[r:RELATIONSHIP]->() 
                    RETURN r.relation as relation, count(r) as count 
                    ORDER BY count DESC
                """).data()
                
                print(f"   Relationship types:")
                for rel_type in rel_types:
                    print(f"     - {rel_type['relation']}: {rel_type['count']}")
                
                # Show sample relationships
                sample_rels = session.run("""
                    MATCH (source:Entity)-[r:RELATIONSHIP]->(target:Entity)
                    RETURN source.name as source, r.relation as relation, target.name as target
                    LIMIT 10
                """).data()
                
                print(f"   Sample relationships:")
                for rel in sample_rels:
                    print(f"     - {rel['source']} --[{rel['relation']}]--> {rel['target']}")
                
                return True
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False
    
    def get_statistics(self):
        """Get knowledge graph statistics"""
        try:
            with self.driver.session() as session:
                stats = session.run("""
                    MATCH (d:Document)
                    OPTIONAL MATCH (e:Entity)
                    OPTIONAL MATCH ()-[r:RELATIONSHIP]->()
                    RETURN count(DISTINCT d) as documents,
                           count(DISTINCT e) as entities,
                           count(DISTINCT r) as relationships,
                           count(DISTINCT e.type) as entity_types
                """).single()
                
                print(f"\n📊 Knowledge Graph Statistics:")
                print(f"   Documents: {stats['documents']}")
                print(f"   Entities: {stats['entities']}")
                print(f"   Relationships: {stats['relationships']}")
                print(f"   Entity Types: {stats['entity_types']}")
                
                return stats
        except Exception as e:
            print(f"❌ Statistics error: {e}")
            return None


# ----------------------------
# NORMALIZATION FUNCTIONS
# ----------------------------
def normalize_entity(entity):
    if isinstance(entity, str):
        return {"name": entity.strip(), "type": "Concept"}
    if isinstance(entity, dict):
        name = entity.get("name") or entity.get("text") or "Unknown"
        etype = entity.get("type") or "Concept"
        return {"name": str(name).strip(), "type": str(etype)}
    return {"name": "Unknown", "type": "Concept"}


def normalize_edge(edge, entity_map):
    sources = edge.get("source") or edge.get("start_node")
    targets = edge.get("target") or edge.get("end_node")
    relation = edge.get("relation") or "related_to"

    if not isinstance(sources, list):
        sources = [sources]
    if not isinstance(targets, list):
        targets = [targets]

    normalized_edges = []
    for s in sources:
        for t in targets:
            s_name = entity_map.get(str(s), str(s))
            t_name = entity_map.get(str(t), str(t))
            normalized_edges.append({
                "source": s_name,
                "target": t_name,
                "relation": relation
            })
    return normalized_edges


def create_extraction_prompt(content):
    truncated_content = content[:2000] if len(content) > 2000 else content
    
    prompt = f"""Extract key entities and their relationships from this text.

TEXT:
{truncated_content}

TASK:
1. Identify important entities (people, concepts, technologies, organizations, methods)
2. Identify relationships between entities

OUTPUT FORMAT (respond with ONLY this JSON, no other text):
{{
  "extracted_entities": [
    {{"name": "Deep Learning", "type": "Technology"}},
    {{"name": "Neural Networks", "type": "Concept"}}
  ],
  "edges": [
    {{"source": "Deep Learning", "target": "Neural Networks", "relation": "uses"}}
  ]
}}"""
    
    return prompt


async def extract_entities_and_relationships(content, llm_client):
    """Extract entities and relationships from text content using Ollama Llama3.2 model."""
    prompt = create_extraction_prompt(content)
    result = await llm_client.generate_response(prompt)

    raw_entities = result.get("extracted_entities", [])
    raw_edges = result.get("edges", [])

    # Normalize entities
    entities = [normalize_entity(e) for e in raw_entities]
    entity_map = {e['name']: e['name'] for e in entities}

    # Normalize edges
    edges = []
    for e in raw_edges:
        edges.extend(normalize_edge(e, entity_map))

    return entities, edges


async def main():
    """Main function to process airline documents and create FIXED LightRAG-inspired knowledge graph"""
    print("="*70)
    print("FIXED LightRAG-inspired Implementation with Ollama Llama3.2")
    print("="*70)
    
    # Test Ollama connection first
    if not test_ollama_connection():
        print("❌ Cannot proceed without Ollama. Please start Ollama with: ollama serve")
        return
    
    print("\nInitializing Ollama client...")
    llm_client = LocalOllamaClient(model_name="llama3.2", use_dummy_responses=False)
    
    # Check if big_tech_docs folder exists
    docs_folder = "./big_tech_docs"
    if not os.path.exists(docs_folder):
        print(f"❌ Error: Folder '{docs_folder}' does not exist!")
        return
    
    # Get all files in the folder
    all_files = [f for f in os.listdir(docs_folder) 
                 if f.lower().endswith(('.pdf', '.md', '.txt'))]
    
    if not all_files:
        print(f"❌ No supported files found in '{docs_folder}'")
        return
    
    print(f"📁 Found {len(all_files)} files to process:")
    for file in all_files:
        print(f"   - {file}")
    
    print("\n" + "="*70)
    print("Extracting Entities and Relationships using Ollama Llama3.2")
    print("="*70)
    
    # Extract entities and relationships from all files
    all_extracted_data = {}
    
    for idx, file_name in enumerate(all_files, 1):
        file_path = os.path.join(docs_folder, file_name)
        print(f"\n[{idx}/{len(all_files)}] Processing: {file_name}")
        
        # Read document content
        content = read_document(file_path)
        
        if not content:
            print("  ⚠️  Could not extract text from document")
            continue
        
        print(f"  📄 Extracted {len(content)} characters")
        print(f"  🤖 Sending to Ollama Llama3.2 (this may take a moment)...")
        
        # Extract entities and relationships using Ollama
        entities, relationships = await extract_entities_and_relationships(content, llm_client)
        
        all_extracted_data[file_name] = {
            "entities": entities,
            "relationships": relationships
        }
        
        print(f"  ✅ Extracted {len(entities)} entities and {len(relationships)} relationships")
        
        # Print entities
        if entities:
            print("  📌 Entities:")
            for entity in entities[:5]:  # Show first 5
                print(f"     - {entity['name']} ({entity['type']})")
            if len(entities) > 5:
                print(f"     ... and {len(entities) - 5} more")
        
        # Print relationships
        if relationships:
            print("  🔗 Relationships:")
            for rel in relationships[:5]:  # Show first 5
                print(f"     - {rel['source']} --[{rel['relation']}]--> {rel['target']}")
            if len(relationships) > 5:
                print(f"     ... and {len(relationships) - 5} more")
    
    # Save extracted data
    output_file = "fixed_lightrag_extraction_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_extracted_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Extracted data saved to: {output_file}")
    
    # Create FIXED LightRAG-inspired knowledge graph
    fixed_graph = FixedLightRAGGraph(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    # First clean the database
    if fixed_graph.clean_database():
        # Then create the knowledge graph
        if fixed_graph.create_knowledge_graph(all_extracted_data):
            # Verify relationships
            fixed_graph.verify_relationships()
            
            # Get statistics
            fixed_graph.get_statistics()
            
            # Close Neo4j connection
            fixed_graph.close()
            print("\n✅ Neo4j connection closed")
    
    print("\n" + "="*70)
    print("FIXED LightRAG-inspired Processing Complete!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
