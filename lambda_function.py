"""
AWS Lambda handler for Clinical Trials MCP Server
Wraps the FastMCP app for Lambda + Function URL deployment
"""
import json
from mangum import Mangum
from mcp_server import mcp

# Create Lambda handler using Mangum adapter
# Mangum wraps ASGI apps (like FastMCP) for AWS Lambda
handler = Mangum(mcp.http_app(), lifespan="off")
