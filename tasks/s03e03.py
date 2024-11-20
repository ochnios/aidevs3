import os
import requests
from openai import OpenAI

print('S03E03\n')

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

def get_table_structure() -> str:
    """Get database schema information"""
    # Get list of tables
    tables_response = query_database("show tables")
    
    # Get structure for each table
    schema_info = []
    for table in tables_response['reply']:
        table_name = table['Tables_in_banan']
        create_table = query_database(f"show create table {table_name}")
        schema_info.append(f"\n=== Table: {table_name} ===\n{create_table}")
    
    # Join all table definitions with double newlines for better readability
    return "\n\n".join(schema_info)

def generate_sql_query(schema: str) -> str:
    """Use OpenAI to generate the correct SQL query"""
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY_FOR_AIDEVS'))
    
    system_prompt = f"""You are a SQL expert. Based on the provided database schema, generate a SQL query that will answer the user's question. 
Provide only the SQL query without any additional text or explanation.

Database schema:
{schema}"""
    
    user_prompt = "które aktywne datacenter (DC_ID) są zarządzane przez pracowników, którzy są na urlopie (is_active=0)"

    print("\n" + "=" * 80)
    print("LLM Request:")
    print(f"System: {system_prompt}")
    print(f"User: {user_prompt}")
    print("=" * 80 + "\n")

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        model="gpt-4",
        temperature=0.0
    )
    
    query = response.choices[0].message.content.strip()
    print(f"\nGenerated SQL query: {query}")
    return query

def send_report(answer: list) -> dict:
    """Send final answer to the central API"""
    payload = {
        "task": "database",
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
        # Step 1: Get database schema
        print("Getting database schema...")
        schema = get_table_structure()
        
        # Step 2: Generate SQL query using OpenAI
        print("\nGenerating SQL query...")
        sql_query = generate_sql_query(schema)
        
        # Step 3: Execute the query to get the answer
        print("\nExecuting final query...")
        query_result = query_database(sql_query)
        
        # Step 4: Extract DC_IDs and send the report
        dc_ids = [row['dc_id'] for row in query_result['reply']]
        result = send_report(dc_ids)
        
    except Exception as e:
        print(f"Error: {e}") 