import os
import json
from pathlib import Path
from openai import OpenAI
import requests
from typing import Dict

from tools import ToolRegistry, LoadFactsTool, LoadTranscriptionTool, SendRequestTool
from planner import Planner

def download_and_save_data(url: str, save_path: Path) -> Dict:
    """Download and save data from URL"""
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    return data

def send_report(answer: Dict[str, str]) -> dict:
    """Send answers to the API"""
    final_answer = {
        "task": "phone",
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

def main():
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY_FOR_AIDEVS'))
    
    try:
        # Setup paths
        base_url = os.getenv('AIDEVS_CENTRALA')
        api_key = os.getenv('AIDEVS_API_KEY')
        
        if not all([base_url, api_key]):
            raise ValueError("Missing required environment variables")

        # Setup directory and files
        phone_dir = Path("../data/phone")
        phone_dir.mkdir(parents=True, exist_ok=True)
        answers_file = phone_dir / "answers.json"

        # Check for existing answers
        if answers_file.exists():
            print("\nFound existing answers, loading them...")
            with open(answers_file, 'r', encoding='utf-8') as f:
                answers = json.load(f)
            print("Sending existing answers to API...")
            response = send_report(answers)
            print(f"API Response: {response}")
            return

        # If no answers exist, proceed with processing questions
        transcriptions = download_and_save_data(
            f"{base_url}/data/{api_key}/phone_sorted.json",
            phone_dir / "phone_sorted.json"
        )
        
        questions = download_and_save_data(
            f"{base_url}/data/{api_key}/phone_questions.json",
            phone_dir / "questions.json"
        )

        # Initialize tools and planner
        registry = ToolRegistry()
        registry.register(LoadFactsTool())
        registry.register(LoadTranscriptionTool())
        registry.register(SendRequestTool())
        
        planner = Planner(client, registry.tools)
        
        # Process all questions
        answers = {}
        for question_id, question in questions.items():
            print(f"\nProcessing question {question_id}: {question}")
            
            tool_results = []
            while True:
                print("=" * 80)
                plan = planner.plan(question, tool_results, question_id)
                print(f"\nPlan: {plan}")
                
                if plan["is_final"]:
                    answers[question_id] = plan['final_answer']
                    print(f"\nFinal answer: {answers[question_id]}")
                    break
                    
                for tool_plan in plan["plan"]["tools"]:
                    print("-" * 80)
                    tool = registry.get_tool(tool_plan["tool"])
                    print(f"\nExecuting {tool.name} with parameters: {tool_plan['parameters']}")
                    result = tool.execute(tool_plan["parameters"])
                    tool_results.append(result)
                    print(f"Tool result: {json.dumps(result, indent=2, ensure_ascii=False)}")

        # Save answers to file
        with open(answers_file, 'w', encoding='utf-8') as f:
            json.dump(answers, f, indent=2, ensure_ascii=False)
        print(f"\nAnswers saved to {answers_file}")

        # Send answers to API
        print("\nSending answers to API...")
        response = send_report(answers)
        print(f"API Response: {response}")

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    main() 