import os
import re
import requests
from pathlib import Path
from openai import OpenAI

print('S02E01\n')

def transcribe_recordings(directory: str, output_file: str) -> str:
    if os.path.exists(output_file):
        print("Using existing transcriptions")
        with open(output_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    print("Generating new transcriptions...")
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY_FOR_AIDEVS'))
    all_transcriptions = []
    
    for audio_file in Path(directory).glob("*.m4a"):
        print(f"Transcribing {audio_file.name}...")
        with open(audio_file, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="pl"
            )
            all_transcriptions.append(f"File {audio_file.name}: {transcript.text}")
    
    combined_text = "\n\n".join(all_transcriptions)
    
    # Save transcriptions
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(combined_text)
    
    return combined_text

def get_street_name(transcriptions: str) -> str:
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY_FOR_AIDEVS'))
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
"content": """You are a detective analyzing witness testimonies to determine the location of Andrzej Maj's university (specific faculty of the university).

Analyze the testimonies carefully and provide your response in the following structured format:

Reasoning:
List all relevant clues and information from testimonies.
Analyze any contradictions or inconsistencies.
Explain your deductive process and why certain clues might be more reliable than others.

Verification:
Cross-check your deduction against known facts about universities faculties and their locations.
Validate if your conclusion makes logical sense given all available information.

Answer:
The final street name of the faculty only, with no additional text."""
            },
            {
                "role": "user",
                "content": f"""<testimonies>
                {transcriptions}
                </testimonies>"""
            }
        ],
        model="gpt-4o",
        temperature=0.0
    )
    
    completion = response.choices[0].message.content.strip()

    print("\nFull response:\n", completion)
    
    # Extract just the answer from the structured response
    answer_match = re.search(r'Answer:\s*(.*?)$', completion, re.DOTALL | re.MULTILINE)
    if answer_match:
        return answer_match.group(1).strip()
    return completion  # Fallback to full response if pattern not found

def send_report(answer: str) -> dict:
    final_answer = {
        "task": "mp3",
        "apikey": os.getenv('AIDEVS_API_KEY'),
        "answer": answer
    }
    response = requests.post(
        f"{os.getenv('AIDEVS_CENTRALA')}/report",
        json=final_answer
    )
    if not response.ok:
        raise Exception(f"Failed to send report: {response.text}")
    return response.json()

if __name__ == "__main__":
    try:
        # Paths
        recordings_dir = "data/przesluchania"
        transcriptions_file = "data/przesluchania/transcriptions.txt"
        
        # Get transcriptions
        transcriptions = transcribe_recordings(recordings_dir, transcriptions_file)
        print("\nTranscriptions completed/loaded")
        
        # Get street name
        street_name = get_street_name(transcriptions)
        print(f"\nFound street name: {street_name}")
        
        # Send answer
        result = send_report(street_name)
        print(f"\nAPI Response: {result}")
        
    except Exception as e:
        print(f"Error: {e}") 