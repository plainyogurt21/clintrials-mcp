#!/usr/bin/env python3
"""
Example of using the Clinical Trials MCP Server with OpenAI
This requires the mcp client library and OpenAI API key
"""

import asyncio
import json
import os
from typing import Any, Dict

# You would need to install these:
# pip install mcp openai

# Uncomment these imports when ready to use:
# import openai
# from mcp.client.session import ClientSession
# from mcp.client.stdio import StdioServerParameters, stdio_client

async def chat_with_clinical_trials():
    """Example of chatting with OpenAI using MCP tools"""
    
    # Set your OpenAI API key
    # openai.api_key = os.getenv("OPENAI_API_KEY")
    
    print("This is an example of how you would integrate with OpenAI.")
    print("You would need to:")
    print("1. Install: pip install mcp openai")
    print("2. Set OPENAI_API_KEY environment variable")
    print("3. Uncomment the code below")
    
    # Example usage (commented out - uncomment when ready):
    """
    # Connect to your MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            
            # Call a tool
            result = await session.call_tool(
                "search_trials_by_condition",
                {
                    "conditions": ["cancer"],
                    "max_studies": 5
                }
            )
            
            # Use the result in an OpenAI chat
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a medical research assistant with access to clinical trials data."},
                    {"role": "user", "content": "What cancer trials are currently recruiting?"},
                    {"role": "assistant", "content": f"Based on clinical trials data: {result.content}"}
                ]
            )
            
            print(response.choices[0].message.content)
    """

if __name__ == "__main__":
    asyncio.run(chat_with_clinical_trials())