#!/usr/bin/env python3
"""
Clinical Trials FastMCP Server

Provides structured access to ClinicalTrials.gov data through MCP tools.
Allows LLMs to search, retrieve, and analyze clinical trial information.
"""

import os
import sys
from typing import Any, Dict, List, Optional

import requests
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field
from typing_extensions import Annotated
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

# Default fields collection (used when explicitly requested)
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

# Former minimal field set (kept for reference/tests)
SEARCH_RESULT_FIELDS = [
    "NCTId", "BriefTitle", "Acronym", "InterventionName",
    "Condition", "Phase", "LeadSponsorName", "CollaboratorName", "HasResults"
]

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
        self.session.headers.update({'User-Agent': 'ClinicalTrials-MCP-Server/1.0'})
    
    def parse_specific_fields(self, studies: List[Dict[str, Any]], requested_fields: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Parse and filter study data based on requested fields.
        
        Always receives full study data from API, then filters based on requested_fields.
        If requested_fields is None, returns all data as-is.
        
        Args:
            studies: List of full study records from API
            requested_fields: List of specific fields to extract, or None for all fields
            
        Returns:
            List of filtered study records
        """
        if not requested_fields:
            return studies
            
        # Normalize requested fields
        normalized_fields = self._normalize_fields(requested_fields)
        if not normalized_fields:
            return studies
            
        filtered_studies = []
        for study in studies:
            filtered_study = self._extract_fields_from_study(study, normalized_fields)
            filtered_studies.append(filtered_study)
            
        return filtered_studies
    
    def _extract_fields_from_study(self, study: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Extract specific fields from a full study record.
        
        Args:
            study: Full study record from API
            fields: List of normalized field names to extract
            
        Returns:
            Filtered study record containing only requested fields
        """
        result = {}
        
        # Always preserve hasResults at top level if present
        if "hasResults" in study:
            result["hasResults"] = study["hasResults"]
            
        protocol_section = study.get("protocolSection", {})
        if not protocol_section:
            return result
            
        result["protocolSection"] = {}
        
        # Field mapping to protocol section modules
        field_mappings = {
            # Identification Module
            "NCTId": ("identificationModule", "nctId"),
            "BriefTitle": ("identificationModule", "briefTitle"),
            "OfficialTitle": ("identificationModule", "officialTitle"),
            "Acronym": ("identificationModule", "acronym"),
            "SecondaryId": ("identificationModule", "secondaryIdInfos"),
            
            # Status Module  
            "OverallStatus": ("statusModule", "overallStatus"),
            "StatusVerifiedDate": ("statusModule", "statusVerifiedDate"),
            "LastUpdatePostDate": ("statusModule", "lastUpdatePostDateStruct"),
            "StartDate": ("statusModule", "startDateStruct"),
            "PrimaryCompletionDate": ("statusModule", "primaryCompletionDateStruct"),
            "CompletionDate": ("statusModule", "completionDateStruct"),
            
            # Conditions Module
            "Condition": ("conditionsModule", "conditions"),
            "Keyword": ("conditionsModule", "keywords"),
            
            # Design Module
            "StudyType": ("designModule", "studyType"),
            "Phase": ("designModule", "phases"),
            "DesignAllocation": ("designModule", "designInfo.allocation"),
            "DesignInterventionModel": ("designModule", "designInfo.interventionModel"),
            "DesignPrimaryPurpose": ("designModule", "designInfo.primaryPurpose"),
            "DesignMasking": ("designModule", "designInfo.maskingInfo.masking"),
            
            # Arms/Interventions Module
            "InterventionType": ("armsInterventionsModule", "interventions"),
            "InterventionName": ("armsInterventionsModule", "interventions"),
            "InterventionDescription": ("armsInterventionsModule", "interventions"),
            "InterventionOtherName": ("armsInterventionsModule", "interventions"),
            "ArmGroupLabel": ("armsInterventionsModule", "armGroups"),
            "ArmGroupType": ("armsInterventionsModule", "armGroups"),
            "ArmGroupDescription": ("armsInterventionsModule", "armGroups"),
            "ArmGroupInterventionName": ("armsInterventionsModule", "armGroups"),
            
            # Outcomes Module
            "PrimaryOutcomeMeasure": ("outcomesModule", "primaryOutcomes"),
            "PrimaryOutcomeDescription": ("outcomesModule", "primaryOutcomes"),
            "SecondaryOutcomeMeasure": ("outcomesModule", "secondaryOutcomes"),
            "SecondaryOutcomeDescription": ("outcomesModule", "secondaryOutcomes"),
            
            # Eligibility Module
            "EligibilityCriteria": ("eligibilityModule", "eligibilityCriteria"),
            "HealthyVolunteers": ("eligibilityModule", "healthyVolunteers"),
            "Sex": ("eligibilityModule", "sex"),
            "MinimumAge": ("eligibilityModule", "minimumAge"),
            "MaximumAge": ("eligibilityModule", "maximumAge"),
            "StdAge": ("eligibilityModule", "stdAges"),
            
            # Locations Module
            "LocationFacility": ("contactsLocationsModule", "locations"),
            "LocationCity": ("contactsLocationsModule", "locations"),
            "LocationState": ("contactsLocationsModule", "locations"),
            "LocationCountry": ("contactsLocationsModule", "locations"),
            "LocationStatus": ("contactsLocationsModule", "locations"),
            
            # Sponsors Module
            "LeadSponsorName": ("sponsorCollaboratorsModule", "leadSponsor"),
            "LeadSponsorClass": ("sponsorCollaboratorsModule", "leadSponsor"),
            "CollaboratorName": ("sponsorCollaboratorsModule", "collaborators"),
            "ResponsiblePartyType": ("sponsorCollaboratorsModule", "responsibleParty"),
            
            # Description Module
            "BriefSummary": ("descriptionModule", "briefSummary"),
            "DetailedDescription": ("descriptionModule", "detailedDescription"),
            
            # Contacts Module
            "CentralContactName": ("contactsLocationsModule", "centralContacts"),
            "CentralContactPhone": ("contactsLocationsModule", "centralContacts"),
            "CentralContactEMail": ("contactsLocationsModule", "centralContacts"),
            "OverallOfficialName": ("contactsLocationsModule", "overallOfficials"),
            
            # Results info
            "HasResults": ("hasResults", None),
            "ResultsFirstSubmitDate": ("statusModule", "resultsFirstSubmitDate"),
            "ResultsFirstPostDate": ("statusModule", "resultsFirstPostDateStruct"),
        }
        
        for field in fields:
            if field in field_mappings:
                module_name, field_path = field_mappings[field]
                
                # Handle hasResults specially (it's at study level, not in protocolSection)
                if field == "HasResults":
                    if "hasResults" in study:
                        result["hasResults"] = study["hasResults"]
                    continue
                    
                # Get the module from protocolSection
                module_data = protocol_section.get(module_name, {})
                if not module_data:
                    continue
                    
                # Ensure the module exists in result
                if module_name not in result["protocolSection"]:
                    result["protocolSection"][module_name] = {}
                    
                # Handle nested field paths (e.g., "designInfo.allocation")
                if "." in field_path:
                    self._extract_nested_field(module_data, field_path, result["protocolSection"][module_name])
                else:
                    # Direct field extraction
                    if field_path in module_data:
                        result["protocolSection"][module_name][field_path] = module_data[field_path]
                        
        return result
    
    def _extract_nested_field(self, source_data: Dict[str, Any], field_path: str, target_data: Dict[str, Any]) -> None:
        """Extract a nested field from source to target data.
        
        Args:
            source_data: Source module data
            field_path: Dot-separated field path (e.g., "designInfo.allocation")
            target_data: Target module data to populate
        """
        path_parts = field_path.split(".")
        current_source = source_data
        
        # Navigate to the parent of the target field
        for part in path_parts[:-1]:
            if part in current_source and isinstance(current_source[part], dict):
                current_source = current_source[part]
                # Create nested structure in target
                if part not in target_data:
                    target_data[part] = {}
                target_data = target_data[part]
            else:
                return  # Path doesn't exist
        
        # Extract the final field
        final_field = path_parts[-1]
        if final_field in current_source:
            target_data[final_field] = current_source[final_field]

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        try:
            resp = self.session.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")

    def _normalize_fields(self, fields: Optional[List[str]]) -> Optional[List[str]]:
        if not fields:
            return fields
        normalized: List[str] = []
        seen = set()
        for f in fields:
            if not isinstance(f, str):
                continue
            fl = f.strip()
            key = fl.lower()
            if key == "conditions":
                fl = "Condition"
            elif key in {"intervention", "interventions", "interventionname"}:
                fl = "InterventionName"
            elif key in {"phase", "phases"}:
                fl = "Phase"
            elif key in {"sponsor", "sponsors"}:
                for sp in ("LeadSponsorName", "CollaboratorName"):
                    if sp not in seen:
                        seen.add(sp)
                        normalized.append(sp)
                continue
            elif key in {"leadsponsor", "leadsponsorname"}:
                fl = "LeadSponsorName"
            elif key in {"collaborator", "collaborators", "collaboratorname"}:
                fl = "CollaboratorName"
            elif key in {"hasresults"}:
                fl = "HasResults"
            elif key in {"nctid"}:
                fl = "NCTId"
            elif key.replace(" ", "") == "brieftitle":
                fl = "BriefTitle"
            if fl not in seen:
                seen.add(fl)
                normalized.append(fl)
        return normalized

    def search_studies(self,
                       conditions: Optional[List[str]] = None,
                       interventions: Optional[List[str]] = None,
                       sponsors: Optional[List[str]] = None,
                       terms: Optional[List[str]] = None,
                       titles: Optional[List[str]] = None,
                       nct_ids: Optional[List[str]] = None,
                       max_studies: int = 50,
                       fields: Optional[List[str]] = None,
                       format_type: str = "json") -> Dict[str, Any]:
        # Always request all fields from API (don't pass fields parameter to API)
        params: Dict[str, Any] = {"format": format_type, "pageSize": min(max_studies, 1000)}
        if conditions:
            params["query.cond"] = " OR ".join(conditions)
        if interventions:
            params["query.intr"] = " OR ".join(interventions)
        if sponsors:
            params["query.spons"] = " OR ".join(sponsors)
        if terms:
            params["query.term"] = " OR ".join(terms)
        if titles:
            params["query.titles"] = " OR ".join(titles)
        if nct_ids:
            params["filter.ids"] = ",".join(nct_ids)
        
        # Get full data from API
        response = self._make_request("/studies", params)
        
        # Filter based on requested fields
        if "studies" in response and fields:
            response["studies"] = self.parse_specific_fields(response["studies"], fields)
            
        return response

    def get_study_by_id(self, nct_id: str, fields: Optional[List[str]] = None,
                         format_type: str = "json") -> Dict[str, Any]:
        # Always request all fields from API
        params: Dict[str, Any] = {"format": format_type}
        
        # Get full data from API
        response = self._make_request(f"/studies/{nct_id}", params)
        
        # Filter based on requested fields
        if fields:
            # For single study, wrap in list for filtering, then unwrap
            filtered_studies = self.parse_specific_fields([response], fields)
            if filtered_studies:
                response = filtered_studies[0]
                
        return response

    def get_field_statistics(self, field_names: Optional[List[str]] = None,
                             field_types: Optional[List[str]] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if field_names:
            params["fields"] = self._normalize_fields(field_names)
        if field_types:
            params["types"] = field_types
        return self._make_request("/stats/field/values", params)


# Initialize FastMCP server and API client
mcp = FastMCP("clinical-trials-server")
api_client = ClinicalTrialsAPI()


def _summarize_studies(studies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Map full study records to minimal, lowerCamelCase summaries per YAML schema.

    Keys returned per study:
      - nctId, briefTitle, acronym, interventions, conditions, phases, sponsors, hasResults
    """
    summarized: List[Dict[str, Any]] = []
    for study in studies or []:
        protocol = study.get("protocolSection", {}) or {}
        ident = protocol.get("identificationModule", {}) or {}
        arms = protocol.get("armsInterventionsModule", {}) or {}
        conds = protocol.get("conditionsModule", {}) or {}
        design = protocol.get("designModule", {}) or {}
        spons = protocol.get("sponsorCollaboratorsModule", {}) or {}

        nct_id = ident.get("nctId")
        brief_title = ident.get("briefTitle")
        acronym = ident.get("acronym")

        interventions = []
        for iv in (arms.get("interventions") or []):
            name = iv.get("name")
            if isinstance(name, str):
                interventions.append(name)

        conditions = [c for c in (conds.get("conditions") or []) if isinstance(c, str)]
        phases = [p for p in (design.get("phases") or []) if isinstance(p, str)]

        sponsors: List[str] = []
        lead = spons.get("leadSponsor") or {}
        if isinstance(lead, dict) and isinstance(lead.get("name"), str):
            sponsors.append(lead.get("name"))
        collabs = spons.get("collaborators") or []
        for c in collabs:
            if isinstance(c, dict) and isinstance(c.get("name"), str):
                sponsors.append(c.get("name"))

        summarized.append({
            "nctId": nct_id,
            "briefTitle": brief_title,
            "acronym": acronym,
            "interventions": interventions,
            "conditions": conditions,
            "phases": phases,
            "sponsors": sponsors,
            "hasResults": bool(study.get("hasResults"))
        })
    return summarized


@mcp.tool
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
      - `fields`: A list of specific fields to return in the results. If not provided, all fields will be returned.
    """
    try:
        # Always get full records from API, then filter
        result = api_client.search_studies(
            conditions=conditions,
            max_studies=max_studies,
            fields=fields
        )
        return result
    except Exception as e:
        raise ToolError(f"Error searching trials by condition: {str(e)}")


@mcp.tool
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
      - `fields`: A list of specific fields to return in the results. If not provided, all fields will be returned.
    """
    try:
        result = api_client.search_studies(
            interventions=interventions,
            max_studies=max_studies,
            fields=fields
        )
        return result
    except Exception as e:
        raise ToolError(f"Error searching trials by intervention: {str(e)}")


@mcp.tool
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
      - `fields`: A list of specific fields to return in the results. If not provided, all fields will be returned.
    """
    try:
        result = api_client.search_studies(
            sponsors=sponsors,
            max_studies=max_studies,
            fields=fields
        )
        return result
    except Exception as e:
        raise ToolError(f"Error searching trials by sponsor: {str(e)}")


@mcp.tool
def search_trials_by_acronym(
    acronyms: Annotated[List[str], Field(description="Trial acronyms to search for, e.g., ['TETON']")],
    max_studies: Annotated[int, Field(ge=1, le=1000, description="Maximum number of studies to return")] = 50,
    exact_match: Annotated[bool, Field(description="If true, match acronym exactly; if false, allow partial matches")]=True,
) -> Dict[str, Any]:
    """
    Search clinical trials by study acronym.

    Uses the Acronym field (protocolSection.identificationModule.acronym) to find
    trials by their public short name. Example: 'TETON'. The API search is seeded
    with the provided acronyms to narrow results, then results are filtered locally
    to ensure the acronym field matches the requested value(s).

    Input:
      - `acronyms`: One or more acronyms to search for (e.g., ['TETON']).
      - `max_studies`: Maximum number of studies to request from the API.
      - `exact_match`: When true (default), matches acronyms exactly (case-insensitive).
                       When false, matches if any provided acronym is contained within
                       the study acronym (case-insensitive partial match).
    """
    try:
        # Request full records; filter locally by acronym
        seed_result = api_client.search_studies(
            titles=acronyms,  # search in title/acronym area
            max_studies=max_studies,
            fields=None,
        )

        # Build case-insensitive acronym set for exact matching
        targets = {a.lower() for a in acronyms}
        filtered: List[Dict[str, Any]] = []

        for study in seed_result.get("studies", []):
            protocol = study.get("protocolSection", {}) or {}
            ident = protocol.get("identificationModule", {}) or {}
            acr = ident.get("acronym")

            if not isinstance(acr, str):
                continue

            acr_l = acr.lower()
            if exact_match:
                if acr_l in targets:
                    filtered.append(study)
            else:
                if any(t in acr_l for t in targets):
                    filtered.append(study)

        # Return filtered full studies
        return {"studies": filtered}
    except Exception as e:
        raise ToolError(f"Error searching trials by acronym: {str(e)}")


@mcp.tool
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
      - `fields`: A list of specific fields to return in the results. If not provided, all fields will be returned.
    """
    try:
        result = api_client.search_studies(
            nct_ids=nct_ids,
            fields=fields
        )
        return result
    except Exception as e:
        raise ToolError(f"Error retrieving trials by NCT IDs: {str(e)}")


@mcp.tool
def search_trials_combined(
    conditions: Annotated[Optional[List[str]], Field(description="Medical conditions to search for")] = None,
    interventions: Annotated[Optional[List[str]], Field(description="Interventions/treatments to search for")] = None,
    sponsors: Annotated[Optional[List[str]], Field(description="Sponsor organizations to search for")] = None,
    acronyms: Annotated[Optional[List[str]], Field(description="Study acronyms to search within titles/acronyms")] = None,
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
      - `fields`: A list of specific fields to return in the results. If not provided, all fields will be returned.
    """
    try:
        result = api_client.search_studies(
            conditions=conditions,
            interventions=interventions,
            sponsors=sponsors,
            terms=terms,
            titles=acronyms,
            nct_ids=nct_ids,
            max_studies=max_studies,
            fields=fields
        )
        return result
    except Exception as e:
        raise ToolError(f"Error in combined trial search: {str(e)}")


@mcp.tool
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
            fields=fields
        )
        return result
    except Exception as e:
        raise ToolError(f"Error retrieving trial details for {nct_id}: {str(e)}")


@mcp.tool
def get_trial_details_batched(
    nct_ids: Annotated[List[str], Field(description="NCT IDs to retrieve in batches of 10")],
    fields: Annotated[Optional[List[str]], Field(description="Specific fields to return for detailed view")] = None,
    batch_size: Annotated[int, Field(ge=1, le=1000, description="Batch size for each API call")] = 10,
) -> Dict[str, Any]:
    """
    Retrieve detailed clinical trial records in batches to reduce payload during discovery.

    - Accepts a list of NCT IDs and fetches details in batches (default 10).
    - Preserves the order of input NCT IDs in the returned list.
    - Use this after search tools which return a minimal field set.
    """
    try:
        # Prepare chunks
        def chunk(seq: List[str], n: int):
            for i in range(0, len(seq), n):
                yield seq[i:i+n]

        all_studies: Dict[str, Any] = {}

        for part in chunk(nct_ids, batch_size):
            page = api_client.search_studies(
                nct_ids=part,
                fields=fields,
                max_studies=len(part),
            )
            for study in page.get("studies", []):
                protocol = study.get("protocolSection", {}) or {}
                ident = protocol.get("identificationModule", {}) or {}
                nid = ident.get("nctId")
                if isinstance(nid, str):
                    all_studies[nid] = study

        # Preserve input order
        ordered = [all_studies[nid] for nid in nct_ids if nid in all_studies]
        return {"studies": ordered}
    except Exception as e:
        raise ToolError(f"Error retrieving batched trial details: {str(e)}")


@mcp.tool
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


@mcp.tool
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


@mcp.tool
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
                "minimal_fields": SEARCH_RESULT_FIELDS,
                "categories": AVAILABLE_FIELD_CATEGORIES
            }
        return result
    except Exception as e:
        raise ToolError(f"Error retrieving available fields: {str(e)}")


@mcp.tool
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
            fields=SEARCH_RESULT_FIELDS
        )
        return {"studies": _summarize_studies(result.get("studies", []))}
    except Exception as e:
        raise ToolError(f"Error in lightweight NCT ID search: {str(e)}")


def _detect_transport() -> str:
    """Detect transport automatically, with env override.

    Priority:
    1) MCP_TRANSPORT env var if set to 'stdio' or 'http'
    2) If stdin is not a TTY (likely launched by an MCP host), use 'stdio'
    3) If PORT env var is set, prefer 'http'
    4) Default to 'http'
    """
    forced = os.environ.get("MCP_TRANSPORT", "").strip().lower()
    if forced in {"stdio", "http"}:
        return forced

    # If we're launched under a host that pipes stdio, stdin won't be a TTY
    try:
        if hasattr(sys.stdin, "isatty") and not sys.stdin.isatty():
            return "stdio"
    except Exception:
        pass

    if os.environ.get("PORT"):
        return "http"
    return "http"


def _run_http():
    """Start server in HTTP mode with CORS (Smithery-compatible)."""
    print("Clinical Trials MCP Server starting in HTTP mode...")

    # Create HTTP app from FastMCP (streaming supported by FastMCP >=2.3)
    app = mcp.http_app()

    # Enable permissive CORS for browser-based clients and Smithery
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["mcp-session-id", "mcp-protocol-version"],
        max_age=86400,
    )

    # Simple health endpoint for local testing
    async def health(_request):
        return JSONResponse({"status": "ok"})

    try:
        app.add_route("/healthz", health, methods=["GET"])  # type: ignore[attr-defined]
    except Exception:
        # Some Starlette app versions may only support add_api_route
        app.add_api_route("/healthz", health, methods=["GET"])  # type: ignore[attr-defined]

    # Respect Smithery PORT env var (defaults to 8081)
    port = int(os.environ.get("PORT", 8081))
    print(f"Listening on port {port}")

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")


def _run_stdio():
    """Start server in stdio mode for MCP hosts like Cline/Claude Code."""
    print("Clinical Trials MCP Server starting in STDIO mode...")
    # FastMCP's stdio runner
    mcp.run()


def main():
    transport = _detect_transport()
    if transport == "stdio":
        _run_stdio()
    else:
        _run_http()


if __name__ == "__main__":
    main()