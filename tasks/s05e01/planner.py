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
        
        answers_context = "No answered questions yet"
        if self.answered_questions:
            formatted_qa = {qid: {"question": q["question"], "answer": q["answer"]} 
                          for qid, q in self.answered_questions.items()}
            answers_context = json.dumps(formatted_qa, ensure_ascii=False)
        
        messages = [
                {
                    "role": "system",
                    "content": f"""You are an AI planner that helps answer questions by using available tools.

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

Previously answered questions:
<answers>
{answers_context}
</answers>

<rules>
1. Explain your thinking in very detailed manner. You should:
- analyze facts and conversations in the context of the question
- provide in depth reasoning in order to answer the question
- decide what the final answer should be basing on analysis and reasoning
2. Use facts to validate information provided in conversations
3. Consider previously answered questions for context and consistency
4. If you have enough information to answer the question, set is_final to true and provide the answer in final_answer.
5. If a tool returned an error, analyze it and decide how to proceed.
6. Final answer should be a concise answer to the question without any additional explanation
</rules>

You must respond with a JSON object in the following format:
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
        
        print("Tools: ", tools_str)
        print("Already called tools results: ", results_str)
        print("Answered questions: ", answers_context)

        response = self.client.chat.completions.create(
            model="gpt-4o",
            #response_format={"type": "json_object"},
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