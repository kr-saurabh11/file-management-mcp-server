"""Configuration and path resolution for FastMCP File Management Server.

This module manages workspace environment settings, path canonicalization,
sandbox security boundaries for file operations, and server runtime configurations.
"""

import os
from pathlib import Path

# Workspace directory used as the default base for relative file paths.
# Defaults to the process's current working directory unless overridden by MCP_WORKSPACE_DIR.
WORKSPACE_DIR: Path = Path(os.getenv("MCP_WORKSPACE_DIR", Path.cwd())).resolve()

# Strict sandboxing flag.
# When enabled (true, 1, yes), strictly prevents any operations on paths outside WORKSPACE_DIR.
ENFORCE_SANDBOX: bool = os.getenv("MCP_ENFORCE_SANDBOX", "false").lower() in (
    "true",
    "1",
    "yes",
)

# Server transport protocol configuration: "stdio" or "streamable-http".
# Defaults to "stdio", overridable via MCP_TRANSPORT or FASTMCP_TRANSPORT.
SERVER_TRANSPORT: str = os.getenv(
    "MCP_TRANSPORT", os.getenv("FASTMCP_TRANSPORT", "stdio")
).lower()

# Server host configuration for streamable-http transport.
# Defaults to "localhost", overridable via MCP_HOST or FASTMCP_HOST.
SERVER_HOST: str = os.getenv("MCP_HOST", os.getenv("FASTMCP_HOST", "localhost"))


def _get_server_port() -> int:
    """Parse and return the server port from environment variables, defaulting to 9001."""
    raw = os.getenv("MCP_PORT", os.getenv("FASTMCP_PORT", "9001"))
    try:
        return int(raw)
    except ValueError:
        return 9001


# Server port configuration for streamable-http transport.
# Defaults to 9001, overridable via MCP_PORT or FASTMCP_PORT.
SERVER_PORT: int = _get_server_port()


def resolve_path(
    file_path: str,
    workspace_dir: Path | None = None,
    enforce_sandbox: bool | None = None,
) -> Path:
    """Resolve, normalize, and validate a file path against workspace security rules.

    Converts relative paths to absolute paths anchored at the workspace directory,
    expands user home symbols ('~'), and resolves symlinks. When sandbox enforcement
    is active, validates that the resulting path does not escape the workspace
    boundary (preventing directory traversal attacks).

    Args:
        file_path: The relative or absolute path string to resolve.
        workspace_dir: Optional override for the base workspace directory.
            Defaults to the global `WORKSPACE_DIR` (or `MCP_WORKSPACE_DIR` env var).
        enforce_sandbox: Optional override for sandbox validation.
            Defaults to the global `ENFORCE_SANDBOX` (or `MCP_ENFORCE_SANDBOX` env var).

    Returns:
        Path: The fully resolved, absolute filesystem path.

    Raises:
        ValueError: If `file_path` is empty or consists solely of whitespace.
        PermissionError: If sandbox enforcement is enabled and the resolved path
            falls outside the designated `workspace_dir`.

    Examples:
        >>> # Resolve a relative path inside default workspace
        >>> resolve_path("data/file.txt")
        PosixPath('/workspace/data/file.txt')

        >>> # Absolute paths within allowed workspace
        >>> resolve_path("/workspace/file.txt")
        PosixPath('/workspace/file.txt')

        >>> # Path escaping workspace with sandbox enabled
        >>> resolve_path("../../etc/passwd", enforce_sandbox=True)
        PermissionError: Access denied: '../../etc/passwd' resolves outside the allowed workspace...
    """
    if not file_path or not file_path.strip():
        raise ValueError("File path cannot be empty.")

    ws_dir = workspace_dir if workspace_dir is not None else WORKSPACE_DIR
    sandbox = enforce_sandbox if enforce_sandbox is not None else ENFORCE_SANDBOX

    path = Path(file_path.strip()).expanduser()
    if not path.is_absolute():
        path = (ws_dir / path).resolve()
    else:
        path = path.resolve()

    if sandbox and not path.is_relative_to(ws_dir):
        raise PermissionError(
            f"Access denied: '{file_path}' resolves outside the allowed workspace '{ws_dir}'."
        )

    return path
