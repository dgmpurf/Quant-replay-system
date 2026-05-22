"""Local-only index for current-candidate artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import CurrentCandidateArtifactIndexSettings, Settings, load_settings


CURRENT_CANDIDATE_INDEX_LIMITATIONS = [
    "Scans local current-candidate artifact folders only.",
    "Reads metadata.json and markdown reports already written by current candidate generation.",
    "Does not regenerate candidates or rerun scoring.",
    "Does not place live orders or call broker APIs.",
]

CURRENT_CANDIDATE_INDEX_COLUMNS = [
    "artifact_type",
    "run_id",
    "decision_date",
    "universe_name",
    "candidate_count",
    "factor_dataset_row_count",
    "scored_dataset_row_count",
    "snapshot_quality_status",
    "report_path",
    "factor_dataset_path",
    "scored_dataset_path",
    "candidates_path",
    "metadata_path",
    "created_at",
    "no_live_trading_statement_present",
]

NO_LIVE_STATEMENTS = [
    "No broker or live trading integration was invoked",
    "No live trading or broker API was invoked",
]


@dataclass(frozen=True)
class CurrentCandidateArtifactIndexPaths:
    artifact_dir: Path
    current_candidate_artifact_index: Path
    current_candidate_artifact_index_csv: Path
    current_candidate_artifact_index_json: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "current_candidate_artifact_index": self.current_candidate_artifact_index,
            "current_candidate_artifact_index_csv": self.current_candidate_artifact_index_csv,
            "current_candidate_artifact_index_json": self.current_candidate_artifact_index_json,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CurrentCandidateArtifactIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_current_candidate_artifacts(
    root: str | Path | None = None,
    *,
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    """Scan current-candidate artifact folders and return an index frame."""

    rows, _ = _scan_artifact_rows(
        Path(root) if root is not None else CurrentCandidateArtifactIndexSettings().root_dir,
        include_missing_metadata=include_missing_metadata,
    )
    return _finalize_index_frame(pd.DataFrame(rows))


def load_current_candidate_metadata(path: str | Path) -> dict[str, Any]:
    """Load one current-candidate metadata JSON file."""

    metadata_path = Path(path)
    if not metadata_path.exists():
        raise FileNotFoundError(f"Current-candidate metadata not found: {metadata_path}")
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def build_current_candidate_artifact_index(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    include_missing_metadata: bool | None = None,
    settings: Settings | CurrentCandidateArtifactIndexSettings | dict[str, Any] | None = None,
) -> CurrentCandidateArtifactIndexResult:
    """Build and optionally write a current-candidate artifact index."""

    project_settings, index_settings = _resolve_settings(settings)
    if index_settings.enable_live_trading or index_settings.enable_broker_api:
        raise ValueError("Current-candidate artifact index cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else index_settings.root_dir
    effective_output_dir = Path(output_dir) if output_dir is not None else index_settings.output_dir
    effective_include_missing = (
        bool(include_missing_metadata)
        if include_missing_metadata is not None
        else index_settings.include_missing_metadata
    )
    rows, warnings = _scan_artifact_rows(effective_root, include_missing_metadata=effective_include_missing)
    index_frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_current_candidate_artifact_index_paths(effective_output_dir)
    audit_metadata = {
        "root_dir": effective_root,
        "include_missing_metadata": effective_include_missing,
        "artifact_count": len(index_frame),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "current_candidate_artifacts_only": True,
        "config_version": index_settings.config_version,
    }
    result = CurrentCandidateArtifactIndexResult(
        artifact_count=len(index_frame),
        index_frame=index_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=CURRENT_CANDIDATE_INDEX_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if index_settings.write_artifacts:
        write_current_candidate_artifact_index(result)
    _ = project_settings
    return result


def resolve_current_candidate_artifact_index_paths(
    output_dir: str | Path,
) -> CurrentCandidateArtifactIndexPaths:
    """Resolve stable current-candidate index artifact paths."""

    artifact_dir = Path(output_dir)
    return CurrentCandidateArtifactIndexPaths(
        artifact_dir=artifact_dir,
        current_candidate_artifact_index=artifact_dir / "current_candidate_artifact_index.md",
        current_candidate_artifact_index_csv=artifact_dir / "current_candidate_artifact_index.csv",
        current_candidate_artifact_index_json=artifact_dir / "current_candidate_artifact_index.json",
        metadata=artifact_dir / "metadata.json",
    )


def write_current_candidate_artifact_index(
    result: CurrentCandidateArtifactIndexResult,
) -> dict[str, Path]:
    """Write current-candidate artifact index markdown, CSV, JSON, and metadata."""

    paths = CurrentCandidateArtifactIndexPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    export = _sanitize_dataframe_for_export(result.index_frame)
    export.to_csv(paths.current_candidate_artifact_index_csv, index=False)
    paths.current_candidate_artifact_index_json.write_text(
        json.dumps(_json_safe(export.to_dict("records")), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    metadata = build_current_candidate_artifact_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.current_candidate_artifact_index.write_text(
        render_current_candidate_artifact_index_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_current_candidate_artifact_index_metadata(
    result: CurrentCandidateArtifactIndexResult,
    paths: CurrentCandidateArtifactIndexPaths,
) -> dict[str, Any]:
    """Build metadata for the current-candidate artifact index output."""

    return {
        "index_id": _generate_index_id(result.index_frame, result.audit_metadata),
        "created_at": _metadata_created_at(result.index_frame),
        "artifact_count": result.artifact_count,
        "config_summary": {
            "root_dir": str(result.audit_metadata.get("root_dir", "")),
            "include_missing_metadata": bool(result.audit_metadata.get("include_missing_metadata", False)),
            "config_version": result.audit_metadata.get("config_version", ""),
        },
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "current_candidate_artifacts_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_current_candidate_artifact_index_report(
    result: CurrentCandidateArtifactIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render the markdown current-candidate artifact index report."""

    meta = metadata or {"index_id": _generate_index_id(result.index_frame, result.audit_metadata)}
    lines = [
        "# Current Candidate Artifact Index",
        "",
        "No broker or live trading integration was invoked. This index scans local current-candidate artifacts only.",
        "",
        "## Index Metadata",
        "",
        _dict_table(
            {
                "index_id": meta.get("index_id", ""),
                "root_dir": result.audit_metadata.get("root_dir", ""),
                "artifact_count": result.artifact_count,
                "include_missing_metadata": result.audit_metadata.get("include_missing_metadata", False),
            }
        ),
        "",
        "## Artifact Index",
        "",
        _markdown_table(
            result.index_frame,
            [
                "run_id",
                "decision_date",
                "universe_name",
                "candidate_count",
                "snapshot_quality_status",
                "report_path",
                "candidates_path",
                "no_live_trading_statement_present",
            ],
            max_rows=100,
        ),
        "",
        "## Warnings",
        "",
        _warnings_section(result.warnings),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in result.known_limitations),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def _scan_artifact_rows(root: Path, *, include_missing_metadata: bool) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not root.exists():
        return rows, [f"Current-candidate artifact root does not exist: {root}"]
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health"}:
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, metadata_path))
                warnings.append(f"Missing metadata included in index: {metadata_path}")
            continue
        try:
            metadata = load_current_candidate_metadata(metadata_path)
        except (OSError, json.JSONDecodeError) as exc:
            if include_missing_metadata:
                rows.append(_invalid_metadata_row(artifact_dir, metadata_path, exc))
                warnings.append(f"Unreadable metadata included in index: {metadata_path}: {exc}")
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    row_counts = metadata.get("row_counts") if isinstance(metadata.get("row_counts"), dict) else {}
    snapshot_quality = metadata.get("snapshot_quality") if isinstance(metadata.get("snapshot_quality"), dict) else {}
    report_path = _metadata_path(output_files, "current_candidates_report", artifact_dir / "current_candidates_report.md")
    return _base_row(
        artifact_type="CURRENT_CANDIDATES",
        run_id=_string_or_empty(metadata.get("run_id")) or artifact_dir.name,
        decision_date=_date_string(metadata.get("decision_date")),
        universe_name=_string_or_empty(metadata.get("universe_name")),
        candidate_count=_int_or_blank(row_counts.get("candidates")),
        factor_dataset_row_count=_int_or_blank(row_counts.get("factor_dataset")),
        scored_dataset_row_count=_int_or_blank(row_counts.get("scored_dataset")),
        snapshot_quality_status=_string_or_empty(snapshot_quality.get("status")),
        report_path=report_path,
        factor_dataset_path=_metadata_path(output_files, "factor_dataset", artifact_dir / "factor_dataset.csv"),
        scored_dataset_path=_metadata_path(output_files, "scored_dataset", artifact_dir / "scored_dataset.csv"),
        candidates_path=_metadata_path(output_files, "candidates", artifact_dir / "candidates.csv"),
        metadata_path=str(metadata_path),
        created_at=_string_or_empty(metadata.get("created_at")),
        no_live_trading_statement_present=_no_live_statement_present(metadata, report_path),
    )


def _missing_metadata_row(artifact_dir: Path, metadata_path: Path) -> dict[str, Any]:
    return _base_row(
        artifact_type="CURRENT_CANDIDATES",
        run_id=artifact_dir.name,
        report_path=str(artifact_dir / "current_candidates_report.md"),
        factor_dataset_path=str(artifact_dir / "factor_dataset.csv"),
        scored_dataset_path=str(artifact_dir / "scored_dataset.csv"),
        candidates_path=str(artifact_dir / "candidates.csv"),
        metadata_path=str(metadata_path),
        no_live_trading_statement_present=False,
    )


def _invalid_metadata_row(artifact_dir: Path, metadata_path: Path, exc: Exception) -> dict[str, Any]:
    row = _missing_metadata_row(artifact_dir, metadata_path)
    row["snapshot_quality_status"] = f"INVALID_METADATA: {exc.__class__.__name__}"
    return row


def _base_row(**values: Any) -> dict[str, Any]:
    row = {column: "" for column in CURRENT_CANDIDATE_INDEX_COLUMNS}
    row.update(values)
    return row


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    index = frame.copy(deep=True)
    for column in CURRENT_CANDIDATE_INDEX_COLUMNS:
        if column not in index.columns:
            index[column] = ""
    if index.empty:
        return index[CURRENT_CANDIDATE_INDEX_COLUMNS]
    return index[CURRENT_CANDIDATE_INDEX_COLUMNS].sort_values(
        ["decision_date", "universe_name", "run_id", "report_path"],
        na_position="last",
    ).reset_index(drop=True)


def _metadata_path(output_files: dict[str, Any], key: str, default: Path) -> str:
    value = output_files.get(key)
    if _present(value):
        return str(value)
    return str(default)


def _no_live_statement_present(metadata: dict[str, Any], report_path: str) -> bool:
    metadata_statement = _string_or_empty(metadata.get("no_live_trading_statement"))
    if any(statement in metadata_statement for statement in NO_LIVE_STATEMENTS):
        return True
    path = Path(report_path) if _present(report_path) else None
    if path is None:
        return False
    candidates = [path]
    if not path.is_absolute():
        candidates.append(Path.cwd() / path)
    for candidate in candidates:
        if candidate.exists():
            try:
                content = candidate.read_text(encoding="utf-8")
            except OSError:
                continue
            return any(statement in content for statement in NO_LIVE_STATEMENTS)
    return False


def _date_string(value: Any) -> str:
    if not _present(value):
        return ""
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        return ""
    return str(timestamp.date())


def _int_or_blank(value: Any) -> int | str:
    if not _present(value):
        return ""
    try:
        return int(value)
    except (TypeError, ValueError):
        return ""


def _present(value: Any) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    return str(value).strip() != ""


def _string_or_empty(value: Any) -> str:
    return str(value).strip() if _present(value) else ""


def _generate_index_id(frame: pd.DataFrame, audit_metadata: dict[str, Any]) -> str:
    payload = {
        "root_dir": str(audit_metadata.get("root_dir", "")),
        "include_missing_metadata": bool(audit_metadata.get("include_missing_metadata", False)),
        "rows": _sanitize_dataframe_for_export(frame).to_dict("records"),
        "config_version": audit_metadata.get("config_version", ""),
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _metadata_created_at(frame: pd.DataFrame) -> str:
    if frame.empty or "created_at" not in frame.columns:
        return "1970-01-01T00:00:00+00:00"
    values = sorted(str(value) for value in frame["created_at"].dropna() if str(value).strip())
    return values[-1] if values else "1970-01-01T00:00:00+00:00"


def _resolve_settings(
    settings: Settings | CurrentCandidateArtifactIndexSettings | dict[str, Any] | None,
) -> tuple[Settings, CurrentCandidateArtifactIndexSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.current_candidate_artifact_index
    if isinstance(settings, Settings):
        return settings, settings.current_candidate_artifact_index
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, CurrentCandidateArtifactIndexSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.current_candidate_artifact_index.model_dump())
        for key, value in settings.items():
            if key == "current_candidate_artifact_index" and isinstance(value, dict):
                payload.update(value)
            elif key in payload:
                payload[key] = value
        return project, CurrentCandidateArtifactIndexSettings(**payload)
    raise TypeError("settings must be Settings, CurrentCandidateArtifactIndexSettings, dict, or None")


def _sanitize_dataframe_for_export(frame: pd.DataFrame) -> pd.DataFrame:
    export = frame.copy(deep=True)
    for column in export.columns:
        if pd.api.types.is_datetime64_any_dtype(export[column]):
            export[column] = export[column].dt.strftime("%Y-%m-%d %H:%M:%S")
        elif export[column].dtype == "object":
            export[column] = export[column].map(_cell_to_export_value)
    return export


def _cell_to_export_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True)
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return value


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 50) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "_No rows._"
    table = frame[available].head(max_rows).copy()
    rows = [
        "| " + " | ".join(available) + " |",
        "| " + " | ".join("---" for _ in available) + " |",
    ]
    for record in table.to_dict("records"):
        rows.append("| " + " | ".join(_format_markdown_value(record[column]) for column in available) + " |")
    return "\n".join(rows)


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        rows.append(f"| {key} | {_format_markdown_value(value)} |")
    return "\n".join(rows)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)


def _format_markdown_value(value: Any) -> str:
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        return f"{value:.6f}"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_json_safe(value), sort_keys=True).replace("|", "\\|")
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).replace("|", "\\|").replace("\n", " ")


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
