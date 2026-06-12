"""Index minimal replay input package fixture smoke artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


INDEX_COLUMNS = [
    "smoke_run_id",
    "generated_at",
    "artifact_path",
    "input_package_path",
    "validator_run_id",
    "validator_artifact_path",
    "validator_status",
    "validator_workflow_stage",
    "pass_candidate",
    "active_replay_input_ready",
    "active_replay_input",
    "forward_labels_exist",
    "weights_trained",
    "active_stock_profile_exists",
    "real_buy_review_eligible",
    "approval_applied",
    "order_placed",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
    "report_only",
    "diagnostic_only",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "smoke_report_path",
    "validator_result_ref_path",
    "expected_pass_candidate_conditions_path",
    "safety_flag_report_path",
    "recommended_next_task_path",
    "metadata_path",
]


@dataclass(frozen=True)
class MinimalReplayInputPackageFixtureSmokeIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    audit_metadata: dict[str, Any]


def build_minimal_replay_input_package_fixture_smoke_index(
    *,
    root: str | Path = "outputs/reports/manual_diagnostics/minimal_replay_input_package_fixture_smoke_v0_1",
    output_dir: str | Path = "outputs/reports/manual_diagnostics/minimal_replay_input_package_fixture_smoke_v0_1/index",
) -> MinimalReplayInputPackageFixtureSmokeIndexResult:
    rows, warnings = _scan_rows(Path(root))
    frame = _finalize(pd.DataFrame(rows, dtype=object))
    paths = {
        "artifact_dir": Path(output_dir),
        "index_csv": Path(output_dir) / "minimal_replay_input_package_fixture_smoke_index.csv",
        "index_report": Path(output_dir) / "minimal_replay_input_package_fixture_smoke_index_report.md",
        "metadata": Path(output_dir) / "metadata.json",
    }
    result = MinimalReplayInputPackageFixtureSmokeIndexResult(
        artifact_count=len(frame),
        index_frame=frame,
        artifact_paths=paths,
        warnings=warnings,
        audit_metadata=_audit_metadata(root, len(frame)),
    )
    write_minimal_replay_input_package_fixture_smoke_index(result)
    return result


def write_minimal_replay_input_package_fixture_smoke_index(
    result: MinimalReplayInputPackageFixtureSmokeIndexResult,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths["index_csv"], index=False)
    paths["metadata"].write_text(
        json.dumps(
            {
                "index_id": _hash_payload(result.index_frame.to_dict("records")),
                "artifact_count": result.artifact_count,
                "warnings": result.warnings,
                "output_files": {key: str(value) for key, value in paths.items() if key != "artifact_dir"},
                **result.audit_metadata,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    paths["index_report"].write_text(
        "\n".join(
            [
                "# Minimal Replay Input Package Fixture Smoke Index",
                "",
                "Report-only smoke index. No replay, active replay input, current-candidates, snapshots, forward labels, training, active stock profiles, research-status integration, data writes, API calls, messages, broker integration, orders, or cache mutation was invoked.",
                "",
                f"- artifact_count: {result.artifact_count}",
                "",
                result.index_frame.to_markdown(index=False) if not result.index_frame.empty else "No smoke artifacts found.",
            ]
        ),
        encoding="utf-8",
    )
    return paths


def _scan_rows(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not root.exists():
        return [], [f"Smoke root does not exist: {root}"]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"} or artifact_dir.name.startswith("_"):
            continue
        metadata_path = artifact_dir / "smoke_metadata.json"
        if not metadata_path.exists():
            warnings.append(f"Missing smoke metadata for artifact: {artifact_dir}")
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read smoke metadata {metadata_path}: {exc}")
            continue
        if _text(metadata.get("smoke_run_id")):
            rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    artifact_paths = metadata.get("artifact_paths") if isinstance(metadata.get("artifact_paths"), dict) else {}
    validator_artifact_path = Path(_text(metadata.get("validator_artifact_path")))
    validator_metadata = _read_json(validator_artifact_path / "metadata.json") if _text(validator_artifact_path) else {}
    return {
        "smoke_run_id": _text(metadata.get("smoke_run_id")),
        "generated_at": _text(metadata.get("generated_at")) or _artifact_mtime(artifact_dir),
        "artifact_path": _text(metadata.get("artifact_path")) or str(artifact_dir),
        "input_package_path": _text(metadata.get("package_path")) or _path_from_artifact_paths(artifact_paths, "input_package", artifact_dir / "input_package"),
        "validator_run_id": _text(metadata.get("validator_run_id")),
        "validator_artifact_path": _text(metadata.get("validator_artifact_path")),
        "validator_status": _text(metadata.get("validator_status")),
        "validator_workflow_stage": _text(validator_metadata.get("workflow_stage")) or _text(metadata.get("validator_status")),
        "pass_candidate": _to_bool(metadata.get("pass_candidate")),
        "active_replay_input_ready": _to_bool(metadata.get("active_replay_input_ready")),
        "active_replay_input": _to_bool(metadata.get("active_replay_input")),
        "forward_labels_exist": _to_bool(metadata.get("forward_labels_exist")),
        "weights_trained": _to_bool(metadata.get("weights_trained")),
        "active_stock_profile_exists": _to_bool(metadata.get("active_stock_profile_exists")),
        "real_buy_review_eligible": _to_bool(metadata.get("real_buy_review_eligible")),
        "approval_applied": _to_bool(metadata.get("approval_applied")),
        "order_placed": _to_bool(metadata.get("order_placed")),
        "llm_api_called": _to_bool(metadata.get("llm_api_called")),
        "external_api_called": _to_bool(metadata.get("external_api_called")),
        "cache_mutated": _to_bool(metadata.get("cache_mutated")),
        "current_candidates_run": _to_bool(metadata.get("current_candidates_run")),
        "snapshot_built": _to_bool(metadata.get("snapshot_built")),
        "signal_semantics_changed": _to_bool(metadata.get("signal_semantics_changed")),
        "report_only": _to_bool(metadata.get("report_only")),
        "diagnostic_only": _to_bool(metadata.get("diagnostic_only")),
        "no_live_trading": _to_bool(metadata.get("no_live_trading")),
        "no_broker_api": _to_bool(metadata.get("no_broker_api")),
        "no_order_placement": _to_bool(metadata.get("no_order_placement")),
        "no_message_sent": _to_bool(metadata.get("no_message_sent")),
        "smoke_report_path": _path_from_artifact_paths(artifact_paths, "smoke_report", artifact_dir / "smoke_report.md"),
        "validator_result_ref_path": _path_from_artifact_paths(artifact_paths, "validator_result_ref", artifact_dir / "validator_result_ref.json"),
        "expected_pass_candidate_conditions_path": _path_from_artifact_paths(artifact_paths, "expected_pass_candidate_conditions", artifact_dir / "expected_pass_candidate_conditions.csv"),
        "safety_flag_report_path": _path_from_artifact_paths(artifact_paths, "safety_flag_report", artifact_dir / "safety_flag_report.csv"),
        "recommended_next_task_path": _path_from_artifact_paths(artifact_paths, "recommended_next_task", artifact_dir / "recommended_next_task.md"),
        "metadata_path": str(metadata_path),
    }


def _path_from_artifact_paths(artifact_paths: dict[str, Any], key: str, fallback: Path) -> str:
    return _text(artifact_paths.get(key)) or str(fallback)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _finalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS, dtype=object)
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[INDEX_COLUMNS].astype(object)


def _audit_metadata(root: str | Path, artifact_count: int) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "root": str(root),
        "artifact_count": artifact_count,
        "report_only": True,
        "diagnostic_only": True,
    }


def _hash_payload(payload: Any) -> str:
    return hashlib.sha1(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]


def _artifact_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat()


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


__all__ = [
    "MinimalReplayInputPackageFixtureSmokeIndexResult",
    "build_minimal_replay_input_package_fixture_smoke_index",
    "write_minimal_replay_input_package_fixture_smoke_index",
]
