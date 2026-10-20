"""Bounded read-only GitHub repository and Actions collection via gh CLI."""

import json
import subprocess
from urllib.parse import quote


class GitHubError(RuntimeError):
    """GitHub CLI returned an error."""


def _api(path: str, *, paginate: bool = True) -> object:
    command = ["gh", "api", path]
    if paginate:
        command.extend(["--paginate", "--slurp"])
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8",
            check=False, timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GitHubError("GitHub CLI is unavailable or timed out") from exc
    if result.returncode:
        raise GitHubError("GitHub API request failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise GitHubError("GitHub returned invalid JSON") from exc


def collect(owner: str) -> list[dict]:
    """Collect owned repositories; authenticated owner's private repos are included."""
    if not owner or not owner.strip():
        raise ValueError("Owner is required")
    safe_owner = quote(owner, safe="")
    me = _api("user", paginate=False)
    if isinstance(me, dict) and str(me.get("login", "")).lower() == owner.lower():
        path = "user/repos?per_page=100&affiliation=owner&sort=updated"
    else:
        path = f"users/{safe_owner}/repos?per_page=100&type=owner&sort=updated"
    pages = _api(path)
    if not isinstance(pages, list) or any(not isinstance(page, list) for page in pages):
        raise GitHubError("Expected a repository list")
    repositories = []
    for item in (item for page in pages for item in page):
        if not isinstance(item, dict) or not isinstance(item.get("owner"), dict):
            continue
        if str(item["owner"].get("login", "")).lower() != owner.lower():
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


_CI_RESULTS = {"success", "failure", "cancelled", "timed_out", "action_required",
               "skipped", "neutral", "startup_failure", "stale"}
_CI_PENDING = {"queued", "in_progress", "waiting", "requested", "pending"}


def enrich_ci(repositories: list[dict], owner: str, limit: int = 20) -> list[dict]:
    """Look up at most limit recent non-archived repos; never mistake errors for success.

    Repos not queried are explicitly 'not_checked'. Empty run history is 'no_runs'.
    """
    if not 1 <= limit <= 100:
        raise ValueError("ci-limit must be between 1 and 100")
    for repo in repositories:
        repo["ci_status"] = "not_checked"
    eligible = [r for r in repositories if not r.get("archived") and r.get("name")]
    eligible.sort(key=lambda r: str(r.get("pushed_at") or ""), reverse=True)
    for repo in eligible[:limit]:
        path = f"repos/{quote(owner, safe='')}/{quote(repo['name'], safe='')}/actions/runs?per_page=1"
        try:
            data = _api(path, paginate=False)
            if not isinstance(data, dict) or not isinstance(data.get("workflow_runs"), list):
                raise GitHubError("Unexpected Actions response")
            runs = data["workflow_runs"]
            if not runs:
                status = "no_runs"
            elif not isinstance(runs[0], dict):
                status = "unavailable"
            elif runs[0].get("status") == "completed":
                conclusion = runs[0].get("conclusion")
                status = conclusion if conclusion in _CI_RESULTS else "unavailable"
            else:
                current = runs[0].get("status")
                status = current if current in _CI_PENDING else "unavailable"
        except GitHubError:
            status = "unavailable"
        repo["ci_status"] = status
    return repositories
