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
    ServerCapabilities,
    ToolsCapability,
)
from pydantic import BaseModel, Field

# Default fields to reduce context size while maintaining key information
DEFAULT_STUDY_FIELDS = [
    "NCTId", "EligibilityCriteria", "PrimaryCompletionDate",
    "ArmGroupLabel", "ArmGroupType", "ArmGroupDescription",
    "Condition", "Keyword", "OfficialTitle", "BriefTitle", "Phase",
    "PrimaryOutcomeMeasure", "SecondaryOutcomeMeasure",
    "InterventionType", "InterventionName", "InterventionDescription",
    "InterventionOtherName", "BriefSummary", "DetailedDescription",
    "LocationFacility", "LeadSponsorName", "CollaboratorName", 
    "Acronym", "LastUpdatePostDate"
]

# Lightweight fields for NCT ID discovery searches
MINIMAL_STUDY_FIELDS = ["NCTId", "BriefTitle", "OverallStatus"]

# Organized field categories for user selection
AVAILABLE_FIELD_CATEGORIES = {
    "identification": {
        "description": "Basic trial identification and titles",
        "fields": ["NCTId", "BriefTitle", "OfficialTitle", "Acronym", "SecondaryId"]
    },
    "status": {
        "description": "Trial status and timeline information", 
        "fields": ["OverallStatus", "StatusVerifiedDate", "LastUpdatePostDate", "StartDate", "PrimaryCompletionDate", "CompletionDate"]
    },
    "conditions": {
        "description": "Medical conditions and keywords",
        "fields": ["Condition", "Keyword"]
    },
    "design": {
        "description": "Study design and methodology",
        "fields": ["StudyType", "Phase", "DesignAllocation", "DesignInterventionModel", "DesignPrimaryPurpose", "DesignMasking"]
    },
    "interventions": {
        "description": "Treatments and interventions being studied",
        "fields": ["InterventionType", "InterventionName", "InterventionDescription", "InterventionOtherName"]
    },
    "arms": {
        "description": "Study arm and group information",
        "fields": ["ArmGroupLabel", "ArmGroupType", "ArmGroupDescription", "ArmGroupInterventionName"]
    },
    "outcomes": {
        "description": "Primary and secondary outcome measures",
        "fields": ["PrimaryOutcomeMeasure", "PrimaryOutcomeDescription", "SecondaryOutcomeMeasure", "SecondaryOutcomeDescription"]
    },
    "eligibility": {
        "description": "Patient eligibility and inclusion criteria",
        "fields": ["EligibilityCriteria", "HealthyVolunteers", "Sex", "MinimumAge", "MaximumAge", "StdAge"]
    },
    "locations": {
        "description": "Study locations and facilities",
        "fields": ["LocationFacility", "LocationCity", "LocationState", "LocationCountry", "LocationStatus"]
    },
    "sponsors": {
        "description": "Sponsoring organizations and collaborators",
        "fields": ["LeadSponsorName", "LeadSponsorClass", "CollaboratorName", "ResponsiblePartyType"]
    },
    "descriptions": {
        "description": "Detailed study descriptions and summaries",
        "fields": ["BriefSummary", "DetailedDescription"]
    },
    "contacts": {
        "description": "Study contact information",
        "fields": ["CentralContactName", "CentralContactPhone", "CentralContactEMail", "OverallOfficialName"]
    },
    "results": {
        "description": "Study results and publications",
        "fields": ["HasResults", "ResultsFirstSubmitDate", "ResultsFirstPostDate"]
    }
}


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
        ),
        Tool(
            name="get_available_fields",
            description="Get organized list of available fields for customizing search results",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional: specific category to return (identification, status, conditions, design, interventions, arms, outcomes, eligibility, locations, sponsors, descriptions, contacts, results)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="search_trials_nct_ids_only",
            description="Lightweight search returning only NCT IDs and minimal metadata for discovery",
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
                    "max_studies": {
                        "type": "integer",
                        "default": 100,
                        "description": "Maximum number of studies to return (optimized for discovery)"
                    }
                },
                "required": []
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Union[CallToolResult, Dict[str, Any]]:
    """Handle tool calls"""
    
    try:
        if name == "search_trials_by_condition":
            result = api_client.search_studies(
                conditions=arguments["conditions"],
                max_studies=arguments.get("max_studies", 50),
                fields=arguments.get("fields") or DEFAULT_STUDY_FIELDS
            )
            
        elif name == "search_trials_by_intervention":
            result = api_client.search_studies(
                interventions=arguments["interventions"],
                max_studies=arguments.get("max_studies", 50),
                fields=arguments.get("fields") or DEFAULT_STUDY_FIELDS
            )
            
        elif name == "search_trials_by_sponsor":
            result = api_client.search_studies(
                sponsors=arguments["sponsors"],
                max_studies=arguments.get("max_studies", 50),
                fields=arguments.get("fields") or DEFAULT_STUDY_FIELDS
            )
            
        elif name == "search_trials_by_nct_ids":
            result = api_client.search_studies(
                nct_ids=arguments["nct_ids"],
                fields=arguments.get("fields") or DEFAULT_STUDY_FIELDS
            )
            
        elif name == "search_trials_combined":
            result = api_client.search_studies(
                conditions=arguments.get("conditions"),
                interventions=arguments.get("interventions"),
                sponsors=arguments.get("sponsors"),
                terms=arguments.get("terms"),
                nct_ids=arguments.get("nct_ids"),
                max_studies=arguments.get("max_studies", 50),
                fields=arguments.get("fields") or DEFAULT_STUDY_FIELDS
            )
            
        elif name == "get_trial_details":
            result = api_client.get_study_by_id(
                nct_id=arguments["nct_id"],
                fields=arguments.get("fields")  # Keep as-is - this is for detailed retrieval
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
            
        elif name == "get_available_fields":
            category = arguments.get("category")
            if category and category in AVAILABLE_FIELD_CATEGORIES:
                result = {
                    "category": category,
                    "description": AVAILABLE_FIELD_CATEGORIES[category]["description"],
                    "fields": AVAILABLE_FIELD_CATEGORIES[category]["fields"]
                }
            else:
                result = {
                    "default_fields": DEFAULT_STUDY_FIELDS,
                    "minimal_fields": MINIMAL_STUDY_FIELDS,
                    "categories": AVAILABLE_FIELD_CATEGORIES
                }
                
        elif name == "search_trials_nct_ids_only":
            result = api_client.search_studies(
                conditions=arguments.get("conditions"),
                interventions=arguments.get("interventions"),
                sponsors=arguments.get("sponsors"),
                terms=arguments.get("terms"),
                max_studies=arguments.get("max_studies", 100),
                fields=MINIMAL_STUDY_FIELDS
            )
            
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Return plain dictionary - let MCP framework handle conversion
        return {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
            "isError": False
        }
        
    except Exception as e:
        # Return plain dictionary for error - let MCP framework handle conversion
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="clinical-trials-server",
                server_version="1.0.0",
                capabilities=ServerCapabilities(
                    tools=ToolsCapability(listChanged=False)
                )
            )
        )


def cli_main():
    """CLI entry point for the server"""
    import asyncio
    import traceback
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down Clinical Trials MCP Server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        print(f"Full traceback: {traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()