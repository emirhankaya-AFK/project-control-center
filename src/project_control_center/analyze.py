"""Deterministic, explainable portfolio analysis."""

from datetime import datetime, timezone
from difflib import SequenceMatcher


def _age_days(timestamp: str, now: datetime) -> int | None:
    try:
        then = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return max(0, (now - then).days)
    except (ValueError, TypeError):
        return None


def analyze(repositories: list[dict], now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    rows = []
    for repo in repositories:
        age = _age_days(repo.get("pushed_at", ""), now)
        findings = []
        if not repo.get("description"):
            findings.append("Açıklama eksik")
        if not repo.get("language"):
            findings.append("Dil bilgisi yok")
        if age is not None and age >= 180 and not repo.get("archived"):
            findings.append(f"{age} gündür kod güncellenmemiş")
        if repo.get("open_issues", 0) >= 10:
            findings.append(f"{repo['open_issues']} açık issue")
        score = max(0, 100 - 20 * (not bool(repo.get("description")))
                    - 10 * (not bool(repo.get("language")))
                    - (25 if age is not None and age >= 180 else 0)
                    - (15 if repo.get("open_issues", 0) >= 10 else 0))
        rows.append({**repo, "age_days": age, "score": score, "findings": findings})

    duplicates = []
    public = [r for r in rows if not r.get("private") and not r.get("archived")]
    for i, left in enumerate(public):
        for right in public[i + 1:]:
            similarity = SequenceMatcher(None, left["name"].lower(), right["name"].lower()).ratio()
            if similarity >= 0.72:
                duplicates.append({"a": left["name"], "b": right["name"], "similarity": round(similarity, 2)})
    duplicates.sort(key=lambda x: x["similarity"], reverse=True)
    rows.sort(key=lambda x: (x["score"], x["name"].lower()))
    return {
        "generated_at": now.isoformat(),
        "total": len(rows),
        "private": sum(bool(r.get("private")) for r in rows),
        "archived": sum(bool(r.get("archived")) for r in rows),
        "repositories": rows,
        "possible_name_overlaps": duplicates,
    }

