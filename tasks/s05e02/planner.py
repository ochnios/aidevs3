from typing import Dict, Any, List
from openai import OpenAI
import json

class Planner:
    def __init__(self, client: OpenAI, tools: Dict[str, Any]):
        self.client = client
        self.tools = tools
        self.answered_questions = {}

    def plan(self, question: str, tool_results: List[Dict[str, Any]] = None, question_id: str = None) -> Dict[str, Any]:
        tools_str = json.dumps({name: tool.signature for name, tool in self.tools.items()}, indent=2, ensure_ascii=False)
        results_str = json.dumps(tool_results, ensure_ascii=False) if tool_results else "No previous results"
        
        messages = [
                {
                    "role": "system",
                    "content": f"""You are an AI Assistant that helps answer questions by using available tools.

Your task is to:
1. Analyze the question and previous tool results (if any)
2. Decide what tools to use next or provide final answer

Available tools with their signatures:
<tools>
{tools_str}
</tools>

Already called tools with results:
<tools_results>
{results_str}
</tools_results>

<rules>
1. Explain your thinking in very detailed manner
2. If you have enough information to answer the question, you should send report
3. When you've finished your job, set is_final to true and provide the final answer for the user
4. Final answer should be in a natural language with details what have you done and what was returned after the report
4. If a tool returned an error, analyze it and decide how to proceed.
</rules>

You must respond with a JSON in the following format without any additional text:
{{
    "thinking": "detailed explanation of your reasoning",
    "plan": {{
        "tools": [
            {{
                "tool": "tool_name",
                "reason": "why this tool is needed",
                "parameters": {{
                    "param1": "value1"
                }}
            }}
        ]
    }},
    "is_final": false,
    "final_answer": null
}}
"""
                },
                {
                    "role": "user",
                    "content": question
                }
            ]
        
        print("Tools results: ", results_str)

        response = self.client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            temperature=0.0,
            messages=messages
        )
        
        result = json.loads(response.choices[0].message.content)
        
        if result["is_final"] and question_id:
            self.answered_questions[question_id] = {
                "question": question,
                "answer": result["final_answer"]
            }
            
        return result 