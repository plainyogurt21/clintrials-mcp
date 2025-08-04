#!/usr/bin/env python3
"""
Debug CallToolResult construction
"""

import json
from mcp.types import CallToolResult, TextContent

def test_callresult():
    """Test CallToolResult construction"""
    print("Testing CallToolResult construction...")
    
    # Test 1: Simple construction
    try:
        content = TextContent(type="text", text="Test message")
        print(f"TextContent created: {content}")
        
        result = CallToolResult(
            content=[content],
            isError=False
        )
        print(f"CallToolResult created successfully: {type(result)}")
        print(f"Content: {result.content}")
        print(f"IsError: {result.isError}")
        
    except Exception as e:
        print(f"Error in test 1: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: JSON construction like in mcp_server
    try:
        test_data = {"message": "hello", "status": "ok"}
        content = TextContent(type="text", text=json.dumps(test_data, indent=2))
        print(f"JSON TextContent created: {content}")
        
        result = CallToolResult(
            content=[content],
            isError=False
        )
        print(f"JSON CallToolResult created successfully")
        
    except Exception as e:
        print(f"Error in test 2: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Check what happens with wrong construction
    try:
        # This might be what's happening
        result = CallToolResult([
            ("meta", None),
            ("content", [TextContent(type="text", text="test")]),
            ("structuredContent", None),
            ("isError", False)
        ])
        print("Wrong construction worked?!")
    except Exception as e:
        print(f"Wrong construction failed as expected: {e}")

if __name__ == "__main__":
    test_callresult()