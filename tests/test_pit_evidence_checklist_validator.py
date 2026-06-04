from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.pit_evidence_checklist_validator import (
    COMPLETED_UPDATE_COLUMNS,
    build_pit_evidence_checklist_validator,
)
from quant_replay_system.pit_evidence_checklist_validator_health import check_pit_evidence_checklist_validator_health
from quant_replay_system.pit_evidence_checklist_validator_index import build_pit_evidence_checklist_validator_index
from quant_replay_system.pit_evidence_checklist_validator_status import run_pit_evidence_checklist_validator_status


def test_current_style_16_row_draft_blocks_every_row(tmp_path: Path) -> None:
    updates = tmp_path / "updates.csv"
    _write_updates(updates, [_needs_more("000001", "stock_core", date) for date in _dates()] + [_needs_more("159915", "etf_core", date) for date in _dates()])
    stock, etf, source = _write_checklists(tmp_path)

    result = build_pit_evidence_checklist_validator(
        completed_updates=updates,
        stock_checklist=stock,
        etf_checklist=etf,
        source_acceptance=source,
        output_dir=tmp_path / "validator",
    )

    assert result.row_count == 16
    assert result.checklist_pass_count == 0
    assert result.blocked_count == 16
    assert result.stock_core_blocked_count == 8
    assert result.etf_core_blocked_count == 8
    assert set(result.validation_frame["symbol"]) == {"000001", "159915"}
    assert "stock ST/no-ST evidence missing" in result.validation_frame.loc[
        result.validation_frame["profile"] == "stock_core", "blocker_reason"
    ].iloc[0]


def test_stock_requires_st_but_etf_does_not(tmp_path: Path) -> None:
    stock, etf, source = _write_checklists(tmp_path)
    updates = tmp_path / "updates.csv"
    stock_row = _complete("000001", "stock_core")
    stock_row["is_st"] = ""
    etf_row = _complete("159915", "etf_core")
    etf_row["is_st"] = ""
    _write_updates(updates, [stock_row, etf_row])

    result = build_pit_evidence_checklist_validator(
        completed_updates=updates,
        stock_checklist=stock,
        etf_checklist=etf,
        source_acceptance=source,
        output_dir=tmp_path / "validator",
    )

    stock_validation = result.validation_frame.loc[result.validation_frame["profile"] == "stock_core"].iloc[0]
    etf_validation = result.validation_frame.loc[result.validation_frame["profile"] == "etf_core"].iloc[0]
    assert stock_validation["stock_st_blocker"] is True
    assert etf_validation["stock_st_blocker"] is False


def test_active_survivorship_timing_and_unacceptable_sources_block(tmp_path: Path) -> None:
    stock, etf, source = _write_checklists(tmp_path)
    updates = tmp_path / "updates.csv"
    row = _complete("000001", "stock_core")
    row["is_active"] = ""
    row["is_active_evidence"] = ""
    row["survivorship_bias_resolved"] = "False"
    row["available_time"] = "2024-04-02 15:30:00"
    row["evidence_source"] = "future-dated processed universe hint"
    _write_updates(updates, [row])

    result = build_pit_evidence_checklist_validator(
        completed_updates=updates,
        stock_checklist=stock,
        etf_checklist=etf,
        source_acceptance=source,
        output_dir=tmp_path / "validator",
    )

    validation = result.validation_frame.iloc[0]
    assert validation["blocked"] is True
    assert validation["survivorship_blocker"] is True
    assert validation["pit_timing_blocker"] is True
    assert "evidence_source" in validation["unacceptable_source_fields"]


def test_complete_synthetic_row_can_be_preview_candidate_only(tmp_path: Path) -> None:
    stock, etf, source = _write_checklists(tmp_path)
    updates = tmp_path / "updates.csv"
    _write_updates(updates, [_complete("000001", "stock_core")])

    result = build_pit_evidence_checklist_validator(
        completed_updates=updates,
        stock_checklist=stock,
        etf_checklist=etf,
        source_acceptance=source,
        output_dir=tmp_path / "validator",
    )

    assert result.checklist_pass_count == 1
    assert len(result.approval_candidate_preview_frame) == 1
    assert result.audit_metadata["approval_applied"] is False
    assert result.audit_metadata["universe_exported"] is False
    assert result.audit_metadata["current_candidates_executed"] is False
    assert result.audit_metadata["snapshot_manifest_built"] is False
    assert result.audit_metadata["forward_returns_computed"] is False


def test_index_health_status_and_cli_work(tmp_path: Path, capsys) -> None:
    stock, etf, source = _write_checklists(tmp_path)
    updates = tmp_path / "updates.csv"
    _write_updates(updates, [_needs_more("000001", "stock_core", "2024-04-02")])
    root = tmp_path / "validator"
    build_pit_evidence_checklist_validator(
        completed_updates=updates,
        stock_checklist=stock,
        etf_checklist=etf,
        source_acceptance=source,
        output_dir=root,
    )

    index = build_pit_evidence_checklist_validator_index(root=root, output_dir=tmp_path / "index")
    health = check_pit_evidence_checklist_validator_health(root=root, output_dir=tmp_path / "health")
    status = run_pit_evidence_checklist_validator_status(root=root, output_dir=tmp_path / "status")

    assert index["artifact_count"] == 1
    assert health["status"] == "PASS"
    assert status["workflow_stage"] == "PIT_EVIDENCE_CHECKLIST_VALIDATION_BLOCKED"

    code = cli.main(["pit-evidence-checklist-validator-status", "--root", str(root), "--output-dir", str(tmp_path / "cli-status")])
    output = capsys.readouterr()
    assert code == 0
    assert "workflow_stage: PIT_EVIDENCE_CHECKLIST_VALIDATION_BLOCKED" in output.out
    assert "No approval applied" in output.out


def test_leading_zero_symbols_are_preserved(tmp_path: Path) -> None:
    stock, etf, source = _write_checklists(tmp_path)
    updates = tmp_path / "updates.csv"
    _write_updates(updates, [_needs_more("000001", "stock_core", "2024-04-02")])

    result = build_pit_evidence_checklist_validator(
        completed_updates=updates,
        stock_checklist=stock,
        etf_checklist=etf,
        source_acceptance=source,
        output_dir=tmp_path / "validator",
    )

    assert result.validation_frame.iloc[0]["symbol"] == "000001"


def _dates() -> list[str]:
    return ["2024-04-02", "2024-04-09", "2024-04-11", "2024-04-16", "2024-04-19", "2024-04-24", "2024-04-26", "2024-05-06"]


def _write_updates(path: Path, rows: list[dict]) -> None:
    pd.DataFrame(rows, columns=COMPLETED_UPDATE_COLUMNS).to_csv(path, index=False)


def _needs_more(symbol: str, universe: str, date: str) -> dict:
    row = {column: "" for column in COMPLETED_UPDATE_COLUMNS}
    row.update(
        {
            "signal_date": date,
            "symbol": symbol,
            "universe_name": universe,
            "review_status": "NEEDS_MORE_EVIDENCE",
            "include_flag": "False",
            "reviewer": "tester",
            "reviewed_at": "2026-06-04T10:00:00+08:00",
            "review_reason": "Needs strict PIT evidence.",
            "evidence_source": "local_market_cache",
            "evidence_reference": "local_market_cache",
            "listed_date": "1991-04-03" if symbol == "000001" else "2011-12-09",
            "listed_date_evidence": "2024-03-29",
            "is_suspended": "False",
            "name": "Ping An Bank" if symbol == "000001" else "ChiNext ETF",
            "instrument_type": "STOCK" if universe == "stock_core" else "ETF",
            "exchange": "SZSE",
            "min_lot": "100",
            "available_time": f"{date} 15:30:00",
            "source": "LOCAL_MARKET_CACHE_REVIEWED",
            "survivorship_bias_resolved": "False",
        }
    )
    return row


def _complete(symbol: str, universe: str) -> dict:
    row = _needs_more(symbol, universe, "2024-04-02")
    row.update(
        {
            "review_status": "NEEDS_MORE_EVIDENCE",
            "evidence_source": "OFFICIAL_SZSE;CNINFO_DISCLOSURE;REVIEWED_RULE_CONTEXT",
            "evidence_reference": "official-status-file",
            "is_active": "True",
            "is_active_evidence": "2024-04-02",
            "is_st": "False" if universe == "stock_core" else "",
            "industry": "Bank" if universe == "stock_core" else "ETF",
            "t_plus_rule": "T+1",
            "as_of_date": "2024-04-02",
            "available_time": "2024-04-02 09:00:00",
            "revision_id": "review-bundle-1",
            "source": "OFFICIAL_SZSE",
            "survivorship_bias_resolved": "True",
        }
    )
    return row


def _write_checklists(tmp_path: Path) -> tuple[Path, Path, Path]:
    source = tmp_path / "source_acceptance.csv"
    source.write_text("source_category,approval_acceptance\nOfficial exchange rules,approval_evidence_for_rule_fields\n", encoding="utf-8")
    cols = [
        "field_name",
        "required_for_stock",
        "required_for_etf",
        "required_evidence_type",
        "acceptable_sources",
        "context_only_sources",
        "rejected_sources",
        "date_specific_or_symbol_level",
        "PIT_requirement",
        "approval_blocker_if_missing",
        "notes",
    ]
    fields = [
        "reviewer",
        "reviewed_at",
        "review_reason",
        "evidence_source",
        "evidence_path_or_reference",
        "listed_date",
        "listed_date_evidence",
        "is_active",
        "is_active_evidence",
        "is_st",
        "is_suspended",
        "as_of_date",
        "name",
        "instrument_type",
        "exchange",
        "industry",
        "min_lot",
        "t_plus_rule",
        "available_time",
        "revision_id",
        "source",
        "survivorship_bias_resolved",
    ]
    rows = [
        {
            "field_name": field,
            "required_for_stock": "true",
            "required_for_etf": "false" if field == "is_st" else "true",
            "required_evidence_type": "strict evidence",
            "acceptable_sources": "official",
            "context_only_sources": "local cache",
            "rejected_sources": "future hint",
            "date_specific_or_symbol_level": "mixed",
            "PIT_requirement": "PIT safe",
            "approval_blocker_if_missing": "true",
            "notes": "",
        }
        for field in fields
    ]
    stock = tmp_path / "stock_checklist.csv"
    etf = tmp_path / "etf_checklist.csv"
    pd.DataFrame(rows, columns=cols).to_csv(stock, index=False)
    pd.DataFrame(rows, columns=cols).to_csv(etf, index=False)
    return stock, etf, source
