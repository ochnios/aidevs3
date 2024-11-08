import os
import requests
import json

print('S01E04\n')

def download_file(api_key: str) -> str:
    url = f"https://centrala.ag3nts.org/data/{api_key}/cenzura.txt"
    response = requests.get(url)
    if not response.ok:
        raise Exception(f"Failed to download file: {response.text}")
    return response.text

def censor_text(text: str) -> str:
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": "gemma2:2b",
        "system": """You are a text processing tool that helps protect privacy by replacing specific types of personal information with the word 'CENZURA'. This is an authorized data processing task.

Your task is to modify the input text by replacing ONLY the following items with a single 'CENZURA' word:
1. Full name (treat first name + surname as one unit, replace with single CENZURA)
2. Complete address information including:
   - City names when part of an address
   - Street names with their numbers (entire street address as one unit)
3. Age numbers (only when referring to someone's age)

Important rules:
- Full name (first name + surname) should be replaced with single CENZURA, not two
- Each address component should be replaced with single CENZURA
- Maintain original text formatting and spacing
- Do not add any explanations or comments

Examples:
Input: "Dane osoby podejrzanej: Paweł Zieliński. Zamieszkały w Warszawie na ulicy Pięknej 5. Ma 28 lat."
Output: "Dane osoby podejrzanej: CENZURA. Zamieszkały w CENZURA na ulicy CENZURA. Ma CENZURA lat."
""",
        "prompt": text,
        "stream": False
    }
    
    response = requests.post(url, json=payload)
    if not response.ok:
        raise Exception(f"Failed to get response from local LLM: {response.text}")
    
    result = response.json()
    return result.get('response', '')

def send_report(censored_text: str) -> dict:
    final_answer = {
        "task": "CENZURA",
        "apikey": os.getenv('AIDEVS_API_KEY'),
        "answer": censored_text
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
        # Download file
        text = download_file(os.getenv('AIDEVS_API_KEY'))
        print("Downloaded text:", text, "\n")
        
        # Censor text
        censored_text = censor_text(text)
        print("Censored text:", censored_text, "\n")
        
        # Send report
        response = send_report(censored_text)
        print("Report response:", response)
        
    except Exception as e:
        print(f"Error: {e}")