#!/usr/bin/env python3
"""
Manual test script that sends JSON-RPC messages to the MCP server
"""

import json
import subprocess
import sys
import time

def send_rpc_message(process, method, params=None):
    """Send a JSON-RPC message to the MCP server"""
    message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method
    }
    if params:
        message["params"] = params
    
    message_str = json.dumps(message) + "\n"
    process.stdin.write(message_str.encode())
    process.stdin.flush()
    
    # Read response
    response_line = process.stdout.readline().decode().strip()
    if response_line:
        return json.loads(response_line)
    return None

def test_mcp_manually():
    """Test the MCP server by sending raw JSON-RPC messages"""
    
    print("Starting MCP server...")
    
    # Start the server process
    process = subprocess.Popen(
        [sys.executable, "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False
    )
    
    try:
        time.sleep(1)  # Give server time to start
        
        print("Sending initialize request...")
        init_response = send_rpc_message(process, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        })
        print(f"Initialize response: {init_response}")
        
        print("\nSending tools/list request...")
        tools_response = send_rpc_message(process, "tools/list")
        print(f"Tools response: {tools_response}")
        
        print("\nSending tool call request...")
        call_response = send_rpc_message(process, "tools/call", {
            "name": "search_trials_by_condition",
            "arguments": {
                "conditions": ["diabetes"],
                "max_studies": 2
            }
        })
        print(f"Call response: {call_response}")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_mcp_manually()