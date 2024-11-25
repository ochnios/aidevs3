import os
import json
import requests
from openai import OpenAI

# Paths and constants
CHECKPOINT_FILE = "data/loop/results.json"
NOTE_FILE = "data/loop/barbara_note.txt"
BARBARA_NOTE_URL = f"{os.getenv('AIDEVS_CENTRALA')}/dane/barbara.txt"

print('S03E04\n')

def load_or_create_results(checkpoint_file: str) -> list:
    if os.path.exists(checkpoint_file):
        print("Loading existing results...")
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
            # Ensure each result has a value field
            for item in results:
                if "value" not in item:
                    item["value"] = ""
            return results
    return []

def save_results(results: list, checkpoint_file: str):
    os.makedirs(os.path.dirname(checkpoint_file), exist_ok=True)
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def download_barbara_note(url: str) -> str:
    response = requests.get(url)
    if not response.ok:
        raise Exception(f"Failed to download Barbara's note: {response.status_code}")
    return response.text

def extract_entities(text: str) -> list:
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY_FOR_AIDEVS'))
    print("Sending request to GPT...")
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """Extract all person names and city names from the text. Extract all names, even rare ones like Azazel or Glitch.
                Rules:
                - For person names: Extract only first names in nominative case (e.g., Barbara not Barbary)
                - Convert to uppercase without Polish characters (e.g., LODZ not ŁÓDŹ, RAFAL not Rafał)
                - Ignore any other information
                Return JSON format: {"entities": [{"key": "extracted_text", "category": "name/city"}]}
                Where category is either "name" for person names or "city" for city names."""
            },
            {
                "role": "user",
                "content": text
            }
        ],
        model="gpt-4o",
        temperature=0.0,
        response_format={ "type": "json_object" }
    )
    
    try:
        content = json.loads(response.choices[0].message.content)
        print("Extracted entities:", content)
        return content["entities"]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing GPT response: {e}")
        return []

def query_api(endpoint: str, query: str) -> dict:
    payload = {
        "apikey": os.getenv('AIDEVS_API_KEY'),
        "query": query
    }
    response = requests.post(
        f"{os.getenv('AIDEVS_CENTRALA')}/{endpoint}",
        json=payload
    )
    if not response.ok:
        raise Exception(f"API query failed: {response.status_code, response.text}")
    return response.json()

def find_barbara_city(results: list) -> str:
    """Find the city that contains BARBARA in its value."""
    for result in results:
        if result["category"] == "city" and "BARBARA" == result["value"]:
            return result["key"]
    raise Exception("No city found containing BARBARA in its value")

def process_new_entities(results: list) -> list:
    # Find first unprocessed entry
    unprocessed = next((item for item in results if not item["value"]), None)
    if not unprocessed:
        return results
    
    print(f"\nProcessing: {unprocessed['key']} ({unprocessed['category']})")
    
    # Query appropriate API
    endpoint = "people" if unprocessed["category"] == "name" else "places"
    response = query_api(endpoint, unprocessed["key"])
    
    # Update the processed item
    unprocessed["value"] = response["message"]
    
    # Extract new entities from the response
    new_entities = extract_entities(str(response))
    
    # Add new unique entities
    existing_keys = {item["key"] for item in results}
    new_unique_entities = [
        {**entity, "value": ""}  # Initialize value field for new entities
        for entity in new_entities 
        if entity["key"] not in existing_keys
    ]
    
    if new_unique_entities:
        results.extend(new_unique_entities)
    
    # Continue processing remaining unprocessed entries
    save_results(results, CHECKPOINT_FILE)
    return process_new_entities(results)

def send_report(answer: str) -> dict:
    response = requests.post(
        f"{os.getenv('AIDEVS_CENTRALA')}/report",
        json={
            "task": "loop",
            "apikey": os.getenv('AIDEVS_API_KEY'),
            "answer": answer
        }
    )
    if not response.ok:
        raise Exception(f"Failed to send report: {response.text}")
    return response.json()

if __name__ == "__main__":
    try:
        # Load or create results
        results = load_or_create_results(CHECKPOINT_FILE)
        
        # If starting fresh, download and process Barbara's note
        if not results:
            print("Starting fresh analysis...")
            note = download_barbara_note(BARBARA_NOTE_URL)
            
            # Save Barbara's note
            os.makedirs(os.path.dirname(NOTE_FILE), exist_ok=True)
            with open(NOTE_FILE, 'w', encoding='utf-8') as f:
                f.write(note)
                
            initial_entities = extract_entities(note)
            results = [{**entity, "value": ""} for entity in initial_entities]
            save_results(results, CHECKPOINT_FILE)
        
        results = process_new_entities(results)
        
        print("\nFinal results:", json.dumps(results, indent=2))

        # Send the final answer
        barbara_city = find_barbara_city(results)
        print(f"\nSending answer: {barbara_city}")
        response = send_report(barbara_city)
        print("Report response:", response)

    except Exception as e:
        print(f"Error: {e}") 