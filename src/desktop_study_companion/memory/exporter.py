from __future__ import annotations

"""Backup and human-readable export helpers."""

import csv
from contextlib import closing
import json
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path


_TABLES = (
    "study_sessions",
    "activity_events",
    "interventions",
    "conversation_messages",
)


def _csv_safe(value):
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


def export_csv_directory(
    db_path: str | Path,
    destination_dir: str | Path,
) -> list[Path]:
    db_path = Path(db_path)
    destination = Path(destination_dir)
    destination.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    with closing(sqlite3.connect(db_path)) as connection:
        connection.row_factory = sqlite3.Row
        for table in _TABLES:
            columns = [
                row[1]
                for row in connection.execute(
                    f"PRAGMA table_info({table})"
                ).fetchall()
            ]
            rows = connection.execute(
                f"SELECT * FROM {table} ORDER BY 1"
            ).fetchall()

            path = destination / f"{table}.csv"
            with path.open("w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.writer(handle)
                writer.writerow(columns)
                for row in rows:
                    writer.writerow([_csv_safe(row[column]) for column in columns])
            created.append(path)

    return created


def create_backup_zip(
    db_path: str | Path,
    data_dir: str | Path,
    destination_zip: str | Path,
    *,
    config_path: str | Path | None = None,
    app_version: str = "unknown",
) -> Path:
    db_path = Path(db_path)
    data_dir = Path(data_dir)
    destination = Path(destination_zip)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot = Path(temp_dir) / "companion.db"
        with closing(sqlite3.connect(db_path)) as source:
            with closing(sqlite3.connect(snapshot)) as target:
                source.backup(target)

        metadata = {
            "created_at": datetime.now().astimezone().isoformat(),
            "app_version": app_version,
            "format": 1,
        }

        with zipfile.ZipFile(
            destination,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            archive.write(snapshot, "data/companion.db")

            if data_dir.exists():
                for path in sorted(data_dir.glob("*.json")):
                    archive.write(path, f"data/{path.name}")

            if config_path is not None:
                config = Path(config_path)
                if config.exists():
                    archive.write(config, "data/config.json")

            archive.writestr(
                "backup-metadata.json",
                json.dumps(metadata, ensure_ascii=False, indent=2),
            )

    return destination
