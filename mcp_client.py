import asyncio
import os
import shutil
import sys
from contextlib import AsyncExitStack
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    """
    Client to manage connections to multiple MCP servers.
    """
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.servers = {}

    async def connect_to_server(self, server_name: str, command: str, args: list[str], env: dict = None):
        """
        Connect to an MCP server via stdio.
        """
        print(f"Connecting to MCP server: {server_name}...")
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )

        try:
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
            await self.session.initialize()
            
            # Store session
            self.servers[server_name] = self.session
            
            # List tools to verify connection
            tools = await self.session.list_tools()
            print(f"Connected to {server_name}. Available tools: {[t.name for t in tools.tools]}")
            
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

    async def list_tools(self, server_name: str):
        if server_name in self.servers:
            return await self.servers[server_name].list_tools()
        return None

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict):
        if server_name in self.servers:
            return await self.servers[server_name].call_tool(tool_name, arguments)
        return None

    async def cleanup(self):
        await self.exit_stack.aclose()

# ------------------------------------------------------------------------------
# Configuration for specific servers
# ------------------------------------------------------------------------------

async def start_mcp_servers():
    client = MCPClient()
    
    # 1. Memory Server (Node.js)
    memory_path = os.path.abspath("mcp-servers/src/memory/dist/index.js")
    if os.path.exists(memory_path):
        await client.connect_to_server(
            "memory", 
            "node", 
            [memory_path],
            env=os.environ.copy()
        )
    else:
        print(f"Warning: Memory server not found at {memory_path}")

    # 2. Time Server (Python)
    # We use source directly or installed module. Since we installed it with pip -e, 
    # we can run it as a module or script. Let's try running as python script due to potential path issues.
    # Actually, better to run as module 'mcp_server_time' if installed.
    # But let's use the explicit path to be safe given our setup.
    time_script = os.path.abspath("mcp-servers/src/time/src/mcp_server_time/server.py")
    if not os.path.exists(time_script):
        # Fallback to checking if it's executable module
        # We will try running via python -m mcp_server_time
        await client.connect_to_server(
            "time",
            sys.executable,
            ["-m", "mcp_server_time"],
             env=os.environ.copy()
        )
    else:
         # If script exists (which it should in src/time/src/...)
         pass
         # Actually, let's stick to module execution as it handles imports correctly
         await client.connect_to_server(
            "time",
            sys.executable,
            ["-m", "mcp_server_time"],
             env=os.environ.copy()
        )

    # 3. Filesystem (Node.js)
    fs_path = os.path.abspath("mcp-servers/src/filesystem/dist/index.js")
    if os.path.exists(fs_path):
        # Filesystem requires args for allowed directories. We'll allow the current project dir.
        allowed_dir = os.path.abspath(".")
        await client.connect_to_server(
            "filesystem",
            "node",
            [fs_path, allowed_dir],
            env=os.environ.copy()
        )

    # 4. Fetch (Python)
    await client.connect_to_server(
        "fetch",
        sys.executable,
        ["-m", "mcp_server_fetch"],
        env=os.environ.copy()
    )

    return client

if __name__ == "__main__":
    # Test script
    async def main():
        client = await start_mcp_servers()
        # Keep alive for a bit to test
        # await asyncio.sleep(5)
        await client.cleanup()
    
    asyncio.run(main())
