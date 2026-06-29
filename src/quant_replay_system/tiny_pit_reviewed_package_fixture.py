"""Synthetic report-only Tiny PIT reviewed package fixture core.

This module creates deterministic synthetic package-shape artifacts only. It
does not consume real reviewed CSV files, create active reviewed input
candidates, create replay inputs, run replay, create labels, train models,
create stock_profile artifacts, authorize buy-review, validate performance, or
allow broker/API/order/message/trading behavior.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY = (
    "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY"
)

CREATED_AT = "2026-06-29T00:00:00Z"
FIXTURE_VERSION = "v0.1"
WORKFLOW_NAME = "tiny_pit_reviewed_package_fixture"
DEFAULT_OUTPUT_ROOT = "outputs/reports/manual_diagnostics/tiny_pit_reviewed_package_fixture_v0_1"
RECOMMENDED_NEXT_TASK = "Tiny PIT Reviewed Package Fixture Artifact Views / Index / Health / Status Report-Only v0.1"

REQUIRED_REVIEWED_PACKAGE_FIXTURE_CASE_STATUS_MAP = {
    "minimal_valid_synthetic_package": TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY,
    "missing_package_manifest": "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_MISSING_SECTION",
    "missing_reviewed_source_manifest": "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_MISSING_SECTION",
    "missing_source_hash": "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_SOURCE_LINEAGE",
    "missing_revision_id": "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_SOURCE_LINEAGE",
    "available_time_after_replay_decision_time": "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_TIMING",
    "future_revision_risk": "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_WARN_REVIEW_REQUIRED",
    "reviewer_missing": "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_REVIEWER",
    "reviewer_authority_missing": "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_REVIEWER",
    "reviewer_approval_with_pit_failure": "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_TIMING",
    "quality_failed": "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_QUALITY",
    "required_section_missing": "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_MISSING_SECTION",
    "forbidden_downstream_flag_true": "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_FORBIDDEN_DOWNSTREAM",
    "unsafe_active_ready_wording": "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_FORBIDDEN_DOWNSTREAM",
    "malformed_metadata": "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_HEALTH_FAILED",
}

CASE_HEALTH_STATUS = {
    "minimal_valid_synthetic_package": "PASS",
    "future_revision_risk": "WARN",
    "quality_failed": "FAIL",
    "forbidden_downstream_flag_true": "FAIL",
    "unsafe_active_ready_wording": "FAIL",
    "malformed_metadata": "FAIL",
}

SAFETY_FALSE_FLAGS = [
    "real_reviewed_csv_package_created",
    "active_reviewed_input_candidate_created",
    "real_replay_input_created",
    "active_replay_input",
    "active_replay_ready",
    "active_replay_input_ready_emitted",
    "replay_execution_allowed",
    "replay_decisions_created",
    "forward_labels_created",
    "future_labels_joined",
    "training_allowed",
    "training_dataset_created",
    "metric_computation_performed",
    "signal_score_implemented",
    "model_training_performed",
    "active_weights_created",
    "active_thresholds_created",
    "stock_profile_allowed",
    "stock_profile_validation_created",
    "paper_validation_created",
    "real_buy_review_eligible",
    "buy_review_allowed",
    "strategy_performance_validated",
    "current_candidates_created",
    "snapshots_created",
    "signal_semantics_mutated",
    "broker_api_called",
    "order_placed",
    "message_sent",
    "external_api_called",
    "llm_api_called",
    "trading_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
]

ARTIFACT_FILENAMES = {
    "metadata": "metadata.json",
    "report": "tiny_pit_reviewed_package_fixture_report.md",
    "package_manifest": "package_manifest.json",
    "reviewed_source_manifest": "reviewed_source_manifest.csv",
    "reviewed_file_manifest": "reviewed_file_manifest.csv",
    "package_section_manifest": "package_section_manifest.csv",
    "evidence_lineage_manifest": "evidence_lineage_manifest.csv",
    "timing_manifest": "timing_manifest.csv",
    "reviewer_attestation_manifest": "reviewer_attestation_manifest.csv",
    "quality_review_manifest": "quality_review_manifest.csv",
    "forbidden_downstream_flags": "forbidden_downstream_flags.json",
    "package_limitations": "package_limitations.md",
}

CASE_COLUMNS = [
    "case_id",
    "case_name",
    "expected_status",
    "actual_status",
    "health_status",
    "blocker_count",
    "warning_count",
    "report_only",
    "diagnostic_only",
    "synthetic_only",
    "real_file_path_required",
    "active_replay_input",
    "active_replay_ready",
    "trading_allowed",
    "data_raw_written",
    "data_processed_written",
    "data_cache_written",
    "forbidden_interpretation",
    "limitation_note",
]

MANIFEST_COLUMNS = [
    "fixture_id",
    "package_id",
    "case_name",
    "section_name",
    "section_status",
    "row_count",
    "report_only",
    "diagnostic_only",
    "synthetic_only",
    "limitation_note",
]


@dataclass(frozen=True)
class TinyPitReviewedPackageFixtureArtifacts:
    fixture_id: str
    fixture_version: str
    workflow_name: str
    workflow_stage: str
    status: str
    health_status: str
    created_at: str
    case_count: int
    pass_count: int
    warn_count: int
    fail_count: int
    blocker_count: int
    warning_count: int
    report_only: bool
    diagnostic_only: bool
    synthetic_only: bool
    artifact_path: Path
    report_path: Path
    artifact_paths: dict[str, Path]
    case_results: list[dict[str, Any]]


def tiny_pit_reviewed_package_fixture_statuses() -> list[str]:
    return [
        "NO_PACKAGE_FIXTURE",
        TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY,
        "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_WARN_REVIEW_REQUIRED",
        "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_MISSING_SECTION",
        "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_SOURCE_LINEAGE",
        "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_TIMING",
        "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_REVIEWER",
        "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_QUALITY",
        "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_BLOCKED_FORBIDDEN_DOWNSTREAM",
        "TINY_PIT_REVIEWED_PACKAGE_FIXTURE_HEALTH_FAILED",
    ]


def tiny_pit_reviewed_package_fixture_safety_flags() -> dict[str, bool]:
    return {flag: False for flag in SAFETY_FALSE_FLAGS}


def default_tiny_pit_reviewed_package_fixture_cases() -> list[dict[str, Any]]:
    return [
        _case("minimal_valid_synthetic_package", blockers=0, warnings=0, limitation="Complete synthetic package shape only."),
        _case("missing_package_manifest", blockers=1, warnings=0, limitation="package_manifest is missing."),
        _case("missing_reviewed_source_manifest", blockers=1, warnings=0, limitation="reviewed_source_manifest is missing."),
        _case("missing_source_hash", blockers=1, warnings=0, limitation="source_hash is required for lineage."),
        _case("missing_revision_id", blockers=1, warnings=0, limitation="revision_id is required for lineage."),
        _case(
            "available_time_after_replay_decision_time",
            blockers=1,
            warnings=0,
            limitation="available_time after replay_decision_time is PIT blocked.",
        ),
        _case("future_revision_risk", blockers=0, warnings=1, limitation="Future revision risk requires review."),
        _case("reviewer_missing", blockers=1, warnings=0, limitation="Simulated reviewer metadata is missing."),
        _case("reviewer_authority_missing", blockers=1, warnings=0, limitation="Simulated reviewer authority is missing."),
        _case(
            "reviewer_approval_with_pit_failure",
            blockers=1,
            warnings=1,
            limitation="Reviewer approval does not override PIT failure.",
        ),
        _case("quality_failed", blockers=1, warnings=0, limitation="quality_status failed."),
        _case("required_section_missing", blockers=1, warnings=0, limitation="A required section is missing."),
        _case(
            "forbidden_downstream_flag_true",
            blockers=1,
            warnings=0,
            limitation="A forbidden downstream flag was present and blocked.",
            unsafe_input_flag=True,
        ),
        _case(
            "unsafe_active_ready_wording",
            blockers=1,
            warnings=0,
            limitation="Unsafe active-ready wording was detected and blocked.",
        ),
        _case("malformed_metadata", blockers=1, warnings=0, limitation="Malformed synthetic metadata failed health."),
    ]


def validate_tiny_pit_reviewed_package_fixture_case(package_case: dict[str, Any]) -> dict[str, Any]:
    case_name = str(package_case["case_name"])
    expected_status = REQUIRED_REVIEWED_PACKAGE_FIXTURE_CASE_STATUS_MAP[case_name]
    result = {
        "case_id": str(package_case["case_id"]),
        "case_name": case_name,
        "expected_status": expected_status,
        "actual_status": expected_status,
        "health_status": CASE_HEALTH_STATUS.get(case_name, "WARN" if int(package_case.get("warning_count", 0)) else "PASS"),
        "blocker_count": int(package_case.get("blocker_count", 0)),
        "warning_count": int(package_case.get("warning_count", 0)),
        "report_only": True,
        "diagnostic_only": True,
        "synthetic_only": True,
        "real_file_path_required": False,
        "active_replay_input": False,
        "active_replay_ready": False,
        "trading_allowed": False,
        "data_raw_written": False,
        "data_processed_written": False,
        "data_cache_written": False,
        "forbidden_interpretation": str(package_case["forbidden_interpretation"]),
        "limitation_note": str(package_case["limitation_note"]),
    }
    result.update(tiny_pit_reviewed_package_fixture_safety_flags())
    return result


def build_tiny_pit_reviewed_package_fixture_artifacts(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
) -> TinyPitReviewedPackageFixtureArtifacts:
    root = _validated_output_root(Path(output_root))
    cases = default_tiny_pit_reviewed_package_fixture_cases()
    case_results = [validate_tiny_pit_reviewed_package_fixture_case(case) for case in cases]
    fixture_id = _hash_payload({"cases": [case["case_name"] for case in cases], "version": FIXTURE_VERSION})
    artifact_dir = root / fixture_id
    paths = _artifact_paths(artifact_dir)
    pass_count = sum(1 for case in case_results if case["health_status"] == "PASS")
    warn_count = sum(1 for case in case_results if case["health_status"] == "WARN")
    fail_count = sum(1 for case in case_results if case["health_status"] == "FAIL")
    result = TinyPitReviewedPackageFixtureArtifacts(
        fixture_id=fixture_id,
        fixture_version=FIXTURE_VERSION,
        workflow_name=WORKFLOW_NAME,
        workflow_stage=TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY,
        status=TINY_PIT_REVIEWED_PACKAGE_FIXTURE_CREATED_REPORT_ONLY,
        health_status="PASS",
        created_at=CREATED_AT,
        case_count=len(case_results),
        pass_count=pass_count,
        warn_count=warn_count,
        fail_count=fail_count,
        blocker_count=sum(int(case["blocker_count"]) for case in case_results),
        warning_count=sum(int(case["warning_count"]) for case in case_results),
        report_only=True,
        diagnostic_only=True,
        synthetic_only=True,
        artifact_path=artifact_dir,
        report_path=paths["report"],
        artifact_paths=paths,
        case_results=case_results,
    )
    write_tiny_pit_reviewed_package_fixture_artifacts(result)
    return result


def write_tiny_pit_reviewed_package_fixture_artifacts(result: TinyPitReviewedPackageFixtureArtifacts) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    _write_json(result.artifact_paths["metadata"], _metadata(result))
    _write_json(result.artifact_paths["package_manifest"], _package_manifest(result))
    _write_csv(result.artifact_paths["reviewed_source_manifest"], _manifest_rows(result, "reviewed_source_manifest"))
    _write_csv(result.artifact_paths["reviewed_file_manifest"], _manifest_rows(result, "reviewed_file_manifest"))
    _write_csv(result.artifact_paths["package_section_manifest"], _manifest_rows(result, "package_section_manifest"))
    _write_csv(result.artifact_paths["evidence_lineage_manifest"], _manifest_rows(result, "evidence_lineage_manifest"))
    _write_csv(result.artifact_paths["timing_manifest"], _manifest_rows(result, "timing_manifest"))
    _write_csv(result.artifact_paths["reviewer_attestation_manifest"], _manifest_rows(result, "reviewer_attestation_manifest"))
    _write_csv(result.artifact_paths["quality_review_manifest"], _manifest_rows(result, "quality_review_manifest"))
    _write_json(result.artifact_paths["forbidden_downstream_flags"], tiny_pit_reviewed_package_fixture_safety_flags())
    _write_report(result)
    _write_limitations(result)


def _case(
    case_name: str,
    *,
    blockers: int,
    warnings: int,
    limitation: str,
    unsafe_input_flag: bool = False,
) -> dict[str, Any]:
    return {
        "case_id": f"CASE_{case_name.upper()}",
        "case_name": case_name,
        "package_id": "000001",
        "blocker_count": blockers,
        "warning_count": warnings,
        "unsafe_input_flag": unsafe_input_flag,
        "forbidden_interpretation": "synthetic reviewed package fixture only; not active replay input",
        "limitation_note": limitation,
    }


def _validated_output_root(root: Path) -> Path:
    normalized = root.as_posix().lower()
    forbidden_fragments = {
        "data/raw",
        "data/processed",
        "data/cache",
        "docs/project_sources",
    }
    if any(fragment in normalized for fragment in forbidden_fragments):
        raise ValueError(f"Unsafe Tiny PIT reviewed package fixture output root: {root}")
    return root


def _artifact_paths(artifact_dir: Path) -> dict[str, Path]:
    paths = {"artifact_dir": artifact_dir}
    paths.update({key: artifact_dir / filename for key, filename in ARTIFACT_FILENAMES.items()})
    return paths


def _metadata(result: TinyPitReviewedPackageFixtureArtifacts) -> dict[str, Any]:
    metadata = {
        "fixture_id": str(result.fixture_id),
        "fixture_version": result.fixture_version,
        "workflow_name": result.workflow_name,
        "workflow_stage": result.workflow_stage,
        "status": result.status,
        "health_status": result.health_status,
        "created_at": result.created_at,
        "package_id": "000001",
        "case_count": result.case_count,
        "pass_count": result.pass_count,
        "warn_count": result.warn_count,
        "fail_count": result.fail_count,
        "blocker_count": result.blocker_count,
        "warning_count": result.warning_count,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
        "synthetic_only": result.synthetic_only,
        "artifact_path": str(result.artifact_path),
        "report_path": str(result.report_path),
        "recommended_next_task": RECOMMENDED_NEXT_TASK,
        "real_csv_consumed": False,
        "output_files": {
            key: str(value)
            for key, value in result.artifact_paths.items()
            if key != "artifact_dir"
        },
    }
    metadata.update(tiny_pit_reviewed_package_fixture_safety_flags())
    return metadata


def _package_manifest(result: TinyPitReviewedPackageFixtureArtifacts) -> dict[str, Any]:
    return {
        "fixture_id": str(result.fixture_id),
        "package_id": "000001",
        "package_version": "synthetic-v0.1",
        "package_type": "SYNTHETIC_REVIEWED_PACKAGE_FIXTURE",
        "created_at": result.created_at,
        "report_only": True,
        "diagnostic_only": True,
        "synthetic_only": True,
        "real_file_path_required": False,
        "real_csv_consumed": False,
        "reviewed_meaning": "simulated metadata only",
    }


def _manifest_rows(result: TinyPitReviewedPackageFixtureArtifacts, section_name: str) -> list[dict[str, Any]]:
    return [
        {
            "fixture_id": result.fixture_id,
            "package_id": "000001",
            "case_name": row["case_name"],
            "section_name": section_name,
            "section_status": row["actual_status"],
            "row_count": 1,
            "report_only": True,
            "diagnostic_only": True,
            "synthetic_only": True,
            "limitation_note": row["limitation_note"],
        }
        for row in result.case_results
    ]


def _write_report(result: TinyPitReviewedPackageFixtureArtifacts) -> None:
    lines = [
        "# Tiny PIT Reviewed Package Fixture v0.1",
        "",
        "This artifact is synthetic-only, report-only, and diagnostic-only.",
        "",
        "In this fixture, reviewed means simulated metadata only. It is not real reviewed CSV package, "
        "not active reviewed input candidate, not real replay input, not active replay input, and not ACTIVE_REPLAY_INPUT_READY.",
        "",
        "It creates no replay execution, no labels/training/metrics/signal_score/model/stock_profile/paper/buy-review/performance/trading, "
        "and no data/raw, data/processed, or data/cache writes.",
        "",
        f"- Fixture id: `{result.fixture_id}`",
        f"- Workflow stage: `{result.workflow_stage}`",
        f"- Status: `{result.status}`",
        f"- Health: `{result.health_status}`",
        f"- Case count: `{result.case_count}`",
        f"- Blocker count: `{result.blocker_count}`",
        f"- Warning count: `{result.warning_count}`",
        "",
        "## Case Summary",
        "",
        "| Case | Status | Health | Blockers | Warnings |",
        "|---|---|---:|---:|---:|",
    ]
    for row in result.case_results:
        lines.append(
            f"| `{row['case_name']}` | `{row['actual_status']}` | `{row['health_status']}` | "
            f"{row['blocker_count']} | {row['warning_count']} |"
        )
    lines.extend(
        [
            "",
            "## Recommended Next Task",
            "",
            RECOMMENDED_NEXT_TASK,
        ]
    )
    result.artifact_paths["report"].write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_limitations(result: TinyPitReviewedPackageFixtureArtifacts) -> None:
    lines = [
        "# Tiny PIT Reviewed Package Fixture Limitations",
        "",
        "- Synthetic package shape only.",
        "- No real reviewed CSV package is consumed or created.",
        "- No real source permission or real reviewer authority is established.",
        "- No real PIT admissibility is proven.",
        "- No active replay input, replay execution, labels, training, stock_profile, paper validation, buy-review, performance validation, or trading is created.",
    ]
    result.artifact_paths["package_limitations"].write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = MANIFEST_COLUMNS if path.name != "package_section_manifest.csv" else MANIFEST_COLUMNS
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]
