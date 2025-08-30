#!/usr/bin/env python3
"""
Clinical Trials FastMCP Server

Provides structured access to ClinicalTrials.gov data through MCP tools.
Allows LLMs to search, retrieve, and analyze clinical trial information.
"""

import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests
import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import Field
from starlette.middleware.cors import CORSMiddleware
from typing_extensions import Annotated

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


# Initialize FastMCP server and API client
mcp = FastMCP("clinical-trials-server")
api_client = ClinicalTrialsAPI()


@mcp.tool()
def search_trials_by_condition(
    conditions: Annotated[List[str], Field(description="Medical conditions to search for")],
    max_studies: Annotated[int, Field(ge=1, le=1000, description="Maximum number of studies to return")] = 50,
    fields: Annotated[Optional[List[str]], Field(description="Specific fields to return")] = None
) -> Dict[str, Any]:
    """
    Search clinical trials by medical condition(s).

    This tool allows you to search for clinical trials based on a list of medical conditions.
    
    Input:
      - `conditions`: A list of strings, where each string is a medical condition to search for. 
                      The search will find trials related to any of the specified conditions.
                      Example: `['cancer', 'diabetes']`
      - `max_studies`: The maximum number of studies to return. Defaults to 50.
      - `fields`: A list of specific fields to return in the results. If not provided, a default set of fields will be returned.
    """
    try:
        result = api_client.search_studies(
            conditions=conditions,
            max_studies=max_studies,
            fields=fields or DEFAULT_STUDY_FIELDS
        )
        return result
    except Exception as e:
        raise ToolError(f"Error searching trials by condition: {str(e)}")


@mcp.tool()
def search_trials_by_intervention(
    interventions: Annotated[List[str], Field(description="Interventions/treatments to search for")],
    max_studies: Annotated[int, Field(ge=1, le=1000, description="Maximum number of studies to return")] = 50,
    fields: Annotated[Optional[List[str]], Field(description="Specific fields to return")] = None
) -> Dict[str, Any]:
    """
    Search clinical trials by intervention/treatment.

    This tool allows you to search for clinical trials based on a list of interventions or treatments.

    Input:
      - `interventions`: A list of strings, where each string is an intervention or treatment to search for.
                         The search will find trials related to any of the specified interventions.
                         Example: `['aspirin', 'chemotherapy']`
      - `max_studies`: The maximum number of studies to return. Defaults to 50.
      - `fields`: A list of specific fields to return in the results. If not provided, a default set of fields will be returned.
    """
    try:
        result = api_client.search_studies(
            interventions=interventions,
            max_studies=max_studies,
            fields=fields or DEFAULT_STUDY_FIELDS
        )
        return result
    except Exception as e:
        raise ToolError(f"Error searching trials by intervention: {str(e)}")


@mcp.tool()
def search_trials_by_sponsor(
    sponsors: Annotated[List[str], Field(description="Sponsor organizations to search for")],
    max_studies: Annotated[int, Field(ge=1, le=1000, description="Maximum number of studies to return")] = 50,
    fields: Annotated[Optional[List[str]], Field(description="Specific fields to return")] = None
) -> Dict[str, Any]:
    """
    Search clinical trials by sponsor/organization.

    This tool allows you to search for clinical trials based on a list of sponsor organizations.

    Input:
      - `sponsors`: A list of strings, where each string is a sponsor organization to search for.
                    The search will find trials sponsored by any of the specified organizations.
                    Example: `['National Cancer Institute', 'Pfizer']`
      - `max_studies`: The maximum number of studies to return. Defaults to 50.
      - `fields`: A list of specific fields to return in the results. If not provided, a default set of fields will be returned.
    """
    try:
        result = api_client.search_studies(
            sponsors=sponsors,
            max_studies=max_studies,
            fields=fields or DEFAULT_STUDY_FIELDS
        )
        return result
    except Exception as e:
        raise ToolError(f"Error searching trials by sponsor: {str(e)}")


@mcp.tool()
def search_trials_by_nct_ids(
    nct_ids: Annotated[List[str], Field(description="NCT IDs to retrieve")],
    fields: Annotated[Optional[List[str]], Field(description="Specific fields to return")] = None
) -> Dict[str, Any]:
    """
    Retrieve specific clinical trials by NCT ID(s).

    This tool allows you to retrieve the details of specific clinical trials by providing their NCT IDs.

    Input:
      - `nct_ids`: A list of strings, where each string is an NCT ID to retrieve.
                   Example: `['NCT04280705', 'NCT04280718']`
      - `fields`: A list of specific fields to return in the results. If not provided, a default set of fields will be returned.
    """
    try:
        result = api_client.search_studies(
            nct_ids=nct_ids,
            fields=fields or DEFAULT_STUDY_FIELDS
        )
        return result
    except Exception as e:
        raise ToolError(f"Error retrieving trials by NCT IDs: {str(e)}")


@mcp.tool()
def search_trials_combined(
    conditions: Annotated[Optional[List[str]], Field(description="Medical conditions to search for")] = None,
    interventions: Annotated[Optional[List[str]], Field(description="Interventions/treatments to search for")] = None,
    sponsors: Annotated[Optional[List[str]], Field(description="Sponsor organizations to search for")] = None,
    terms: Annotated[Optional[List[str]], Field(description="General search terms")] = None,
    nct_ids: Annotated[Optional[List[str]], Field(description="Specific NCT IDs to include")] = None,
    max_studies: Annotated[int, Field(ge=1, le=1000, description="Maximum number of studies to return")] = 50,
    fields: Annotated[Optional[List[str]], Field(description="Specific fields to return")] = None
) -> Dict[str, Any]:
    """
    Search clinical trials using multiple criteria.

    This tool allows you to perform a combined search using multiple criteria such as conditions, interventions, sponsors, and general terms.

    Input:
      - `conditions`: A list of medical conditions to search for.
      - `interventions`: A list of interventions or treatments to search for.
      - `sponsors`: A list of sponsor organizations to search for.
      - `terms`: A list of general search terms.
      - `nct_ids`: A list of specific NCT IDs to include in the search.
      - `max_studies`: The maximum number of studies to return. Defaults to 50.
      - `fields`: A list of specific fields to return in the results. If not provided, a default set of fields will be returned.
    """
    try:
        result = api_client.search_studies(
            conditions=conditions,
            interventions=interventions,
            sponsors=sponsors,
            terms=terms,
            nct_ids=nct_ids,
            max_studies=max_studies,
            fields=fields or DEFAULT_STUDY_FIELDS
        )
        return result
    except Exception as e:
        raise ToolError(f"Error in combined trial search: {str(e)}")


@mcp.tool()
def get_trial_details(
    nct_id: Annotated[str, Field(description="NCT ID of the trial to retrieve")],
    fields: Annotated[Optional[List[str]], Field(description="Specific fields to return")] = None
) -> Dict[str, Any]:
    """
    Get comprehensive details for a single clinical trial.

    This tool retrieves detailed information for a single clinical trial given its NCT ID.

    Input:
      - `nct_id`: The NCT ID of the trial to retrieve.
                  Example: `'NCT04280705'`
      - `fields`: A list of specific fields to return. If not provided, all available fields will be returned.
    """
    try:
        result = api_client.get_study_by_id(
            nct_id=nct_id,
            fields=fields  # Keep as-is - this is for detailed retrieval
        )
        return result
    except Exception as e:
        raise ToolError(f"Error retrieving trial details for {nct_id}: {str(e)}")


@mcp.tool()
def analyze_trial_phases(
    conditions: Annotated[Optional[List[str]], Field(description="Medical conditions to analyze")] = None,
    interventions: Annotated[Optional[List[str]], Field(description="Interventions to analyze")] = None,
    sponsors: Annotated[Optional[List[str]], Field(description="Sponsors to analyze")] = None,
    max_studies: Annotated[int, Field(ge=1, le=1000, description="Maximum number of studies to analyze")] = 1000
) -> Dict[str, Any]:
    """
    Analyze the distribution of trial phases for given search criteria.

    This tool analyzes the distribution of clinical trial phases (e.g., Phase 1, Phase 2, Phase 3) 
    for a given set of search criteria.

    Input:
      - `conditions`: A list of medical conditions to filter the analysis.
      - `interventions`: A list of interventions to filter the analysis.
      - `sponsors`: A list of sponsors to filter the analysis.
      - `max_studies`: The maximum number of studies to include in the analysis. Defaults to 1000.
    """
    try:
        # Get studies with phase information
        search_result = api_client.search_studies(
            conditions=conditions,
            interventions=interventions,
            sponsors=sponsors,
            max_studies=max_studies,
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
        return result
    except Exception as e:
        raise ToolError(f"Error analyzing trial phases: {str(e)}")


@mcp.tool()
def get_field_statistics(
    field_names: Annotated[Optional[List[str]], Field(description="Field names to get statistics for")] = None,
    field_types: Annotated[Optional[List[str]], Field(description="Field types to filter by (ENUM, STRING, DATE, INTEGER, NUMBER, BOOLEAN)")] = None
) -> Dict[str, Any]:
    """
    Get statistical information about field values.

    This tool retrieves statistical information about the values of specified fields in the ClinicalTrials.gov database.

    Input:
      - `field_names`: A list of field names to get statistics for.
      - `field_types`: A list of field types to filter by.
                       Example: `['ENUM', 'STRING']`
    """
    try:
        result = api_client.get_field_statistics(
            field_names=field_names,
            field_types=field_types
        )
        return result
    except Exception as e:
        raise ToolError(f"Error retrieving field statistics: {str(e)}")


@mcp.tool()
def get_available_fields(
    category: Annotated[Optional[str], Field(description="Optional: specific category to return (identification, status, conditions, design, interventions, arms, outcomes, eligibility, locations, sponsors, descriptions, contacts, results)")] = None
) -> Dict[str, Any]:
    """
    Get organized list of available fields for customizing search results.

    This tool provides a list of available fields that can be used to customize the results of other search tools.
    The fields are organized into categories.

    Input:
      - `category`: An optional string to specify a category of fields to return.
                    If not provided, all categories and default fields will be returned.
                    Example: `'conditions'`
    """
    try:
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
        return result
    except Exception as e:
        raise ToolError(f"Error retrieving available fields: {str(e)}")


@mcp.tool()
def search_trials_nct_ids_only(
    conditions: Annotated[Optional[List[str]], Field(description="Medical conditions to search for")] = None,
    interventions: Annotated[Optional[List[str]], Field(description="Interventions/treatments to search for")] = None,
    sponsors: Annotated[Optional[List[str]], Field(description="Sponsor organizations to search for")] = None,
    terms: Annotated[Optional[List[str]], Field(description="General search terms")] = None,
    max_studies: Annotated[int, Field(ge=1, le=1000, description="Maximum number of studies to return (optimized for discovery)")] = 100
) -> Dict[str, Any]:
    """
    Lightweight search returning only NCT IDs and minimal metadata for discovery.

    This tool performs a lightweight search that returns only the NCT IDs and minimal metadata 
    for the purpose of discovering relevant trials.

    Input:
      - `conditions`: A list of medical conditions to search for.
      - `interventions`: A list of interventions or treatments to search for.
      - `sponsors`: A list of sponsor organizations to search for.
      - `terms`: A list of general search terms.
      - `max_studies`: The maximum number of studies to return. Defaults to 100.
    """
    try:
        result = api_client.search_studies(
            conditions=conditions,
            interventions=interventions,
            sponsors=sponsors,
            terms=terms,
            max_studies=max_studies,
            fields=MINIMAL_STUDY_FIELDS
        )
        return result
    except Exception as e:
        raise ToolError(f"Error in lightweight NCT ID search: {str(e)}")


def main():
    """Entry point supporting both HTTP and STDIO transports."""
    transport_mode = os.getenv("TRANSPORT", "stdio")

    if transport_mode == "http":
        print("Clinical Trials MCP Server starting in HTTP mode...")
        app = mcp.streamable_http_app()
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["mcp-session-id", "mcp-protocol-version"],
            max_age=86400,
        )

        port = int(os.environ.get("PORT", 8081))
        print(f"Listening on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")
    else:
        print("Clinical Trials MCP Server starting in stdio mode...")
        mcp.run()


def cli_main():
    main()


if __name__ == "__main__":
    main()
