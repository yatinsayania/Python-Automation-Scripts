#!/usr/bin/env python3
"""backup_report.py

Check whether expected backups were created within a time window.

Examples:
  python backup_report.py --paths /backups/app1 /backups/app2
  python backup_report.py --manifest expected_backups.txt --json

Manifest format:
  one path per line
  optional comments start with #
"""

import argparse
import json
from datetime import datetime
from pathlib import Path


def load_manifest(manifest_path: Path):
    items = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        items.append(Path(line).expanduser())
    return items


def latest_mtime(path: Path):
    if path.is_file():
        return datetime.fromtimestamp(path.stat().st_mtime), path

    latest = None
    latest_path = None
    for p in path.rglob("*"):
        if p.is_file():
            m = datetime.fromtimestamp(p.stat().st_mtime)
            if latest is None or m > latest:
                latest = m
                latest_path = p
    return latest, latest_path


def analyze(paths, max_age_hours, min_size_mb):
    now = datetime.now()
    rows = []

    for raw in paths:
        p = Path(raw).expanduser()
        exists = p.exists()
        is_dir = p.is_dir()
        size_bytes = 0
        latest_time = None
        latest_file = None
        status = "MISSING"
        reason = ""

        if exists:
            if is_dir:
                for f in p.rglob("*"):
                    if f.is_file():
                        try:
                            size_bytes += f.stat().st_size
                        except OSError:
                            pass
                latest_time, latest_file = latest_mtime(p)
            else:
                try:
                    size_bytes = p.stat().st_size
                except OSError:
                    size_bytes = 0
                latest_time, latest_file = latest_mtime(p)

            size_mb = size_bytes / (1024 * 1024)
            age_ok = False
            size_ok = size_mb >= min_size_mb

            if latest_time is not None:
                age_hours = (now - latest_time).total_seconds() / 3600
                age_ok = age_hours <= max_age_hours
            else:
                age_hours = None

            if latest_time is None:
                status = "EMPTY"
                reason = "No files found"
            elif not age_ok and not size_ok:
                status = "FAIL"
                reason = f"Older than {max_age_hours}h and smaller than {min_size_mb} MB"
            elif not age_ok:
                status = "STALE"
                reason = f"Latest file older than {max_age_hours}h"
            elif not size_ok:
                status = "SMALL"
                reason = f"Total size below {min_size_mb} MB"
            else:
                status = "OK"
                reason = "Backup looks current"
        else:
            age_hours = None

        rows.append(
            {
                "path": str(p),
                "exists": exists,
                "type": "dir" if is_dir else "file" if exists else "missing",
                "size_mb": round(size_bytes / (1024 * 1024), 2),
                "latest_file": str(latest_file) if latest_file else "",
                "latest_time": latest_time.isoformat(timespec="seconds") if latest_time else "",
                "status": status,
                "reason": reason,
            }
        )

    return rows


def main():
    parser = argparse.ArgumentParser(description="Generate a backup verification report.")
    parser.add_argument("--paths", nargs="*", help="Backup files or folders to check")
    parser.add_argument("--manifest", help="Text file containing one backup path per line")
    parser.add_argument("--max-age-hours", type=float, default=24, help="Max age allowed for latest backup file")
    parser.add_argument("--min-size-mb", type=float, default=1, help="Minimum acceptable backup size")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()

    paths = list(args.paths or [])
    if args.manifest:
        paths.extend([str(p) for p in load_manifest(Path(args.manifest))])

    if not paths:
        parser.error("Provide --paths and/or --manifest")

    report = analyze(paths, args.max_age_hours, args.min_size_mb)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{'STATUS':<8} {'SIZE(MB)':>10} {'LATEST TIME':<20} PATH")
        print("-" * 80)
        for r in report:
            print(f"{r['status']:<8} {r['size_mb']:>10} {r['latest_time']:<20} {r['path']}")
            if r["reason"]:
                print(f"{'':<8} {'':>10} {'':<20} {r['reason']}")

    if any(r["status"] in {"MISSING", "FAIL", "STALE", "EMPTY", "SMALL"} for r in report):
        raise SystemExit(2)


if __name__ == "__main__":
    main()


What it does
Checks whether backup files or folders exist.

Finds the latest modified file inside a folder.

Flags backups as OK, STALE, SMALL, EMPTY, FAIL, or MISSING.

Supports either direct --paths or a --manifest file.

Can output plain text or JSON.

Example usage
bash
python backup_report.py --paths /backups/sapb1 /backups/mysql --max-age-hours 24 --min-size-mb 10
bash
python backup_report.py --manifest expected_backups.txt --json
Suggested repo location
You can add it under:

scripts/backup_report.py

or directly in the repository root if you prefer simple access

Would you like me to also create a matching expected_backups.txt template and a README section for this script?

