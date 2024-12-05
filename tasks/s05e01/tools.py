from abc import ABC, abstractmethod
from typing import Any, Dict, List
import json
import os
import requests
from pathlib import Path

class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the tool"""
        pass

    @property
    @abstractmethod
    def signature(self) -> Dict[str, Any]:
        """Return the tool's parameter signature"""
        pass

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters and handle errors"""
        try:
            result = self._execute(parameters)
            return {
                "tool": self.name,
                "parameters": parameters,
                "result": result,
                "error": None
            }
        except Exception as e:
            return {
                "tool": self.name,
                "parameters": parameters,
                "result": None,
                "error": str(e)
            }

    @abstractmethod
    def _execute(self, parameters: Dict[str, Any]) -> Any:
        """Internal execution method to be implemented by tools"""
        pass

class LoadFactsTool(Tool):
    def __init__(self):
        self.facts_path = Path("../data/pliki_z_fabryki/facts/facts.json")
        # Load available files on initialization
        with open(self.facts_path, 'r', encoding='utf-8') as f:
            facts = json.load(f)
            self.available_files = list(set(f["file"] for f in facts))

    @property
    def name(self) -> str:
        return "load_facts"

    @property
    def signature(self) -> Dict[str, Any]:
        return {
            "file": {
                "type": "string",
                "description": "Filter for specific file. Use 'all' to get all facts. Available files: " + 
                             ", ".join(self.available_files),
                "required": False,
                "enum": ["all"] + self.available_files
            }
        }

    def _execute(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        file_filter = parameters.get("file")
        
        with open(self.facts_path, 'r', encoding='utf-8') as f:
            facts = json.load(f)
        
        if file_filter and file_filter != "all":
            facts = [f for f in facts if f["file"] == file_filter]
            
        return facts

class LoadTranscriptionTool(Tool):
    def __init__(self):
        self.transcriptions_path = Path("../data/phone")
        # Load available conversations on initialization
        with open(self.transcriptions_path / "phone_sorted.json", 'r', encoding='utf-8') as f:
            self.available_conversations = list(json.load(f).keys())

    @property
    def name(self) -> str:
        return "load_transcription"

    @property
    def signature(self) -> Dict[str, Any]:
        return {
            "conversation": {
                "type": "string",
                "description": "Name of the conversation to load. Use 'all' to get all conversations. " +
                             "Available conversations: " + ", ".join(self.available_conversations),
                "required": True,
                "enum": ["all"] + self.available_conversations
            }
        }

    def _execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        conversation_name = parameters.get("conversation")
        if not conversation_name:
            raise ValueError("Conversation name is required")

        file_path = self.transcriptions_path / "phone_sorted.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            all_transcriptions = json.load(f)
            
        if conversation_name == "all":
            return all_transcriptions
            
        if conversation_name not in all_transcriptions:
            raise ValueError(f"Conversation {conversation_name} not found")
            
        return all_transcriptions[conversation_name]

class SendRequestTool(Tool):
    @property
    def name(self) -> str:
        return "send_request"

    @property
    def signature(self) -> Dict[str, Any]:
        return {
            "url": {
                "type": "string",
                "description": "URL to send the request to",
                "required": True
            },
            "method": {
                "type": "string",
                "description": "HTTP method (GET or POST)",
                "required": True,
                "enum": ["GET", "POST"]
            },
            "body": {
                "type": "object",
                "description": "Request body for POST requests",
                "required": False
            }
        }

    def _execute(self, parameters: Dict[str, Any]) -> Any:
        url = parameters.get("url")
        method = parameters.get("method", "GET")
        body = parameters.get("body")
        
        if not url:
            raise ValueError("URL is required")
            
        if method == "POST":
            if body is None:
                raise ValueError("Body is required for POST requests")
            response = requests.post(url, json=body)
        else:
            response = requests.get(url)
            
        response.raise_for_status()
        return response.json()

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool:
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        return self.tools[name]

    def get_available_tools(self) -> list[str]:
        return list(self.tools.keys()) 