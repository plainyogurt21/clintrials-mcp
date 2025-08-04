#!/usr/bin/env python3
"""
Test MCP tool calls directly
"""

import asyncio
import json
from mcp_server import handle_call_tool

async def test_tool_calls():
    """Test MCP tool calls"""
    
    print("Testing MCP tool calls...")
    
    # Test search by sponsor
    print("\n1. Testing search_trials_by_sponsor...")
    try:
        result = await handle_call_tool(
            "search_trials_by_sponsor",
            {"sponsors": ["Gossamer Bio"], "max_studies": 2}
        )
        print(f"Result type: {type(result)}")
        print(f"Result content: {len(result.content)} items")
        print(f"First content type: {type(result.content[0])}")
        print(f"First content: {result.content[0].text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tool_calls())