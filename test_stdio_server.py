#!/usr/bin/env python3
"""
Test MCP server through stdio protocol
"""

import asyncio
import json
import subprocess
import sys
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.session import ClientSession

async def test_stdio_server():
    """Test the MCP server through stdio"""
    print("Testing MCP server through stdio protocol...")
    
    # Create server parameters
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"]
    )
    
    try:
        # Create stdio client
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the session
                init_result = await session.initialize()
                print(f"Initialization result: {init_result}")
                
                # List tools
                tools = await session.list_tools()
                print(f"Available tools: {[tool.name for tool in tools.tools]}")
                
                # Test a tool call
                print("\nTesting tool call...")
                try:
                    result = await session.call_tool(
                        "search_trials_by_sponsor",
                        {"sponsors": ["Test"], "max_studies": 1}
                    )
                    print(f"Result type: {type(result)}")
                    print(f"Result content: {result.content}")
                    print(f"Result isError: {result.isError}")
                    
                except Exception as e:
                    print(f"Tool call error: {e}")
                    import traceback
                    traceback.print_exc()
                    
    except Exception as e:
        print(f"Server connection error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_stdio_server())