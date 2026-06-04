from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.pit_official_status_evidence_packet import (
    SUPPORTING_LOCAL_EOD_CACHE,
    SUPPORTING_OFFICIAL_SYMBOL_LEVEL,
    STRONG_OFFICIAL_DATE_SPECIFIC,
    build_pit_official_status_evidence_packet,
    classify_official_status_evidence_strength,
)
from quant_replay_system.pit_official_status_evidence_packet_health import (
    check_pit_official_status_evidence_packet_health,
)
from quant_replay_system.pit_official_status_evidence_packet_index import (
    build_pit_official_status_evidence_packet_index,
)
from quant_replay_system.pit_official_status_evidence_packet_status import (
    run_pit_official_status_evidence_packet_status,
)


def test_build_packet_preserves_symbols_and_classifies_evidence_strength(tmp_path: Path) -> None:
    inputs = _write_packet_inputs(tmp_path)

    result = build_pit_official_status_evidence_packet(
        source_smoke_root=inputs["smoke"],
        non_relaxed_root=inputs["non_relaxed"],
        validator=inputs["validator"],
        activated_plan=inputs["activated_plan"],
        stock_checklist=inputs["stock_checklist"],
        etf_checklist=inputs["etf_checklist"],
        source_acceptance=inputs["source_acceptance"],
        output_dir=tmp_path / "packet",
    )

    assert result.row_count == 4
    assert set(result.source_rows["symbol"]) == {"000001", "159915"}
    assert result.source_rows["symbol"].iloc[0] == "000001"
    assert result.supporting_local_eod_cache_count >= 4
    assert result.supporting_official_symbol_level_count >= 1
    assert result.strong_official_date_specific_count >= 1
    assert result.checklist_pass_count == 0
    assert result.blocked_count == 4
    assert result.approval_applied is False
    assert result.universe_exported is False
    assert result.current_candidates_generated is False

    draft = pd.read_csv(result.artifact_paths["updated_draft_completed_updates"], dtype=str, keep_default_na=False)
    assert set(draft["review_status"]) == {"NEEDS_MORE_EVIDENCE"}
    assert "APPROVED_FOR_PIT_UNIVERSE" not in set(draft["review_status"])
    assert set(draft["include_flag"]) == {"False"}


def test_strength_classifier_keeps_official_symbol_context_below_date_specific_proof() -> None:
    assert (
        classify_official_status_evidence_strength(
            source_type="official_exchange_daily_status",
            pit_suitability="DATE_SPECIFIC_STATUS_CANDIDATE",
            date_specific=True,
            local_cache=False,
            context_only=False,
        )
        == STRONG_OFFICIAL_DATE_SPECIFIC
    )
    assert (
        classify_official_status_evidence_strength(
            source_type="official_exchange_disclosure",
            pit_suitability="PARTIAL_CONTEXT_ONLY",
            date_specific=False,
            local_cache=False,
            context_only=False,
        )
        == SUPPORTING_OFFICIAL_SYMBOL_LEVEL
    )
    assert (
        classify_official_status_evidence_strength(
            source_type="local_market_cache",
            pit_suitability="EOD_SUPPORT_ONLY",
            date_specific=True,
            local_cache=True,
            context_only=False,
        )
        == SUPPORTING_LOCAL_EOD_CACHE
    )


def test_index_health_status_and_cli_work(tmp_path: Path, capsys) -> None:
    inputs = _write_packet_inputs(tmp_path)
    root = tmp_path / "packet"
    build_pit_official_status_evidence_packet(
        source_smoke_root=inputs["smoke"],
        non_relaxed_root=inputs["non_relaxed"],
        validator=inputs["validator"],
        activated_plan=inputs["activated_plan"],
        stock_checklist=inputs["stock_checklist"],
        etf_checklist=inputs["etf_checklist"],
        source_acceptance=inputs["source_acceptance"],
        output_dir=root,
    )

    index = build_pit_official_status_evidence_packet_index(root=root, output_dir=tmp_path / "index")
    health = check_pit_official_status_evidence_packet_health(root=root, output_dir=tmp_path / "health")
    status = run_pit_official_status_evidence_packet_status(root=root, output_dir=tmp_path / "status")

    assert index["artifact_count"] == 1
    assert health["status"] == "PASS"
    assert status["workflow_stage"] == "PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_BLOCKED"
    assert status["blocked_count"] == 4

    code = cli.main(["pit-official-status-evidence-packet-status", "--root", str(root), "--output-dir", str(tmp_path / "cli-status")])
    output = capsys.readouterr()
    assert code == 0
    assert "workflow_stage: PIT_OFFICIAL_STATUS_EVIDENCE_PACKET_BLOCKED" in output.out
    assert "blocked_count: 4" in output.out


def test_packet_cli_builds_report_only_artifacts(tmp_path: Path, capsys) -> None:
    inputs = _write_packet_inputs(tmp_path)

    code = cli.main(
        [
            "pit-official-status-evidence-packet",
            "--source-smoke-root",
            str(inputs["smoke"]),
            "--non-relaxed-root",
            str(inputs["non_relaxed"]),
            "--validator",
            str(inputs["validator"]),
            "--activated-plan",
            str(inputs["activated_plan"]),
            "--stock-checklist",
            str(inputs["stock_checklist"]),
            "--etf-checklist",
            str(inputs["etf_checklist"]),
            "--source-acceptance",
            str(inputs["source_acceptance"]),
            "--output-dir",
            str(tmp_path / "packet"),
        ]
    )
    output = capsys.readouterr()

    assert code == 0
    assert "row_count: 4" in output.out
    assert "checklist_pass_count: 0" in output.out
    assert "No approval applied" in output.out


def _write_packet_inputs(tmp_path: Path) -> dict[str, Path]:
    smoke = tmp_path / "smoke"
    smoke.mkdir()
    non_relaxed = tmp_path / "non_relaxed"
    non_relaxed.mkdir()
    activated = tmp_path / "activated_plan"
    activated.mkdir()
    validator = tmp_path / "validator" / "validator-a"
    validator.mkdir(parents=True)

    rows = _update_rows()
    pd.DataFrame(
        [
            {
                "signal_date": row["signal_date"],
                "symbol": row["symbol"],
                "profile": row["universe_name"],
                "local_cache_row_found": "true",
                "local_cache_support": "active/suspension context only under EOD policy",
                "official_daily_status_source_found": "true" if row["symbol"] == "000001" and row["signal_date"] == "2024-04-02" else "false",
                "official_date_specific_status_found": "true" if row["symbol"] == "000001" and row["signal_date"] == "2024-04-02" else "false",
                "monthly_or_disclosure_context_found": "SZSE April 2024 ETF monthly stats and CNInfo fund report context" if row["symbol"] == "159915" else "partial_disclosure_context",
                "not_delisted_evidence_status": "missing",
                "st_no_st_evidence_status": "missing" if row["symbol"] == "000001" else "not_applicable",
                "suspension_status_evidence_status": "supporting_context_only",
                "active_status_evidence_status": "supporting_context_only",
                "survivorship_resolution_status": "missing",
                "approval_candidate": "false",
                "next_probe": "keep blocked",
            }
            for row in rows
        ]
    ).to_csv(smoke / "per_symbol_date_status_probe.csv", index=False)
    pd.DataFrame(
        [
            {
                "source_name": "Official daily status smoke source",
                "source_url_or_path": "https://example.test/szse/daily-status",
                "source_type": "official_exchange_daily_status",
                "access_status": "HTTP_200",
                "requires_login_or_captcha": "false",
                "downloadable": "true",
                "parseable": "true",
                "fields_observed": "symbol,date,status",
                "symbols_observed": "000001",
                "dates_observed": "2024-04-02",
                "PIT_suitability": "DATE_SPECIFIC_STATUS_CANDIDATE",
                "can_support_not_delisted": "no",
                "can_support_ST_no_ST": "no",
                "can_support_suspension_status": "yes",
                "can_support_active_status": "yes",
                "context_only_or_approval_candidate": "approval_candidate_context_only",
                "content_type": "text/csv",
                "content_length": "128",
                "error": "",
            },
            {
                "source_name": "SZSE April 2024 ETF monthly statistics",
                "source_url_or_path": "https://example.test/szse/april-etf",
                "source_type": "official_exchange_monthly_statistics",
                "access_status": "HTTP_200",
                "requires_login_or_captcha": "false",
                "downloadable": "true",
                "parseable": "true",
                "fields_observed": "symbol,month",
                "symbols_observed": "159915",
                "dates_observed": "2024-04",
                "PIT_suitability": "PERIOD_CONTEXT_ONLY",
                "can_support_not_delisted": "no",
                "can_support_ST_no_ST": "not_applicable",
                "can_support_suspension_status": "no",
                "can_support_active_status": "context_only",
                "context_only_or_approval_candidate": "context_only",
                "content_type": "text/html",
                "content_length": "256",
                "error": "",
            },
        ]
    ).to_csv(smoke / "source_access_results.csv", index=False)
    pd.DataFrame().to_csv(smoke / "source_parse_results.csv", index=False)

    pd.DataFrame(
        [
            {
                "symbol": "159915",
                "source_name": "SZSE April 2024 ETF monthly statistics",
                "source_type": "official_exchange_monthly_statistics",
                "url": "https://example.test/szse/april-etf",
                "accessed_at": "2026-06-04T23:27:55+08:00",
                "supports_fields": "symbol,monthly_context",
                "pit_safe_for_signal_date": "PARTIAL_CONTEXT_ONLY",
                "blockers_closed": "none",
                "limitations": "symbol-level context only",
            }
        ]
    ).to_csv(non_relaxed / "non_relaxed_source_records.csv", index=False)
    pd.DataFrame(rows).to_csv(non_relaxed / "updated_non_relaxed_draft_completed_updates.csv", index=False)
    pd.DataFrame(rows[:2]).to_csv(activated / "stock_core_first_batch_package.csv", index=False)
    pd.DataFrame(rows[2:]).to_csv(activated / "etf_core_first_batch_package.csv", index=False)

    _write_validator(validator, rows)
    stock_checklist = tmp_path / "stock_checklist.csv"
    etf_checklist = tmp_path / "etf_checklist.csv"
    _write_checklist(stock_checklist, "stock_core")
    _write_checklist(etf_checklist, "etf_core")
    source_acceptance = tmp_path / "source_acceptance.csv"
    pd.DataFrame([{"source_category": "local_market_cache", "approval_acceptance": "supporting_eod_only"}]).to_csv(source_acceptance, index=False)
    return {
        "smoke": smoke,
        "non_relaxed": non_relaxed,
        "activated_plan": activated,
        "validator": validator,
        "stock_checklist": stock_checklist,
        "etf_checklist": etf_checklist,
        "source_acceptance": source_acceptance,
    }


def _update_rows() -> list[dict]:
    rows = []
    for symbol, universe, instrument in [("000001", "stock_core", "STOCK"), ("159915", "etf_core", "ETF")]:
        for date in ["2024-04-02", "2024-04-09"]:
            rows.append(
                {
                    "signal_date": date,
                    "symbol": symbol,
                    "universe_name": universe,
                    "review_status": "NEEDS_MORE_EVIDENCE",
                    "include_flag": "False",
                    "reviewer": "codex_diagnostics",
                    "reviewed_at": "2026-06-04T23:27:55+08:00",
                    "review_reason": "diagnostics-only evidence packet input",
                    "evidence_source": "official_public_sources;local_market_cache_context",
                    "evidence_path": "data/cache/market/daily_bars.csv",
                    "evidence_reference": f"local_market_cache:{symbol}:{date}",
                    "listed_date": "1991-04-03" if symbol == "000001" else "2011-12-09",
                    "delisted_date": "",
                    "is_active": "",
                    "is_st": "",
                    "is_suspended": "False",
                    "listed_date_evidence": "official_symbol_level",
                    "delisted_date_evidence": "",
                    "is_active_evidence": "",
                    "survivorship_bias_resolved": "False",
                    "as_of_date": "????",
                    "name": "Ping An Bank" if symbol == "000001" else "ChiNext ETF",
                    "instrument_type": instrument,
                    "exchange": "SZSE",
                    "industry": "",
                    "min_lot": "100",
                    "t_plus_rule": "T+1_context",
                    "available_time": f"{date} 15:30:00",
                    "revision_id": "nonapproved_draft",
                    "source": "AKSHARE_OPTIONAL",
                }
            )
    return rows


def _write_validator(path: Path, rows: list[dict]) -> None:
    validation = pd.DataFrame(
        [
            {
                "validator_id": path.name,
                "signal_date": row["signal_date"],
                "symbol": row["symbol"],
                "universe_name": row["universe_name"],
                "profile": row["universe_name"],
                "review_status": row["review_status"],
                "checklist_status": "CHECKLIST_BLOCKED_NON_RELAXED_EVIDENCE",
                "checklist_pass": False,
                "blocked": True,
                "blocker_reason": "missing not-delisted/ST/survivorship evidence",
                "missing_required_fields": "delisted_date_evidence,is_active_evidence,survivorship_bias_resolved",
                "unacceptable_source_fields": "",
                "pit_timing_blocker": True,
                "survivorship_blocker": True,
                "stock_st_blocker": row["universe_name"] == "stock_core",
                "no_approval_applied": True,
                "no_universe_export": True,
                "no_data_raw_write": True,
                "no_data_processed_write": True,
                "no_current_candidates_generated": True,
                "no_snapshot_built": True,
                "no_forward_labels": True,
                "no_live_trading": True,
                "no_broker_api": True,
                "no_order_placement": True,
                "no_message_sent": True,
                "checklist_validation_only": True,
            }
            for row in rows
        ]
    )
    validation.to_csv(path / "pit_evidence_checklist_validation.csv", index=False)
    pd.DataFrame(
        [
            {
                "validator_id": path.name,
                "status": "WARN",
                "row_count": len(rows),
                "checklist_pass_count": 0,
                "blocked_count": len(rows),
                "stock_core_blocked_count": 2,
                "etf_core_blocked_count": 2,
                "missing_evidence_count": len(rows),
                "unacceptable_source_count": 0,
                "pit_timing_blocked_count": len(rows),
                "survivorship_blocked_count": len(rows),
                "stock_st_blocked_count": 2,
            }
        ]
    ).to_csv(path / "pit_evidence_checklist_validation_summary.csv", index=False)
    pd.DataFrame().to_csv(path / "missing_evidence_matrix.csv", index=False)
    pd.DataFrame().to_csv(path / "approval_candidate_preview.csv", index=False)
    (path / "report.md").write_text("No approval applied.", encoding="utf-8")
    (path / "metadata.json").write_text('{"validator_id":"validator-a","status":"WARN","row_count":4,"checklist_pass_count":0,"blocked_count":4}', encoding="utf-8")


def _write_checklist(path: Path, profile: str) -> None:
    fields = ["reviewer", "reviewed_at", "listed_date", "is_active", "survivorship_bias_resolved"]
    if profile == "stock_core":
        fields.append("is_st")
    pd.DataFrame(
        [
            {
                "field_name": field,
                "required": "true",
                "acceptable_sources": "official_public_sources",
                "notes": "test checklist",
            }
            for field in fields
        ]
    ).to_csv(path, index=False)
