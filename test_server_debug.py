#!/usr/bin/env python3
"""
Debug MCP Server tool calls
"""

import asyncio
import json
from mcp_server import handle_call_tool, api_client

async def test_handle_call_tool():
    """Test the handle_call_tool function directly"""
    print("Testing handle_call_tool function...")
    
    # Test 1: Valid tool call
    try:
        print("\n=== Test 1: Valid tool call ===")
        result = await handle_call_tool(
            "search_trials_by_sponsor",
            {"sponsors": ["Test Sponsor"], "max_studies": 1}
        )
        
        print(f"Result type: {type(result)}")
        print(f"Result content type: {type(result.content)}")
        print(f"First content item type: {type(result.content[0])}")
        print(f"IsError: {result.isError}")
        print(f"Content preview: {result.content[0].text[:100]}...")
        
    except Exception as e:
        print(f"Error in test 1: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Invalid tool call
    try:
        print("\n=== Test 2: Invalid tool call ===")
        result = await handle_call_tool("nonexistent_tool", {})
        
        print(f"Error result type: {type(result)}")
        print(f"Error result content type: {type(result.content)}")
        print(f"Error result isError: {result.isError}")
        print(f"Error content: {result.content[0].text}")
        
    except Exception as e:
        print(f"Error in test 2: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Test API call directly
    try:
        print("\n=== Test 3: Direct API call ===")
        api_result = api_client.search_studies(
            sponsors=["Test Sponsor"],
            max_studies=1
        )
        print(f"API result type: {type(api_result)}")
        print(f"API result keys: {list(api_result.keys()) if isinstance(api_result, dict) else 'Not a dict'}")
        
    except Exception as e:
        print(f"Error in test 3: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_handle_call_tool())