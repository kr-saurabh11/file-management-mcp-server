"""Unit and integration tests for the FastMCP File Operations Server.

Tests cover:
- Tool implementations (`create_file`, `read_file`, `delete_file`, `write_file`)
- Edge cases (missing files, overwrite guards, directories, offsets/limits, invalid modes)
- MCP server protocol dispatching via `mcp.call_tool` and `mcp.list_tools`
- Tool alias routing for `edit_file`
- Security and workspace boundary sandboxing (`MCP_ENFORCE_SANDBOX`)
"""

from pathlib import Path
import pytest
from fastmcp.exceptions import ToolError

from file_manager import (
    create_file,
    delete_file,
    mcp,
    read_file,
    write_file,
)


# ==============================================================================
# 1. create_file tool tests
# ==============================================================================


def test_create_file_empty(test_dir: Path):
    """Test creating a new empty file at a valid path."""
    target = test_dir / "new_file.txt"
    res = create_file(str(target))
    assert target.exists()
    assert target.read_text(encoding="utf-8") == ""
    assert "Successfully created file" in res


def test_create_file_with_content_and_nested_dirs(test_dir: Path):
    """Test creating a file with initial content and automatically creating parent folders."""
    target = test_dir / "sub" / "folder" / "hello.txt"
    res = create_file(str(target), content="Hello, MCP World!")
    assert target.exists()
    assert target.read_text(encoding="utf-8") == "Hello, MCP World!"
    assert "17 bytes written" in res


def test_create_file_already_exists_fails_without_overwrite(test_dir: Path):
    """Test that creating an existing file raises FileExistsError when overwrite=False."""
    target = test_dir / "existing.txt"
    target.write_text("initial", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists"):
        create_file(str(target), content="new content", overwrite=False)

    assert target.read_text(encoding="utf-8") == "initial"


def test_create_file_already_exists_succeeds_with_overwrite(test_dir: Path):
    """Test that creating an existing file succeeds and overwrites content when overwrite=True."""
    target = test_dir / "existing.txt"
    target.write_text("initial", encoding="utf-8")

    res = create_file(str(target), content="overwritten", overwrite=True)
    assert target.read_text(encoding="utf-8") == "overwritten"
    assert "Successfully created file" in res


def test_create_file_on_directory_fails(test_dir: Path):
    """Test that attempting to create a file over an existing directory raises IsADirectoryError."""
    sub_dir = test_dir / "dir_target"
    sub_dir.mkdir()

    with pytest.raises(IsADirectoryError):
        create_file(str(sub_dir))


# ==============================================================================
# 2. read_file tool tests
# ==============================================================================


def test_read_file_full(test_dir: Path):
    """Test reading the complete text content of a file."""
    target = test_dir / "sample.txt"
    sample_text = "Line 1\nLine 2\nLine 3\n"
    target.write_text(sample_text, encoding="utf-8")

    content = read_file(str(target))
    assert content == sample_text


def test_read_file_offset_and_limit(test_dir: Path):
    """Test line-based pagination using offset and limit parameters."""
    target = test_dir / "multiline.txt"
    target.write_text("L0\nL1\nL2\nL3\nL4\n", encoding="utf-8")

    # Read from offset 1 with limit 2 -> L1, L2
    result = read_file(str(target), offset=1, limit=2)
    assert result == "L1\nL2\n"

    # Read from offset 3 to end
    result_end = read_file(str(target), offset=3)
    assert result_end == "L3\nL4\n"


def test_read_file_non_existent(test_dir: Path):
    """Test that reading a non-existent file raises FileNotFoundError."""
    target = test_dir / "missing.txt"
    with pytest.raises(FileNotFoundError):
        read_file(str(target))


def test_read_file_directory(test_dir: Path):
    """Test that attempting to read a directory raises IsADirectoryError."""
    with pytest.raises(IsADirectoryError):
        read_file(str(test_dir))


def test_read_file_negative_offset_or_limit(test_dir: Path):
    """Test that negative offset or limit values raise ValueError."""
    target = test_dir / "file.txt"
    target.write_text("content", encoding="utf-8")

    with pytest.raises(ValueError, match="Offset cannot be negative"):
        read_file(str(target), offset=-1)

    with pytest.raises(ValueError, match="Limit cannot be negative"):
        read_file(str(target), limit=-1)


# ==============================================================================
# 3. delete_file tool tests
# ==============================================================================


def test_delete_file_success(test_dir: Path):
    """Test safely deleting an existing file."""
    target = test_dir / "delete_me.txt"
    target.write_text("bye", encoding="utf-8")
    assert target.exists()

    res = delete_file(str(target))
    assert not target.exists()
    assert "Successfully deleted file" in res


def test_delete_file_missing_fails(test_dir: Path):
    """Test that deleting a missing file raises FileNotFoundError when missing_ok=False."""
    target = test_dir / "non_existent.txt"
    with pytest.raises(FileNotFoundError):
        delete_file(str(target), missing_ok=False)


def test_delete_file_missing_ok(test_dir: Path):
    """Test that deleting a missing file succeeds cleanly when missing_ok=True."""
    target = test_dir / "non_existent.txt"
    res = delete_file(str(target), missing_ok=True)
    assert "missing_ok=True" in res


def test_delete_file_on_directory_fails(test_dir: Path):
    """Test that delete_file refuses to delete a directory and raises IsADirectoryError."""
    sub = test_dir / "sub_folder"
    sub.mkdir()
    with pytest.raises(IsADirectoryError):
        delete_file(str(sub))


# ==============================================================================
# 4. write_file / edit_file tool tests
# ==============================================================================


def test_write_file_overwrite_mode(test_dir: Path):
    """Test overwriting an existing file's entire content."""
    target = test_dir / "write_test.txt"
    target.write_text("old text", encoding="utf-8")

    res = write_file(str(target), content="fresh content", mode="overwrite")
    assert target.read_text(encoding="utf-8") == "fresh content"
    assert "mode='overwrite'" in res


def test_write_file_append_mode(test_dir: Path):
    """Test appending content to the end of an existing file."""
    target = test_dir / "append_test.txt"
    target.write_text("Hello", encoding="utf-8")

    res = write_file(str(target), content=" World!", mode="append")
    assert target.read_text(encoding="utf-8") == "Hello World!"
    assert "mode='append'" in res


def test_write_file_create_if_missing(test_dir: Path):
    """Test that write_file automatically creates the file and parent folders when missing."""
    target = test_dir / "new_nested" / "file.txt"
    write_file(str(target), content="created via write", mode="overwrite")
    assert target.exists()
    assert target.read_text(encoding="utf-8") == "created via write"


def test_write_file_create_if_missing_false(test_dir: Path):
    """Test that write_file raises FileNotFoundError if create_if_missing=False on missing file."""
    target = test_dir / "ghost.txt"
    with pytest.raises(FileNotFoundError):
        write_file(str(target), content="fail", mode="overwrite", create_if_missing=False)


def test_write_file_replace_mode(test_dir: Path):
    """Test editing a file via targeted string replacement in replace mode."""
    target = test_dir / "replace_test.txt"
    target.write_text("The quick brown fox jumps over the lazy dog.", encoding="utf-8")

    res = write_file(
        str(target),
        mode="replace",
        target_text="brown fox",
        replacement_text="white cat",
    )
    assert target.read_text(encoding="utf-8") == "The quick white cat jumps over the lazy dog."
    assert "replaced 1 occurrence" in res


def test_write_file_replace_mode_target_not_found(test_dir: Path):
    """Test that replace mode raises ValueError when the target search text is absent."""
    target = test_dir / "replace_fail.txt"
    target.write_text("Hello world", encoding="utf-8")

    with pytest.raises(ValueError, match="Target text was not found"):
        write_file(
            str(target),
            mode="replace",
            target_text="non-existent text",
            replacement_text="new",
        )


def test_write_file_replace_aliases(test_dir: Path):
    """Test that old_text and new_text parameter aliases work seamlessly for replacements."""
    target = test_dir / "alias_test.txt"
    target.write_text("foo bar foo baz", encoding="utf-8")

    # Using old_text and new_text aliases
    write_file(str(target), old_text="foo", new_text="qux")
    assert target.read_text(encoding="utf-8") == "qux bar qux baz"


# ==============================================================================
# 5. MCP Protocol Server Integration tests
# ==============================================================================


@pytest.mark.asyncio
async def test_mcp_list_tools():
    """Verify that FastMCP exposes the 4 expected standard tools via MCP list_tools."""
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "create_file" in tool_names
    assert "read_file" in tool_names
    assert "delete_file" in tool_names
    assert "write_file" in tool_names
    assert len(tools) == 4


@pytest.mark.asyncio
async def test_mcp_call_tools_end_to_end(test_dir: Path):
    """Test an end-to-end multi-step workflow invoking tools via MCP call_tool."""
    target = test_dir / "mcp_flow.txt"
    target_str = str(target)

    # 1. create_file via call_tool
    res1 = await mcp.call_tool("create_file", {"path": target_str, "content": "Step 1\n"})
    assert "Successfully created" in res1.content[0].text

    # 2. write_file (append) via call_tool
    res2 = await mcp.call_tool(
        "write_file", {"path": target_str, "content": "Step 2\n", "mode": "append"}
    )
    assert "Successfully appended" in res2.content[0].text

    # 3. read_file via call_tool
    res3 = await mcp.call_tool("read_file", {"path": target_str})
    assert res3.content[0].text == "Step 1\nStep 2\n"

    # 4. edit_file alias via call_tool
    res4 = await mcp.call_tool(
        "edit_file",
        {
            "path": target_str,
            "old_text": "Step 1",
            "new_text": "Phase 1",
        },
    )
    assert "Successfully edited" in res4.content[0].text

    # Verify content after edit
    res5 = await mcp.call_tool("read_file", {"path": target_str})
    assert res5.content[0].text == "Phase 1\nStep 2\n"

    # 5. delete_file via call_tool
    res6 = await mcp.call_tool("delete_file", {"path": target_str})
    assert "Successfully deleted" in res6.content[0].text
    assert not target.exists()


@pytest.mark.asyncio
async def test_mcp_call_tool_error_handling(test_dir: Path):
    """Verify that FastMCP translates application exceptions into standard ToolError responses."""
    missing_path = str(test_dir / "does_not_exist.txt")
    with pytest.raises(ToolError):
        await mcp.call_tool("read_file", {"path": missing_path})


# ==============================================================================
# 6. Sandboxing tests
# ==============================================================================


def test_sandbox_security(test_dir: Path, monkeypatch):
    """Verify sandbox containment prevents unauthorized directory traversal outside workspace."""
    sandbox_dir = test_dir / "sandbox"
    sandbox_dir.mkdir()
    outside_dir = test_dir / "outside"
    outside_dir.mkdir()

    monkeypatch.setattr("file_manager.config.WORKSPACE_DIR", sandbox_dir)
    monkeypatch.setattr("file_manager.config.ENFORCE_SANDBOX", True)

    # File inside sandbox should succeed
    inside_file = sandbox_dir / "safe.txt"
    create_file(str(inside_file), content="safe")
    assert inside_file.exists()

    # File outside sandbox should raise PermissionError
    outside_file = outside_dir / "forbidden.txt"
    with pytest.raises(PermissionError, match="Access denied"):
        create_file(str(outside_file), content="forbidden")
