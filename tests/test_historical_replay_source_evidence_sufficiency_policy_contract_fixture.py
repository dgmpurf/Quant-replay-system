from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pytest

from quant_replay_system.historical_replay_source_evidence_sufficiency_policy_contract_fixture import (
    BLOCKER_VOCABULARY,
    EVIDENCE_FAMILY_CONTRACT_FIELDS,
    OUTPUT_FILES,
    SAFETY_FALSE_FIELDS,
    SELECTED_ROW_FIELDS,
    STATUS_CREATED,
    STATUS_VOCABULARY,
    run_historical_replay_source_evidence_sufficiency_policy_contract_fixture,
)


EXPECTED_SYMBOLS = [
    "000001",
    "000002",
    "159915",
    "300750",
    "510300",
    "600000",
    "600519",
    "601318",
    "688981",
]


def _build(tmp_path: Path):
    return run_historical_replay_source_evidence_sufficiency_policy_contract_fixture(
        root=tmp_path,
        output_dir=tmp_path / "fixture",
        run_id="fixture-run",
    )


def _csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def test_core_writes_exact_artifact_and_count_contract(tmp_path: Path) -> None:
    result = _build(tmp_path)
    metadata = result.metadata

    assert result.status == STATUS_CREATED
    assert result.health_status == "PASS"
    assert set(result.artifact_paths) == set(OUTPUT_FILES)
    assert {path.name for path in result.artifact_paths.values()} == set(OUTPUT_FILES.values())
    assert all(path.is_file() for path in result.artifact_paths.values())
    assert len(list(result.artifact_paths["metadata"].parent.iterdir())) == 10

    expected_counts = {
        "row_count": 9,
        "stock_row_count": 7,
        "etf_row_count": 2,
        "profile_conflict_count": 7,
        "profile_aligned_context_count": 2,
        "unresolved_profile_conflict_count": 7,
        "selected_row_with_blocker_count": 9,
        "evidence_family_count": 17,
        "row_evidence_family_contract_count": 153,
        "applicable_contract_row_count": 144,
        "instrument_not_applicable_context_row_count": 9,
        "core_artifact_count": 10,
        "required_field_row_count": 45,
        "status_vocabulary_row_count": 17,
        "blocker_vocabulary_row_count": 28,
        "timing_revision_rule_count": 18,
        "stock_etf_matrix_row_count": 4,
        "sufficiency_candidate_count": 0,
        "evidence_accepted_count": 0,
        "evidence_closed_count": 0,
        "pit_admissible_count": 0,
        "replay_ready_count": 0,
        "safety_true_count": 0,
    }
    assert {key: metadata[key] for key in expected_counts} == expected_counts
    assert metadata["report_only"] is True
    assert metadata["diagnostic_only"] is True
    assert metadata["local_only"] is True
    assert metadata["synthetic_only"] is True
    assert all(metadata[field] is False for field in SAFETY_FALSE_FIELDS)


def test_selected_rows_preserve_identity_profiles_blockers_and_false_states(
    tmp_path: Path,
) -> None:
    result = _build(tmp_path)
    fields, rows = _csv_rows(result.artifact_paths["selected_rows"])

    assert fields == SELECTED_ROW_FIELDS
    assert [row["symbol"] for row in rows] == EXPECTED_SYMBOLS
    assert [row["row_id"] for row in rows] == [
        f"20240402_etf_core_{symbol}" for symbol in EXPECTED_SYMBOLS
    ]
    assert sum(row["instrument_type"] == "STOCK" for row in rows) == 7
    assert sum(row["instrument_type"] == "ETF" for row in rows) == 2
    assert all(row["selected_row_blockers"] for row in rows)

    stocks = [row for row in rows if row["instrument_type"] == "STOCK"]
    etfs = [row for row in rows if row["instrument_type"] == "ETF"]
    assert all(row["recommended_profile"] == "stock_core" for row in stocks)
    assert all(row["profile_conflict"] == "true" for row in stocks)
    assert all(row["profile_policy_status"] == "unresolved_profile_conflict" for row in stocks)
    assert all(row["recommended_profile"] == "etf_core" for row in etfs)
    assert all(row["profile_conflict"] == "false" for row in etfs)
    assert all(
        row["profile_policy_status"]
        == "profile_aligned_context_only_not_universe_proof"
        for row in etfs
    )
    for row in rows:
        assert row["selected_row_sufficiency_candidate"] == "false"
        assert row["selected_row_evidence_accepted"] == "false"
        assert row["selected_row_evidence_closed"] == "false"
        assert row["selected_row_pit_admissible"] == "false"
        assert row["selected_row_replay_ready"] == "false"


def test_evidence_family_contract_preserves_applicability_and_default_separation(
    tmp_path: Path,
) -> None:
    result = _build(tmp_path)
    fields, rows = _csv_rows(result.artifact_paths["evidence_family_contract"])

    assert fields == EVIDENCE_FAMILY_CONTRACT_FIELDS
    assert len(rows) == 153
    assert len({row["evidence_family_id"] for row in rows}) == 17
    assert sum(row["instrument_applicability"] == "applies" for row in rows) == 144
    assert sum(
        row["instrument_applicability"] == "not_applicable_context_only"
        for row in rows
    ) == 9
    assert all(
        row[field] == "false"
        for row in rows
        for field in (
            "evidence_presence",
            "sufficiency_candidate",
            "evidence_accepted",
            "evidence_closed",
            "pit_admissible",
            "replay_ready",
        )
    )
    assert all(
        row["insufficiency_blockers"]
        for row in rows
        if row["instrument_applicability"] == "applies"
    )

    ef04 = [row for row in rows if row["evidence_family_id"] == "EF04"]
    ef05 = [row for row in rows if row["evidence_family_id"] == "EF05"]
    assert sum(row["instrument_applicability"] == "applies" for row in ef04) == 7
    assert sum(row["instrument_applicability"] == "not_applicable_context_only" for row in ef04) == 2
    assert sum(row["instrument_applicability"] == "applies" for row in ef05) == 2
    assert sum(row["instrument_applicability"] == "not_applicable_context_only" for row in ef05) == 7


def test_vocabularies_timing_and_stock_etf_matrix_are_exact(tmp_path: Path) -> None:
    result = _build(tmp_path)
    _, statuses = _csv_rows(result.artifact_paths["status_vocabulary"])
    _, blockers = _csv_rows(result.artifact_paths["blocker_vocabulary"])
    _, timing = _csv_rows(result.artifact_paths["timing_revision_matrix"])
    _, stock_etf = _csv_rows(result.artifact_paths["stock_etf_matrix"])
    _, contracts = _csv_rows(result.artifact_paths["evidence_family_contract"])

    assert [row["status"] for row in statuses] == STATUS_VOCABULARY
    assert [row["blocker_id"] for row in blockers] == BLOCKER_VOCABULARY
    assert len(timing) == 18
    assert sum(row["category"] == "timing" for row in timing) == 10
    assert sum(row["category"] == "revision" for row in timing) == 8
    assert all(row["blocker"] in BLOCKER_VOCABULARY for row in timing)
    assert [row["applicability_rule_id"] for row in stock_etf] == [
        "APP_STOCK_ST",
        "APP_ETF_ST",
        "APP_STOCK_ETF_NA",
        "APP_ETF_ETF_NA",
    ]
    assigned_text = " ".join(
        row["source_eligibility_context"] for row in contracts
    )
    assert "evidence_family_sufficiency_candidate_not_accepted" not in assigned_text
    assert "row_has_sufficiency_candidates_not_closed" not in assigned_text


@pytest.mark.parametrize(
    "unsafe_root",
    [
        Path("data/raw/source-evidence-fixture"),
        Path("data/processed/source-evidence-fixture"),
        Path("data/cache/source-evidence-fixture"),
        Path("docs/project_sources/source-evidence-fixture"),
    ],
)
def test_output_root_guard_rejects_protected_roots(unsafe_root: Path) -> None:
    with pytest.raises(ValueError, match="unsafe_output_root"):
        run_historical_replay_source_evidence_sufficiency_policy_contract_fixture(
            root=".", output_dir=unsafe_root, run_id="unsafe"
        )


def test_output_root_guard_rejects_run_id_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="invalid run_id"):
        run_historical_replay_source_evidence_sufficiency_policy_contract_fixture(
            root=tmp_path, output_dir=tmp_path / "fixture", run_id="../escape"
        )


def test_public_artifacts_do_not_disclose_full_hash_private_path_or_secret(
    tmp_path: Path,
) -> None:
    result = _build(tmp_path)
    public_text = "\n".join(
        path.read_text(encoding="utf-8") for path in result.artifact_paths.values()
    )
    assert re.search(r"(?i)(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", public_text) is None
    assert re.search(r"(?i)\b[a-z]:\\users\\", public_text) is None
    assert re.search(
        r"(?i)\b(?:secret|credential|token|password|api[_-]?key)\s*[:=]\s*\S+",
        public_text,
    ) is None
    assert str(tmp_path) not in public_text
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    assert all(not Path(value).is_absolute() for value in metadata["artifact_paths"].values())
