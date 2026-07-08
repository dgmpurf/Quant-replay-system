"""Report-only official manual evidence collection template fixture.

The fixture creates deterministic empty/synthetic human-fillable templates for
the selected 2024-04-02 / etf_core historical replay sample. It does not collect,
accept, close, or validate official evidence and it does not authorize replay,
labels, models, stock profiles, buy-review, or trading.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STATUS_CREATED = "OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_CREATED_REPORT_ONLY"
STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT = (
    "official_manual_evidence_collection_template_fixture_blocked_by_unsafe_output_root"
)
WORKFLOW_STAGE = (
    "HISTORICAL_REPLAY_OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_CREATED_REPORT_ONLY"
)
WORKFLOW_NAME = "historical_replay_official_manual_evidence_collection_template_fixture"
DEFAULT_OUTPUT_ROOT = Path(
    "outputs/reports/manual_diagnostics/"
    "historical_replay_official_manual_evidence_collection_template_fixture_v0_1"
)
RECOMMENDED_NEXT_TASK = (
    "Historical Replay Reviewer No-Hit Acceptance Planning for 2024-04-02 etf_core Report-Only v0.1"
)

OUTPUT_FILES = {
    "metadata": "metadata.json",
    "evidence_collection_template": "official_evidence_collection_template.csv",
    "source_lineage_template": "official_source_lineage_template.csv",
    "no_hit_query_handoff_template": "official_no_hit_query_handoff_template.csv",
    "survivorship_rationale_template": "official_survivorship_rationale_template.csv",
    "reviewer_notes_template": "official_reviewer_notes_template.csv",
    "validation_checklist": "official_template_validation_checklist.md",
    "report": "official_manual_evidence_collection_template_report.md",
    "safety_flags": "official_manual_evidence_collection_template_safety_flags.json",
}

SAFETY_FALSE_FIELDS = [
    "official_source_hierarchy_approved",
    "official_evidence_collection_started",
    "official_evidence_collection_approved",
    "official_evidence_accepted",
    "official_evidence_closed",
    "official_status_evidence_closed",
    "pit_evidence_closed",
    "pit_admissibility_approved",
    "active_replay_input",
    "replay_execution_allowed",
    "replay_decision_freeze_allowed",
    "forward_labels_created",
    "training_dataset_created",
    "metric_computation_performed",
    "model_training_performed",
    "stock_profile_validation_created",
    "paper_expansion_allowed",
    "buy_review_allowed",
    "trading_allowed",
    "broker_api_called",
    "order_placed",
    "message_sent",
    "external_api_called",
    "llm_api_called",
    "current_candidates_executed",
    "snapshot_built",
    "signal_semantics_mutated",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]

POSITIVE_CONTEXT_FLAGS = {
    "report_only": True,
    "diagnostic_only": True,
    "local_only": True,
    "selected_sample_context_only": True,
    "empty_or_synthetic_template_only": True,
    "filled_evidence_template_created": False,
    "official_evidence_collection_started": False,
}

REQUIRED_EVIDENCE_TEMPLATE_FIELDS = [
    "template_row_id",
    "historical_decision_date",
    "universe_name",
    "symbol",
    "instrument_type",
    "legacy_universe_label",
    "recommended_profile",
    "profile_conflict",
    "evidence_family",
    "template_status",
    "blocker_reason",
    "limitation_note",
    "evidence_collection_status",
    "evidence_observation_value",
    "evidence_observation_scope",
    "evidence_observation_date",
    "evidence_publication_time",
    "evidence_available_time",
    "evidence_available_time_timezone",
    "evidence_raw_reference",
    "evidence_revision_id",
    "evidence_limitation_note",
]

SOURCE_LINEAGE_FIELDS = [
    "template_row_id",
    "historical_decision_date",
    "universe_name",
    "symbol",
    "instrument_type",
    "legacy_universe_label",
    "recommended_profile",
    "profile_conflict",
    "evidence_family",
    "source_id",
    "source_name",
    "source_type",
    "source_class",
    "permission_class",
    "raw_reference_type",
    "raw_reference",
    "source_hash_preview",
    "source_hash_disclosure_policy",
    "local_file_hash_preview",
    "local_file_hash_disclosure_policy",
    "revision_id",
    "revision_id_type",
    "available_time",
    "available_time_timezone",
    "available_time_policy",
    "quality_status",
    "limitation_note",
]

NO_HIT_FIELDS = [
    "template_row_id",
    "historical_decision_date",
    "universe_name",
    "symbol",
    "instrument_type",
    "no_hit_review_needed",
    "no_hit_source_family",
    "no_hit_query_window_start",
    "no_hit_query_window_end",
    "no_hit_query_terms",
    "no_hit_result",
    "no_hit_acceptance_status",
    "no_hit_reviewer_required",
    "reviewer_id_or_alias",
    "reviewer_role",
    "reviewer_scope",
    "no_hit_acceptance_rationale",
    "no_hit_limitation_note",
]

SURVIVORSHIP_FIELDS = [
    "template_row_id",
    "historical_decision_date",
    "universe_name",
    "symbol",
    "instrument_type",
    "survivorship_warning_flag",
    "survivorship_source_id",
    "survivorship_raw_reference",
    "survivorship_revision_id",
    "survivorship_available_time",
    "survivorship_rationale",
    "survivorship_review_status",
    "survivorship_limitation_note",
]

REVIEWER_FIELDS = [
    "template_row_id",
    "historical_decision_date",
    "universe_name",
    "symbol",
    "instrument_type",
    "reviewer_id_or_alias",
    "reviewer_role",
    "reviewer_scope",
    "reviewed_at",
    "reviewer_attestation_status",
    "reviewer_limitation_note",
    "reviewer_private_identity_disclosed",
]

SELECTED_ROWS = [
    ("000001", "STOCK", "stock_core", True),
    ("000002", "STOCK", "stock_core", True),
    ("159915", "ETF", "etf_core", False),
    ("300750", "STOCK", "stock_core", True),
    ("510300", "ETF", "etf_core", False),
    ("600000", "STOCK", "stock_core", True),
    ("600519", "STOCK", "stock_core", True),
    ("601318", "STOCK", "stock_core", True),
    ("688981", "STOCK", "stock_core", True),
]

COMMON_EVIDENCE_FAMILIES = [
    "listed_active_status",
    "delisted_not_delisted_status",
    "suspension_trading_status",
    "universe_membership",
    "source_lineage",
    "reviewer_no_hit_handoff",
    "survivorship_rationale",
]

PROTECTED_PATH_PARTS = [
    ("data", "raw"),
    ("data", "processed"),
    ("data", "cache"),
    ("docs", "project_sources"),
]


@dataclass(frozen=True)
class HistoricalReplayOfficialManualEvidenceCollectionTemplateFixtureResult:
    run_id: str
    status: str
    health_status: str
    workflow_stage: str
    artifact_paths: dict[str, Path]
    metadata: dict[str, Any]


def run_historical_replay_official_manual_evidence_collection_template_fixture(
    *,
    root: str | Path,
    output_dir: str | Path | None = None,
    run_id: str | None = None,
    historical_decision_date: str = "2024-04-02",
    universe_name: str = "etf_core",
) -> HistoricalReplayOfficialManualEvidenceCollectionTemplateFixtureResult:
    """Create deterministic empty/synthetic manual evidence template artifacts."""

    root_path = Path(root)
    output_root = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_ROOT
    _validate_output_root(output_root)
    if run_id is None:
        run_id = _generate_run_id(root_path, historical_decision_date, universe_name)
    _validate_run_id(run_id)

    output_root_resolved = output_root.resolve()
    artifact_dir = (output_root / run_id).resolve()
    if not _is_relative_to(artifact_dir, output_root_resolved):
        raise ValueError(f"{STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT}: output path escapes requested root")

    evidence_rows = _evidence_rows(run_id, historical_decision_date, universe_name)
    lineage_rows = _lineage_rows(evidence_rows)
    no_hit_rows = _no_hit_rows(run_id, historical_decision_date, universe_name)
    survivorship_rows = _survivorship_rows(run_id, historical_decision_date, universe_name)
    reviewer_rows = _reviewer_rows(run_id, historical_decision_date, universe_name)
    metadata = _metadata(
        run_id=run_id,
        historical_decision_date=historical_decision_date,
        universe_name=universe_name,
        evidence_rows=evidence_rows,
        lineage_rows=lineage_rows,
        no_hit_rows=no_hit_rows,
        survivorship_rows=survivorship_rows,
        reviewer_rows=reviewer_rows,
    )
    paths = _paths(artifact_dir)
    metadata["artifact_paths"] = {key: filename for key, filename in OUTPUT_FILES.items()}
    metadata["report_path"] = OUTPUT_FILES["report"]

    artifact_dir.mkdir(parents=True, exist_ok=True)
    _write_json(paths["metadata"], metadata)
    _write_csv(paths["evidence_collection_template"], evidence_rows, REQUIRED_EVIDENCE_TEMPLATE_FIELDS)
    _write_csv(paths["source_lineage_template"], lineage_rows, SOURCE_LINEAGE_FIELDS)
    _write_csv(paths["no_hit_query_handoff_template"], no_hit_rows, NO_HIT_FIELDS)
    _write_csv(paths["survivorship_rationale_template"], survivorship_rows, SURVIVORSHIP_FIELDS)
    _write_csv(paths["reviewer_notes_template"], reviewer_rows, REVIEWER_FIELDS)
    paths["validation_checklist"].write_text(_validation_checklist(), encoding="utf-8")
    paths["report"].write_text(_report(metadata), encoding="utf-8")
    _write_json(paths["safety_flags"], _safety_flags())

    return HistoricalReplayOfficialManualEvidenceCollectionTemplateFixtureResult(
        run_id=run_id,
        status=STATUS_CREATED,
        health_status="PASS",
        workflow_stage=WORKFLOW_STAGE,
        artifact_paths=paths,
        metadata=metadata,
    )


def _evidence_rows(run_id: str, decision_date: str, universe_name: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for symbol, instrument_type, recommended_profile, profile_conflict in SELECTED_ROWS:
        families = list(COMMON_EVIDENCE_FAMILIES)
        families.insert(2, "st_no_st_status" if instrument_type == "STOCK" else "etf_st_not_applicable_policy")
        for family in families:
            blockers = _blockers(family, profile_conflict)
            rows.append(
                {
                    "template_row_id": f"{run_id}_{symbol}_{family}",
                    "historical_decision_date": decision_date,
                    "universe_name": universe_name,
                    "symbol": symbol,
                    "instrument_type": instrument_type,
                    "legacy_universe_label": universe_name,
                    "recommended_profile": recommended_profile,
                    "profile_conflict": _bool_text(profile_conflict),
                    "evidence_family": family,
                    "template_status": _template_status(family),
                    "blocker_reason": ";".join(blockers),
                    "limitation_note": "template_placeholder_only",
                    "evidence_collection_status": "not_collected",
                    "evidence_observation_value": "missing",
                    "evidence_observation_scope": "missing",
                    "evidence_observation_date": "missing",
                    "evidence_publication_time": "missing",
                    "evidence_available_time": "missing",
                    "evidence_available_time_timezone": "missing",
                    "evidence_raw_reference": "missing",
                    "evidence_revision_id": "missing",
                    "evidence_limitation_note": "template_placeholder_only_not_evidence",
                }
            )
    return rows


def _lineage_rows(evidence_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in evidence_rows:
        rows.append(
            {
                "template_row_id": row["template_row_id"],
                "historical_decision_date": row["historical_decision_date"],
                "universe_name": row["universe_name"],
                "symbol": row["symbol"],
                "instrument_type": row["instrument_type"],
                "legacy_universe_label": row["legacy_universe_label"],
                "recommended_profile": row["recommended_profile"],
                "profile_conflict": row["profile_conflict"],
                "evidence_family": row["evidence_family"],
                "source_id": "missing",
                "source_name": "missing",
                "source_type": "missing",
                "source_class": "official_or_reviewed_source_required",
                "permission_class": "missing",
                "raw_reference_type": "missing",
                "raw_reference": "missing",
                "source_hash_preview": "not_collected",
                "source_hash_disclosure_policy": "preview_only_or_hidden_full_hash",
                "local_file_hash_preview": "not_collected",
                "local_file_hash_disclosure_policy": "preview_only_not_pit_evidence",
                "revision_id": "missing",
                "revision_id_type": "missing",
                "available_time": "missing",
                "available_time_timezone": "missing",
                "available_time_policy": "must_not_be_after_decision_time",
                "quality_status": "missing",
                "limitation_note": "template_placeholder_only",
            }
        )
    return rows


def _no_hit_rows(run_id: str, decision_date: str, universe_name: str) -> list[dict[str, str]]:
    return [
        {
            "template_row_id": f"{run_id}_{symbol}_no_hit",
            "historical_decision_date": decision_date,
            "universe_name": universe_name,
            "symbol": symbol,
            "instrument_type": instrument_type,
            "no_hit_review_needed": "true",
            "no_hit_source_family": "official_manual_evidence_collection_template",
            "no_hit_query_window_start": "missing",
            "no_hit_query_window_end": "missing",
            "no_hit_query_terms": "template_placeholder_only",
            "no_hit_result": "missing",
            "no_hit_acceptance_status": "not_accepted",
            "no_hit_reviewer_required": "true",
            "reviewer_id_or_alias": "missing",
            "reviewer_role": "missing",
            "reviewer_scope": "missing",
            "no_hit_acceptance_rationale": "missing",
            "no_hit_limitation_note": "template_placeholder_only",
        }
        for symbol, instrument_type, _, _ in SELECTED_ROWS
    ]


def _survivorship_rows(run_id: str, decision_date: str, universe_name: str) -> list[dict[str, str]]:
    return [
        {
            "template_row_id": f"{run_id}_{symbol}_survivorship",
            "historical_decision_date": decision_date,
            "universe_name": universe_name,
            "symbol": symbol,
            "instrument_type": instrument_type,
            "survivorship_warning_flag": "true",
            "survivorship_source_id": "missing",
            "survivorship_raw_reference": "missing",
            "survivorship_revision_id": "missing",
            "survivorship_available_time": "missing",
            "survivorship_rationale": "missing",
            "survivorship_review_status": "not_reviewed",
            "survivorship_limitation_note": "blocker_missing_survivorship_rationale",
        }
        for symbol, instrument_type, _, _ in SELECTED_ROWS
    ]


def _reviewer_rows(run_id: str, decision_date: str, universe_name: str) -> list[dict[str, str]]:
    return [
        {
            "template_row_id": f"{run_id}_{symbol}_reviewer",
            "historical_decision_date": decision_date,
            "universe_name": universe_name,
            "symbol": symbol,
            "instrument_type": instrument_type,
            "reviewer_id_or_alias": "missing",
            "reviewer_role": "missing",
            "reviewer_scope": "missing",
            "reviewed_at": "missing",
            "reviewer_attestation_status": "not_attested",
            "reviewer_limitation_note": "template_placeholder_only",
            "reviewer_private_identity_disclosed": "no",
        }
        for symbol, instrument_type, _, _ in SELECTED_ROWS
    ]


def _metadata(
    *,
    run_id: str,
    historical_decision_date: str,
    universe_name: str,
    evidence_rows: list[dict[str, str]],
    lineage_rows: list[dict[str, str]],
    no_hit_rows: list[dict[str, str]],
    survivorship_rows: list[dict[str, str]],
    reviewer_rows: list[dict[str, str]],
) -> dict[str, Any]:
    safety = _safety_flags()
    return {
        **safety,
        "run_id": run_id,
        "workflow_name": WORKFLOW_NAME,
        "workflow_stage": WORKFLOW_STAGE,
        "runtime_status": STATUS_CREATED,
        "health_status": "PASS",
        "historical_decision_date": historical_decision_date,
        "universe_name": universe_name,
        "row_count": len(SELECTED_ROWS),
        "stock_row_count": sum(row[1] == "STOCK" for row in SELECTED_ROWS),
        "etf_row_count": sum(row[1] == "ETF" for row in SELECTED_ROWS),
        "evidence_collection_template_row_count": len(evidence_rows),
        "source_lineage_template_row_count": len(lineage_rows),
        "no_hit_template_row_count": len(no_hit_rows),
        "survivorship_template_row_count": len(survivorship_rows),
        "reviewer_notes_template_row_count": len(reviewer_rows),
        "profile_conflict_count": sum(row[3] for row in SELECTED_ROWS),
        "survivorship_warning_count": len(SELECTED_ROWS),
        "safety_true_count": sum(1 for field in SAFETY_FALSE_FIELDS if safety[field]),
        "recommended_next_task": RECOMMENDED_NEXT_TASK,
    }


def _blockers(family: str, profile_conflict: bool) -> list[str]:
    blockers = [
        "blocker_missing_source_id",
        "blocker_missing_raw_reference",
        "blocker_missing_permission_class",
        "blocker_missing_revision_id",
        "blocker_missing_available_time",
        "blocker_missing_timezone_policy",
        "blocker_missing_quality_status",
        "blocker_missing_limitation_note",
    ]
    if family == "st_no_st_status":
        blockers.append("blocker_missing_stock_st_source")
    if family == "etf_st_not_applicable_policy":
        blockers.append("blocker_missing_etf_st_not_applicable_policy")
    if family == "reviewer_no_hit_handoff":
        blockers.append("blocker_missing_no_hit_query_window")
    if family == "survivorship_rationale":
        blockers.append("blocker_missing_survivorship_rationale")
    if profile_conflict:
        blockers.append("blocker_profile_conflict_unreviewed")
    return blockers


def _template_status(family: str) -> str:
    if family == "source_lineage":
        return "source_lineage_required"
    if family == "reviewer_no_hit_handoff":
        return "no_hit_query_required"
    if family == "survivorship_rationale":
        return "survivorship_rationale_required"
    if family in {"st_no_st_status", "etf_st_not_applicable_policy"}:
        return "manual_review_required"
    return "evidence_collection_required"


def _safety_flags() -> dict[str, bool]:
    return {**{field: False for field in SAFETY_FALSE_FIELDS}, **POSITIVE_CONTEXT_FLAGS}


def _paths(artifact_dir: Path) -> dict[str, Path]:
    return {key: artifact_dir / filename for key, filename in OUTPUT_FILES.items()}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _validation_checklist() -> str:
    return "\n".join(
        [
            "# Official Manual Evidence Collection Template Validation Checklist",
            "",
            "- Template rows are empty placeholders and are not official evidence.",
            "- Reviewer fields are aliases/placeholders only and disclose no confidential reviewer details.",
            "- Source hash previews are not full hashes and do not validate source content.",
            "- No row closes PIT evidence or authorizes replay, buy-review, or trading.",
            "",
        ]
    )


def _report(metadata: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Historical Replay Official Manual Evidence Collection Template Fixture Report",
            "",
            "This fixture is report-only, diagnostic-only, local-only, and empty-or-synthetic.",
            "It creates human-fillable templates only. It does not collect, accept, close, or approve official evidence.",
            "row_ready_for_manual_fill_not_pit_approved means manual-fill context only, not PIT approval.",
            "",
            f"- Run id: `{metadata['run_id']}`",
            f"- Historical decision date: `{metadata['historical_decision_date']}`",
            f"- Universe: `{metadata['universe_name']}`",
            f"- Evidence collection template rows: `{metadata['evidence_collection_template_row_count']}`",
            f"- Source lineage template rows: `{metadata['source_lineage_template_row_count']}`",
            f"- Safety true count: `{metadata['safety_true_count']}`",
            f"- Recommended next task: `{RECOMMENDED_NEXT_TASK}`",
            "",
        ]
    )


def _validate_output_root(output_root: Path) -> None:
    parts = tuple(part.lower() for part in output_root.parts)
    for protected in PROTECTED_PATH_PARTS:
        for index in range(0, max(len(parts) - len(protected) + 1, 0)):
            if parts[index : index + len(protected)] == protected:
                raise ValueError(f"{STATUS_BLOCKED_BY_UNSAFE_OUTPUT_ROOT}: {output_root}")


def _validate_run_id(run_id: str) -> None:
    if any(part in run_id for part in ("..", "/", "\\")) or not run_id.strip():
        raise ValueError("invalid run_id")


def _generate_run_id(root: Path, decision_date: str, universe_name: str) -> str:
    digest = hashlib.sha256(f"{root}|{decision_date}|{universe_name}|{WORKFLOW_NAME}".encode("utf-8")).hexdigest()
    return digest[:12]


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _bool_text(value: bool) -> str:
    return "true" if value else "false"
