"""Core file operations for the FastMCP File Management Server.

This module provides standard file management functions that adhere to the
Model Context Protocol (MCP) tool conventions. All operations support both
relative and absolute paths, UTF-8 text encoding, parent directory auto-creation,
and optional sandbox boundary validation.
"""

from pathlib import Path
from typing import Literal

from file_manager.config import resolve_path


def create_file(
    path: str,
    content: str = "",
    overwrite: bool = False,
    encoding: str = "utf-8",
) -> str:
    """Create a new file with optional initial content.

    Creates a new text file at the specified path. If parent directories in the
    path do not exist, they are created automatically. If the target path
    already exists as an existing file, the operation will fail unless
    `overwrite=True` is explicitly specified.

    Args:
        path: Target file path (relative to the workspace root or an absolute path).
        content: Optional initial text content to populate the file with. Defaults to empty string.
        overwrite: If True, replaces existing file content. If False, raises an error if the file exists.
        encoding: Character encoding for writing text (default: "utf-8").

    Returns:
        Confirmation message containing the resolved path and number of bytes written.

    Raises:
        FileExistsError: If the target file already exists and overwrite is False.
        IsADirectoryError: If the target path points to an existing directory.
        PermissionError: If sandbox mode is enabled and the path resolves outside the workspace.
        ValueError: If the file path is empty or invalid.

    Examples:
        >>> create_file("notes.txt", content="Initial draft")
        "Successfully created file 'notes.txt' (13 bytes written)."

        >>> create_file("nested/dir/app.log", overwrite=True)
        "Successfully created file 'nested/dir/app.log' (0 bytes written)."
    """
    resolved_path = resolve_path(path)

    if resolved_path.exists():
        if resolved_path.is_dir():
            raise IsADirectoryError(f"Target path '{path}' already exists as a directory.")
        if not overwrite:
            raise FileExistsError(
                f"File '{path}' already exists. Set overwrite=True or use write_file to modify it."
            )

    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_path.write_text(content, encoding=encoding)
    bytes_written = len(content.encode(encoding))
    return f"Successfully created file '{path}' ({bytes_written} bytes written)."


def read_file(
    path: str,
    offset: int = 0,
    limit: int | None = None,
    encoding: str = "utf-8",
) -> str:
    """Read the text content of a file.

    Reads and returns the content of the specified text file. Supports line-based
    pagination through `offset` and `limit`, allowing AI agents to inspect
    specific portions of large files without loading the entire content into memory.

    Args:
        path: File path to read (relative to the workspace root or an absolute path).
        offset: Zero-indexed line number to start reading from (default: 0).
        limit: Maximum number of lines to return. If None, reads from offset to the end of the file.
        encoding: Text encoding to use when decoding file bytes (default: "utf-8").

    Returns:
        The complete text content of the file or the specified slice of lines.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        IsADirectoryError: If the path points to a directory rather than a file.
        PermissionError: If sandbox mode is enabled and the path resolves outside the workspace.
        ValueError: If offset or limit are negative, or if the file cannot be decoded as text.

    Examples:
        >>> # Read full file
        >>> read_file("config.json")
        '{"port": 8080}'

        >>> # Read lines 10 to 25 (15 lines starting at line index 10)
        >>> read_file("large.log", offset=10, limit=15)
        'Line 10\\nLine 11\\n...'
    """
    if offset < 0:
        raise ValueError(f"Offset cannot be negative: {offset}")
    if limit is not None and limit < 0:
        raise ValueError(f"Limit cannot be negative: {limit}")

    resolved_path = resolve_path(path)

    if not resolved_path.exists():
        raise FileNotFoundError(f"File '{path}' does not exist.")
    if resolved_path.is_dir():
        raise IsADirectoryError(f"Path '{path}' is a directory, not a file.")

    try:
        content = resolved_path.read_text(encoding=encoding)
    except UnicodeDecodeError as err:
        raise ValueError(
            f"Unable to decode '{path}' with encoding '{encoding}'. The file may be binary. ({err})"
        ) from err

    if offset == 0 and limit is None:
        return content

    lines = content.splitlines(keepends=True)
    end = offset + limit if limit is not None else None
    return "".join(lines[offset:end])


def delete_file(
    path: str,
    missing_ok: bool = False,
) -> str:
    """Delete a file from the filesystem.

    Safely removes a file at the given path. As a safety measure, this function
    strictly refuses to delete directories (directory removal requires dedicated
    directory cleanup tools).

    Args:
        path: File path to delete (relative to the workspace root or an absolute path).
        missing_ok: If True, suppress errors if the file does not exist. Defaults to False.

    Returns:
        Confirmation message confirming file deletion or indicating file was already absent.

    Raises:
        FileNotFoundError: If the target file does not exist and missing_ok is False.
        IsADirectoryError: If the specified path is a directory.
        PermissionError: If sandbox mode is enabled and the path resolves outside the workspace.
        ValueError: If the path is empty or invalid.

    Examples:
        >>> delete_file("temp.txt")
        "Successfully deleted file 'temp.txt'."

        >>> delete_file("cache.tmp", missing_ok=True)
        "File 'cache.tmp' does not exist (missing_ok=True, no action taken)."
    """
    resolved_path = resolve_path(path)

    if not resolved_path.exists():
        if missing_ok:
            return f"File '{path}' does not exist (missing_ok=True, no action taken)."
        raise FileNotFoundError(f"File '{path}' does not exist.")

    if resolved_path.is_dir():
        raise IsADirectoryError(f"Path '{path}' is a directory. delete_file only deletes files.")

    resolved_path.unlink()
    return f"Successfully deleted file '{path}'."


def write_file(
    path: str,
    content: str = "",
    mode: Literal["overwrite", "append", "replace"] = "overwrite",
    target_text: str | None = None,
    replacement_text: str | None = None,
    old_text: str | None = None,
    new_text: str | None = None,
    create_if_missing: bool = True,
    encoding: str = "utf-8",
) -> str:
    """Write or edit content in a file.

    Provides comprehensive file writing and editing capabilities supporting three
    distinct operation modes:
    1. 'overwrite': Replaces the entire content of an existing file or creates a new file.
    2. 'append': Appends content to the end of an existing file (or creates it if missing).
    3. 'replace': Performs targeted search-and-replace of specific text snippets within the file.

    For convenience and compatibility across different LLM tool call schemas,
    `old_text` and `new_text` are accepted as intuitive aliases for `target_text`
    and `replacement_text`.

    Args:
        path: Path to the file to write or edit (relative to workspace or absolute).
        content: Text content to write, append, or use as replacement text.
        mode: Operation mode: 'overwrite', 'append', or 'replace' (default: 'overwrite').
        target_text: Exact string to find and replace when mode is 'replace'.
        replacement_text: Replacement string for target_text (defaults to content if omitted).
        old_text: Convenient alias for target_text. Automatically activates 'replace' mode.
        new_text: Convenient alias for replacement_text.
        create_if_missing: If True, creates the file when writing/appending to a missing file.
        encoding: Character encoding for text reading and writing (default: "utf-8").

    Returns:
        Detailed status message describing the outcome, bytes written/appended, or occurrences replaced.

    Raises:
        FileNotFoundError: If the target file does not exist and create_if_missing is False,
            or if attempting to replace text in a non-existent file.
        IsADirectoryError: If the path is an existing directory.
        PermissionError: If sandbox mode is enabled and the path resolves outside the workspace.
        ValueError: If mode is unsupported, or if target_text is missing or not found in replace mode.

    Examples:
        >>> # Overwrite / create file
        >>> write_file("config.env", content="DEBUG=1\\n", mode="overwrite")
        "Successfully wrote 8 bytes to 'config.env' (mode='overwrite')."

        >>> # Append to file
        >>> write_file("config.env", content="PORT=8080\\n", mode="append")
        "Successfully appended 10 bytes to 'config.env' (mode='append', total 18 bytes)."

        >>> # Targeted text edit
        >>> write_file("config.env", mode="replace", target_text="DEBUG=1", replacement_text="DEBUG=0")
        "Successfully edited 'config.env': replaced 1 occurrence(s) of specified text (mode='replace')."
    """
    resolved_path = resolve_path(path)

    if resolved_path.exists() and resolved_path.is_dir():
        raise IsADirectoryError(f"Target path '{path}' is a directory, not a file.")

    # Support aliases for targeted replacement
    if old_text is not None and target_text is None:
        target_text = old_text
        mode = "replace"
    if new_text is not None and replacement_text is None:
        replacement_text = new_text

    if mode == "overwrite":
        if not resolved_path.exists() and not create_if_missing:
            raise FileNotFoundError(f"File '{path}' does not exist and create_if_missing is False.")
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path.write_text(content, encoding=encoding)
        bytes_written = len(content.encode(encoding))
        return f"Successfully wrote {bytes_written} bytes to '{path}' (mode='overwrite')."

    elif mode == "append":
        if not resolved_path.exists():
            if not create_if_missing:
                raise FileNotFoundError(f"File '{path}' does not exist and create_if_missing is False.")
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            resolved_path.write_text(content, encoding=encoding)
            bytes_written = len(content.encode(encoding))
            return f"Successfully created and wrote {bytes_written} bytes to '{path}' (mode='append')."

        current_data = resolved_path.read_text(encoding=encoding)
        new_data = current_data + content
        resolved_path.write_text(new_data, encoding=encoding)
        bytes_appended = len(content.encode(encoding))
        return f"Successfully appended {bytes_appended} bytes to '{path}' (mode='append', total {len(new_data.encode(encoding))} bytes)."

    elif mode == "replace":
        if not resolved_path.exists():
            raise FileNotFoundError(f"Cannot edit non-existent file '{path}'.")

        search_target = target_text
        if not search_target:
            raise ValueError("When mode is 'replace', 'target_text' (or 'old_text') must be provided.")

        rep_text = replacement_text if replacement_text is not None else content
        current_data = resolved_path.read_text(encoding=encoding)

        if search_target not in current_data:
            raise ValueError(f"Target text was not found in file '{path}'.")

        occurrences = current_data.count(search_target)
        updated_data = current_data.replace(search_target, rep_text)
        resolved_path.write_text(updated_data, encoding=encoding)
        return (
            f"Successfully edited '{path}': replaced {occurrences} occurrence(s) "
            f"of specified text (mode='replace')."
        )

    else:
        raise ValueError(
            f"Invalid mode '{mode}'. Supported modes are: 'overwrite', 'append', 'replace'."
        )
