#!/usr/bin/env python3
"""
Test script for Clinical Trials MCP Server functions
"""

import json
from mcp_server import ClinicalTrialsAPI, api_client

def test_api_functions():
    """Test all API functions"""
    
    print("Testing Clinical Trials API functions...")
    
    # Test 1: Search by sponsor
    print("\n1. Testing search by sponsor (Gossamer Bio)...")
    try:
        result = api_client.search_studies(
            sponsors=["Gossamer Bio"],
            max_studies=5
        )
        print(f"Found {len(result.get('studies', []))} studies")
        if result.get('studies'):
            study = result['studies'][0]
            print(f"First study: {study.get('protocolSection', {}).get('identificationModule', {}).get('nctId', 'Unknown')}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Search by condition
    print("\n2. Testing search by condition (diabetes)...")
    try:
        result = api_client.search_studies(
            conditions=["diabetes"],
            max_studies=3
        )
        print(f"Found {len(result.get('studies', []))} studies")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Search by intervention
    print("\n3. Testing search by intervention (insulin)...")
    try:
        result = api_client.search_studies(
            interventions=["insulin"],
            max_studies=3
        )
        print(f"Found {len(result.get('studies', []))} studies")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Get specific study details
    print("\n4. Testing get study by ID...")
    try:
        # First get a study ID from search
        search_result = api_client.search_studies(
            conditions=["cancer"],
            max_studies=1
        )
        if search_result.get('studies'):
            nct_id = search_result['studies'][0].get('protocolSection', {}).get('identificationModule', {}).get('nctId')
            if nct_id:
                result = api_client.get_study_by_id(nct_id)
                print(f"Retrieved details for {nct_id}")
            else:
                print("No NCT ID found")
        else:
            print("No studies found")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: Get field statistics
    print("\n5. Testing field statistics...")
    try:
        result = api_client.get_field_statistics()
        print(f"Field statistics keys: {list(result.keys()) if result else 'None'}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api_functions()