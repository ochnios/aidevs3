import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

print('S00E01')


api_key = os.getenv('OPENAI_API_KEY_FOR_AIDEVS')
client = OpenAI(
    api_key=api_key
)


def get_answer(content) -> str:
    return client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "Answer user question. If it is possible, answer with number and nothing more.",
            },
            {
                "role": "user",
                "content": content,
            }
        ],
        model="gpt-4o"
    ).choices[0].message.content


# Download page content
url = os.getenv('AIDEVS_XYZ')
response = requests.get(url)
response.raise_for_status()  # Raise an error for bad responses

# Parse the page content and extract the text from the element with id=human-question
soup = BeautifulSoup(response.content, 'html.parser')
human_question_element = soup.find(id='human-question')
content = human_question_element.get_text()

print("\ncontent: ", content)

# Pass this text to get_answer(content) function
answer = get_answer(content)
print("\nanswer: ", answer)

# Send the returned answer with POST method as a form with values: username, password, and answer
post_data = {
    'username': 'xxx',
    'password': 'xxx',
    'answer': answer
}
post_response = requests.post(url, data=post_data)
post_response.raise_for_status()

# Print formatted HTML of the response
formatted_html = BeautifulSoup(post_response.content, 'html.parser').prettify()
print("\nresponse:", formatted_html)
