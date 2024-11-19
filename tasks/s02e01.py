import os
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
                "role": "user",
                "content": """You are a helpful assistant. 
                Based on the provided witness testimonies, determine the street where Andrzej Maj teaches. 
                Even if the street name is not directly mentioned, use your knowledge to deduce it. Respond only with the street name."""
            },
            {
                "role": "user",
                "content": f"""Based on these testimonies, what street is Andrzej Maj's university located on?
                <transcriptions>
                {transcriptions}
                </transcriptions>"""
            }
        ],
        model="o1-preview",
        temperature=1
    )
    # print(response.model_dump_json(indent=2))
    return response.choices[0].message.content.strip()

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