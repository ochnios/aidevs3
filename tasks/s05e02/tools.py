import requests
import sys
import os
from abc import ABC, abstractmethod
from typing import Any, Dict


parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from s03e03 import query_database, get_table_structure

class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the tool"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return the tool's parameter description"""
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

class GetDatabaseSchemaTool(Tool):
    @property
    def name(self) -> str:
        return "get_database_schema"
    
    @property
    def description(self) -> str:
        return "Returns the database schema"
    
    @property
    def signature(self) -> Dict[str, Any]:
        return {}

    def _execute(self, parameters: Dict[str, Any]) -> Any:
        return get_table_structure()

class RunSqlQueryTool(Tool):
    @property
    def name(self) -> str:
        return "run_sql_query"

    @property
    def description(self) -> str:
        return "Runs SQL query and returns the result"

    @property
    def signature(self) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "SQL query to run",
                "required": True
            }
        }

    def _execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        query = parameters.get("query")
        if not query:
            raise ValueError("Query is required")

        return query_database(query)
    
class RunSqlQueryTool(Tool):
    @property
    def name(self) -> str:
        return "run_sql_query"

    @property
    def description(self) -> str:
        return "Runs given SQL query and returns the result"

    @property
    def signature(self) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "SQL query to run",
                "required": True
            }
        }

    def _execute(self, parameters: Dict[str, Any]) -> Any:
        query = parameters.get("query")
        
        if not query:
            raise ValueError("Query is required")
        
        return query_database(query)

class GetPlaceInfoTool(Tool):
    @property
    def name(self) -> str:
        return "get_place_info"

    @property
    def description(self) -> str:
        return "Returns list of people which were seen in given place"

    @property
    def signature(self) -> Dict[str, Any]:
        return {
            "name": {
                "type": "string",
                "description": "Name of the place, without diacritics e.g. SLASK instead of Śląsk",
                "required": True
            }
        }

    def _execute(self, parameters: Dict[str, Any]) -> Any:
        name = parameters.get("name")
        if not name:
            raise ValueError("Name is required")

        payload = {
            "apikey": os.getenv('AIDEVS_API_KEY'),
            "query": name
        }
        response = requests.post(
            f"{os.getenv('AIDEVS_CENTRALA')}/places",
            json=payload
        )
        
        if not response.ok:
            raise Exception(f"API query failed: {response.status_code, response.text}")
        
        return response.json()
    
class GetPersonInfoTool(Tool):
    @property
    def name(self) -> str:
        return "get_person_info"

    @property
    def description(self) -> str:
        return "Returns list of places where given person was seen"

    @property
    def signature(self) -> Dict[str, Any]:
        return {
            "firstname": {
                "type": "string",
                "description": "First name of the person, without diacritics e.g. LUCJA instead of ŁUCJA",
                "required": True
            }
        }

    def _execute(self, parameters: Dict[str, Any]) -> Any:
        firstname = parameters.get("firstname")
        if not firstname:
            raise ValueError("First name is required")

        payload = {
            "apikey": os.getenv('AIDEVS_API_KEY'),
            "query": firstname
        }
        response = requests.post(
            f"{os.getenv('AIDEVS_CENTRALA')}/people",
            json=payload
        )
        
        if not response.ok:
            raise Exception(f"API query failed: {response.status_code, response.text}")
        
        return response.json()

class SendReportTool(Tool):
    @property
    def name(self) -> str:
        return "send_report"

    @property
    def description(self) -> str:
        return "Sends the final answer to the central API"

    @property
    def signature(self) -> Dict[str, Any]:
        return {
            "answer": {
                "type": "dict",
                "description": """Answer to send to the central API in format like:
{
    "name1": {
        "lat": 12.345,
        "lon": 65.431
    },
    "name2": {
        "lat": 19.433,
        "lon": 12.123
    }
}
""",
                "required": True
            }
        }

    def _execute(self, parameters: Dict[str, Any]) -> Any:
        answer = parameters.get("answer")
        
        if not answer:
            raise ValueError("Answer is required")
            
        payload = {
        "task": "database",
            "apikey": os.getenv('AIDEVS_API_KEY'),
            "answer": answer
        }
        
        response = requests.post(
            f"{os.getenv('AIDEVS_CENTRALA')}/report",
            json=payload
        )
        if not response.ok:
            raise Exception(f"Failed to send report: {response.text}")
        
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