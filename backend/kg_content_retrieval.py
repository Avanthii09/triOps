#!/usr/bin/env python3
"""
KG Content Retrieval System
This script retrieves content from Neo4j knowledge graph and displays it
"""

import os
import json
from typing import List, Dict, Any
from datetime import datetime
from neo4j import GraphDatabase

# Neo4j credentials
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "avanthika123"

class KGContentRetriever:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver = None
        
    def connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
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
    
    def get_database_stats(self):
        """Get basic statistics about the knowledge graph"""
        try:
            with self.driver.session() as session:
                stats = session.run("""
                    MATCH (d:Document)
                    OPTIONAL MATCH (e:Entity)
                    OPTIONAL MATCH ()-[r:RELATIONSHIP]->()
                    OPTIONAL MATCH ()-[c:CONTAINS]->()
                    RETURN count(DISTINCT d) as documents,
                           count(DISTINCT e) as entities,
                           count(DISTINCT r) as entity_relationships,
                           count(DISTINCT c) as document_relationships
                """).single()
                
                print(f"\n📊 Knowledge Graph Statistics:")
                print(f"   Documents: {stats['documents']}")
                print(f"   Entities: {stats['entities']}")
                print(f"   Entity-to-Entity Relationships: {stats['entity_relationships']}")
                print(f"   Document-to-Entity Relationships: {stats['document_relationships']}")
                
                return dict(stats)
        except Exception as e:
            print(f"❌ Statistics error: {e}")
            return None
    
    def get_relationship_types(self):
        """Get all relationship types in the database"""
        try:
            with self.driver.session() as session:
                results = session.run("""
                    MATCH ()-[r:RELATIONSHIP]->()
                    RETURN DISTINCT r.relation as relation_type, 
                           count(r) as count
                    ORDER BY count DESC
                """)
                
                print(f"\n🔗 Relationship Types:")
                relationship_types = []
                for record in results:
                    rel_type = record['relation_type']
                    count = record['count']
                    print(f"   {rel_type}: {count} relationships")
                    relationship_types.append({'type': rel_type, 'count': count})
                
                return relationship_types
        except Exception as e:
            print(f"❌ Relationship types error: {e}")
            return []
    
    def get_entity_types(self):
        """Get all entity types in the database"""
        try:
            with self.driver.session() as session:
                results = session.run("""
                    MATCH (e:Entity)
                    RETURN DISTINCT e.type as entity_type, 
                           count(e) as count
                    ORDER BY count DESC
                """)
                
                print(f"\n🏷️  Entity Types:")
                entity_types = []
                for record in results:
                    entity_type = record['entity_type']
                    count = record['count']
                    print(f"   {entity_type}: {count} entities")
                    entity_types.append({'type': entity_type, 'count': count})
                
                return entity_types
        except Exception as e:
            print(f"❌ Entity types error: {e}")
            return []
    
    def basic_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Basic semantic search for entities"""
        print(f"\n🔍 Basic Search: '{query}'")
        try:
            with self.driver.session() as session:
                results = session.run("""
                    MATCH (e:Entity)
                    WHERE toLower(e.name) CONTAINS toLower($search_term)
                    RETURN e.name as name, e.type as type, e.confidence as confidence
                    ORDER BY e.confidence DESC
                    LIMIT $limit
                """, search_term=query, limit=limit)
                
                results_list = list(results)
                print(f"Found {len(results_list)} results:")
                for i, result in enumerate(results_list, 1):
                    print(f"  {i}. {result['name']} ({result['type']}) - confidence: {result['confidence']}")
                
                return [dict(record) for record in results_list]
        except Exception as e:
            print(f"❌ Basic search error: {e}")
            return []
    
    def center_search(self, center_node: str, limit: int = 10) -> List[Dict]:
        """Center-based search - find nodes connected to a central entity"""
        print(f"\n🎯 Center Search around: '{center_node}'")
        try:
            with self.driver.session() as session:
                results = session.run("""
                    MATCH (center:Entity)
                    WHERE toLower(center.name) CONTAINS toLower($center)
                    MATCH (center)-[r:RELATIONSHIP]->(target)
                    RETURN target.name as name, target.type as type, r.relation as relation,
                           r.confidence as confidence, r.source_document as source_doc
                    ORDER BY r.confidence DESC
                    LIMIT $limit
                """, center=center_node, limit=limit)
                
                results_list = list(results)
                print(f"Found {len(results_list)} nodes connected to '{center_node}':")
                for i, result in enumerate(results_list, 1):
                    print(f"  {i}. {result['name']} ({result['type']}) - {result['relation']} (conf: {result['confidence']})")
                
                return [dict(record) for record in results_list]
        except Exception as e:
            print(f"❌ Center search error: {e}")
            return []
    
    def reverse_center_search(self, center_node: str, limit: int = 10) -> List[Dict]:
        """Reverse center search - find nodes that connect TO the center entity"""
        print(f"\n🔄 Reverse Center Search to: '{center_node}'")
        try:
            with self.driver.session() as session:
                results = session.run("""
                    MATCH (center:Entity)
                    WHERE toLower(center.name) CONTAINS toLower($center)
                    MATCH (source)-[r:RELATIONSHIP]->(center)
                    RETURN source.name as name, source.type as type, r.relation as relation,
                           r.confidence as confidence, r.source_document as source_doc
                    ORDER BY r.confidence DESC
                    LIMIT $limit
                """, center=center_node, limit=limit)
                
                results_list = list(results)
                print(f"Found {len(results_list)} nodes connecting to '{center_node}':")
                for i, result in enumerate(results_list, 1):
                    print(f"  {i}. {result['name']} ({result['type']}) - {result['relation']} (conf: {result['confidence']})")
                
                return [dict(record) for record in results_list]
        except Exception as e:
            print(f"❌ Reverse center search error: {e}")
            return []
    
    def bidirectional_search(self, entity: str, limit: int = 15) -> List[Dict]:
        """Bidirectional search - find all connections to and from an entity"""
        print(f"\n↔️  Bidirectional Search for: '{entity}'")
        try:
            with self.driver.session() as session:
                results = session.run("""
                    MATCH (e:Entity {name: $entity})
                    OPTIONAL MATCH (e)-[r1:RELATIONSHIP]->(target)
                    OPTIONAL MATCH (source)-[r2:RELATIONSHIP]->(e)
                    WITH e, 
                         collect(DISTINCT {name: target.name, type: target.type, 
                                         relation: r1.relation, confidence: r1.confidence,
                                         source_doc: r1.source_document, direction: 'outgoing'}) as outgoing,
                         collect(DISTINCT {name: source.name, type: source.type,
                                         relation: r2.relation, confidence: r2.confidence,
                                         source_doc: r2.source_document, direction: 'incoming'}) as incoming
                    UNWIND (outgoing + incoming) as connections
                    RETURN connections
                    ORDER BY connections.confidence DESC
                    LIMIT $limit
                """, entity=entity, limit=limit)
                
                results_list = list(results)
                print(f"Found {len(results_list)} connections for '{entity}':")
                for i, result in enumerate(results_list, 1):
                    conn = result['connections']
                    direction = "→" if conn['direction'] == 'outgoing' else "←"
                    print(f"  {i}. {conn['name']} ({conn['type']}) {direction} {conn['relation']} (conf: {conn['confidence']})")
                
                return [dict(record) for record in results_list]
        except Exception as e:
            print(f"❌ Bidirectional search error: {e}")
            return []
    
    def multi_hop_search(self, start_entity: str, hops: int = 2, limit_per_hop: int = 5) -> List[Dict]:
        """Multi-hop search - traverse relationships across multiple hops"""
        print(f"\n🔗 Multi-Hop Search from: '{start_entity}' (max {hops} hops)")
        try:
            with self.driver.session() as session:
                # Build dynamic Cypher query for multi-hop traversal
                cypher_query = f"""
                    MATCH (start:Entity)
                    WHERE toLower(start.name) CONTAINS toLower($start)
                    MATCH path = (start)-[r*1..{hops}]->(end:Entity)
                    WHERE start.name <> end.name
                    WITH path, 
                         [rel IN relationships(path) | rel.relation] as relations,
                         [node IN nodes(path) | node.name] as entity_names,
                         reduce(conf = 1.0, rel IN relationships(path) | conf * rel.confidence) as path_confidence
                    RETURN entity_names, relations, path_confidence,
                           length(path) as hop_count,
                           [rel IN relationships(path) | rel.source_document] as source_docs
                    ORDER BY path_confidence DESC
                    LIMIT $limit
                """
                
                results = session.run(cypher_query, start=start_entity, limit=limit_per_hop * hops)
                
                paths = []
                for record in results:
                    paths.append({
                        'entity_names': record['entity_names'],
                        'relations': record['relations'],
                        'path_confidence': record['path_confidence'],
                        'hop_count': record['hop_count'],
                        'source_docs': record['source_docs']
                    })
                
                print(f"Found {len(paths)} multi-hop paths:")
                for i, path in enumerate(paths, 1):
                    print(f"  {i}. Path: {' → '.join(path['entity_names'])}")
                    print(f"     Relations: {' → '.join(path['relations'])}")
                    print(f"     Confidence: {path['path_confidence']:.3f} ({path['hop_count']} hops)")
                    print(f"     Sources: {', '.join(set(path['source_docs']))}")
                    print()
                
                return paths
        except Exception as e:
            print(f"❌ Multi-hop search error: {e}")
            return []
    
    def relationship_type_search(self, relation_type: str, limit: int = 10) -> List[Dict]:
        """Search for all relationships of a specific type"""
        print(f"\n🔍 Relationship Type Search: '{relation_type}'")
        try:
            with self.driver.session() as session:
                results = session.run("""
                    MATCH (source)-[r:RELATIONSHIP {relation: $relation}]->(target)
                    RETURN source.name as source_name, source.type as source_type,
                           target.name as target_name, target.type as target_type,
                           r.confidence as confidence, r.source_document as source_doc
                    ORDER BY r.confidence DESC
                    LIMIT $limit
                """, relation=relation_type, limit=limit)
                
                results_list = list(results)
                print(f"Found {len(results_list)} '{relation_type}' relationships:")
                for i, result in enumerate(results_list, 1):
                    print(f"  {i}. {result['source_name']} --[{relation_type}]--> {result['target_name']}")
                    print(f"     Confidence: {result['confidence']}, Source: {result['source_doc']}")
                
                return [dict(record) for record in results_list]
        except Exception as e:
            print(f"❌ Relationship type search error: {e}")
            return []
    
    def get_entity_context(self, entity_name: str) -> Dict[str, Any]:
        """Get comprehensive context about an entity"""
        print(f"\n📋 Entity Context for: '{entity_name}'")
        try:
            with self.driver.session() as session:
                # Get entity details
                entity_result = session.run("""
                    MATCH (e:Entity)
                    WHERE toLower(e.name) CONTAINS toLower($name)
                    RETURN e.name as name, e.type as type, e.confidence as confidence
                    LIMIT 1
                """, name=entity_name).single()
                
                if not entity_result:
                    print(f"❌ Entity '{entity_name}' not found")
                    return None
                
                entity_info = dict(entity_result)
                print(f"Entity: {entity_info['name']} (Type: {entity_info['type']}, Confidence: {entity_info['confidence']})")
                
                # Get outgoing relationships
                outgoing = session.run("""
                    MATCH (e:Entity {name: $name})-[r:RELATIONSHIP]->(target)
                    RETURN target.name as target_name, target.type as target_type,
                           r.relation as relation, r.confidence as confidence,
                           r.source_document as source_doc
                    ORDER BY r.confidence DESC
                """, name=entity_name)
                
                outgoing_list = list(outgoing)
                print(f"\nOutgoing relationships ({len(outgoing_list)}):")
                for i, rel in enumerate(outgoing_list, 1):
                    print(f"  {i}. {rel['target_name']} ({rel['target_type']}) - {rel['relation']} (conf: {rel['confidence']})")
                
                # Get incoming relationships
                incoming = session.run("""
                    MATCH (source)-[r:RELATIONSHIP]->(e:Entity {name: $name})
                    RETURN source.name as source_name, source.type as source_type,
                           r.relation as relation, r.confidence as confidence,
                           r.source_document as source_doc
                    ORDER BY r.confidence DESC
                """, name=entity_name)
                
                incoming_list = list(incoming)
                print(f"\nIncoming relationships ({len(incoming_list)}):")
                for i, rel in enumerate(incoming_list, 1):
                    print(f"  {i}. {rel['source_name']} ({rel['source_type']}) - {rel['relation']} (conf: {rel['confidence']})")
                
                # Get documents that mention this entity
                documents = session.run("""
                    MATCH (d:Document)-[:CONTAINS]->(e:Entity {name: $name})
                    RETURN d.name as doc_name, d.processed_at as processed_at
                """, name=entity_name)
                
                docs_list = list(documents)
                print(f"\nMentioned in documents ({len(docs_list)}):")
                for i, doc in enumerate(docs_list, 1):
                    print(f"  {i}. {doc['doc_name']}")
                
                entity_info['outgoing_relationships'] = [dict(record) for record in outgoing_list]
                entity_info['incoming_relationships'] = [dict(record) for record in incoming_list]
                entity_info['mentioned_in_documents'] = [dict(record) for record in docs_list]
                
                return entity_info
        except Exception as e:
            print(f"❌ Entity context error: {e}")
            return None
    
    def retrieve_content_for_query(self, query: str) -> Dict[str, Any]:
        """Retrieve all relevant content for a query"""
        print(f"\n{'='*70}")
        print(f"🔍 Retrieving Content for Query: '{query}'")
        print(f"{'='*70}")
        
        query_lower = query.lower()
        retrieved_content = {
            'query': query,
            'basic_search': [],
            'center_searches': [],
            'multi_hop_searches': [],
            'relationship_searches': [],
            'entity_contexts': []
        }
        
        # Extract key entities from query - adapted for airline data
        key_entities = []
        entity_keywords = ["emirates", "indigo", "airlines", "airline", "dubai", "rahul", "sheikh", "ahmed", "boeing", "airbus", "aircraft", "ceo", "founder", "government"]
        
        for keyword in entity_keywords:
            if keyword in query_lower:
                key_entities.append(keyword.title())
        
        # Basic search
        if key_entities:
            for entity in key_entities[:3]:  # Limit to first 3 entities
                basic_results = self.basic_search(entity, limit=5)
                retrieved_content['basic_search'].extend(basic_results)
        
        # Center searches
        if key_entities:
            for entity in key_entities[:2]:  # Limit to first 2 entities
                center_results = self.center_search(entity, limit=5)
                retrieved_content['center_searches'].extend(center_results)
                
                reverse_results = self.reverse_center_search(entity, limit=5)
                retrieved_content['center_searches'].extend(reverse_results)
        
        # Multi-hop searches
        if key_entities:
            for entity in key_entities[:2]:  # Limit to first 2 entities
                multi_hop_results = self.multi_hop_search(entity, hops=2, limit_per_hop=3)
                retrieved_content['multi_hop_searches'].extend(multi_hop_results)
        
        # Relationship type searches
        if "ceo" in query_lower or "leader" in query_lower:
            ceo_results = self.relationship_type_search("led", limit=5)
            retrieved_content['relationship_searches'].extend(ceo_results)
        
        if "found" in query_lower or "founded" in query_lower:
            founded_results = self.relationship_type_search("founded", limit=5)
            retrieved_content['relationship_searches'].extend(founded_results)
        
        if "operate" in query_lower or "aircraft" in query_lower:
            operated_results = self.relationship_type_search("operated", limit=5)
            retrieved_content['relationship_searches'].extend(operated_results)
        
        # Entity contexts
        if key_entities:
            for entity in key_entities[:2]:  # Limit to first 2 entities
                entity_context = self.get_entity_context(entity)
                if entity_context:
                    retrieved_content['entity_contexts'].append(entity_context)
        
        # Summary
        total_items = (len(retrieved_content['basic_search']) + 
                      len(retrieved_content['center_searches']) + 
                      len(retrieved_content['multi_hop_searches']) + 
                      len(retrieved_content['relationship_searches']) + 
                      len(retrieved_content['entity_contexts']))
        
        print(f"\n📊 Content Retrieval Summary:")
        print(f"   Basic search results: {len(retrieved_content['basic_search'])}")
        print(f"   Center search results: {len(retrieved_content['center_searches'])}")
        print(f"   Multi-hop search results: {len(retrieved_content['multi_hop_searches'])}")
        print(f"   Relationship search results: {len(retrieved_content['relationship_searches'])}")
        print(f"   Entity contexts: {len(retrieved_content['entity_contexts'])}")
        print(f"   Total items retrieved: {total_items}")
        
        return retrieved_content


def main():
    """Main function to demonstrate KG content retrieval"""
    print("="*70)
    print("🧠 KG Content Retrieval System")
    print("="*70)
    
    # Initialize the retriever
    retriever = KGContentRetriever(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    if not retriever.connect():
        print("❌ Cannot connect to Neo4j. Please ensure Neo4j is running.")
        return
    
    print("✅ Connected to Neo4j successfully!")
    
    # Get database overview
    retriever.get_database_stats()
    retriever.get_relationship_types()
    retriever.get_entity_types()
    
    # Test queries adapted for airline data
    test_queries = [
        "Who is the CEO of Emirates Airlines?",
        "What aircraft does Indigo Airlines operate?",
        "Who founded Emirates Airlines?",
        "What is the relationship between Dubai government and Emirates?",
        "Find connections between Rahul Bhatia and Indigo Airlines"
    ]
    
    print(f"\n{'='*70}")
    print("🧪 Testing Content Retrieval")
    print(f"{'='*70}")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*50}")
        print(f"Test {i}/{len(test_queries)}")
        print(f"{'='*50}")
        
        try:
            content = retriever.retrieve_content_for_query(query)
            
            # Save content to file for review
            filename = f"retrieved_content_{i}_{query.replace('?', '').replace(' ', '_')[:20]}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Content saved to: {filename}")
            
        except Exception as e:
            print(f"\n❌ Error processing query: {e}")
    
    # Close connections
    retriever.close()
    print("\n✅ Content retrieval complete!")


if __name__ == "__main__":
    main()
