import os
import requests
from openai import OpenAI

print('S00E02\n')


def get_correct_answer(question: str) -> str:
    # Handle special cases first
    question_lower = question.lower()
    
    if "capital" in question_lower and "poland" in question_lower:
        return "KRAKÓW"
    if "hitchhiker" in question_lower or "guide to the galaxy" in question_lower:
        return "69"
    if "current year" in question_lower or "what year" in question_lower:
        return "1999"
    
    # For other questions, use GPT to get truthful answers
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY_FOR_AIDEVS'))
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. Answer questions directly and concisely. If asked a calculation or factual question, provide just the answer without explanation."
            },
            {
                "role": "user",
                "content": question
            }
        ],
        model="gpt-4o",
        temperature=0
    )
    return response.choices[0].message.content

def verify_robot():
    base_url = "https://xyz.ag3nts.org/verify"
    
    # Start conversation with READY
    initial_payload = {
        "text": "READY",
        "msgID": "0"
    }
    
    response = requests.post(base_url, json=initial_payload)
    if not response.ok:
        raise Exception(f"Failed to start verification: {response.text}")
    
    # Get question from robot
    robot_response = response.json()
    question = robot_response["text"]
    msg_id = robot_response["msgID"]
    
    print(f"Robot asks: {question}")
    
    # Get and send answer
    answer = get_correct_answer(question)
    answer_payload = {
        "text": answer,
        "msgID": msg_id
    }
    
    print(f"Sending answer: {answer}")
    final_response = requests.post(base_url, json=answer_payload)
    
    if not final_response.ok:
        raise Exception(f"Failed to verify: {final_response.text}")
    
    print(f"Final response: {final_response.text}")
    return final_response.json()

if __name__ == "__main__":
    try:
        result = verify_robot()
        print("Success! Flag:", result.get("text", "No flag found"))
    except Exception as e:
        print(f"Error: {e}") 