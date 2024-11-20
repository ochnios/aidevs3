import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from uuid import uuid4

import requests
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

print('S03E02\n')

def create_embeddings(text: str) -> list[float]:
    """Create embeddings using OpenAI API"""
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY_FOR_AIDEVS'))
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-large"
    )
    return response.data[0].embedding

def index_reports(directory: str, collection_name: str) -> None:
    """Index all reports from directory into Qdrant"""
    client = QdrantClient("localhost", port=6333)
    
    # Check if collection exists
    if client.collection_exists(collection_name):
        print(f"Collection {collection_name} already exists, recreating...")
    
    # Create collection if it doesn't exist
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
    )
    print(f"Collection {collection_name} created")
    
    # Process each file
    points = []
    for file_path in Path(directory).glob("*.txt"):
        # Extract date from filename (YYYY-MM-DD.txt)
        date = file_path.stem
        
        # Read and process the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        print(f"Creating embedding for {file_path.name}...")
        # Create embedding
        embedding = create_embeddings(content)
        print(f"Embedding created for {file_path.name}")
        
        # Create point with metadata
        points.append(PointStruct(
            id=str(uuid4()),  # Use UUID instead of date as ID
            vector=embedding,
            payload={
                "date": date,  # Store date in metadata
                "content": content
            }
        ))
    
    # Upload points in batch
    print(f"\nUploading {len(points)} points to Qdrant...")
    client.upsert(
        collection_name=collection_name,
        points=points
    )
    print(f"Successfully indexed {len(points)} reports")

def search_reports(query: str, collection_name: str) -> str:
    """Search reports using query embedding"""
    client = QdrantClient("localhost", port=6333)
    
    # Check if collection exists
    if not client.collection_exists(collection_name):
        raise Exception(f"Collection {collection_name} does not exist")
    
    print(f"Creating embedding for query: {query}")
    # Create query embedding
    query_embedding = create_embeddings(query)
    print("Query embedding created")
    
    # Search
    print("\nSearching for matching reports...")
    results = client.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=1
    )
    
    if not results:
        raise Exception("No results found")
    
    print(f"Found matching report with score: {results[0].score}")
    
    # Convert date format from YYYY_MM_DD to YYYY-MM-DD
    date = results[0].payload["date"].replace('_', '-')
    return date

def send_report(answer: str) -> Dict[str, Any]:
    """Send answer to the API"""
    response = requests.post(
        f"{os.getenv('AIDEVS_CENTRALA')}/report",
        json={
            "task": "wektory",
            "apikey": os.getenv('AIDEVS_API_KEY'),
            "answer": answer
        }
    )
    if not response.ok:
        raise Exception(f"Failed to send report: {response.text}")
    return response.json()

if __name__ == "__main__":
    try:
        # Constants
        REPORTS_DIR = "data/pliki_z_fabryki/weapons_tests/do-not-share"
        COLLECTION_NAME = "weapons_reports"
        QUERY = "W raporcie, z którego dnia znajduje się wzmianka o kradzieży prototypu broni?"
        
        # Index reports
        index_reports(REPORTS_DIR, COLLECTION_NAME)
        print("\nIndexing completed")
        
        # Search for the answer
        date = search_reports(QUERY, COLLECTION_NAME)
        print(f"\nFound date: {date}")
        
        # Send answer
        result = send_report(date)
        print(f"\nAPI Response: {result}")
        
    except Exception as e:
        print(f"Error: {e}") 