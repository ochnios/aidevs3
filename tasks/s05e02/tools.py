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
                "description": "Name of the place should be uppercase and without diacritics e.g. SLASK instead of Śląsk",
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
    
class GetPersonLocationTool(Tool):
    @property
    def name(self) -> str:
        return "get_person_location"

    @property
    def description(self) -> str:
        return "Returns gps coordinates of given person"

    @property
    def signature(self) -> Dict[str, Any]:
        return {
            "userID": {
                "type": "string",
                "description": "User ID from the database",
                "required": True
            }
        }

    def _execute(self, parameters: Dict[str, Any]) -> Any:
        userID = parameters.get("userID")
        if not userID:
            raise ValueError("User ID is required")

        payload = {
            "userID": userID
        }
        response = requests.post(
            f"{os.getenv('AIDEVS_CENTRALA')}/gps",
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
    "firstname1": {
        "lat": 12.345,
        "lon": 65.431
    },
    "firstname2": {
        "lat": 19.433,
        "lon": 12.123
    }

Firstname of the person should be uppercase and without diacritics e.g. RAFAL instead of Rafał
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
        "task": "gps",
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

class GetTablesListTool(Tool):
    @property
    def name(self) -> str:
        return "get_tables_list"

    @property
    def description(self) -> str:
        return "Returns a list of tables in the database"

    @property
    def signature(self) -> Dict[str, Any]:
        return {}

    def _execute(self, parameters: Dict[str, Any]) -> Any:
        return query_database("show tables")

class GetTableSchemaTool(Tool):
    @property
    def name(self) -> str:
        return "get_table_schema"

    @property
    def description(self) -> str:
        return "Returns the schema of a specified table"

    @property
    def signature(self) -> Dict[str, Any]:
        return {
            "table_name": {
                "type": "string",
                "description": "Name of the table to fetch schema for",
                "required": True
            }
        }

    def _execute(self, parameters: Dict[str, Any]) -> Any:
        table_name = parameters.get("table_name")
        if not table_name:
            raise ValueError("Table name is required")

        return query_database(f"show create table {table_name}")

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