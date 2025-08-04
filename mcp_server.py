#!/usr/bin/env python3
"""
Clinical Trials MCP Server

Provides structured access to ClinicalTrials.gov data through MCP tools.
Allows LLMs to search, retrieve, and analyze clinical trial information.
"""

import json
import sys
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import requests
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
)
from pydantic import BaseModel, Field


class ClinicalTrialsAPI:
    """Client for ClinicalTrials.gov API v2"""
    
    BASE_URL = "https://clinicaltrials.gov/api/v2"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ClinicalTrials-MCP-Server/1.0'
        })
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request with error handling"""
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")
    
    def search_studies(self, 
                      conditions: Optional[List[str]] = None,
                      interventions: Optional[List[str]] = None,
                      sponsors: Optional[List[str]] = None,
                      terms: Optional[List[str]] = None,
                      nct_ids: Optional[List[str]] = None,
                      max_studies: int = 50,
                      fields: Optional[List[str]] = None,
                      format_type: str = "json") -> Dict[str, Any]:
        """Search clinical trials with multiple filters"""
        
        params = {
            "format": format_type,
            "pageSize": min(max_studies, 1000)
        }
        
        if conditions:
            params["query.cond"] = " OR ".join(conditions)
        
        if interventions:
            params["query.intr"] = " OR ".join(interventions)
            
        if sponsors:
            params["query.spons"] = " OR ".join(sponsors)
            
        if terms:
            params["query.term"] = " OR ".join(terms)
            
        if nct_ids:
            params["filter.ids"] = nct_ids
            
        if fields:
            params["fields"] = ",".join(fields)
        
        return self._make_request("/studies", params)
    
    def get_study_by_id(self, nct_id: str, 
                       fields: Optional[List[str]] = None,
                       format_type: str = "json") -> Dict[str, Any]:
        """Get detailed information for a single study"""
        
        params = {"format": format_type}
        
        if fields:
            params["fields"] = ",".join(fields)
            
        return self._make_request(f"/studies/{nct_id}", params)
    
    def get_field_statistics(self, 
                           field_names: Optional[List[str]] = None,
                           field_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get field value statistics"""
        
        params = {}
        
        if field_names:
            params["fields"] = field_names
            
        if field_types:
            params["types"] = field_types
            
        return self._make_request("/stats/field/values", params)


# Initialize the MCP server
server = Server("clinical-trials-server")
api_client = ClinicalTrialsAPI()


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="search_trials_by_condition",
            description="Search clinical trials by medical condition(s)",
            inputSchema={
                "type": "object",
                "properties": {
                    "conditions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Medical conditions to search for"
                    },
                    "max_studies": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum number of studies to return"
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific fields to return"
                    }
                },
                "required": ["conditions"]
            }
        ),
        Tool(
            name="search_trials_by_intervention",
            description="Search clinical trials by intervention/treatment",
            inputSchema={
                "type": "object",
                "properties": {
                    "interventions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Interventions/treatments to search for"
                    },
                    "max_studies": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum number of studies to return"
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific fields to return"
                    }
                },
                "required": ["interventions"]
            }
        ),
        Tool(
            name="search_trials_by_sponsor",
            description="Search clinical trials by sponsor/organization",
            inputSchema={
                "type": "object",
                "properties": {
                    "sponsors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Sponsor organizations to search for"
                    },
                    "max_studies": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum number of studies to return"
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific fields to return"
                    }
                },
                "required": ["sponsors"]
            }
        ),
        Tool(
            name="search_trials_by_nct_ids",
            description="Retrieve specific clinical trials by NCT ID(s)",
            inputSchema={
                "type": "object",
                "properties": {
                    "nct_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "NCT IDs to retrieve"
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific fields to return"
                    }
                },
                "required": ["nct_ids"]
            }
        ),
        Tool(
            name="search_trials_combined",
            description="Search clinical trials using multiple criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "conditions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Medical conditions to search for"
                    },
                    "interventions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Interventions/treatments to search for"
                    },
                    "sponsors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Sponsor organizations to search for"
                    },
                    "terms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "General search terms"
                    },
                    "nct_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific NCT IDs to include"
                    },
                    "max_studies": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum number of studies to return"
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific fields to return"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_trial_details",
            description="Get comprehensive details for a single clinical trial",
            inputSchema={
                "type": "object",
                "properties": {
                    "nct_id": {
                        "type": "string",
                        "description": "NCT ID of the trial to retrieve"
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific fields to return"
                    }
                },
                "required": ["nct_id"]
            }
        ),
        Tool(
            name="analyze_trial_phases",
            description="Analyze the distribution of trial phases for given search criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "conditions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Medical conditions to analyze"
                    },
                    "interventions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Interventions to analyze"
                    },
                    "sponsors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Sponsors to analyze"
                    },
                    "max_studies": {
                        "type": "integer",
                        "default": 1000,
                        "description": "Maximum number of studies to analyze"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_field_statistics",
            description="Get statistical information about field values",
            inputSchema={
                "type": "object",
                "properties": {
                    "field_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Field names to get statistics for"
                    },
                    "field_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Field types to filter by (ENUM, STRING, DATE, INTEGER, NUMBER, BOOLEAN)"
                    }
                },
                "required": []
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls"""
    
    try:
        if name == "search_trials_by_condition":
            result = api_client.search_studies(
                conditions=arguments["conditions"],
                max_studies=arguments.get("max_studies", 50),
                fields=arguments.get("fields")
            )
            
        elif name == "search_trials_by_intervention":
            result = api_client.search_studies(
                interventions=arguments["interventions"],
                max_studies=arguments.get("max_studies", 50),
                fields=arguments.get("fields")
            )
            
        elif name == "search_trials_by_sponsor":
            result = api_client.search_studies(
                sponsors=arguments["sponsors"],
                max_studies=arguments.get("max_studies", 50),
                fields=arguments.get("fields")
            )
            
        elif name == "search_trials_by_nct_ids":
            result = api_client.search_studies(
                nct_ids=arguments["nct_ids"],
                fields=arguments.get("fields")
            )
            
        elif name == "search_trials_combined":
            result = api_client.search_studies(
                conditions=arguments.get("conditions"),
                interventions=arguments.get("interventions"),
                sponsors=arguments.get("sponsors"),
                terms=arguments.get("terms"),
                nct_ids=arguments.get("nct_ids"),
                max_studies=arguments.get("max_studies", 50),
                fields=arguments.get("fields")
            )
            
        elif name == "get_trial_details":
            result = api_client.get_study_by_id(
                nct_id=arguments["nct_id"],
                fields=arguments.get("fields")
            )
            
        elif name == "analyze_trial_phases":
            # Get studies with phase information
            search_result = api_client.search_studies(
                conditions=arguments.get("conditions"),
                interventions=arguments.get("interventions"),
                sponsors=arguments.get("sponsors"),
                max_studies=arguments.get("max_studies", 1000),
                fields=["NCTId", "Phase", "BriefTitle", "OverallStatus"]
            )
            
            # Analyze phases
            phase_counts = {}
            total_studies = len(search_result.get("studies", []))
            
            for study in search_result.get("studies", []):
                protocol_section = study.get("protocolSection", {})
                design_module = protocol_section.get("designModule", {})
                phases = design_module.get("phases", ["Unknown"])
                
                for phase in phases:
                    phase_counts[phase] = phase_counts.get(phase, 0) + 1
            
            result = {
                "total_studies": total_studies,
                "phase_distribution": phase_counts,
                "phase_percentages": {
                    phase: round((count / total_studies) * 100, 2) if total_studies > 0 else 0
                    for phase, count in phase_counts.items()
                }
            }
            
        elif name == "get_field_statistics":
            result = api_client.get_field_statistics(
                field_names=arguments.get("field_names"),
                field_types=arguments.get("field_types")
            )
            
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
        
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="clinical-trials-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None
                )
            )
        )


def cli_main():
    """CLI entry point for the server"""
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down Clinical Trials MCP Server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()