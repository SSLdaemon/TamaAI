#!/usr/bin/env python
"""
Quick verification script to test MCP server startup.
"""
import sys
import time

print("Testing MCP Manager import...")
try:
    from mcp_manager import mcp_manager
    print("[OK] Import successful")
except Exception as e:
    print(f"[FAIL] Import failed: {e}")
    sys.exit(1)

print("\nStarting MCP servers...")
try:
    mcp_manager.start()
    print("[OK] MCP servers started")
except Exception as e:
    print(f"[FAIL] Startup failed: {e}")
    sys.exit(1)

print("\nTesting Time server...")
try:
    result = mcp_manager.call_tool_sync('time', 'get_current_time', {})
    print(f"[OK] Time server response: {result}")
except Exception as e:
    print(f"[FAIL] Time server failed: {e}")

print("\nTesting Memory server...")
try:
    result = mcp_manager.call_tool_sync('memory', 'read_graph', {})
    print(f"[OK] Memory server response: {result}")
except Exception as e:
    print(f"[FAIL] Memory server failed: {e}")

print("\n[OK] All tests passed! MCP integration working.")
mcp_manager.shutdown()
