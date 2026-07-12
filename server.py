from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Fast Note Sync")

# ── Config ───────────────────────────────────────────────────────────
def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().with_name(".env")
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://dansoft.net.br:9009/api")
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("API_TOKEN nao configurado. Defina a variavel no arquivo .env.")

REQUEST_TIMEOUT = float(os.getenv("API_TIMEOUT_SECONDS", "20"))


# ── HTTP Helpers ─────────────────────────────────────────────────────

def _auth_headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_TOKEN}",
        "X-Client": "Cherry Studio",
        "X-Client-Name": "Hermes MCP",
        "X-Client-Version": "1.0",
        "X-Default-Vault-Name": "_Obsidian",
    }


def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    """GET request to the API."""
    url = f"{API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    with httpx.Client(timeout=REQUEST_TIMEOUT, headers=_auth_headers()) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


def _post(path: str, body: dict[str, Any] | None = None) -> Any:
    """POST request to the API."""
    url = f"{API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    headers = _auth_headers()
    with httpx.Client(timeout=REQUEST_TIMEOUT, headers=headers) as client:
        resp = client.post(url, json=body)
        resp.raise_for_status()
        return resp.json()


def _delete(path: str, params: dict[str, Any] | None = None, body: dict[str, Any] | None = None) -> Any:
    """DELETE request to the API."""
    url = f"{API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    headers = _auth_headers()
    with httpx.Client(timeout=REQUEST_TIMEOUT, headers=headers) as client:
        if body:
            resp = client.request("DELETE", url, params=params, json=body)
        else:
            resp = client.delete(url, params=params)
        resp.raise_for_status()
        return resp.json()


def _patch(path: str, body: dict[str, Any] | None = None) -> Any:
    """PATCH request to the API."""
    url = f"{API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    headers = _auth_headers()
    with httpx.Client(timeout=REQUEST_TIMEOUT, headers=headers) as client:
        resp = client.patch(url, json=body)
        resp.raise_for_status()
        return resp.json()


def _put(path: str, body: dict[str, Any] | None = None) -> Any:
    """PUT request to the API."""
    url = f"{API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    headers = _auth_headers()
    with httpx.Client(timeout=REQUEST_TIMEOUT, headers=headers) as client:
        resp = client.put(url, json=body)
        resp.raise_for_status()
        return resp.json()


# ═══════════════════════════════════════════════════════════════════════
#  🔴 ESSENTIAL ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

# ── System / Health ───────────────────────────────────────────────────

@mcp.tool
def health_check() -> dict[str, Any]:
    """Check service health status, including database connection."""
    return _get("/health")


@mcp.tool
def get_version() -> dict[str, Any]:
    """Get current server software version, Git tag, and build time."""
    return _get("/version")


@mcp.tool
def get_webgui_config() -> dict[str, Any]:
    """Get non-sensitive configuration required for frontend display (font settings, registration status, etc.)."""
    return _get("/webgui/config")


# ── User ──────────────────────────────────────────────────────────────

@mcp.tool
def get_user_info() -> dict[str, Any]:
    """Get current authenticated user info."""
    return _get("/user/info")


# ── Vaults ────────────────────────────────────────────────────────────

@mcp.tool
def list_vaults() -> dict[str, Any]:
    """Get all note vaults for the current user."""
    return _get("/vault")


@mcp.tool
def get_vault_detail(vault_id: int) -> dict[str, Any]:
    """Get specific vault configuration details by vault ID."""
    return _get("/vault/get", params={"id": vault_id})


# ── Folders ───────────────────────────────────────────────────────────

@mcp.tool
def get_folder_info(vault: str, path: str = "", path_hash: str = "") -> dict[str, Any]:
    """Get folder info by path or pathHash from a given vault."""
    params: dict[str, Any] = {"vault": vault}
    if path:
        params["path"] = path
    if path_hash:
        params["pathHash"] = path_hash
    return _get("/folder", params=params)


@mcp.tool
def create_folder(vault: str, path: str) -> dict[str, Any]:
    """Create a new folder or restore a deleted one by path."""
    return _post("/folder", body={"vault": vault, "path": path})


@mcp.tool
def delete_folder(vault: str, path: str = "", path_hash: str = "") -> dict[str, Any]:
    """Soft delete a folder by path or pathHash."""
    body: dict[str, Any] = {"vault": vault}
    if path:
        body["path"] = path
    if path_hash:
        body["pathHash"] = path_hash
    return _delete("/folder", body=body)


@mcp.tool
def get_folder_tree(vault: str, depth: int = 3) -> dict[str, Any]:
    """Get the complete folder tree structure for a vault."""
    return _get("/folder/tree", params={"vault": vault, "depth": depth})


@mcp.tool
def list_folders(vault: str, path: str = "", path_hash: str = "") -> dict[str, Any]:
    """Get folder list by parent path or pathHash."""
    params: dict[str, Any] = {"vault": vault}
    if path:
        params["path"] = path
    if path_hash:
        params["pathHash"] = path_hash
    return _get("/folders", params=params)


@mcp.tool
def list_folder_notes(
    vault: str,
    path: str = "",
    path_hash: str = "",
    sort_by: str = "",
    sort_order: str = "",
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """List non-deleted notes in a specific folder with pagination and sorting."""
    params: dict[str, Any] = {
        "vault": vault,
        "page": page,
        "pageSize": page_size,
    }
    if path:
        params["path"] = path
    if path_hash:
        params["pathHash"] = path_hash
    if sort_by:
        params["sortBy"] = sort_by
    if sort_order:
        params["sortOrder"] = sort_order
    return _get("/folder/notes", params=params)


# ── Notes ─────────────────────────────────────────────────────────────

@mcp.tool
def get_note(
    vault: str,
    path: str = "",
    path_hash: str = "",
    is_recycle: bool = False,
) -> dict[str, Any]:
    """Get specific note content and metadata by path or path hash."""
    params: dict[str, Any] = {"vault": vault, "isRecycle": is_recycle}
    if path:
        params["path"] = path
    if path_hash:
        params["pathHash"] = path_hash
    return _get("/note", params=params)


@mcp.tool
def create_or_update_note(vault: str, path: str, content: str) -> dict[str, Any]:
    """Create a new note or update an existing one (identified by path)."""
    return _post("/note", body={"vault": vault, "path": path, "content": content})


@mcp.tool
def delete_note(vault: str, path: str = "", path_hash: str = "") -> dict[str, Any]:
    """Move a note to trash."""
    body: dict[str, Any] = {"vault": vault}
    if path:
        body["path"] = path
    if path_hash:
        body["pathHash"] = path_hash
    return _delete("/note", body=body)


@mcp.tool
def search_notes(
    vault: str,
    keyword: str = "",
    search_content: bool = False,
    search_mode: str = "path",
    is_recycle: bool = False,
    sort_by: str = "",
    sort_order: str = "",
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Search/list notes with pagination, keyword filtering, and content search.

    Search modes: 'path' (default), 'content', 'regex'.
    """
    params: dict[str, Any] = {
        "vault": vault,
        "isRecycle": is_recycle,
        "page": page,
        "pageSize": page_size,
    }
    if keyword:
        params["keyword"] = keyword
    if search_content:
        params["searchContent"] = "true"
    if search_mode:
        params["searchMode"] = search_mode
    if sort_by:
        params["sortBy"] = sort_by
    if sort_order:
        params["sortOrder"] = sort_order
    return _get("/notes", params=params)


@mcp.tool
def get_note_outlinks(vault: str, path: str = "", path_hash: str = "") -> dict[str, Any]:
    """Get other notes that the specified note links to."""
    params: dict[str, Any] = {"vault": vault}
    if path:
        params["path"] = path
    if path_hash:
        params["pathHash"] = path_hash
    return _get("/note/outlinks", params=params)


@mcp.tool
def get_note_backlinks(vault: str, path: str = "", path_hash: str = "") -> dict[str, Any]:
    """Get all other notes that link to the specified note."""
    params: dict[str, Any] = {"vault": vault}
    if path:
        params["path"] = path
    if path_hash:
        params["pathHash"] = path_hash
    return _get("/note/backlinks", params=params)


# ── Files ─────────────────────────────────────────────────────────────

@mcp.tool
def get_file_list(
    vault: str,
    is_recycle: bool = False,
    keyword: str = "",
    sort_by: str = "",
    sort_order: str = "",
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Get attachment list with pagination, search, filter, and sort support."""
    params: dict[str, Any] = {
        "vault": vault,
        "isRecycle": is_recycle,
        "page": page,
        "pageSize": page_size,
    }
    if keyword:
        params["keyword"] = keyword
    if sort_by:
        params["sortBy"] = sort_by
    if sort_order:
        params["sortOrder"] = sort_order
    return _get("/files", params=params)


@mcp.tool
def get_file_info(
    vault: str,
    path: str = "",
    path_hash: str = "",
    is_recycle: bool = False,
) -> dict[str, Any]:
    """Get attachment metadata by path."""
    params: dict[str, Any] = {"vault": vault, "isRecycle": is_recycle}
    if path:
        params["path"] = path
    if path_hash:
        params["pathHash"] = path_hash
    return _get("/file/info", params=params)


# ═══════════════════════════════════════════════════════════════════════
#  🟡 IMPORTANT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

# ── Note mutations ────────────────────────────────────────────────────

@mcp.tool
def append_to_note(vault: str, path: str, content: str) -> dict[str, Any]:
    """Append content to the end of a note."""
    return _post("/note/append", body={"vault": vault, "path": path, "content": content})


@mcp.tool
def prepend_to_note(vault: str, path: str, content: str) -> dict[str, Any]:
    """Insert content at the beginning of a note (after frontmatter)."""
    return _post("/note/prepend", body={"vault": vault, "path": path, "content": content})


@mcp.tool
def set_note_frontmatter(vault: str, path: str, key: str, value: str) -> dict[str, Any]:
    """Set a frontmatter field on a note."""
    return _patch("/note/frontmatter", body={"vault": vault, "path": path, "updates": {key: [value]}})


@mcp.tool
def delete_note_frontmatter(vault: str, path: str, key: str) -> dict[str, Any]:
    """Delete a frontmatter field from a note."""
    return _patch("/note/frontmatter", body={"vault": vault, "path": path, "remove": [key]})


@mcp.tool
def move_note(vault: str, old_path: str, new_path: str) -> dict[str, Any]:
    """Move a note to a new path."""
    return _post("/note/rename", body={"vault": vault, "oldPath": old_path, "path": new_path})


@mcp.tool
def rename_note(vault: str, old_path: str, new_path: str) -> dict[str, Any]:
    """Rename a note to a new path."""
    return _post("/note/rename", body={"vault": vault, "oldPath": old_path, "path": new_path})


@mcp.tool
def replace_in_note(vault: str, path: str, old_text: str, new_text: str, is_regex: bool = False) -> dict[str, Any]:
    """Find and replace in a note, supporting regular expressions."""
    return _post("/note/replace", body={"vault": vault, "path": path, "find": old_text, "replace": new_text, "regex": is_regex})


@mcp.tool
def restore_note(vault: str, path: str, path_hash: str = "") -> dict[str, Any]:
    """Restore deleted note from trash."""
    return _put("/note/restore", body={"vault": vault, "path": path, "pathHash": path_hash})


# ── Note History ──────────────────────────────────────────────────────

@mcp.tool
def get_note_history(vault: str, path: str, page: int = 1, page_size: int = 10) -> dict[str, Any]:
    """Get all history records for a specific note with pagination."""
    return _get("/note/histories", params={"vault": vault, "path": path, "page": page, "pageSize": page_size})


@mcp.tool
def get_note_history_detail(history_id: int) -> dict[str, Any]:
    """Get specific note history content by history record ID."""
    return _get("/note/history", params={"id": history_id})


# ── Shares ────────────────────────────────────────────────────────────

@mcp.tool
def list_shares(sort_by: str = "created_at", sort_order: str = "desc", page: int = 1, page_size: int = 10) -> dict[str, Any]:
    """Get all shares of the user with sorting and pagination."""
    return _get("/shares", params={"sort_by": sort_by, "sort_order": sort_order, "page": page, "pageSize": page_size})


# ── Storage ───────────────────────────────────────────────────────────

@mcp.tool
def get_storage_configs() -> dict[str, Any]:
    """Get storage configuration list."""
    return _get("/storage")


@mcp.tool
def get_enabled_storage_types() -> dict[str, Any]:
    """Get list of enabled storage types (localfs, oss, s3, r2, minio, webdav)."""
    return _get("/storage/enabled_types")


# ── Git Sync ──────────────────────────────────────────────────────────

@mcp.tool
def get_git_sync_configs() -> dict[str, Any]:
    """Get git sync configurations."""
    return _get("/git-sync/configs")


# ── Admin ─────────────────────────────────────────────────────────────

@mcp.tool
def get_system_info() -> dict[str, Any]:
    """Get system information and Go runtime data (requires admin)."""
    return _get("/admin/systeminfo")


# ── Backup ────────────────────────────────────────────────────────────

@mcp.tool
def get_backup_configs() -> dict[str, Any]:
    """Get backup configurations."""
    return _get("/backup/configs")


if __name__ == "__main__":
    mcp.run()
