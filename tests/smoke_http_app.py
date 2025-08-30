#!/usr/bin/env python3
"""
Minimal smoke test that ensures the HTTP app can be created.
Does not perform network calls or start a server.
"""

import os, sys

# Ensure project root on sys.path when running from tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import mcp_server
except Exception as e:
    print(f"FAIL: could not import mcp_server: {e}")
    sys.exit(1)

try:
    app = mcp_server.mcp.streamable_http_app()
except Exception as e:
    print(f"FAIL: could not create streamable_http_app: {e}")
    sys.exit(1)

print("OK: HTTP app created")
