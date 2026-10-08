import csv
import zipfile

from desktop_study_companion.memory.exporter import (
    create_backup_zip,
    export_csv_directory,
)
from desktop_study_companion.memory.sqlite_store import SQLiteMemoryStore
from desktop_study_companion.study.models import StudySession


def test_csv_export_and_backup_zip(tmp_path) -> None:
    data = tmp_path / "data"
    db = data / "companion.db"
    store = SQLiteMemoryStore(db)
    session = StudySession(goal="Teste", planned_minutes=20)
    session.start()
    session.complete()
    store.save_session(session)
    store.close()

    (data / "directives.json").write_text("[]", encoding="utf-8")

    export_dir = tmp_path / "csv"
    created = export_csv_directory(db, export_dir)
    assert len(created) == 3

    with (export_dir / "study_sessions.csv").open(
        encoding="utf-8-sig"
    ) as handle:
        rows = list(csv.reader(handle))
    assert rows[0][0] == "id"
    assert any("Teste" in row for row in rows[1:])

    backup = create_backup_zip(
        db,
        data,
        tmp_path / "backup.zip",
        app_version="test",
    )

    with zipfile.ZipFile(backup) as archive:
        names = set(archive.namelist())
    assert "data/companion.db" in names
    assert "data/directives.json" in names
    assert "backup-metadata.json" in names
