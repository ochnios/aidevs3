import os
import json
import requests
from openai import OpenAI

print('S01E03\n')

def read_json_file(filepath: str) -> dict:
    with open(filepath, 'r') as file:
        return json.load(file)

def validate_calculation(question: str, given_answer: int) -> int:
    # Extract numbers and operator from the question
    parts = question.split()
    if len(parts) != 3:
        return given_answer
    
    try:
        num1 = int(parts[0])
        num2 = int(parts[2])
        operator = parts[1]
        
        if operator == '+':
            return num1 + num2
        elif operator == '-':
            return num1 - num2
        elif operator == '*':
            return num1 * num2
        elif operator == '/':
            return num1 / num2
    except:
        return given_answer
    
    return given_answer

def get_test_answer(question: str) -> str:
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY_FOR_AIDEVS'))
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. Answer questions directly and concisely. Provide just the answer without explanation."
            },
            {
                "role": "user",
                "content": question
            }
        ],
        model="gpt-4o",
        temperature=0
    )
    print(f"LLM Input: {question}")
    print(f"LLM Output: {response.choices[0].message.content}")
    return response.choices[0].message.content

def process_json_data(data: dict) -> dict:
    # Add required fields
    result = {
        "apikey": os.getenv('AIDEVS_API_KEY'),
        "description": "This is simple calibration data used for testing purposes. Do not use it in production environment!",
        "copyright": "Copyright (C) 2238 by BanAN Technologies Inc.",
        "test-data": []
    }
    
    # Process each item in test-data
    for item in data["test-data"]:
        new_item = item.copy()
        
        # Validate calculation if present
        if "question" in item and "answer" in item:
            correct_answer = validate_calculation(item["question"], item["answer"])
            new_item["answer"] = correct_answer
        
        # Process test questions if present
        if "test" in item:
            test_answer = get_test_answer(item["test"]["q"])
            new_item["test"]["a"] = test_answer
        
        result["test-data"].append(new_item)
    
    return result

def send_report(data: dict) -> dict:
    final_answer = {
        "task": "JSON",
        "apikey": os.getenv('AIDEVS_API_KEY'),
        "answer": data
    }
    response = requests.post(
        "https://centrala.ag3nts.org/report",
        json=final_answer
    )
    if not response.ok:
        raise Exception(f"Failed to send report: {response.text}")
    return response.json()

if __name__ == "__main__":
    try:
        # Read input JSON
        input_data = read_json_file("data/json.txt")
        # print("Input JSON:", json.dumps(input_data, indent=2))
        
        # Process data
        result_data = process_json_data(input_data)
        # print("\nProcessed JSON:", json.dumps(result_data, indent=2))
        
        # Send report
        response = send_report(result_data)
        print("\nReport response:", response)
        
    except Exception as e:
        print(f"Error: {e}") 