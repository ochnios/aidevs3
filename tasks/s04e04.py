import os
import json
import argparse
from pathlib import Path
from flask import Flask, request, jsonify
from openai import OpenAI
import requests

print('S04E04\n')

app = Flask(__name__)
client = None
map_content = None

def load_map() -> str:
    """Load map content from file"""
    map_path = Path("data/webhook/mapa.txt")
    if not map_path.exists():
        raise FileNotFoundError("Map file not found")
    return map_path.read_text(encoding='utf-8')

def analyze_drone_location(instruction: str) -> dict:
    """Analyze drone location using GPT-4o"""
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a drone navigation expert. Analyze the provided map and drone movement instructions to determine the final drone location.

Rules:
1. The response must be in Polish
2. The location description must be maximum 2 words
3. Be precise and concise
4. Use thinking field to explain your reasoning

<map>
{map_content}
</map>

Output format:
{{
    "thinking": "Explain your reasoning here",
    "description": "max two words in Polish describing the final location"
}}"""
                },
                {
                    "role": "user",
                    "content": f"<instruction>{instruction}</instruction>"
                }
            ],
            model="gpt-4o-mini",
            temperature=0.0,
        )
        
        result = json.loads(response.choices[0].message.content.strip())
        print(f"\nLLM Analysis:\nInput: {instruction}\nOutput: {json.dumps(result, indent=2)}\n")
        
        return result
    except Exception as e:
        print(f"Error in analyze_drone_location: {str(e)}")
        return {"description": "nieznana lokalizacja"}

def send_webhook_url() -> dict:
    """Send webhook URL to the API"""
    webhook_data = {
        "task": "webhook",
        "apikey": os.getenv('AIDEVS_API_KEY'),
        "answer": os.getenv('AIDEVS_WEBHOOK_URL')
    }
    response = requests.post(
        f"{os.getenv('AIDEVS_CENTRALA')}/report",
        json=webhook_data
    )
    print(f"Webhook response: {response.text}")
    if not response.ok:
        raise Exception(f"Failed to send webhook URL: {response.text}")
    return response.json()

@app.route('/', methods=['POST'])
def webhook():
    """Handle incoming webhook requests"""
    try:
        data = request.get_json()
        print(f"\nReceived webhook request: {json.dumps(data, indent=2)}")
        
        if not data or 'instruction' not in data:
            return jsonify({"error": "Missing instruction"}), 400
        
        result = analyze_drone_location(data['instruction'])
        print(f"Sending response: {json.dumps(result, indent=2)}")
        return jsonify(result)
        
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return jsonify({"error": str(e)}), 500

def main():
    global client, map_content
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-start', action='store_true', help='Send webhook URL to API')
    args = parser.parse_args()
    
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY_FOR_AIDEVS'))
        
        if args.start:
            print("\nSending webhook URL to API...")
            response = send_webhook_url()
            print(f"Response: {json.dumps(response, indent=2)}")
            return
            
        print("\nLoading map data...")
        map_content = load_map()
        
        webhook_url = os.getenv('AIDEVS_WEBHOOK_URL')
        webhook_port = os.getenv('AIDEVS_WEBHOOK_PORT')
        if not webhook_url:
            raise ValueError("AIDEVS_WEBHOOK_URL environment variable not set")
        if not webhook_port:
            raise ValueError("AIDEVS_WEBHOOK_PORT environment variable not set")
            
        port = int(webhook_port)
        print(f"\nStarting webhook server on port {port}...")
        app.run(host='localhost', port=port, debug=True)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    main() 