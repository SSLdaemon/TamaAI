"""
Simple integration layer for MCP servers with Flask.
Since Flask is synchronous and MCP is async, we use a background thread.
"""
import asyncio
import threading
from mcp_client import start_mcp_servers

class MCPManager:
    """
    Manages MCP client in a background thread for use with Flask.
    """
    def __init__(self):
        self.client = None
        self.loop = None
        self.thread = None
        self._ready = threading.Event()

    def start(self):
        """Start MCP servers in background thread."""
        def run_async_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.client = self.loop.run_until_complete(start_mcp_servers())
            self._ready.set()
            # Keep loop running
            self.loop.run_forever()

        self.thread = threading.Thread(target=run_async_loop, daemon=True)
        self.thread.start()
        self._ready.wait()  # Wait for initialization
        print("MCP Manager started successfully")

    def call_tool_sync(self, server_name: str, tool_name: str, arguments: dict):
        """Synchronous wrapper for calling MCP tools from Flask routes."""
        if not self.client:
            return {"error": "MCP client not initialized"}
        
        future = asyncio.run_coroutine_threadsafe(
            self.client.call_tool(server_name, tool_name, arguments),
            self.loop
        )
        return future.result(timeout=10)

    def shutdown(self):
        """Shutdown MCP servers."""
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)

# Global instance
mcp_manager = MCPManager()
