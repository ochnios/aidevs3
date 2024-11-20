import os
import json
import glob
from openai import OpenAI
import requests

print('S03E01\n')

def load_json_cache(file_path: str) -> list:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_to_json(data: list, file_path: str):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_person_from_text(client: OpenAI, content: str) -> str:
    print("\n=== PERSON EXTRACTION ===")
    print(f"Input text:\n{content}\n")
    
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """Przeanalizuj tekst i wyodrębnij pełne imię i nazwisko osoby, której dotyczy. 
                Odpowiedz wyłącznie imieniem i nazwiskiem, bez dodatkowego tekstu.
                Jeśli nie ma osoby w tekście, odpowiedz 'NONE'."""
            },
            {
                "role": "user",
                "content": content
            }
        ],
        model="gpt-4o",
        temperature=0.0
    )
    result = response.choices[0].message.content.strip()
    print(f"Extracted person: {result}\n")
    return result

def process_facts_files(client: OpenAI) -> list:
    facts_dir = "data/pliki_z_fabryki/facts"
    facts_json = os.path.join(facts_dir, "facts.json")
    
    # Load existing cache
    facts_data = load_json_cache(facts_json)
    processed_files = {item["file"] for item in facts_data}
    
    # Process new files
    for file_path in glob.glob(os.path.join(facts_dir, "*.txt")):
        filename = os.path.basename(file_path)
        if filename == "facts.json" or filename in processed_files:
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        if "entry deleted" in content.lower():
            continue
            
        person = extract_person_from_text(client, content)
        if person != "NONE":
            facts_data.append({
                "file": filename,
                "person": person,
                "content": content
            })
            save_to_json(facts_data, facts_json)
            
    return facts_data

def process_report_files(client: OpenAI) -> list:
    reports_dir = "data/pliki_z_fabryki"
    reports_json = os.path.join(reports_dir, "reports.json")
    
    # Load existing cache
    reports_data = load_json_cache(reports_json)
    processed_files = {item["file"] for item in reports_data}
    
    # Process new files
    for file_path in glob.glob(os.path.join(reports_dir, "*.txt")):
        filename = os.path.basename(file_path)
        if filename in processed_files:
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        person = extract_person_from_text(client, content)
        reports_data.append({
            "file": filename,
            "person": person if person != "NONE" else "",
            "content": content,
            "tags": ""  # Initialize empty tags field
        })
        save_to_json(reports_data, reports_json)
            
    return reports_data

def generate_tags(client: OpenAI, report: dict, facts_data: list, reports_data: list) -> str:
    print("\n=== TAG GENERATION ===")
    print(f"Processing file: {report['file']}")
    
    # Prepare context
    facts_context = ""
    if report["person"]:
        person_facts = [f for f in facts_data if f["person"] == report["person"]]
        if person_facts:
            facts_context = "<fakty_o_osobie>\n" + "\n".join(f["content"] for f in person_facts) + "\n</fakty_o_osobie>\n"
    
    other_reports = "Inne raporty:\n" + "\n".join(
        r["content"] for r in reports_data 
        if r["file"] != report["file"]
    )
    
    prompt = f"""Wygeneruj co najmniej 10 tagów dla podanego raportu, uwzględniając kontekst z:
- faktów o osobie (jeśli podane) - kim jest, czym się zajmuje (bardzo konkretnie), gdzie mieszka oraz inne istotne szczegóły
- innych raportów

Tagi powinny być rozdzielone przecinkami, nie dodawaj znaku '#' przed tagami.
Odpowiedz wyłącznie listą tagów, bez dodatkowego tekstu.
Pierwszy tag MUSI być nazwą sektora/działu wyciągniętą z nazwy pliku w formacie: 'sektor X1', 'sektor X2' itp.

{facts_context}

<inne_raporty>
{other_reports}
</inne_raporty>

<glowny_raport>
Nazwa pliku: {report['file']}
{report['content']}
</glowny_raport>
"""
    
    print(f"\nPrompt:\n{prompt}\n")
    
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": prompt
            }
        ],
        model="gpt-4o",
        temperature=0.0
    )
    result = response.choices[0].message.content.strip()
    print(f"Generated tags: {result}\n")
    
    # Update tags in reports.json
    reports_dir = "data/pliki_z_fabryki"
    reports_json = os.path.join(reports_dir, "reports.json")
    reports_data = load_json_cache(reports_json)
    
    for r in reports_data:
        if r["file"] == report["file"]:
            r["tags"] = result
            break
            
    save_to_json(reports_data, reports_json)
    
    return result

def send_report(tags_dict: dict) -> dict:
    final_answer = {
        "task": "dokumenty",
        "apikey": os.getenv('AIDEVS_API_KEY'),
        "answer": tags_dict
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
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY_FOR_AIDEVS'))
        
        # Process facts and reports
        facts_data = process_facts_files(client)
        reports_data = process_report_files(client)
        
        # Generate tags for reports
        tags_dict = {}
        for report in reports_data:
            tags = generate_tags(client, report, facts_data, reports_data)
            tags_dict[report["file"]] = tags
            
        # Send results
        result = send_report(tags_dict)
        print(f"\nAPI Response: {result}")
        
    except Exception as e:
        print(f"Error: {e}") 