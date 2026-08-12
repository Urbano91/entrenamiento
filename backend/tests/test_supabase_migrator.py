"""Garantías locales del migrador SQLite -> Supabase; nunca conecta a red."""

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "migrate_sqlite_to_supabase.py"
DATABASE = ROOT / "database" / "futbol_entrenamiento.sqlite"

spec = importlib.util.spec_from_file_location("sqlite_to_supabase", SCRIPT)
migrator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = migrator
spec.loader.exec_module(migrator)


def test_dry_run_inventory_and_counts_are_complete():
    result = migrator.audit_source(DATABASE)
    counts = {table.name: table.row_count for table in result.tables}

    assert result.ok, result.errors
    assert len(result.tables) == 20
    assert result.total_rows == 2474
    assert counts["ejercicios"] == 114
    assert counts["imagenes"] == 122
    assert counts["texto_original"] == 989
    assert counts["ejercicio_objetivo"] == 709


def test_generated_plan_contains_only_creations():
    result = migrator.audit_source(DATABASE)

    assert len(result.table_ddl) == len(result.tables)
    assert all(statement.startswith("CREATE TABLE ") for statement in result.table_ddl)
    assert all(
        statement.startswith(("CREATE INDEX ", "CREATE UNIQUE INDEX "))
        for statement in result.index_ddl
    )
    assert not any(
        statement.lstrip().upper().startswith(("DROP ", "TRUNCATE ", "DELETE ", "UPDATE "))
        for statement in [*result.table_ddl, *result.index_ddl]
    )


def test_primary_keys_foreign_keys_nulls_and_normalization_are_valid():
    result = migrator.audit_source(DATABASE)

    assert result.ok, result.errors
    assert result.unique_keys_checked == 33
    assert result.foreign_keys_checked == 23
    assert result.check_constraints == 1
    assert result.image_files_checked == 122
    assert not result.errors


def test_sqlite_sequence_values_are_preserved_in_plan():
    result = migrator.audit_source(DATABASE)
    tables = {table.name: table for table in result.tables}

    assert tables["objetivos"].sequence_value == 182
    assert tables["materiales"].sequence_value == 54
    assert tables["documentos_planificacion"].sequence_value == 2
    assert tables["ejercicio_objetivo"].identity_column is None


def test_dry_run_does_not_require_supabase_credentials(monkeypatch):
    for variable in (
        "SUPABASE_DB_HOST", "SUPABASE_DB_PORT", "SUPABASE_DB_NAME",
        "SUPABASE_DB_USER", "SUPABASE_DB_PASSWORD",
    ):
        monkeypatch.delenv(variable, raising=False)

    result = migrator.audit_source(DATABASE)
    assert result.ok, result.errors
