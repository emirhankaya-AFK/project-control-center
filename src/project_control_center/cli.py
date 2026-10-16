"""Command line interface."""

import argparse
import json
from pathlib import Path

from .analyze import analyze
from .github import GitHubError, collect
from .report import render_html


def main() -> int:
    parser = argparse.ArgumentParser(description="GitHub proje kontrol merkezi")
    parser.add_argument("--owner", help="GitHub kullanıcı adı; canlı veri çeker")
    parser.add_argument("--input", type=Path, help="Önceden kaydedilmiş JSON snapshot")
    parser.add_argument("--output", type=Path, default=Path("reports"), help="Rapor klasörü")
    parser.add_argument("--include-private", action="store_true", help="Özel repo adlarını rapora dahil et")
    args = parser.parse_args()
    if bool(args.owner) == bool(args.input):
        parser.error("--owner veya --input seçeneklerinden yalnızca birini ver")
    try:
        if args.input:
            repositories = json.loads(args.input.read_text(encoding="utf-8"))
        else:
            repositories = collect(args.owner)
    except (GitHubError, OSError, ValueError) as exc:
        parser.exit(1, f"Hata: {exc}\n")
    if not isinstance(repositories, list):
        parser.exit(1, "Hata: JSON bir repo listesi olmalı\n")
    if not args.include_private:
        repositories = [r for r in repositories if not r.get("private")]
    audit = analyze(repositories)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output / "index.html").write_text(render_html(audit), encoding="utf-8")
    print(f"{audit['total']} repo incelendi: {args.output / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

