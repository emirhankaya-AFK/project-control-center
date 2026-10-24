"""Command line interface."""

import argparse
import json
from pathlib import Path

from .analyze import analyze
from .github import GitHubError, collect, enrich_ci
from .report import render_html


def main() -> int:
    parser = argparse.ArgumentParser(description="GitHub proje kontrol merkezi")
    parser.add_argument("--owner", help="GitHub kullanıcı adı; canlı veri çeker")
    parser.add_argument("--input", type=Path, help="Önceden kaydedilmiş JSON snapshot")
    parser.add_argument("--output", type=Path, default=Path("reports"), help="Rapor klasörü")
    parser.add_argument("--include-private", action="store_true", help="Özel repo adlarını yerel rapora dahil et")
    parser.add_argument("--check-ci", action="store_true", help="Actions durumunu salt-okunur kontrol et")
    parser.add_argument("--ci-limit", type=int, default=20, help="En fazla kaç repo için Actions sorgusu (1-100)")
    args = parser.parse_args()
    if bool(args.owner) == bool(args.input):
        parser.error("--owner veya --input seçeneklerinden yalnızca birini ver")
    if args.check_ci and not args.owner:
        parser.error("--check-ci sadece --owner ile kullanılabilir")
    if not 1 <= args.ci_limit <= 100:
        parser.error("--ci-limit 1-100 arasında olmalı")
    try:
        if args.input:
            repositories = json.loads(args.input.read_text(encoding="utf-8"))
        else:
            repositories = collect(args.owner, require_owner_auth=args.include_private)
        if not isinstance(repositories, list) or any(not isinstance(r, dict) for r in repositories):
            raise ValueError("JSON bir repo nesneleri listesi olmalı")
        if not args.include_private:
            repositories = [r for r in repositories if not r.get("private")]
        if args.check_ci:
            enrich_ci(repositories, args.owner, limit=args.ci_limit)
        audit = analyze(repositories)
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        (args.output / "index.html").write_text(render_html(audit), encoding="utf-8")
    except (GitHubError, OSError, ValueError, TypeError) as exc:
        parser.exit(1, f"Hata: {exc}\n")
    print(f"{audit['total']} repo incelendi: {args.output / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
