"""Read-only GitHub repository collection using the existing gh login."""

import json
import subprocess
from urllib.parse import quote


class GitHubError(RuntimeError):
    """GitHub CLI returned an error."""


def _api(path: str) -> object:
    result = subprocess.run(
        ["gh", "api", path, "--paginate", "--slurp"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=120,
    )
    if result.returncode:
        raise GitHubError(result.stderr.strip() or "GitHub API request failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise GitHubError("GitHub returned invalid JSON") from exc


def collect(owner: str) -> list[dict]:
    """Collect metadata. Never downloads code, secrets or private issues."""
    safe_owner = quote(owner, safe="")
    items = _api(f"users/{safe_owner}/repos?per_page=100&type=owner&sort=updated")
    if not isinstance(items, list) or any(not isinstance(page, list) for page in items):
        raise GitHubError("Expected a repository list")
    repositories = []
    for item in (item for page in items for item in page):
        if not isinstance(item, dict) or item.get("owner", {}).get("login", "").lower() != owner.lower():
            continue
        repositories.append({
            "name": item.get("name", ""),
            "description": item.get("description") or "",
            "url": item.get("html_url", ""),
            "private": bool(item.get("private")),
            "archived": bool(item.get("archived")),
            "fork": bool(item.get("fork")),
            "language": item.get("language") or "",
            "stars": int(item.get("stargazers_count") or 0),
            "open_issues": int(item.get("open_issues_count") or 0),
            "updated_at": item.get("updated_at") or "",
            "pushed_at": item.get("pushed_at") or "",
            "default_branch": item.get("default_branch") or "",
            "size_kb": int(item.get("size") or 0),
        })
    return repositories

