#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
import tarfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from packaging import version


@dataclass(frozen=True)
class PackageRecord:
    name: str
    version: str
    timestamp: int
    filename: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan APK repository garbage collection from APKINDEX.tar.gz")
    parser.add_argument("--index", required=True, type=Path, help="Path to APKINDEX.tar.gz")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for plan files")
    parser.add_argument("--keep-days", type=int, default=180, help="Keep packages newer than this many days")
    parser.add_argument("--arch", required=True, help="Architecture name for logging")
    parser.add_argument("--now", type=int, default=None, help="Override current Unix timestamp")
    return parser.parse_args()


def read_index(index_path: Path) -> list[PackageRecord]:
    if not index_path.exists():
        raise FileNotFoundError(f"missing APKINDEX archive: {index_path}")

    with tarfile.open(index_path, mode="r:gz") as archive:
        member = next((item for item in archive.getmembers() if item.name == "APKINDEX"), None)
        if member is None:
            raise RuntimeError(f"{index_path} does not contain APKINDEX")

        handle = archive.extractfile(member)
        if handle is None:
            raise RuntimeError(f"failed to read APKINDEX from {index_path}")

        content = handle.read().decode("utf-8")

    records: list[PackageRecord] = []
    current: dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                records.append(record_from_fields(current, index_path))
                current = {}
            continue

        if ":" not in line:
            raise RuntimeError(f"malformed APKINDEX line: {raw_line!r}")

        field, value = line.split(":", 1)
        current[field] = value.lstrip()

    if current:
        records.append(record_from_fields(current, index_path))

    if not records:
        raise RuntimeError(f"no package entries found in {index_path}")

    return records


def record_from_fields(fields: dict[str, str], index_path: Path) -> PackageRecord:
    missing = [field for field in ("P", "V", "t") if field not in fields]
    if missing:
        raise RuntimeError(f"{index_path}: missing APKINDEX fields {', '.join(missing)} in entry {fields!r}")

    name = fields["P"]
    version = fields["V"]

    try:
        timestamp = int(fields["t"])
    except ValueError as exc:
        raise RuntimeError(f"{index_path}: invalid timestamp for {name}-{version}: {fields['t']!r}") from exc

    filename = f"{name}-{version}.apk"
    return PackageRecord(name=name, version=version, timestamp=timestamp, filename=filename)


def apk_version_compare(left: str, right: str) -> int:
    left = version.parse(left)
    right = version.parse(right)

    if left < right:
        return -1
    if left > right:
        return 1
    
    return 0


def latest_by_name(records: list[PackageRecord]) -> dict[str, PackageRecord]:
    latest: dict[str, PackageRecord] = {}
    for record in records:
        current = latest.get(record.name)
        if current is None:
            latest[record.name] = record
            continue

        comparison = apk_version_compare(record.version, current.version)
        if comparison > 0 or (comparison == 0 and record.timestamp > current.timestamp):
            latest[record.name] = record
    return latest


def build_plan(records: list[PackageRecord], keep_days: int, now: int | None) -> tuple[list[PackageRecord], list[PackageRecord]]:
    latest = latest_by_name(records)
    now_ts = now if now is not None else int(datetime.now(timezone.utc).timestamp())
    cutoff = now_ts - int(timedelta(days=keep_days).total_seconds())

    keep: list[PackageRecord] = []
    delete: list[PackageRecord] = []

    for record in records:
        is_recent = record.timestamp >= cutoff
        is_latest = latest[record.name] == record
        if is_recent or is_latest:
            keep.append(record)
        else:
            delete.append(record)

    return keep, delete


def write_plan(output_dir: Path, arch: str, records: list[PackageRecord], keep: list[PackageRecord], delete: list[PackageRecord]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    delete_path = output_dir / "delete.txt"
    keep_path = output_dir / "keep.txt"
    summary_path = output_dir / f"plan_{arch}.json"

    delete_path.write_text(
        "\n".join(record.filename for record in sorted(delete, key=lambda item: item.filename)) + ("\n" if delete else ""),
        encoding="utf-8",
    )
    keep_path.write_text(
        "\n".join(record.filename for record in sorted(keep, key=lambda item: item.filename)) + ("\n" if keep else ""),
        encoding="utf-8",
    )

    summary = {
        "arch": arch,
        "package_count": len(records),
        "keep_count": len(keep),
        "delete_count": len(delete),
        "delete": [record.filename for record in sorted(delete, key=lambda item: item.filename)],
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    records = read_index(args.index)
    keep, delete = build_plan(records, args.keep_days, args.now)
    write_plan(args.output_dir, args.arch, records, keep, delete)

    now_ts = args.now if args.now is not None else int(datetime.now(timezone.utc).timestamp())
    cutoff_dt = datetime.fromtimestamp(now_ts - int(timedelta(days=args.keep_days).total_seconds()), tz=timezone.utc)
    print(
        f"scanned {len(records)} packages, keeping {len(keep)}, deleting {len(delete)}; cutoff={cutoff_dt.isoformat()}!!!!",
        file=sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())