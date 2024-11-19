import os
import base64
from pathlib import Path
from openai import OpenAI

print('S02E02\n')
print('Polish prompts works better for recognizing polish cities...\n')

def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_maps(directory: str) -> str:
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY_FOR_AIDEVS'))
    all_images_content = []
    
    for image_file in Path(directory).glob("*.jpg"):
        print(f"\nAnalyzing {image_file.name}...")
        base64_image = encode_image_to_base64(image_file)
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": """Jesteś ekspertem kartografii analizującym fragmenty map. Przedstaw jasną, zwięzłą analizę, stosując się do tych wytycznych:

1. Wymień wszystkie nazwy ulic i dróg widoczne na mapie
2. Zidentyfikuj główne punkty orientacyjne, budynki lub miejsca warte uwagi
3. Zaznacz wszelkie cechy geograficzne (rzeki, parki, itp.)
4. Zwróć uwagę na jakiekolwiek wyróżniające się cechy

Odpowiedz bez formatowania, zwykłym tekstem.
"""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            model="gpt-4o",
            temperature=0
        )
        
        completion = response.choices[0].message.content.strip()
        print(f"\nAnalysis result:\n{completion}\n")
        print("-" * 80)
        all_images_content.append(f"Analysis of {image_file.name}:\n{completion}")
    
    return "\n\n".join(all_images_content)

def investigate(analysis_results: str) -> str:
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY_FOR_AIDEVS'))
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": """Jesteś detektywem analizującym opisy fragmentów map. 
Twoim zadaniem jest identyfikacja miasta na podstawie podanych opisów.
- Każdy opis zawiera nazwy ulic, charakterystyczne punkty i miejsa warte uwagi.
- Jeden z opisów opisuje pochodzi z innego miasta niż pozostałe.
- Oprócz opisów zostają podane dodatkowe informacje o poszukiwanym mieście.

Przedstaw swoją odpowiedź w formacie:
1. Analiza:
- Wymień kluczowe cechy z każdego opisu
- Zidentyfikuj, który opis wydaje się pochodzić z innego miasta i dlaczego
- Wyjaśnij, jakie wzorce łączą pozostałe opisy

2. Odpowiedź:
[nazwa miasta]"""
            },
            {
                "role": "user",
                "content": f"""<opisy>{analysis_results}</opisy>"""
            },
            {
                "role": "user",
                "content": f"""<dodatkowe_informacje>W mieście, którego szukamy, znajdują się spichlerze i twierdza</dodatkowe_informacje>"""
            }
        ],
        model="gpt-4o",
        temperature=0
    )
    
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    try:
        # Paths
        maps_dir = "data/mapy"
        
        # Analyze maps
        print("\nStarting map analysis...")
        analysis_results = analyze_maps(maps_dir)
        print("\nMap analysis completed")
        print("=" * 80)
        print(analysis_results)
        print("=" * 80)
        
        # Get city name
        invesigation_results = investigate(analysis_results)
        print(f"\Investigation results:\n{invesigation_results}")
        
    except Exception as e:
        print(f"Error: {e}") 