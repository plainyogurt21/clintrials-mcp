"""
AWS Lambda handler for Clinical Trials MCP Server
Wraps the FastMCP app for Lambda + Function URL deployment
"""
import os
from mangum import Mangum
from mcp_server import mcp
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

# Set HTTP mode for Lambda
os.environ["TRANSPORT"] = "http"

# Create HTTP app
app = mcp.http_app()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id", "mcp-protocol-version"],
    max_age=86400,
)

# Add health endpoint
async def health(request):
    return JSONResponse({"status": "ok"})

# Add /sse alias for /mcp endpoint for backward compatibility
async def sse_redirect(request):
    # Redirect to /mcp
    from starlette.responses import RedirectResponse
    return RedirectResponse(url="/mcp", status_code=307)

app.router.routes.insert(0, Route("/healthz", health, methods=["GET"]))
app.router.routes.insert(0, Route("/sse", sse_redirect, methods=["GET", "POST"]))

# Create Lambda handler using Mangum adapter
handler = Mangum(app, lifespan="off")
