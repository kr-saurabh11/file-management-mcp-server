# FastMCP File Management Server

A Model Context Protocol (MCP) server built with **FastMCP** that provides standard, secure, and robust file management tools for AI agents and LLM applications (such as Claude Desktop, Cursor, Antigravity, and custom MCP clients).

---

## Directory Structure

This project follows the modern Python `src` layout convention recommended for robust packaging, clean separation of concerns, and reliable dependency management:

```
file-management-mcp-server/
├── src/
│   └── file_manager/
│       ├── __init__.py               # Package exports & version
│       ├── __main__.py               # Support for `python -m file_manager`
│       ├── config.py                 # Workspace path, sandbox security & server config
│       ├── server.py                 # FastMCP server instance, tool registration & entrypoints
│       └── tools/
│           ├── __init__.py           # Re-exports file tools
│           └── file_operations.py    # Core logic for create, read, delete, write
├── tests/
│   ├── __init__.py                   # Test suite package
│   ├── conftest.py                   # Pytest fixtures
│   └── test_server.py                # 31 unit, integration, transport and MCP protocol tests
├── .gitignore                        # Comprehensive ignore rules for Python, IDEs, and OS
├── .python-version                   # Python version pin (3.12)
├── mcp_server.json                   # MCP client configuration (stdio & streamable-http)
├── pyproject.toml                    # Project configuration, build backend, and CLI script
└── README.md                         # Project documentation
```

---

## Features & Protocol Compliance

This server strictly adheres to the **Model Context Protocol (MCP)** standard:
- **Standard Tool Definitions**: Exposes clean JSON Schemas with typed parameters, clear descriptions, and required parameter validations.
- **Transport**: Supports both **standard I/O (`stdio`)** and **Streamable HTTP (`streamable-http`)** transports for flexible integration with any MCP client host.
- **Robust Error Handling**: Encapsulates file system exceptions into standard MCP protocol errors (`isError: true` with human-readable error messages).
- **Workspace & Sandbox Controls**: Supports relative path resolution against a configurable workspace directory and optional sandbox enforcement to prevent unauthorized directory traversal.

---

## Available Tools

The server exposes 4 standard file management tools:

### 1. `create_file`
Creates a new file on the filesystem with optional initial content. Automatically creates parent directories if they do not exist.

* **Parameters**:
  * `path` (`string`, **required**): Relative or absolute path to the file to create.
  * `content` (`string`, default: `""`): Optional initial text content.
  * `overwrite` (`boolean`, default: `false`): If `true`, overwrites existing files. If `false`, raises a `FileExistsError` if the file already exists.
  * `encoding` (`string`, default: `"utf-8"`): Text character encoding.
* **Returns**: Status message with path and byte count written.

### 2. `read_file`
Reads the text content of a file. Supports line offset and limit pagination for safely reading large files.

* **Parameters**:
  * `path` (`string`, **required**): Relative or absolute path to the file.
  * `offset` (`integer`, default: `0`): Line number to start reading from (0-indexed).
  * `limit` (`integer | null`, default: `null`): Maximum number of lines to read. If omitted or `null`, reads to the end of the file.
  * `encoding` (`string`, default: `"utf-8"`): Text encoding.
* **Returns**: Text content of the file or the requested slice of lines.

### 3. `delete_file`
Permanently deletes a file from the filesystem. Protects against accidental directory deletion.

* **Parameters**:
  * `path` (`string`, **required**): Relative or absolute path to the file to delete.
  * `missing_ok` (`boolean`, default: `false`): If `true`, suppresses errors when the file does not exist.
* **Returns**: Confirmation message indicating whether the file was deleted.

### 4. `write_file`
Writes or edits content in a file. Supports overwriting, appending, or targeted search-and-replace edits.

* **Parameters**:
  * `path` (`string`, **required**): Path to the file to write or edit.
  * `content` (`string`, default: `""`): The text content to write, append, or use as replacement text.
  * `mode` (`string`, default: `"overwrite"`, choices: `["overwrite", "append", "replace"]`):
    * `"overwrite"`: Completely replaces the file content (or creates the file).
    * `"append"`: Appends content to the end of the file.
    * `"replace"`: Replaces specific text inside the file.
  * `target_text` (`string | null`, default: `null`): The text snippet to search and replace when `mode="replace"`.
  * `replacement_text` (`string | null`, default: `null`): The replacement string for `target_text` (defaults to `content`).
  * `old_text` (`string | null`, default: `null`): Alias for `target_text`.
  * `new_text` (`string | null`, default: `null`): Alias for `replacement_text`.
  * `create_if_missing` (`boolean`, default: `true`): Whether to create the file if it does not exist (for `overwrite` and `append`).
  * `encoding` (`string`, default: `"utf-8"`): Text encoding.
* **Returns**: Confirmation message detailing the bytes written, appended, or occurrences replaced.
* *Note: The server also provides dynamic alias routing for `edit_file` and `write_or_edit_file` to ensure backwards compatibility with clients using alternative tool names.*

---

## Local Setup & Installation

### Prerequisites
- Python **3.12+**
- [`uv`](https://docs.astral.sh/uv/) (recommended) or standard `pip`

### 1. Clone & Navigate to Repository
```bash
git clone <repo-url>
cd file-management-mcp-server
```

### 2. Install Dependencies
Using `uv`:
```bash
uv sync
```

Or using standard `pip`:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest pytest-asyncio
```

---

## How to Run Locally

You can run, inspect, and test the server locally using several convenient methods.

The server defaults to **`stdio`** transport. You can switch to **Streamable HTTP** (bound to `localhost:9001`) using CLI flags or environment variables.

### Method 1: Package CLI Command

Run via `stdio` (default):
```bash
uv run file-management-mcp-server
```

Run via **Streamable HTTP** on `localhost:9001`:
```bash
uv run file-management-mcp-server --streamable-http
```

Use explicit transport flag:
```bash
uv run file-management-mcp-server --transport streamable-http
uv run file-management-mcp-server --transport stdio
```

Override host and port for HTTP transport:
```bash
uv run file-management-mcp-server --streamable-http --host 0.0.0.0 --port 9001
```

### Method 2: Python Module Invocation
Run directly using Python's module flag:
```bash
# stdio (default)
uv run python -m file_manager

# streamable-http
uv run python -m file_manager --streamable-http
uv run python -m file_manager --transport streamable-http --host localhost --port 9001
```

### Method 3: FastMCP CLI
Run the server using the `fastmcp` command-line runner:
```bash
# stdio
uv run fastmcp run src/file_manager/server.py

# streamable-http
uv run fastmcp run src/file_manager/server.py --transport streamable-http --host localhost --port 9001
```

### Method 4: Inspect Tool Schemas
Inspect the registered tools and their MCP parameter schemas:
```bash
# Display summary of all registered tools
uv run fastmcp list src/file_manager/server.py

# Output complete JSON schema adhering to MCP protocol specification
uv run fastmcp inspect src/file_manager/server.py --format mcp
```

### Method 5: Test Tool Execution via CLI (`fastmcp call`)
FastMCP allows calling tools directly from the terminal without an LLM:

```bash
# 1. Create a file
uv run fastmcp call src/file_manager/server.py create_file path=notes.txt content="Initial notes"

# 2. Read the file
uv run fastmcp call src/file_manager/server.py read_file path=notes.txt

# 3. Write / Append to the file
uv run fastmcp call src/file_manager/server.py write_file path=notes.txt content="\nAdded line 2" mode=append

# 4. Write / Edit by search-and-replace
uv run fastmcp call src/file_manager/server.py write_file path=notes.txt mode=replace target_text="Added line 2" replacement_text="Edited line 2"

# 5. Delete the file
uv run fastmcp call src/file_manager/server.py delete_file path=notes.txt
```

### Method 6: Interactive MCP Inspector Web UI
To test tools interactively with a graphical web UI:
```bash
uv run fastmcp dev inspector src/file_manager/server.py
```
This opens the MCP Inspector interface in your browser, where you can inspect capabilities, select tools, provide arguments, and view real-time JSON-RPC request/response payloads.

---

## Configuring with MCP Clients

The repository includes a ready-made [`mcp_server.json`](mcp_server.json) you can copy or reference:

```json
 {
      "mcpServers": {
        "my-file-manager-mcp-server-streamable-http": {
      "type": "streamable-http",
      "url": "http://localhost:9001/mcp"
    },
        "my-file-manager-mcp-server-stdio": {
          "command": "uv",
          "args": [
            "run",
            "--directory",
            "/absolute/path/to/file-management-mcp-server",
            "python",
            "server.py"
          ]
        }
      }
 }
```

> [!IMPORTANT]
> Before using the **streamable-http** entry, start the server first:
> ```bash
> uv run file-management-mcp-server --streamable-http
> ```
> The server will listen on `http://localhost:9001/mcp`.

---

### Claude Desktop

Add the server to your Claude Desktop configuration file:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

**Option A — stdio (process-based, no server pre-start required):**
```json
{
  "mcpServers": {
    "file-manager": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/file-management-mcp-server",
        "file-management-mcp-server",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

**Option B — Streamable HTTP (start server separately first):**
```json
{
  "mcpServers": {
    "file-manager": {
      "type": "streamable-http",
      "url": "http://localhost:9001/mcp"
    }
  }
}
```

---

### Antigravity / Cursor / Other MCP Clients

In your workspace configuration (e.g., `.cursor/mcp.json`):

**Option A — stdio:**
```json
{
  "mcpServers": {
    "file-manager": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "${workspaceFolder}",
        "file-management-mcp-server",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

**Option B — Streamable HTTP (start server separately first):**
```json
{
  "mcpServers": {
    "file-manager": {
      "type": "streamable-http",
      "url": "http://localhost:9001/mcp"
    }
  }
}
```

---

## Environment Variables & Sandboxing

You can customize file resolution, sandbox security, and server transport settings using environment variables:

| Variable | Default | Description |
|---|---|---|
| `MCP_WORKSPACE_DIR` | Current working directory (`pwd`) | Root directory used to resolve relative paths. |
| `MCP_ENFORCE_SANDBOX` | `false` | When set to `true`, strictly blocks any operations targeting paths outside `MCP_WORKSPACE_DIR` with a `PermissionError`. |
| `MCP_TRANSPORT` | `stdio` | Transport protocol: `stdio` or `streamable-http`. Also accepted as `FASTMCP_TRANSPORT`. |
| `MCP_HOST` | `localhost` | Host address for the streamable-http server. Also accepted as `FASTMCP_HOST`. |
| `MCP_PORT` | `9001` | Port for the streamable-http server. Also accepted as `FASTMCP_PORT`. |

Example running with strict sandboxing over stdio:
```bash
MCP_ENFORCE_SANDBOX=true MCP_WORKSPACE_DIR=/path/to/safe_folder uv run file-management-mcp-server
```

Example running as streamable-http via environment variable:
```bash
MCP_TRANSPORT=streamable-http MCP_HOST=localhost MCP_PORT=9001 uv run file-management-mcp-server
```

---

## Running the Automated Test Suite

The project includes an end-to-end test suite covering all tools, parameter validations, edge cases, MCP protocol calls, transport configuration, and sandboxing:

```bash
uv run pytest -v
```

All 31 tests verify compliance with file creation, reading with offsets/limits, deletion with safety checks, writing with overwrite/append/replace, MCP tool dispatching, transport configuration, and CLI argument parsing.
