from __future__ import annotations

import argparse
import shutil
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


def selected(name: str) -> bool:
    normalized = "/" + name.replace("\\", "/").lower()
    base = PurePosixPath(name).name.lower()
    if not base.endswith((".xlsx", ".xlsm")):
        return False
    if any(f"/monthly report oct 2025/{folder}/" in normalized for folder in ("accrd", "ph", "pi")):
        return True
    if "/survey data/" in normalized and base.startswith(("accrd - bm", "accrd - cz", "accrd - tp", "gph - bm", "pit - bm")):
        return True
    return "/in/" in normalized and base.startswith(("in01ph", "in01pi", "in02pi"))


def extract(source: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    count = 0
    with ZipFile(source) as archive:
        for item in archive.infolist():
            if item.is_dir() or not selected(item.filename):
                continue
            member = PurePosixPath(item.filename)
            parts = member.parts
            relative = Path(*parts[1:]) if parts and parts[0].lower() == "monthly report oct 2025" else Path(*parts)
            destination = (output / relative).resolve()
            if output.resolve() not in destination.parents:
                raise ValueError(f"Unsafe ZIP member: {item.filename}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(item) as source_handle, destination.open("wb") as destination_handle:
                shutil.copyfileobj(source_handle, destination_handle)
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract only HydroSafe's three-structure XLSX scope")
    parser.add_argument("--zip", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(f"Extracted {extract(args.zip, args.output)} selected workbooks to {args.output}")


if __name__ == "__main__":
    main()
