import os
import json
from pathlib import Path
from openai import OpenAI
import requests
from typing import Dict
from datetime import datetime

from tools import GetTablesListTool, GetTableSchemaTool, GetPersonLocationTool, GetPlaceInfoTool, RunSqlQueryTool, SendReportTool, ToolRegistry
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

def main():
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY_FOR_AIDEVS'))
    
    try:
        # Setup paths
        base_url = os.getenv('AIDEVS_CENTRALA')
        api_key = os.getenv('AIDEVS_API_KEY')
        
        if not all([base_url, api_key]):
            raise ValueError("Missing required environment variables")

        gps_dir = Path("../data/gps")
        questions = download_and_save_data(
            f"{base_url}/data/{api_key}/gps_question.json",
            gps_dir / "question.json"
        )

        # Initialize tools and planner
        registry = ToolRegistry()
        registry.register(GetPlaceInfoTool())
        registry.register(GetPersonLocationTool())
        registry.register(GetTablesListTool())
        registry.register(GetTableSchemaTool())
        registry.register(RunSqlQueryTool())
        registry.register(SendReportTool())

        tools_str = json.dumps({name: tool.signature for name, tool in registry.tools.items()}, indent=2, ensure_ascii=False)
        print(f"\nAvailable tools with their signatures:\n{tools_str}")
        
        planner = Planner(client, registry.tools)
        
        # Process all questions
        answers = {}
        start_time = datetime.now()
        print(f"\nStarting questions processing at: {start_time}")
        
        for question_id, question in questions.items():
            question_start = datetime.now()
            print(f"\nProcessing {question_id}: {question}")
            print(f"Question started at: {question_start}")
            
            tool_results = []
            while True:
                print("=" * 80)
                plan = planner.plan(question, tool_results, question_id)
                print(f"\nPlan: {plan}")
                    
                for tool_plan in plan["plan"]["tools"]:
                    print("-" * 80)
                    tool = registry.get_tool(tool_plan["tool"])
                    parameters = tool_plan.get("parameters", {})
                    print(f"\nExecuting {tool.name} with parameters: {parameters}")
                    result = tool.execute(parameters)
                    tool_results.append(result)
                    print(f"Tool result: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    
                    # input("Press any key to continue...")

                if plan["is_final"]:
                    answers[question_id] = plan['final_answer']
                    print(f"\nFinal answer: {answers[question_id]}")
                    break

            question_end = datetime.now()
            question_duration = question_end - question_start
            print(f"Question finished at: {question_end}")
            print(f"Question processing took: {question_duration}")

        end_time = datetime.now()
        total_duration = end_time - start_time
        print(f"\nAll questions processed at: {end_time}")
        print(f"Total processing time: {total_duration}")
        print(f"\nFinal answers: {answers}")

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    main() 