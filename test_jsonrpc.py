#!/usr/bin/env python3
"""
Test JSON-RPC MCP server calls
"""

import asyncio
import json
import sys
from io import StringIO
from mcp_server import server

async def test_jsonrpc_call():
    """Test a full JSON-RPC call"""
    
    # Simulate the exact call from Claude Desktop
    call_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "search_trials_by_sponsor",
            "arguments": {
                "sponsors": ["Gossamer Bio"],
                "max_studies": 50
            }
        }
    }
    
    print("Testing JSON-RPC call...")
    print(f"Request: {json.dumps(call_request, indent=2)}")
    
    try:
        # Test the tool call directly
        from mcp_server import handle_call_tool
        result = await handle_call_tool(
            "search_trials_by_sponsor",
            {"sponsors": ["Gossamer Bio"], "max_studies": 50}
        )
        
        print(f"\nResult type: {type(result)}")
        print(f"Result isError: {result.isError}")
        print(f"Content length: {len(result.content)}")
        
        # Check the structure
        print(f"Content[0] type: {type(result.content[0])}")
        print(f"Content[0] text length: {len(result.content[0].text)}")
        
        # Parse the JSON to check if it's valid
        response_data = json.loads(result.content[0].text)
        studies = response_data.get('studies', [])
        print(f"Found {len(studies)} studies")
        
        if studies:
            first_study = studies[0]
            nct_id = first_study.get('protocolSection', {}).get('identificationModule', {}).get('nctId', 'Unknown')
            print(f"First study NCT ID: {nct_id}")
        
        # Test serialization
        print("\nTesting serialization...")
        serialized = result.model_dump()
        print(f"Serialized keys: {list(serialized.keys())}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_jsonrpc_call())