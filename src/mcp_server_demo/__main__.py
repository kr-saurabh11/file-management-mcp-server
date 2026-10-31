"""CLI module entrypoint for FastMCP File Management Server.

Enables running the server directly via Python's module invocation flag:
    $ python -m mcp_server_demo
    $ uv run python -m mcp_server_demo
"""

from mcp_server_demo.server import main

if __name__ == "__main__":
    main()
