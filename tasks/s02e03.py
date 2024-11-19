import os
import json
import requests
from pathlib import Path
from openai import OpenAI

print('S02E03\n')

def get_robot_description(api_key: str) -> str:
    """Fetch and save the robot description from the centrala endpoint"""
    # Create directory if it doesn't exist
    data_dir = Path("data/robotid")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Path for saving description
    json_path = data_dir / "description.json"
    
    print("Fetching new robot description...")
    response = requests.get(
        f"{os.getenv('AIDEVS_CENTRALA')}/data/{api_key}/robotid.json"
    )
    if not response.ok:
        raise Exception(f"Failed to get robot description: {response.text}")
    
    description = response.json()
    
    # Save description for reference
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(description, f, indent=2)
    
    return description

def generate_robot_image(description: str) -> str:
    """Generate and save robot image using DALL-E 3 based on the description"""
    data_dir = Path("data/robotid")
    image_path = data_dir / "robot.png"
    
    print("Generating new robot image...")
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY_FOR_AIDEVS'))
    
    enhanced_prompt = f"""Create a detailed technical visualization of a robot with these characteristics: 
    {description}
    The image should be clear, detailed, and focus on the robot against a simple background."""
    
    response = client.images.generate(
        model="dall-e-3",
        prompt=enhanced_prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    
    image_url = response.data[0].url
    
    # Download and save the image
    image_response = requests.get(image_url)
    if image_response.ok:
        with open(image_path, 'wb') as f:
            f.write(image_response.content)
        print(f"Saved image to {image_path}")
    
    return image_url

def send_report(image_url: str) -> dict:
    """Send the generated image URL to the centrala"""
    final_answer = {
        "task": "robotid",
        "apikey": os.getenv('AIDEVS_API_KEY'),
        "answer": image_url
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
        # Get fresh robot description
        description = get_robot_description(os.getenv('AIDEVS_API_KEY'))
        print(f"\nReceived robot description: {description}")
        
        # Generate image
        image_url = generate_robot_image(description)
        print(f"\nGenerated image URL: {image_url}")
        
        # Send answer
        result = send_report(image_url)
        print(f"\nAPI Response: {result}")
        
    except Exception as e:
        print(f"Error: {e}") 