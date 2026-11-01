"""FastMCP File Management Server package.

This package provides a production-grade, standard Model Context Protocol (MCP)
server offering secure and flexible file management operations:
- `create_file`: Create a new file with optional content and overwrite guard.
- `read_file`: Read full or sliced file content with line offset and limit pagination.
- `delete_file`: Safely delete a file with directory protection and missing_ok flag.
- `write_file`: Write, append, or edit file content (with search-and-replace support).
- `resolve_path`: Path canonicalization and sandbox security enforcement.
- `mcp`: The underlying FastMCP application instance.
- `main`: Entrypoint to launch the server over standard I/O (stdio).
"""

from file_manager.config import (
    ENFORCE_SANDBOX,
    SERVER_HOST,
    SERVER_PORT,
    SERVER_TRANSPORT,
    WORKSPACE_DIR,
    resolve_path,
)
from file_manager.server import (
    create_file,
    delete_file,
    main,
    mcp,
    read_file,
    run,
    write_file,
)

__version__ = "0.1.0"

__all__ = [
    "ENFORCE_SANDBOX",
    "SERVER_HOST",
    "SERVER_PORT",
    "SERVER_TRANSPORT",
    "WORKSPACE_DIR",
    "__version__",
    "create_file",
    "delete_file",
    "main",
    "mcp",
    "read_file",
    "resolve_path",
    "run",
    "write_file",
]
