#!/usr/bin/env python3
"""
Test script for the Clinical Trials MCP Server
"""

import asyncio
import json
from mcp_server import server, handle_list_tools, handle_call_tool

async def test_server():
    """Test the MCP server functionality"""
    
    print("=== Testing Clinical Trials MCP Server ===\n")
    
    # Test 1: List available tools
    print("1. Testing tool listing...")
    tools = await handle_list_tools()
    print(f"Found {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    print()
    
    # Test 2: Search by condition
    print("2. Testing search by condition (lung cancer)...")
    try:
        result = await handle_call_tool(
            "search_trials_by_condition",
            {
                "conditions": ["lung cancer"],
                "max_studies": 5,
                "fields": ["NCTId", "BriefTitle", "OverallStatus", "Phase"]
            }
        )
        print("✅ Search by condition successful")
        response_data = json.loads(result.content[0].text)
        print(f"Found {len(response_data.get('studies', []))} studies")
        if response_data.get('studies'):
            first_study = response_data['studies'][0]
            nct_id = first_study.get('protocolSection', {}).get('identificationModule', {}).get('nctId', 'Unknown')
            title = first_study.get('protocolSection', {}).get('identificationModule', {}).get('briefTitle', 'Unknown')
            print(f"First study: {nct_id} - {title}")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Test 3: Search by intervention
    print("3. Testing search by intervention (immunotherapy)...")
    try:
        result = await handle_call_tool(
            "search_trials_by_intervention",
            {
                "interventions": ["immunotherapy"],
                "max_studies": 3,
                "fields": ["NCTId", "BriefTitle"]
            }
        )
        print("✅ Search by intervention successful")
        response_data = json.loads(result.content[0].text)
        print(f"Found {len(response_data.get('studies', []))} studies")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Test 4: Get specific trial details
    print("4. Testing get trial details...")
    try:
        result = await handle_call_tool(
            "get_trial_details",
            {
                "nct_id": "NCT04852770",
                "fields": ["NCTId", "BriefTitle", "OverallStatus"]
            }
        )
        print("✅ Get trial details successful")
        response_data = json.loads(result.content[0].text)
        if 'protocolSection' in response_data:
            title = response_data.get('protocolSection', {}).get('identificationModule', {}).get('briefTitle', 'Unknown')
            status = response_data.get('protocolSection', {}).get('statusModule', {}).get('overallStatus', 'Unknown')
            print(f"Trial: {title}")
            print(f"Status: {status}")
        else:
            print("Trial details retrieved but structure may differ")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Test 5: Analyze trial phases
    print("5. Testing phase analysis...")
    try:
        result = await handle_call_tool(
            "analyze_trial_phases",
            {
                "conditions": ["diabetes"],
                "max_studies": 50
            }
        )
        print("✅ Phase analysis successful")
        response_data = json.loads(result.content[0].text)
        print(f"Total studies analyzed: {response_data.get('total_studies', 0)}")
        if response_data.get('phase_distribution'):
            print("Phase distribution:")
            for phase, count in response_data['phase_distribution'].items():
                percentage = response_data['phase_percentages'].get(phase, 0)
                print(f"  {phase}: {count} studies ({percentage}%)")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    print("=== Testing Complete ===")

if __name__ == "__main__":
    asyncio.run(test_server())