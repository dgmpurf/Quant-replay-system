"""Local-only index for market-update-handoff artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketUpdateHandoffIndexSettings, Settings, load_settings


NO_LIVE_STATEMENTS = [
    "No broker or live trading integration was invoked",
    "No live trading or broker API was invoked",
]

MARKET_UPDATE_HANDOFF_INDEX_LIMITATIONS = [
    "Scans local market-update-handoff artifact folders only.",
    "Reads metadata and report files already written by local workflows.",
    "Does not mutate the market cache, fetch real data, place orders, or call broker APIs.",
]

INDEX_COLUMNS = [
    "handoff_id",
    "artifact_dir",
    "created_at",
    "status",
    "included_row_count",
    "batch_market_csv_path",
    "generated_pipeline_manifest_path",
    "generated_pipeline_manifest_artifact_path",
    "pipeline_id",
    "pipeline_status",
    "data_pipeline_report_path",
    "snapshot_manifest_path",
    "snapshot_quality_status",
    "snapshot_quality_report_path",
    "current_candidate_run_id",
    "current_candidate_report_path",
    "current_candidate_metadata_path",
    "factor_dataset_path",
    "scored_dataset_path",
    "candidates_path",
    "factor_dataset_rows",
    "scored_dataset_rows",
    "candidate_count",
    "handoff_report_path",
    "handoff_rows_path",
    "metadata_path",
    "warning_count",
    "no_live_trading_statement_present",
]


@dataclass(frozen=True)
class MarketUpdateHandoffIndexArtifactPaths:
    artifact_dir: Path
    market_update_handoff_index: Path
    market_update_handoff_index_csv: Path
    market_update_handoff_index_json: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_update_handoff_index": self.market_update_handoff_index,
            "market_update_handoff_index_csv": self.market_update_handoff_index_csv,
            "market_update_handoff_index_json": self.market_update_handoff_index_json,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MarketUpdateHandoffIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_market_update_handoff_artifacts(
    root: str | Path | None = None,
    *,
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    rows, _ = _scan_rows(
        Path(root) if root is not None else MarketUpdateHandoffIndexSettings().root_dir,
        include_missing_metadata=include_missing_metadata,
    )
    return _finalize_index_frame(pd.DataFrame(rows))


def build_market_update_handoff_index(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    include_missing_metadata: bool | None = None,
    settings: Settings | MarketUpdateHandoffIndexSettings | dict[str, Any] | None = None,
) -> MarketUpdateHandoffIndexResult:
    project_settings, index_settings = _resolve_settings(settings)
    if index_settings.enable_live_trading or index_settings.enable_broker_api:
        raise ValueError("Market update handoff index cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else index_settings.root_dir
    effective_output = Path(output_dir) if output_dir is not None else index_settings.output_dir
    effective_include_missing = (
        bool(include_missing_metadata)
        if include_missing_metadata is not None
        else index_settings.include_missing_metadata
    )
    rows, warnings = _scan_rows(effective_root, include_missing_metadata=effective_include_missing)
    frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_market_update_handoff_index_paths(effective_output)
    audit_metadata = {
        "root_dir": effective_root,
        "include_missing_metadata": effective_include_missing,
        "artifact_count": len(frame),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "market_update_handoff_index_only": True,
        "config_version": index_settings.config_version,
    }
    result = MarketUpdateHandoffIndexResult(
        artifact_count=len(frame),
        index_frame=frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=MARKET_UPDATE_HANDOFF_INDEX_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if index_settings.write_artifacts:
        write_market_update_handoff_index(result)
    _ = project_settings
    return result


def resolve_market_update_handoff_index_paths(output_dir: str | Path) -> MarketUpdateHandoffIndexArtifactPaths:
    artifact_dir = Path(output_dir)
    return MarketUpdateHandoffIndexArtifactPaths(
        artifact_dir=artifact_dir,
        market_update_handoff_index=artifact_dir / "market_update_handoff_index.md",
        market_update_handoff_index_csv=artifact_dir / "market_update_handoff_index.csv",
        market_update_handoff_index_json=artifact_dir / "market_update_handoff_index.json",
        metadata=artifact_dir / "metadata.json",
    )


def write_market_update_handoff_index(result: MarketUpdateHandoffIndexResult) -> dict[str, Path]:
    paths = MarketUpdateHandoffIndexArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    export = _sanitize_dataframe_for_export(result.index_frame)
    export.to_csv(paths.market_update_handoff_index_csv, index=False)
    paths.market_update_handoff_index_json.write_text(
        json.dumps(_json_safe(export.to_dict("records")), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    metadata = build_market_update_handoff_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.market_update_handoff_index.write_text(
        render_market_update_handoff_index_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_market_update_handoff_index_metadata(
    result: MarketUpdateHandoffIndexResult,
    paths: MarketUpdateHandoffIndexArtifactPaths,
) -> dict[str, Any]:
    return {
        "index_id": _generate_index_id(result.index_frame, result.audit_metadata),
        "artifact_count": result.artifact_count,
        "root_dir": str(result.audit_metadata.get("root_dir", "")),
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }


def render_market_update_handoff_index_report(
    result: MarketUpdateHandoffIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {"index_id": _generate_index_id(result.index_frame, result.audit_metadata)}
    lines = [
        "# Market Update Handoff Artifact Index",
        "",
        "No live trading or broker API was invoked. This index scans local handoff artifacts only.",
        "",
        "## Index Metadata",
        "",
        _dict_table(
            {
                "index_id": meta.get("index_id", ""),
                "root_dir": result.audit_metadata.get("root_dir", ""),
                "artifact_count": result.artifact_count,
            }
        ),
        "",
        "## Handoff Artifacts",
        "",
        _markdown_table(
            result.index_frame,
            [
                "handoff_id",
                "status",
                "pipeline_id",
                "snapshot_quality_status",
                "current_candidate_run_id",
                "candidate_count",
                "handoff_report_path",
            ],
        ),
    ]
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in result.known_limitations)
    return "\n".join(lines) + "\n"


def _scan_rows(root: Path, *, include_missing_metadata: bool) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not root.exists():
        warnings.append(f"Market update handoff root not found: {root}")
        return rows, warnings
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"}:
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, metadata_path))
            else:
                warnings.append(f"Skipping handoff folder missing metadata.json: {artifact_dir}")
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Skipping unreadable metadata {metadata_path}: {exc}")
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, metadata_path, status="FAIL"))
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    paths = metadata.get("artifact_paths", {}) if isinstance(metadata.get("artifact_paths"), dict) else {}
    audit = metadata.get("audit_metadata", {}) if isinstance(metadata.get("audit_metadata"), dict) else {}
    current_paths = (
        metadata.get("current_candidate_artifact_paths", {})
        if isinstance(metadata.get("current_candidate_artifact_paths"), dict)
        else {}
    )
    if not current_paths:
        current_paths = _infer_current_candidate_paths(
            run_id=str(metadata.get("current_candidate_run_id") or audit.get("current_candidate_run_id") or ""),
            decision_date=str(audit.get("decision_date") or ""),
            universe_name=str(audit.get("universe_name") or ""),
        )
    pipeline_id = str(metadata.get("pipeline_id") or audit.get("pipeline_id") or "")
    pipeline_report_path = str(metadata.get("data_pipeline_report_path") or "")
    if not pipeline_report_path and pipeline_id:
        pipeline_report_path = str(_infer_data_pipeline_artifact(pipeline_id, "data_pipeline_report.md"))
    snapshot_manifest_path = str(metadata.get("snapshot_manifest_path") or "")
    if not snapshot_manifest_path and pipeline_id:
        snapshot_manifest_path = str(_infer_data_pipeline_artifact(pipeline_id, "snapshot_manifest.json"))
    shapes = {
        "factor_dataset_rows": _shape_rows(metadata.get("factor_dataset_shape")),
        "scored_dataset_rows": _shape_rows(metadata.get("scored_dataset_shape")),
        "candidate_count": int(_number(metadata.get("candidate_count"))),
    }
    handoff_report = _path_or_default(paths.get("market_update_handoff_report"), artifact_dir / "market_update_handoff_report.md")
    row = {
        "handoff_id": str(metadata.get("handoff_id") or artifact_dir.name),
        "artifact_dir": str(artifact_dir),
        "created_at": str(metadata.get("created_at") or ""),
        "status": str(metadata.get("status") or ""),
        "included_row_count": int(_number(_first_summary_value(metadata, "included_row_count"))),
        "batch_market_csv_path": str(metadata.get("batch_market_csv_path") or ""),
        "generated_pipeline_manifest_path": str(metadata.get("generated_pipeline_manifest_path") or ""),
        "generated_pipeline_manifest_artifact_path": str(paths.get("generated_pipeline_manifest") or ""),
        "pipeline_id": pipeline_id,
        "pipeline_status": str(metadata.get("pipeline_status") or ""),
        "data_pipeline_report_path": pipeline_report_path,
        "snapshot_manifest_path": snapshot_manifest_path,
        "snapshot_quality_status": str(metadata.get("snapshot_quality_status") or ""),
        "snapshot_quality_report_path": str(metadata.get("snapshot_quality_report_path") or ""),
        "current_candidate_run_id": str(metadata.get("current_candidate_run_id") or ""),
        "current_candidate_report_path": str(current_paths.get("current_candidates_report") or ""),
        "current_candidate_metadata_path": str(current_paths.get("metadata") or ""),
        "factor_dataset_path": str(current_paths.get("factor_dataset") or ""),
        "scored_dataset_path": str(current_paths.get("scored_dataset") or ""),
        "candidates_path": str(current_paths.get("candidates") or ""),
        "factor_dataset_rows": shapes["factor_dataset_rows"],
        "scored_dataset_rows": shapes["scored_dataset_rows"],
        "candidate_count": shapes["candidate_count"],
        "handoff_report_path": str(handoff_report),
        "handoff_rows_path": str(paths.get("market_update_handoff_rows") or artifact_dir / "market_update_handoff_rows.csv"),
        "metadata_path": str(metadata_path),
        "warning_count": len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else 0,
        "no_live_trading_statement_present": _report_has_no_live_statement(handoff_report),
    }
    if not row["included_row_count"]:
        row["included_row_count"] = int(_number(metadata.get("audit_metadata", {}).get("included_row_count", 0)))
    return row


def _missing_metadata_row(artifact_dir: Path, metadata_path: Path, *, status: str = "MISSING_METADATA") -> dict[str, Any]:
    return {
        **{column: "" for column in INDEX_COLUMNS},
        "handoff_id": artifact_dir.name,
        "artifact_dir": str(artifact_dir),
        "status": status,
        "metadata_path": str(metadata_path),
        "handoff_report_path": str(artifact_dir / "market_update_handoff_report.md"),
    }


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=INDEX_COLUMNS)
    output = frame.copy(deep=True)
    for column in INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    output = output[INDEX_COLUMNS]
    if "created_at" in output.columns:
        output["_created_sort"] = pd.to_datetime(output["created_at"], errors="coerce")
        output = output.sort_values(["_created_sort", "handoff_id"], ascending=[False, False], na_position="last")
        output = output.drop(columns=["_created_sort"])
    return output.reset_index(drop=True)


def _path_or_default(value: Any, default: Path) -> Path:
    text = str(value or "").strip()
    return Path(text) if text else default


def _infer_data_pipeline_artifact(pipeline_id: str, filename: str) -> Path:
    return Path("outputs/reports/data_pipeline") / pipeline_id / filename


def _infer_current_candidate_paths(*, run_id: str, decision_date: str, universe_name: str) -> dict[str, str]:
    if not run_id:
        return {}
    root = Path("outputs/reports/current_candidates")
    candidates: list[Path] = []
    if decision_date and universe_name:
        candidates.append(root / f"{decision_date}_{universe_name}_{run_id}")
    candidates.extend(path for path in root.glob(f"*_{run_id}") if path.is_dir())
    for folder in candidates:
        if folder.exists():
            return {
                "current_candidates_report": str(folder / "current_candidates_report.md"),
                "metadata": str(folder / "metadata.json"),
                "factor_dataset": str(folder / "factor_dataset.csv"),
                "scored_dataset": str(folder / "scored_dataset.csv"),
                "candidates": str(folder / "candidates.csv"),
            }
    return {}


def _report_has_no_live_statement(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return any(statement in content for statement in NO_LIVE_STATEMENTS)


def _first_summary_value(metadata: dict[str, Any], key: str) -> Any:
    summary = metadata.get("summary")
    if isinstance(summary, list) and summary:
        return summary[0].get(key)
    return ""


def _shape_rows(value: Any) -> int:
    if isinstance(value, (list, tuple)) and value:
        return int(_number(value[0]))
    return 0


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _resolve_settings(
    settings: Settings | MarketUpdateHandoffIndexSettings | dict[str, Any] | None,
) -> tuple[Settings, MarketUpdateHandoffIndexSettings]:
    project = load_settings(Path("config/default.yaml"))
    if settings is None:
        return project, project.market_update_handoff_index
    if isinstance(settings, Settings):
        return settings, settings.market_update_handoff_index
    if isinstance(settings, MarketUpdateHandoffIndexSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.market_update_handoff_index.model_dump())
        payload.update(settings.get("market_update_handoff_index", settings))
        return project, MarketUpdateHandoffIndexSettings(**payload)
    raise TypeError("settings must be Settings, MarketUpdateHandoffIndexSettings, dict, or None")


def _generate_index_id(frame: pd.DataFrame, metadata: dict[str, Any]) -> str:
    payload = {
        "root_dir": str(metadata.get("root_dir", "")),
        "handoff_ids": sorted(frame.get("handoff_id", pd.Series(dtype="object")).astype(str).tolist()),
        "config_version": metadata.get("config_version", ""),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _sanitize_dataframe_for_export(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy(deep=True)
    for column in output.columns:
        if output[column].dtype == "object":
            output[column] = output[column].map(lambda value: "" if pd.isna(value) else value)
    return output


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "No artifacts found."
    available = [column for column in columns if column in frame.columns]
    return frame[available].to_markdown(index=False)


def _dict_table(values: dict[str, Any]) -> str:
    return pd.DataFrame([{"field": key, "value": value} for key, value in values.items()]).to_markdown(index=False)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if pd.isna(value) if not isinstance(value, (list, tuple, dict, set)) else False:
        return ""
    return value
