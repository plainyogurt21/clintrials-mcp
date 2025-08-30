# Clinical Trials MCP Server

An MCP (Model Context Protocol) server that provides structured access to ClinicalTrials.gov data, allowing LLMs to search, retrieve, and analyze clinical trial information.

## Features

- **Multi-parameter Search**: Search trials by condition, intervention, sponsor, NCT ID, or combination
- **Detailed Retrieval**: Get comprehensive trial details including results, eligibility, outcomes
- **Statistical Analysis**: Analyze trial phases, field statistics, and data distributions
- **Flexible Field Selection**: Request specific data fields to optimize responses
- **Error Handling**: Robust error handling with meaningful error messages

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the MCP server:
```bash
python mcp_server.py
```

## Available Tools

### Search Tools

#### `search_trials_by_condition`
Search clinical trials by medical condition(s).

**Parameters:**
- `conditions` (required): Array of medical conditions to search for
- `max_studies` (optional): Maximum number of studies to return (default: 50)
- `fields` (optional): Specific fields to return

**Example:**
```json
{
  "conditions": ["lung cancer", "breast cancer"],
  "max_studies": 100,
  "fields": ["NCTId", "BriefTitle", "OverallStatus", "Phase"]
}
```

#### `search_trials_by_intervention`
Search clinical trials by intervention/treatment.

**Parameters:**
- `interventions` (required): Array of interventions/treatments to search for
- `max_studies` (optional): Maximum number of studies to return (default: 50)
- `fields` (optional): Specific fields to return

**Example:**
```json
{
  "interventions": ["pembrolizumab", "immunotherapy"],
  "max_studies": 50
}
```

#### `search_trials_by_sponsor`
Search clinical trials by sponsor/organization.

**Parameters:**
- `sponsors` (required): Array of sponsor organizations to search for
- `max_studies` (optional): Maximum number of studies to return (default: 50)
- `fields` (optional): Specific fields to return

**Example:**
```json
{
  "sponsors": ["Pfizer", "Novartis"],
  "max_studies": 75
}
```

#### `search_trials_by_nct_ids`
Retrieve specific clinical trials by NCT ID(s).

**Parameters:**
- `nct_ids` (required): Array of NCT IDs to retrieve
- `fields` (optional): Specific fields to return

**Example:**
```json
{
  "nct_ids": ["NCT04852770", "NCT01728545"],
  "fields": ["NCTId", "BriefTitle", "DetailedDescription"]
}
```

#### `search_trials_combined`
Search clinical trials using multiple criteria.

**Parameters:**
- `conditions` (optional): Array of medical conditions
- `interventions` (optional): Array of interventions/treatments
- `sponsors` (optional): Array of sponsor organizations
- `terms` (optional): Array of general search terms
- `nct_ids` (optional): Array of specific NCT IDs to include
- `max_studies` (optional): Maximum number of studies to return (default: 50)
- `fields` (optional): Specific fields to return

**Example:**
```json
{
  "conditions": ["diabetes"],
  "interventions": ["insulin"],
  "sponsors": ["Novo Nordisk"],
  "max_studies": 100
}
```

### Detailed Retrieval Tools

#### `get_trial_details`
Get comprehensive details for a single clinical trial.

**Parameters:**
- `nct_id` (required): NCT ID of the trial to retrieve
- `fields` (optional): Specific fields to return

**Example:**
```json
{
  "nct_id": "NCT04852770",
  "fields": ["ProtocolSection", "ResultsSection"]
}
```

### Analysis Tools

#### `analyze_trial_phases`
Analyze the distribution of trial phases for given search criteria.

**Parameters:**
- `conditions` (optional): Array of medical conditions to analyze
- `interventions` (optional): Array of interventions to analyze
- `sponsors` (optional): Array of sponsors to analyze
- `max_studies` (optional): Maximum number of studies to analyze (default: 1000)

**Example:**
```json
{
  "conditions": ["cancer"],
  "max_studies": 500
}
```

#### `get_field_statistics`
Get statistical information about field values.

**Parameters:**
- `field_names` (optional): Array of field names to get statistics for
- `field_types` (optional): Array of field types to filter by (ENUM, STRING, DATE, INTEGER, NUMBER, BOOLEAN)

**Example:**
```json
{
  "field_names": ["Phase", "OverallStatus"],
  "field_types": ["ENUM"]
}
```

## Common Field Names

Here are some commonly used field names you can specify in the `fields` parameter:

### Basic Information
- `NCTId` - Clinical trial identifier
- `BriefTitle` - Short title of the study
- `OfficialTitle` - Full official title
- `Acronym` - Study acronym
- `OverallStatus` - Current status (e.g., RECRUITING, COMPLETED)

### Study Design
- `Phase` - Study phases (e.g., PHASE1, PHASE2, PHASE3)
- `StudyType` - Type of study (INTERVENTIONAL, OBSERVATIONAL)
- `PrimaryPurpose` - Main purpose (TREATMENT, PREVENTION, etc.)
- `InterventionModel` - Study design model

### Participants
- `Condition` - Medical conditions studied
- `EligibilityCriteria` - Inclusion/exclusion criteria
- `HealthyVolunteers` - Whether healthy volunteers are accepted
- `Sex` - Participant sex (MALE, FEMALE, ALL)
- `MinimumAge` - Minimum age for participation
- `MaximumAge` - Maximum age for participation

### Interventions
- `InterventionName` - Names of interventions
- `InterventionType` - Types of interventions (DRUG, DEVICE, etc.)
- `InterventionDescription` - Detailed intervention descriptions

### Outcomes
- `PrimaryOutcome` - Primary endpoint measures
- `SecondaryOutcome` - Secondary endpoint measures
- `OtherOutcome` - Other outcome measures

### Administrative
- `LeadSponsorName` - Name of the lead sponsor
- `Collaborator` - Collaborating organizations
- `StartDate` - Study start date
- `CompletionDate` - Study completion date
- `LastUpdatePostDate` - Last update date

### Results
- `HasResults` - Whether results are available
- `ResultsFirstPostDate` - Date results were first posted

## Usage Examples

### Search for COVID-19 vaccine trials:
```json
{
  "tool": "search_trials_by_condition",
  "arguments": {
    "conditions": ["COVID-19"],
    "interventions": ["vaccine"],
    "max_studies": 50
  }
}
```

### Get detailed information about a specific trial:
```json
{
  "tool": "get_trial_details",
  "arguments": {
    "nct_id": "NCT04368728"
  }
}
```

### Analyze cancer trial phases by pharmaceutical companies:
```json
{
  "tool": "analyze_trial_phases",
  "arguments": {
    "conditions": ["cancer"],
    "sponsors": ["Pfizer", "Merck", "Bristol-Myers Squibb"],
    "max_studies": 1000
  }
}
```

### Search for trials with multiple criteria:
```json
{
  "tool": "search_trials_combined",
  "arguments": {
    "conditions": ["Alzheimer's disease"],
    "interventions": ["monoclonal antibody"],
    "max_studies": 100,
    "fields": ["NCTId", "BriefTitle", "Phase", "OverallStatus", "LeadSponsorName"]
  }
}
```

## API Integration

This server integrates with the ClinicalTrials.gov API v2:
- Base URL: `https://clinicaltrials.gov/api/v2`
- Uses proper error handling and retry logic
- Supports all major search parameters and filters
- Handles pagination automatically
- Respects API rate limits

## Error Handling

The server includes comprehensive error handling:
- API request failures are caught and reported
- Invalid parameters are validated
- Network issues are handled gracefully
- Meaningful error messages are returned to the client

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## HTTP Server Usage (Local)

The server runs in HTTP mode by default and is compatible with Claude Code, Smithery, and other MCP desktop servers that support Streamable HTTP.

- Install: `pip install -r requirements.txt`
- Run: `PORT=8081 python mcp_server.py`
- Health check: `curl -s http://localhost:8081/healthz` → `{ "status": "ok" }`

### Docker

- Build: `docker build -t clinical-trials-mcp .`
- Run: `docker run -p 8081:8081 -e PORT=8081 clinical-trials-mcp`

### CORS Preflight Test

```
curl -i -X OPTIONS \
  -H 'Origin: http://localhost:3000' \
  -H 'Access-Control-Request-Method: POST' \
  http://localhost:8081/
```

You should see `HTTP/1.1 200 OK` and permissive `access-control-allow-*` headers.

### Smithery

This repo includes a `Dockerfile` and `smithery.yaml` configured for container runtime with HTTP transport. Deploy via https://smithery.ai/new and ensure the app listens on the `PORT` environment variable (Smithery sets it to 8081).
