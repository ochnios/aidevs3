import os
import json
import base64
from pathlib import Path
from openai import OpenAI
import requests

print('S02E04\n')

def load_processed_results(results_file: str) -> dict:
    if os.path.exists(results_file):
        with open(results_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"people": [], "hardware": [], "other": []}

def save_processed_results(results: dict, results_file: str):
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

def get_file_content(file_path: Path, client: OpenAI) -> str:
    if file_path.suffix == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    elif file_path.suffix == '.mp3':
        print(f"Transcribing {file_path.name}...")
        with open(file_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="en"
            )
            return transcript.text
    
    elif file_path.suffix == '.png':
        print(f"Analyzing image {file_path.name}...")
        with open(file_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at analyzing images and extracting text content. Please examine this image carefully and extract any visible text (OCR)."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            model="gpt-4o",
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    
    return ""

def categorize_content(content: str, client: OpenAI) -> str:
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """Analyze the given content and categorize it into one of these categories by following these steps:

1. First analyze if the content matches these specific criteria:
- 'people': ONLY if about CAPTURED humans or FOUND human traces (not about regular human presence)
- 'hardware': ONLY if about HARDWARE faults or about HARDWARE and SOFTWARE faults (only software faults are not included here)
- 'other': if it doesn't clearly fit the above categories

2. Provide your response in this exact format:
Reasoning: [explain in 1-2 sentences why this fits or doesn't fit each relevant category]

Verification: [verify your reasoning by checking if it strictly adheres to the category criteria and confirm or adjust your initial thoughts]

Category: [category]

Only the text after "Category: " will be processed, so ensure it's exactly one of: 'people', 'hardware', or 'other'."""
            },
            {
                "role": "user",
                "content": content
            }
        ],
        model="gpt-4o",
        temperature=0
    )
    
    full_response = response.choices[0].message.content.strip().lower()
    print(f"\nFull response:\n{full_response}\n")
    
    category = full_response.split('category:')[-1].strip()
    return category

def process_files(directory: str, results_file: str) -> dict:
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY_FOR_AIDEVS'))
    results = load_processed_results(results_file)
    processed_files = set(results['people'] + results['hardware'] + results['other'])
    
    for file_path in Path(directory).glob("*.*"):
        if file_path.suffix not in ['.txt', '.mp3', '.png'] or file_path.name in processed_files:
            continue
        
        print(f"\nProcessing {file_path.name}...")
        
        try:
            # Get content
            content = get_file_content(file_path, client)
            print(f"\nContent/Description:\n{content}")
            
            # Categorize
            category = categorize_content(content, client)
            print(f"Category: {category}")
            
            # Store result
            results[category].append(file_path.name)
            save_processed_results(results, results_file)
            
            print("-" * 80)
            
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
            continue
    
    return {"people": results["people"], "hardware": results["hardware"]}

def send_report(answer: dict) -> dict:
    response = requests.post(
        f"{os.getenv('AIDEVS_CENTRALA')}/report",
        json={
            "task": "kategorie",
            "apikey": os.getenv('AIDEVS_API_KEY'),
            "answer": answer
        }
    )
    if not response.ok:
        raise Exception(f"Failed to send report: {response.text}")
    return response.json()

if __name__ == "__main__":
    try:
        # Paths
        files_dir = "data/pliki_z_fabryki"
        results_file = "data/pliki_z_fabryki/results.json"
        
        # Process files
        print("\nStarting files processing...")
        results = process_files(files_dir, results_file)
        print("\nFiles processing completed")
        print("=" * 80)
        print(json.dumps(results, indent=2))
        print("=" * 80)
        
        # Send answer
        result = send_report(results)
        print(f"\nAPI Response: {result}")
        
    except Exception as e:
        print(f"Error: {e}") 