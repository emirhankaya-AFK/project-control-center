"""Deterministic, explainable portfolio analysis."""

from collections import Counter
from datetime import datetime, timezone
from difflib import SequenceMatcher

_BAD_CI = {"failure", "timed_out", "action_required", "startup_failure"}
_CI_LABELS = {"success": "Başarılı", "failure": "Başarısız", "timed_out": "Zaman aşımı",
              "action_required": "Müdahale gerekli", "startup_failure": "Başlatılamadı",
              "cancelled": "İptal", "stale": "Eski", "skipped": "Atlandı",
              "neutral": "Nötr", "queued": "Kuyrukta", "in_progress": "Çalışıyor",
              "waiting": "Bekliyor", "requested": "İstendi", "pending": "Beklemede",
              "no_runs": "Çalışma bulunamadı", "not_checked": "Kontrol edilmedi",
              "unavailable": "Doğrulanamadı"}


def _age_days(timestamp: str, now: datetime) -> int | None:
    try:
        then = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if then.tzinfo is None:
            then = then.replace(tzinfo=timezone.utc)
        return max(0, (now - then).days)
    except (ValueError, TypeError, AttributeError):
        return None


def analyze(repositories: list[dict], now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    rows = []
    for repo in repositories:
        age = _age_days(repo.get("pushed_at", ""), now)
        findings = []
        archived = bool(repo.get("archived"))
        ci_status = repo.get("ci_status", "not_checked")
        if ci_status not in _CI_LABELS:
            ci_status = "unavailable"
        if not repo.get("description"):
            findings.append("Açıklama eksik")
        if not repo.get("language"):
            findings.append("Dil bilgisi yok")
        if age is not None and age >= 180 and not archived:
            findings.append(f"{age} gündür kod güncellenmemiş")
        if repo.get("open_issues", 0) >= 10:
            findings.append(f"{repo['open_issues']} açık issue")
        if ci_status in _BAD_CI and not archived:
            findings.append(f"Son CI: {_CI_LABELS[ci_status]}")
        elif ci_status == "unavailable":
            findings.append("CI durumu doğrulanamadı")
        score = max(0, 100 - 20 * (not bool(repo.get("description")))
                    - 10 * (not bool(repo.get("language")))
                    - (25 if age is not None and age >= 180 else 0)
                    - (15 if repo.get("open_issues", 0) >= 10 else 0)
                    - (30 if ci_status in _BAD_CI and not archived else 0))
        if archived:
            action = "Arşivlenmiş; eylem gerekmiyor"
        elif ci_status in _BAD_CI:
            action = "Son GitHub Actions çalışmasının loglarını incele"
        elif repo.get("open_issues", 0) >= 10:
            action = "Açık issue listesini önceliklendir"
        elif age is not None and age >= 180:
            action = "Projeyi sürdürme veya arşivleme kararını ver"
        elif not repo.get("description"):
            action = "Proje amacını README ve açıklamada netleştir"
        elif ci_status in {"not_checked", "unavailable"}:
            action = "CI durumunu doğrula"
        elif ci_status == "no_runs":
            action = "Workflow tanımı ve tetiklemelerini kontrol et"
        else:
            action = "Rutin bakım"
        rows.append({**repo, "age_days": age, "score": score, "findings": findings,
                     "ci_status": ci_status, "ci_label": _CI_LABELS[ci_status],
                     "next_action": action})
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
        "generated_at": now.isoformat(), "total": len(rows),
        "private": sum(bool(r.get("private")) for r in rows),
        "archived": sum(bool(r.get("archived")) for r in rows),
        "ci_summary": dict(Counter(r["ci_status"] for r in rows)),
        "repositories": rows, "possible_name_overlaps": duplicates,
    }
