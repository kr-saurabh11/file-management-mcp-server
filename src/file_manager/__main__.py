"""CLI module entrypoint for FastMCP File Management Server.

Enables running the server directly via Python's module invocation flag:
    $ python -m file_manager
    $ uv run python -m file_manager
"""

from file_manager.server import main

if __name__ == "__main__":
    main()
