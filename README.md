# Clinical Trials MCP Server

An MCP (Model Context Protocol) server that provides structured access to ClinicalTrials.gov data, allowing LLMs to search, retrieve, and analyze clinical trial information.

## Features

- **Multi-parameter Search**: Search trials by condition, intervention, sponsor, NCT ID, or combination
- **Detailed Retrieval**: Get comprehensive trial details including results, eligibility, outcomes
- **Statistical Analysis**: Analyze trial phases, field statistics, and data distributions
- **Flexible Field Selection**: Request specific data fields to optimize responses
- **Error Handling**: Robust error handling with meaningful error messages

## Installation

1. Install dependencies (Python runtime is required):
```bash
pip install -r requirements.txt
```

> **Note:** JavaScript package managers like `npm`, `pnpm`, or `bun` are not required for this project because all runtime dependencies are Python packages managed through `requirements.txt`.

2. Run the MCP server:
```bash
python mcp_server.py
```

## Deployment Options

### Option 1: AWS Lambda + Function URL (Recommended - FREE & Fastest)

**Cost:** FREE for first 1M requests/month, then $0.20 per 1M requests
**Setup time:** 2 minutes

1. **Install AWS CLI and configure credentials:**
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Key, and region
   ```

2. **Deploy to Lambda:**
   ```bash
   ./deploy-lambda.sh
   # Takes ~60 seconds, automatically creates function + public URL
   ```

3. **Copy the Function URL and configure Cloudflare:**
   ```bash
   npx wrangler secret put BACKEND_URL
   # Paste your Lambda Function URL when prompted
   ```

4. **Deploy Cloudflare Worker:**
   ```bash
   npx wrangler deploy
   ```

Your MCP server will be available at: `https://<worker-name>.workers.dev/sse`

**Pros:** Completely free tier, auto-scales, no server management
**Cons:** Cold starts (~1-2s first request after idle)

### Option 2: AWS App Runner (Always-on, Low Cost)

**Cost:** ~$5/month for 1 vCPU + 2GB RAM (pay per use)
**Setup time:** 5 minutes

Use this if you need consistent performance without cold starts.

See `deploy-apprunner.sh` for instructions or deploy via AWS Console.

### Option 3: Railway (Easiest, No AWS Required)

**Cost:** Free 500 hours/month, then $5/month
**Setup time:** 3 minutes

1. Sign up at [railway.app](https://railway.app)
2. New Project → Deploy from GitHub → Select this repo
3. Copy deployment URL
4. `npx wrangler secret put BACKEND_URL` (paste Railway URL)
5. `npx wrangler deploy`

### Option 4: Render (Alternative to Railway)

**Cost:** Free 750 hours/month, then $7/month

Same process as Railway, uses `render.yaml` config.

### Option 5: Local Development with Cloudflare Tunnel

If you want to test locally while keeping everything fronted by Cloudflare:

1. **Start Python backend locally:**
   ```bash
   npm run backend:http
   # Listens on http://127.0.0.1:8081
   ```

2. **Create Cloudflare tunnel:**
   ```bash
   # Install cloudflared
   brew install cloudflare/cloudflare/cloudflared  # macOS

   # Create tunnel
   cloudflared tunnel --url http://127.0.0.1:8081
   # Copy the https://*.trycloudflare.com URL
   ```

3. **Configure Worker for local dev:**
   Create `.dev.vars`:
   ```
   BACKEND_URL="https://your-tunnel.trycloudflare.com"
   ```

4. **Test locally:**
   ```bash
   npm run cf:dev
   # Worker runs at http://localhost:8788
   ```

5. **Deploy to production:**
   ```bash
   npx wrangler secret put BACKEND_URL
   # Paste your tunnel URL
   npx wrangler deploy
   ```

### Architecture

```
MCP Client (Playground/Claude)
        ↓
Cloudflare Worker (proxy)
        ↓
Python FastMCP Backend (Lambda/App Runner/Railway/Render)
        ↓
ClinicalTrials.gov API
```

### Cost Comparison

| Option | Free Tier | After Free Tier | Best For |
|--------|-----------|-----------------|----------|
| AWS Lambda | 1M requests/month | $0.20 per 1M | Personal use, low traffic |
| AWS App Runner | None | ~$5/month | Production, no cold starts |
| Railway | 500 hours/month | $5/month | Quick setup, no AWS |
| Render | 750 hours/month | $7/month | Alternative to Railway |

**Recommendation:** Start with AWS Lambda (completely free for most use cases)

### Fully Cloudflare entrypoint (keep Python) using Cloudflare Tunnel

If you want everything to be fronted and managed by Cloudflare while keeping the Python backend, use Cloudflare Tunnel to expose your local/server backend securely and set the Worker to proxy to it.

1. Install and authenticate Cloudflared on the machine running your Python backend:
   - macOS: `brew install cloudflare/cloudflare/cloudflared`
   - Login: `cloudflared tunnel login`

2. Quick dev tunnel (ephemeral URL):
   - Start your backend: `npm run backend:http` (listens on `http://127.0.0.1:8081`)
   - Open a tunnel: `cloudflared tunnel --url http://127.0.0.1:8081`
   - Copy the printed `https://<random>.trycloudflare.com` and set it as your Worker secret:
     ```
     npx wrangler secret put FASTMCP_BASE_URL
     # paste: https://<random>.trycloudflare.com
     ```
   - Deploy the Worker: `npm run cf:deploy`

3. Stable tunnel with your domain (recommended):
   - Create a named tunnel: `cloudflared tunnel create clintrials-mcp`
   - Route DNS (replace `mcp.yourdomain.com` with a hostname in a Cloudflare-managed zone):
     `cloudflared tunnel route dns clintrials-mcp mcp.yourdomain.com`
   - Create `~/.cloudflared/config.yml` with:
     ```yaml
     tunnel: clintrials-mcp
     credentials-file: /Users/<you>/.cloudflared/<tunnel-id>.json
     ingress:
       - hostname: mcp.yourdomain.com
         service: http://127.0.0.1:8081
       - service: http_status:404
     ```
   - Run it: `cloudflared tunnel run clintrials-mcp`
   - Verify: `curl https://mcp.yourdomain.com/healthz` returns `{ "status": "ok" }`
   - Set the Worker secret to your stable hostname:
     ```
     npx wrangler secret put FASTMCP_BASE_URL
     # paste: https://mcp.yourdomain.com
     ```
   - Deploy: `npm run cf:deploy`

Result:
- Users and MCP clients connect only to Cloudflare (`workers.dev` or your domain).
- The Worker proxies `/sse` and other API calls to your Python backend over the private tunnel, preserving SSE streams.
- You keep your existing Python tools; no TypeScript porting required.

## Available Tools

### Search Tools

#### `search_trials_by_acronym`
Search clinical trials by study acronym (protocolSection.identificationModule.acronym).

**Parameters:**
- `acronyms` (required): Array of acronyms to search for (e.g., ["TETON"]).
- `max_studies` (optional): Maximum number of studies to return (default: 50)
- `fields` (optional): Specific fields to return (Acronym is always included for filtering)
- `exact_match` (optional): Exact match when true; partial contains match when false (default: true)

**Example:**
```json
{
  "acronyms": ["TETON"],
  "max_studies": 100,
  "exact_match": true
}
```

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

## Search Result Fields

All search tools return a standardized, minimal set of fields to keep payloads small:

- `NCTId`: Trial identifier
- `BriefTitle`: Title
- `Acronym`: Study acronym
- `InterventionName`: Intervention names
- `Condition`: Medical conditions
- `Phase`: Trial phase(s)
- `LeadSponsorName` and `CollaboratorName`: Sponsors
- `HasResults`: Whether results are posted

Use `get_trial_details_batched` to fetch full details once you’ve identified relevant trials.

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

### Search for COVID-19 vaccine trials, then fetch details in batches:
```json
{
  "tool": "search_trials_by_condition",
  "arguments": {
    "conditions": ["COVID-19"],
    "max_studies": 50
  }
}
```

Then, request detailed records in batches of 10:

```json
{
  "tool": "get_trial_details_batched",
  "arguments": {
    "nct_ids": ["NCT01234567", "NCT07654321"],
    "batch_size": 10
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

## Transport Modes (Auto)

This server now auto-detects the transport to run:

- Auto detection order:
  1) `MCP_TRANSPORT=stdio|http` forces a mode
  2) If stdin is not a TTY (launched by an MCP host), uses `stdio`
  3) If `PORT` is set, uses `http`
  4) Otherwise defaults to `http`

### Force a mode

- STDIO: `MCP_TRANSPORT=stdio python mcp_server.py`
- HTTP: `MCP_TRANSPORT=http PORT=8081 python mcp_server.py`

### Cline configuration examples

- HTTP entry:
```
"clinical-trials-mcp": {
  "disabled": false,
  "timeout": 120,
  "type": "http",
  "url": "http://localhost:8081",
  "autoApprove": []
}
```

- STDIO entry:
```
"clinical-trials-mcp": {
  "disabled": false,
  "timeout": 120,
  "type": "stdio",
  "command": "/path/to/venv/bin/python",
  "args": [ "/path/to/clintrials-mcp/mcp_server.py" ]
}
```

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
