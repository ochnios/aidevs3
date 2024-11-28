import os
import requests
from neo4j import GraphDatabase

print('S03E05\n')

def mask_sensitive_data(data: dict) -> dict:
    """Create a copy of dict with masked sensitive data"""
    if isinstance(data, dict):
        masked = data.copy()
        if 'apikey' in masked:
            masked['apikey'] = '***'
        return masked
    return data

def query_database(query: str) -> dict:
    """Execute query against the database API"""
    payload = {
        "task": "database",
        "apikey": os.getenv('AIDEVS_API_KEY'),
        "query": query
    }
    print(f"\nSending query: {mask_sensitive_data(payload)}")
    
    response = requests.post(
        f"{os.getenv('AIDEVS_CENTRALA')}/apidb",
        json=payload
    )
    if not response.ok:
        raise Exception(f"Database query failed: {response.text}")
    
    result = response.json()
    print(f"Query response: {mask_sensitive_data(result)}")
    return result

def fetch_data():
    """Fetch users and connections from MySQL"""
    print("\nFetching users...")
    users = query_database("SELECT id, username FROM users")
    
    print("\nFetching connections...")
    connections = query_database("SELECT user1_id, user2_id FROM connections")
    
    return users['reply'], connections['reply']

def setup_neo4j_database(users, connections):
    """Setup Neo4j database with users and their connections"""
    # Update connection details
    neo4j_uri = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', 'neo4j') # change in http://127.0.0.1:7474/browser/
    
    print(f"\nConnecting to Neo4j at {neo4j_uri}...")
    driver = GraphDatabase.driver(
        neo4j_uri, 
        auth=(neo4j_user, neo4j_password)
    )
    
    # Verify connection
    try:
        driver.verify_connectivity()
        print("Successfully connected to Neo4j")
    except Exception as e:
        raise Exception(f"Failed to connect to Neo4j: {str(e)}")

    def clear_database(tx):
        tx.run("MATCH (n) DETACH DELETE n")
    
    def create_users(tx, users):
        for user in users:
            tx.run("CREATE (u:User {id: $id, name: $name})",
                   id=user['id'], name=user['username'])
    
    def create_connections(tx, connections):
        for conn in connections:
            tx.run("""
                MATCH (u1:User {id: $user1_id})
                MATCH (u2:User {id: $user2_id})
                CREATE (u1)-[:KNOWS]->(u2)
            """, user1_id=conn['user1_id'], user2_id=conn['user2_id'])
    
    print("\nSetting up Neo4j database...")
    with driver.session() as session:
        print("Clearing existing data...")
        session.execute_write(clear_database)
        
        print("Creating user nodes...")
        session.execute_write(create_users, users)
        
        print("Creating relationships...")
        session.execute_write(create_connections, connections)
    
    return driver

def find_shortest_path(driver):
    """Find shortest path from Rafał to Barbara"""
    with driver.session() as session:
        print("\nFinding shortest path...")
        result = session.run("""
            MATCH (start:User {name: 'Rafał'}),
                  (end:User {name: 'Barbara'}),
                  p = shortestPath((start)-[:KNOWS*]->(end))
            RETURN [node in nodes(p) | node.name] as path
        """)
        path = result.single()
        if path is None:
            raise Exception("No path found between Rafał and Barbara")
        return path['path']

def send_report(answer: str) -> dict:
    """Send final answer to the central API"""
    payload = {
        "task": "connections",
        "apikey": os.getenv('AIDEVS_API_KEY'),
        "answer": answer
    }
    print(f"\nSending final answer: {mask_sensitive_data(payload)}")
    
    response = requests.post(
        f"{os.getenv('AIDEVS_CENTRALA')}/report",
        json=payload
    )
    if not response.ok:
        raise Exception(f"Failed to send report: {response.text}")
    
    result = response.json()
    print(f"Final response: {mask_sensitive_data(result)}")
    return result

if __name__ == "__main__":
    try:
        # Step 1: Fetch data from MySQL
        users, connections = fetch_data()
        
        # Step 2: Setup Neo4j database
        driver = setup_neo4j_database(users, connections)
        
        # Step 3: Find shortest path
        path = find_shortest_path(driver)
        
        # Step 4: Format and send the answer
        answer = ", ".join(path)
        print(f"\nFound path: {answer}")
        
        result = send_report(answer)
        
        # Cleanup
        driver.close()
        
    except Exception as e:
        print(f"Error: {e}") 