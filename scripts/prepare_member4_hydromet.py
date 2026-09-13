from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

from backend.agents.member6_risk.hydromet import read_hydromet_daily


FIELDS = (
    "reservoir_level",
    "tailwater",
    "inflow",
    "rainfall",
    "temperature",
)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(source: Path, output: Path, manifest_path: Path) -> dict:
    observations = read_hydromet_daily(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("date", *FIELDS))
        writer.writeheader()
        for item in observations:
            writer.writerow(
                {
                    "date": item.observed_at,
                    "reservoir_level": item.reservoir_level_m,
                    "tailwater": item.tailwater_level_m,
                    "inflow": item.inflow_m3_s,
                    "rainfall": item.daily_rainfall_mm,
                    "temperature": item.mean_temperature_c,
                }
            )

    dates = [date.fromisoformat(item.observed_at) for item in observations]
    present = set(dates)
    missing_dates: list[str] = []
    cursor = min(dates)
    while cursor <= max(dates):
        if cursor not in present:
            missing_dates.append(cursor.isoformat())
        cursor += timedelta(days=1)
    complete_rows = sum(
        all(
            value is not None
            for value in (
                item.reservoir_level_m,
                item.tailwater_level_m,
                item.inflow_m3_s,
                item.daily_rainfall_mm,
                item.mean_temperature_c,
            )
        )
        for item in observations
    )
    manifest = {
        "source_file": source.name,
        "source_sha256": file_hash(source),
        "normalized_file": output.name,
        "normalized_sha256": file_hash(output),
        "rows": len(observations),
        "complete_rows": complete_rows,
        "date_start": min(dates).isoformat(),
        "date_end": max(dates).isoformat(),
        "missing_dates": missing_dates,
        "columns": ["date", *FIELDS],
        "units": {
            "reservoir_level": "m",
            "tailwater": "m",
            "inflow": "m3/s",
            "rainfall": "mm",
            "temperature": "C",
        },
        "source_header_aliases": {
            "Date": "date",
            "Reservoir water level": "reservoir_level",
            "Tail water level": "tailwater",
            "In flow": "inflow",
            "Daily rainfall": "rainfall",
            "Daily mean temperature": "temperature",
        },
        "usage": "Shared Member 4 statistical-screening history. It is not a labelled failure dataset or an approved action-level source.",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare Member 4's canonical five-parameter CSV")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("backend/datasets/hydromet/member4_hydromet.csv"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("backend/datasets/hydromet/member4_manifest.json"),
    )
    args = parser.parse_args()
    print(json.dumps(prepare(args.input, args.output, args.manifest), indent=2))


if __name__ == "__main__":
    main()
