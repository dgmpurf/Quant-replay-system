"""Local-only index for paper-trading artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import PaperArtifactIndexSettings, Settings, load_settings


PAPER_ARTIFACT_INDEX_LIMITATIONS = [
    "Scans local paper-trading artifact folders only.",
    "Reads metadata.json and report files already written by local workflows.",
    "Does not place live orders or call broker APIs.",
    "Does not validate fills, review updates, or accounting; it only indexes existing artifacts.",
]

INDEX_COLUMNS = [
    "artifact_type",
    "artifact_id",
    "artifact_date",
    "created_at",
    "status",
    "report_path",
    "metadata_path",
    "decisions_path",
    "reviewed_decisions_path",
    "fills_path",
    "reconciliation_report_path",
    "issue_count",
    "error_count",
    "warning_count",
    "open_position_count",
    "closed_trade_count",
    "paper_cash",
    "total_equity",
    "no_live_trading_statement_present",
]

ARTIFACT_FOLDERS = {
    "DAILY": "daily",
    "REVIEW": "reviews",
    "RECONCILIATION": "reconciliation",
}

NO_LIVE_STATEMENTS = [
    "No broker or live trading integration was invoked",
    "No live trading or broker API was invoked",
]


@dataclass(frozen=True)
class PaperArtifactIndexArtifactPaths:
    artifact_dir: Path
    paper_artifact_index: Path
    paper_artifact_index_csv: Path
    paper_artifact_index_json: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "paper_artifact_index": self.paper_artifact_index,
            "paper_artifact_index_csv": self.paper_artifact_index_csv,
            "paper_artifact_index_json": self.paper_artifact_index_json,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PaperArtifactIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_paper_trading_artifacts(
    root: str | Path | None = None,
    *,
    artifact_type: str = "all",
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    """Scan paper-trading artifact folders and return an index DataFrame."""

    rows, _ = _scan_artifact_rows(
        Path(root) if root is not None else PaperArtifactIndexSettings().root_dir,
        artifact_type=artifact_type,
        include_missing_metadata=include_missing_metadata,
    )
    return _finalize_index_frame(pd.DataFrame(rows))


def load_paper_artifact_metadata(path: str | Path) -> dict[str, Any]:
    """Load one paper artifact metadata JSON file."""

    metadata_path = Path(path)
    if not metadata_path.exists():
        raise FileNotFoundError(f"Paper artifact metadata not found: {metadata_path}")
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def build_paper_artifact_index(
    *,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    artifact_type: str | None = None,
    include_missing_metadata: bool | None = None,
    settings: Settings | PaperArtifactIndexSettings | dict[str, Any] | None = None,
) -> PaperArtifactIndexResult:
    """Build and optionally write a consolidated paper-trading artifact index."""

    project_settings, index_settings = _resolve_settings(settings)
    if index_settings.enable_live_trading or index_settings.enable_broker_api:
        raise ValueError("Paper artifact index cannot enable live trading or broker API access")

    effective_root = Path(root) if root is not None else index_settings.root_dir
    effective_output_dir = Path(output_dir) if output_dir is not None else index_settings.output_dir
    effective_type = artifact_type if artifact_type is not None else index_settings.artifact_type
    effective_include_missing = (
        bool(include_missing_metadata)
        if include_missing_metadata is not None
        else index_settings.include_missing_metadata
    )
    rows, warnings = _scan_artifact_rows(
        effective_root,
        artifact_type=effective_type,
        include_missing_metadata=effective_include_missing,
    )
    index_frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_paper_artifact_index_paths(effective_output_dir)
    audit_metadata = {
        "root_dir": effective_root,
        "artifact_type": _normalize_artifact_type(effective_type),
        "include_missing_metadata": effective_include_missing,
        "artifact_count": len(index_frame),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
        "config_version": index_settings.config_version,
    }
    result = PaperArtifactIndexResult(
        artifact_count=len(index_frame),
        index_frame=index_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=PAPER_ARTIFACT_INDEX_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if index_settings.write_artifacts:
        write_paper_artifact_index(result)
    _ = project_settings
    return result


def resolve_paper_artifact_index_paths(output_dir: str | Path) -> PaperArtifactIndexArtifactPaths:
    """Resolve stable artifact paths for the paper artifact index."""

    artifact_dir = Path(output_dir)
    return PaperArtifactIndexArtifactPaths(
        artifact_dir=artifact_dir,
        paper_artifact_index=artifact_dir / "paper_artifact_index.md",
        paper_artifact_index_csv=artifact_dir / "paper_artifact_index.csv",
        paper_artifact_index_json=artifact_dir / "paper_artifact_index.json",
        metadata=artifact_dir / "metadata.json",
    )


def write_paper_artifact_index(result: PaperArtifactIndexResult) -> dict[str, Path]:
    """Write paper artifact index markdown, CSV, JSON, and metadata."""

    paths = PaperArtifactIndexArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    export = _sanitize_dataframe_for_export(result.index_frame)
    export.to_csv(paths.paper_artifact_index_csv, index=False)
    paths.paper_artifact_index_json.write_text(
        json.dumps(_json_safe(export.to_dict("records")), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    metadata = build_paper_artifact_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.paper_artifact_index.write_text(render_paper_artifact_index_report(result, metadata), encoding="utf-8")
    return paths.as_dict()


def build_paper_artifact_index_metadata(
    result: PaperArtifactIndexResult,
    paths: PaperArtifactIndexArtifactPaths,
) -> dict[str, Any]:
    """Build metadata for the paper artifact index output."""

    return {
        "index_id": _generate_index_id(result.index_frame, result.audit_metadata),
        "created_at": _metadata_created_at(result.index_frame),
        "artifact_count": result.artifact_count,
        "artifact_type_counts": _artifact_type_counts(result.index_frame),
        "config_summary": {
            "root_dir": str(result.audit_metadata.get("root_dir", "")),
            "artifact_type": result.audit_metadata.get("artifact_type", "all"),
            "include_missing_metadata": bool(result.audit_metadata.get("include_missing_metadata", False)),
            "config_version": result.audit_metadata.get("config_version", ""),
        },
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_paper_artifact_index_report(
    result: PaperArtifactIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render the markdown paper artifact index report."""

    meta = metadata or {
        "index_id": _generate_index_id(result.index_frame, result.audit_metadata),
        "artifact_type_counts": _artifact_type_counts(result.index_frame),
    }
    lines = [
        "# Paper Trading Artifact Index",
        "",
        "No broker or live trading integration was invoked. This index scans local paper-trading artifacts only.",
        "",
        "## Index Metadata",
        "",
        _dict_table(
            {
                "index_id": meta.get("index_id", ""),
                "root_dir": result.audit_metadata.get("root_dir", ""),
                "artifact_count": result.artifact_count,
                "artifact_type": result.audit_metadata.get("artifact_type", "all"),
                "include_missing_metadata": result.audit_metadata.get("include_missing_metadata", False),
            }
        ),
        "",
        "## Artifact Type Summary",
        "",
        _markdown_table(_artifact_type_summary_frame(result.index_frame), ["artifact_type", "artifact_count"]),
        "",
        "## Artifact Index",
        "",
        _markdown_table(
            result.index_frame,
            [
                "artifact_type",
                "artifact_id",
                "artifact_date",
                "status",
                "report_path",
                "issue_count",
                "error_count",
                "warning_count",
                "open_position_count",
                "closed_trade_count",
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


def _scan_artifact_rows(
    root: Path,
    *,
    artifact_type: str,
    include_missing_metadata: bool,
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for type_label, folder_name in _selected_artifact_folders(artifact_type).items():
        artifact_root = root / folder_name
        if not artifact_root.exists():
            continue
        for artifact_dir in sorted(path for path in artifact_root.iterdir() if path.is_dir()):
            metadata_path = artifact_dir / "metadata.json"
            if not metadata_path.exists():
                if include_missing_metadata:
                    rows.append(_missing_metadata_row(type_label, artifact_dir, metadata_path))
                    warnings.append(f"Missing metadata included in index: {metadata_path}")
                continue
            try:
                metadata = load_paper_artifact_metadata(metadata_path)
            except (OSError, json.JSONDecodeError) as exc:
                if include_missing_metadata:
                    rows.append(_invalid_metadata_row(type_label, artifact_dir, metadata_path, exc))
                    warnings.append(f"Unreadable metadata included in index: {metadata_path}: {exc}")
                continue
            rows.append(_row_from_metadata(type_label, artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(
    artifact_type: str,
    artifact_dir: Path,
    metadata_path: Path,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    if artifact_type == "DAILY":
        report_path = _metadata_path(output_files, "paper_report", artifact_dir / "paper_report.md")
        daily_summary_path = _metadata_path(output_files, "daily_summary", artifact_dir / "daily_summary.csv")
        daily_summary = _load_first_summary_row(daily_summary_path)
        reconciliation = metadata.get("reconciliation") if isinstance(metadata.get("reconciliation"), dict) else {}
        reconciliation_report_path = _path_or_blank(
            reconciliation.get("report_path") or output_files.get("reconciliation_report")
        )
        return _base_row(
            artifact_type=artifact_type,
            artifact_id=_string_or_empty(metadata.get("journal_id")) or artifact_dir.name,
            artifact_date=_date_string(metadata.get("paper_date")),
            created_at=_string_or_empty(metadata.get("created_at")),
            status=_string_or_empty(metadata.get("status")) or _string_or_empty(reconciliation.get("status")),
            report_path=report_path,
            metadata_path=metadata_path,
            decisions_path=_metadata_path(output_files, "decisions", artifact_dir / "decisions.csv"),
            reviewed_decisions_path=_path_or_blank(metadata.get("reviewed_decisions_path")),
            fills_path=_metadata_path(output_files, "fills", artifact_dir / "fills.csv"),
            reconciliation_report_path=reconciliation_report_path,
            issue_count=_int_or_blank(reconciliation.get("issue_count")),
            error_count=_int_or_blank(reconciliation.get("error_count")),
            warning_count=_int_or_blank(reconciliation.get("warning_count")),
            open_position_count=_int_or_blank(metadata.get("open_position_count")),
            closed_trade_count=_int_or_blank(metadata.get("closed_trade_count")),
            paper_cash=_value_from_summary(daily_summary, "paper_cash"),
            total_equity=_value_from_summary(daily_summary, "total_equity"),
            no_live_trading_statement_present=_no_live_statement_present(metadata, report_path),
        )
    if artifact_type == "REVIEW":
        report_path = _metadata_path(output_files, "paper_review_report", artifact_dir / "paper_review_report.md")
        return _base_row(
            artifact_type=artifact_type,
            artifact_id=_string_or_empty(metadata.get("review_id")) or artifact_dir.name,
            artifact_date=_date_from_created_at(metadata.get("created_at")),
            created_at=_string_or_empty(metadata.get("created_at")),
            status="REVIEWED",
            report_path=report_path,
            metadata_path=metadata_path,
            reviewed_decisions_path=_metadata_path(output_files, "reviewed_decisions", artifact_dir / "reviewed_decisions.csv"),
            warning_count=len(metadata.get("warnings", [])) if isinstance(metadata.get("warnings"), list) else "",
            no_live_trading_statement_present=_no_live_statement_present(metadata, report_path),
        )
    report_path = _metadata_path(output_files, "reconciliation_report", artifact_dir / "reconciliation_report.md")
    return _base_row(
        artifact_type=artifact_type,
        artifact_id=_string_or_empty(metadata.get("reconciliation_id")) or artifact_dir.name,
        artifact_date=_date_from_created_at(metadata.get("created_at")),
        created_at=_string_or_empty(metadata.get("created_at")),
        status=_string_or_empty(metadata.get("status")),
        report_path=report_path,
        metadata_path=metadata_path,
        reconciliation_report_path=report_path,
        issue_count=_int_or_blank(metadata.get("issue_count")),
        error_count=_int_or_blank(metadata.get("error_count")),
        warning_count=_int_or_blank(metadata.get("warning_count")),
        no_live_trading_statement_present=_no_live_statement_present(metadata, report_path),
    )


def _missing_metadata_row(artifact_type: str, artifact_dir: Path, metadata_path: Path) -> dict[str, Any]:
    return _base_row(
        artifact_type=artifact_type,
        artifact_id=artifact_dir.name,
        status="MISSING_METADATA",
        metadata_path=metadata_path,
        report_path=_default_report_path(artifact_type, artifact_dir),
        no_live_trading_statement_present=False,
    )


def _invalid_metadata_row(
    artifact_type: str,
    artifact_dir: Path,
    metadata_path: Path,
    exc: Exception,
) -> dict[str, Any]:
    return _base_row(
        artifact_type=artifact_type,
        artifact_id=artifact_dir.name,
        status="INVALID_METADATA",
        metadata_path=metadata_path,
        report_path=_default_report_path(artifact_type, artifact_dir),
        warning_count=1,
        no_live_trading_statement_present=False,
    ) | {"status": f"INVALID_METADATA: {exc.__class__.__name__}"}


def _base_row(**values: Any) -> dict[str, Any]:
    row = {column: "" for column in INDEX_COLUMNS}
    row.update(values)
    return row


def _selected_artifact_folders(artifact_type: str) -> dict[str, str]:
    normalized = _normalize_artifact_type(artifact_type)
    if normalized == "all":
        return ARTIFACT_FOLDERS
    reverse = {"daily": "DAILY", "review": "REVIEW", "reconciliation": "RECONCILIATION"}
    return {reverse[normalized]: ARTIFACT_FOLDERS[reverse[normalized]]}


def _normalize_artifact_type(value: str) -> str:
    normalized = str(value or "all").lower().strip()
    if normalized not in {"daily", "review", "reconciliation", "all"}:
        raise ValueError("artifact_type must be one of: daily, review, reconciliation, all")
    return normalized


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    index = frame.copy(deep=True)
    for column in INDEX_COLUMNS:
        if column not in index.columns:
            index[column] = ""
    if index.empty:
        return index[INDEX_COLUMNS]
    index = index[INDEX_COLUMNS].sort_values(
        ["artifact_type", "artifact_date", "artifact_id", "report_path"],
        na_position="last",
    )
    return index.reset_index(drop=True)


def _metadata_path(output_files: dict[str, Any], key: str, default: Path) -> str:
    value = output_files.get(key)
    if _present(value):
        return str(value)
    return str(default)


def _path_or_blank(value: Any) -> str:
    return str(value) if _present(value) else ""


def _default_report_path(artifact_type: str, artifact_dir: Path) -> str:
    filenames = {
        "DAILY": "paper_report.md",
        "REVIEW": "paper_review_report.md",
        "RECONCILIATION": "reconciliation_report.md",
    }
    return str(artifact_dir / filenames[artifact_type])


def _no_live_statement_present(metadata: dict[str, Any], report_path: str) -> bool:
    metadata_statement = _string_or_empty(metadata.get("no_live_trading_statement"))
    if any(statement in metadata_statement for statement in NO_LIVE_STATEMENTS):
        return True
    path = Path(report_path) if _present(report_path) else None
    if path is not None:
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


def _load_first_summary_row(path_value: str) -> dict[str, Any]:
    if not _present(path_value):
        return {}
    path = Path(path_value)
    candidates = [path]
    if not path.is_absolute():
        candidates.append(Path.cwd() / path)
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            frame = pd.read_csv(candidate)
        except (OSError, pd.errors.ParserError):
            return {}
        if frame.empty:
            return {}
        return frame.iloc[0].to_dict()
    return {}


def _value_from_summary(summary: dict[str, Any], column: str) -> Any:
    value = summary.get(column, "")
    return "" if not _present(value) else value


def _date_string(value: Any) -> str:
    if not _present(value):
        return ""
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        return ""
    return str(timestamp.date())


def _date_from_created_at(value: Any) -> str:
    return _date_string(value) if _present(value) else ""


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


def _artifact_type_counts(frame: pd.DataFrame) -> dict[str, int]:
    if frame.empty or "artifact_type" not in frame.columns:
        return {}
    counts = frame["artifact_type"].astype(str).value_counts().sort_index()
    return {str(key): int(value) for key, value in counts.items()}


def _artifact_type_summary_frame(frame: pd.DataFrame) -> pd.DataFrame:
    counts = _artifact_type_counts(frame)
    return pd.DataFrame(
        [{"artifact_type": key, "artifact_count": value} for key, value in counts.items()]
    )


def _generate_index_id(frame: pd.DataFrame, audit_metadata: dict[str, Any]) -> str:
    payload = {
        "root_dir": str(audit_metadata.get("root_dir", "")),
        "artifact_type": audit_metadata.get("artifact_type", "all"),
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
    settings: Settings | PaperArtifactIndexSettings | dict[str, Any] | None,
) -> tuple[Settings, PaperArtifactIndexSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.paper_artifact_index
    if isinstance(settings, Settings):
        return settings, settings.paper_artifact_index
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, PaperArtifactIndexSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.paper_artifact_index.model_dump())
        for key, value in settings.items():
            if key == "paper_artifact_index" and isinstance(value, dict):
                payload.update(value)
            elif key in payload:
                payload[key] = value
        return project, PaperArtifactIndexSettings(**payload)
    raise TypeError("settings must be Settings, PaperArtifactIndexSettings, dict, or None")


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
