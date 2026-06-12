"""Index report-only historical replay input gate validator fixture artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


INDEX_COLUMNS = [
    "fixture_run_id",
    "generated_at",
    "artifact_path",
    "status",
    "case_count",
    "blocked_case_count",
    "pass_candidate_case_count",
    "active_ready_case_count",
    "validation_issue_count",
    "overclaim_guard_pass_count",
    "overclaim_guard_total_count",
    "active_replay_input",
    "forward_labels_exist",
    "weights_trained",
    "active_stock_profile_exists",
    "real_buy_review_eligible",
    "report_only",
    "diagnostic_only",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "validator_implemented",
    "active_ready_status_allowed",
    "report_path",
    "fixture_cases_path",
    "blocked_requirements_path",
    "expected_status_matrix_path",
    "fixture_input_schema_path",
    "overclaim_guard_report_path",
    "validation_issues_path",
    "metadata_path",
]


@dataclass(frozen=True)
class HistoricalReplayInputGateValidatorFixtureIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_historical_replay_input_gate_validator_fixture_index(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_fixture_v0_1/index",
) -> HistoricalReplayInputGateValidatorFixtureIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "historical_replay_input_gate_validator_fixture_index.csv",
        "index_report": Path(output_dir) / "historical_replay_input_gate_validator_fixture_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = HistoricalReplayInputGateValidatorFixtureIndexResult(
        artifact_count=len(frame),
        index_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata=_audit_metadata(root, len(frame)),
    )
    write_historical_replay_input_gate_validator_fixture_index(result)
    return result


def write_historical_replay_input_gate_validator_fixture_index(
    result: HistoricalReplayInputGateValidatorFixtureIndexResult,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths["index_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            _json_safe(
                {
                    "index_id": _hash_payload(result.index_frame.to_dict("records")),
                    "artifact_count": result.artifact_count,
                    "warnings": result.warnings,
                    "output_files": {
                        key: str(value) for key, value in paths.items() if key != "artifact_dir"
                    },
                    **result.audit_metadata,
                }
            ),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    paths["index_report"].write_text(
        "\n".join(
            [
                "# Historical Replay Input Gate Validator Fixture Index",
                "",
                "Report-only index. No replay, current-candidates, snapshots, forward labels, training, active stock profiles, real validator, research-status integration, data writes, API calls, messages, broker integration, orders, or cache mutation was invoked.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False)
                if not result.index_frame.empty
                else "No fixture artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Fixture root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            warnings.append(f"Missing metadata for fixture artifact: {artifact_dir}")
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read fixture metadata {metadata_path}: {exc}")
            continue
        if _text(metadata.get("fixture_run_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    artifact_paths = metadata.get("artifact_paths") if isinstance(metadata.get("artifact_paths"), dict) else {}
    return {
        "fixture_run_id": _text(metadata.get("fixture_run_id")),
        "generated_at": _text(metadata.get("generated_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": _text(metadata.get("artifact_path")) or str(artifact_dir),
        "status": _text(metadata.get("status")) or "PASS",
        "case_count": _to_int(metadata.get("case_count")),
        "blocked_case_count": _to_int(metadata.get("blocked_case_count")),
        "pass_candidate_case_count": _to_int(metadata.get("pass_candidate_case_count")),
        "active_ready_case_count": _to_int(metadata.get("active_ready_case_count")),
        "validation_issue_count": _to_int(metadata.get("validation_issue_count")),
        "overclaim_guard_pass_count": _to_int(metadata.get("overclaim_guard_pass_count")),
        "overclaim_guard_total_count": _to_int(metadata.get("overclaim_guard_total_count")),
        "active_replay_input": _to_bool(metadata.get("active_replay_input")),
        "forward_labels_exist": _to_bool(metadata.get("forward_labels_exist")),
        "weights_trained": _to_bool(metadata.get("weights_trained")),
        "active_stock_profile_exists": _to_bool(metadata.get("active_stock_profile_exists")),
        "real_buy_review_eligible": _to_bool(metadata.get("real_buy_review_eligible")),
        "report_only": _to_bool(metadata.get("report_only")),
        "diagnostic_only": _to_bool(metadata.get("diagnostic_only")),
        "no_live_trading": _to_bool(metadata.get("no_live_trading")),
        "no_broker_api": _to_bool(metadata.get("no_broker_api")),
        "no_order_placement": _to_bool(metadata.get("no_order_placement")),
        "no_message_sent": _to_bool(metadata.get("no_message_sent")),
        "llm_api_called": _to_bool(metadata.get("llm_api_called")),
        "external_api_called": _to_bool(metadata.get("external_api_called")),
        "cache_mutated": _to_bool(metadata.get("cache_mutated")),
        "current_candidates_run": _to_bool(metadata.get("current_candidates_run")),
        "snapshot_built": _to_bool(metadata.get("snapshot_built")),
        "signal_semantics_changed": _to_bool(metadata.get("signal_semantics_changed")),
        "validator_implemented": _to_bool(metadata.get("validator_implemented")),
        "active_ready_status_allowed": _to_bool(metadata.get("active_ready_status_allowed")),
        "report_path": _path_text(artifact_paths, "report", artifact_dir / "historical_replay_input_gate_validator_fixture_report.md"),
        "fixture_cases_path": _path_text(artifact_paths, "fixture_cases", artifact_dir / "fixture_cases.csv"),
        "blocked_requirements_path": _path_text(artifact_paths, "blocked_requirements", artifact_dir / "blocked_requirements.csv"),
        "expected_status_matrix_path": _path_text(artifact_paths, "expected_status_matrix", artifact_dir / "expected_status_matrix.csv"),
        "fixture_input_schema_path": _path_text(artifact_paths, "fixture_input_schema", artifact_dir / "fixture_input_schema.csv"),
        "overclaim_guard_report_path": _path_text(artifact_paths, "overclaim_guard_report", artifact_dir / "overclaim_guard_report.csv"),
        "validation_issues_path": _path_text(artifact_paths, "validation_issues", artifact_dir / "validation_issues.csv"),
        "metadata_path": str(metadata_path),
    }


def _path_text(paths: dict[str, Any], key: str, fallback: Path) -> str:
    value = paths.get(key)
    return _text(value) or str(fallback)


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS, dtype=object)
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[INDEX_COLUMNS].astype(object)


def _audit_metadata(root: str | Path, artifact_count: int) -> dict[str, Any]:
    return {
        "root": str(root),
        "artifact_count": artifact_count,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "report_only": True,
        "diagnostic_only": True,
        "active_replay_input": False,
        "forward_labels_exist": False,
        "weights_trained": False,
        "active_stock_profile_exists": False,
        "real_buy_review_eligible": False,
    }


def _artifact_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat()


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


__all__ = [
    "HistoricalReplayInputGateValidatorFixtureIndexResult",
    "build_historical_replay_input_gate_validator_fixture_index",
]
