"""Local-only index for PIT universe evidence completion helper artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import read_csv_preserve_symbol_columns


PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_INDEX_COLUMNS = [
    "artifact_type",
    "helper_id",
    "review_id",
    "status",
    "row_count",
    "needs_evidence_count",
    "rows_with_base_hints_count",
    "future_dated_hint_count",
    "authoritative_hint_count",
    "approved_count",
    "valid_for_signal_date_count",
    "no_universe_export",
    "no_data_raw_write",
    "no_data_processed_write",
    "no_current_candidates_generated",
    "no_snapshot_built",
    "no_forward_labels",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "report_path",
    "template_csv_path",
    "metadata_path",
    "created_at",
]

INDEX_LIMITATIONS = [
    "Scans local PIT universe evidence completion helper artifacts only.",
    "Does not approve rows, export universe files, write data/raw or data/processed, run current-candidates, build snapshots, or compute forward labels.",
    "Does not mutate cache, call APIs, send messages, place orders, call brokers, or enable live trading.",
]


@dataclass(frozen=True)
class PitUniverseEvidenceCompletionHelperIndexPaths:
    artifact_dir: Path
    pit_universe_evidence_completion_helper_index_csv: Path
    pit_universe_evidence_completion_helper_index_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "pit_universe_evidence_completion_helper_index_csv": (
                self.pit_universe_evidence_completion_helper_index_csv
            ),
            "pit_universe_evidence_completion_helper_index_report": (
                self.pit_universe_evidence_completion_helper_index_report
            ),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PitUniverseEvidenceCompletionHelperIndexResult:
    artifact_count: int
    index_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def scan_pit_universe_evidence_completion_helper_artifacts(
    root: str | Path = "outputs/reports/point_in_time_universe_evidence_completion_helper",
    *,
    include_missing_metadata: bool = False,
) -> pd.DataFrame:
    rows, _warnings = _scan_artifact_rows(Path(root), include_missing_metadata=include_missing_metadata)
    return _finalize_index_frame(pd.DataFrame(rows))


def build_pit_universe_evidence_completion_helper_index(
    *,
    root: str | Path = "outputs/reports/point_in_time_universe_evidence_completion_helper",
    output_dir: str | Path = "outputs/reports/point_in_time_universe_evidence_completion_helper/index",
    include_missing_metadata: bool = False,
) -> PitUniverseEvidenceCompletionHelperIndexResult:
    effective_root = Path(root)
    rows, warnings = _scan_artifact_rows(effective_root, include_missing_metadata=include_missing_metadata)
    index_frame = _finalize_index_frame(pd.DataFrame(rows))
    paths = resolve_pit_universe_evidence_completion_helper_index_paths(output_dir)
    result = PitUniverseEvidenceCompletionHelperIndexResult(
        artifact_count=len(index_frame),
        index_frame=index_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=INDEX_LIMITATIONS,
        audit_metadata={
            "root_dir": effective_root,
            "artifact_count": len(index_frame),
            "include_missing_metadata": include_missing_metadata,
            "universe_exported": False,
            "would_write_data_raw": False,
            "would_write_data_processed": False,
            "current_candidates_executed": False,
            "snapshot_manifest_built": False,
            "forward_returns_computed": False,
            "cache_mutated": False,
            "network_api_called": False,
            "external_api_called": False,
            "llm_api_called": False,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "message_delivery_enabled": False,
            "message_sent": False,
            "pit_universe_evidence_completion_helper_artifacts_only": True,
        },
    )
    write_pit_universe_evidence_completion_helper_index(result)
    return result


def resolve_pit_universe_evidence_completion_helper_index_paths(
    output_dir: str | Path,
) -> PitUniverseEvidenceCompletionHelperIndexPaths:
    artifact_dir = Path(output_dir)
    return PitUniverseEvidenceCompletionHelperIndexPaths(
        artifact_dir=artifact_dir,
        pit_universe_evidence_completion_helper_index_csv=artifact_dir
        / "pit_universe_evidence_completion_helper_index.csv",
        pit_universe_evidence_completion_helper_index_report=artifact_dir
        / "pit_universe_evidence_completion_helper_index_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def write_pit_universe_evidence_completion_helper_index(
    result: PitUniverseEvidenceCompletionHelperIndexResult,
) -> dict[str, Path]:
    paths = PitUniverseEvidenceCompletionHelperIndexPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.index_frame.to_csv(paths.pit_universe_evidence_completion_helper_index_csv, index=False)
    metadata = build_pit_universe_evidence_completion_helper_index_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.pit_universe_evidence_completion_helper_index_report.write_text(
        render_pit_universe_evidence_completion_helper_index_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_pit_universe_evidence_completion_helper_index_metadata(
    result: PitUniverseEvidenceCompletionHelperIndexResult,
    paths: PitUniverseEvidenceCompletionHelperIndexPaths,
) -> dict[str, Any]:
    return {
        "index_id": _hash_payload({"rows": result.index_frame.to_dict("records")}, length=12),
        "created_at": _metadata_created_at(result.index_frame),
        "artifact_count": result.artifact_count,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        **result.audit_metadata,
        "no_live_trading_statement": (
            "No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, "
            "forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, "
            "or cache mutation was invoked."
        ),
    }


def render_pit_universe_evidence_completion_helper_index_report(
    result: PitUniverseEvidenceCompletionHelperIndexResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    meta = metadata or {}
    return "\n".join(
        [
            "# PIT Universe Evidence Completion Helper Index",
            "",
            "No universe export, data/raw write, data/processed write, current-candidates generation, snapshot build, forward labels, live trading, broker API, order placement, message delivery, LLM/API, external API, or cache mutation was invoked. This index scans local evidence-completion helper artifacts only.",
            "",
            "## Summary",
            "",
            _dict_table({"index_id": meta.get("index_id", ""), "artifact_count": result.artifact_count}),
            "",
            "## Helper Runs",
            "",
            _markdown_table(
                result.index_frame,
                [
                    "helper_id",
                    "review_id",
                    "needs_evidence_count",
                    "rows_with_base_hints_count",
                    "future_dated_hint_count",
                    "authoritative_hint_count",
                    "report_path",
                ],
            ),
            "",
            "## Warnings",
            "",
            _warnings_section(result.warnings),
            "",
        ]
    )


def _scan_artifact_rows(root: Path, *, include_missing_metadata: bool) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not root.exists():
        return rows, [f"PIT universe evidence completion helper root does not exist: {root}"]
    for artifact_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if artifact_dir.name in {"index", "health", "status"}:
            continue
        metadata_path = artifact_dir / "metadata.json"
        if not metadata_path.exists():
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir))
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"Could not read PIT universe evidence helper metadata {metadata_path}: {exc}")
            if include_missing_metadata:
                rows.append(_missing_metadata_row(artifact_dir, status="UNREADABLE_METADATA"))
            continue
        helper_id = _string_or_empty(metadata.get("helper_id"))
        if not helper_id:
            continue
        rows.append(_row_from_metadata(artifact_dir, metadata_path, metadata))
    return rows, warnings


def _row_from_metadata(artifact_dir: Path, metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    template_csv = Path(
        output_files.get("evidence_completion_template")
        or artifact_dir / "pit_universe_evidence_completion_template.csv"
    )
    report = Path(output_files.get("gap_report") or artifact_dir / "pit_universe_evidence_gap_report.md")
    template = _read_csv(template_csv)
    return {
        "artifact_type": "PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER",
        "helper_id": _string_or_empty(metadata.get("helper_id")) or artifact_dir.name,
        "review_id": _string_or_empty(metadata.get("review_id")) or _first_text(template, "review_id"),
        "status": _string_or_empty(metadata.get("status")) or "WARN",
        "row_count": _to_int(metadata.get("row_count", len(template))),
        "needs_evidence_count": _to_int(metadata.get("needs_evidence_count", _needs_evidence_count(template))),
        "rows_with_base_hints_count": _to_int(
            metadata.get("rows_with_base_hints_count", _present_count(template, "hint_source_path"))
        ),
        "future_dated_hint_count": _to_int(
            metadata.get("future_dated_hint_count", _true_count(template, "hint_is_future_dated_for_signal_date"))
        ),
        "authoritative_hint_count": _to_int(
            metadata.get("authoritative_hint_count", _true_count(template, "hint_authoritative_for_pit"))
        ),
        "approved_count": _to_int(metadata.get("approved_count", _approved_count(template))),
        "valid_for_signal_date_count": _to_int(
            metadata.get("valid_for_signal_date_count", _true_count(template, "current_valid_for_signal_date"))
        ),
        "no_universe_export": _to_bool(metadata.get("no_universe_export", not _to_bool(metadata.get("universe_exported")))),
        "no_data_raw_write": _to_bool(metadata.get("no_data_raw_write", not _to_bool(metadata.get("would_write_data_raw")))),
        "no_data_processed_write": _to_bool(
            metadata.get("no_data_processed_write", not _to_bool(metadata.get("would_write_data_processed")))
        ),
        "no_current_candidates_generated": _to_bool(
            metadata.get("no_current_candidates_generated", not _to_bool(metadata.get("current_candidates_executed")))
        ),
        "no_snapshot_built": _to_bool(metadata.get("no_snapshot_built", not _to_bool(metadata.get("snapshot_manifest_built")))),
        "no_forward_labels": _to_bool(metadata.get("no_forward_labels", not _to_bool(metadata.get("forward_returns_computed")))),
        "no_live_trading": _to_bool(metadata.get("no_live_trading", _all_true(template, "no_live_trading"))),
        "no_broker_api": _to_bool(metadata.get("no_broker_api", _all_true(template, "no_broker_api"))),
        "no_order_placement": _to_bool(metadata.get("no_order_placement", _all_true(template, "no_order_placement"))),
        "no_message_sent": _to_bool(metadata.get("no_message_sent", _all_true(template, "no_message_sent"))),
        "report_path": str(report),
        "template_csv_path": str(template_csv),
        "metadata_path": str(metadata_path),
        "created_at": _string_or_empty(metadata.get("created_at")) or _artifact_mtime(artifact_dir),
    }


def _missing_metadata_row(artifact_dir: Path, *, status: str = "MISSING_METADATA") -> dict[str, Any]:
    row = {column: "" for column in PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_INDEX_COLUMNS}
    row.update(
        {
            "artifact_type": "PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER",
            "helper_id": artifact_dir.name,
            "status": status,
            "report_path": str(artifact_dir / "pit_universe_evidence_gap_report.md"),
            "template_csv_path": str(artifact_dir / "pit_universe_evidence_completion_template.csv"),
            "metadata_path": str(artifact_dir / "metadata.json"),
            "created_at": _artifact_mtime(artifact_dir),
        }
    )
    return row


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception:
        return pd.DataFrame()


def _finalize_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_INDEX_COLUMNS)
    output = frame.copy()
    for column in PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_INDEX_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    bool_columns = [
        "no_universe_export",
        "no_data_raw_write",
        "no_data_processed_write",
        "no_current_candidates_generated",
        "no_snapshot_built",
        "no_forward_labels",
        "no_live_trading",
        "no_broker_api",
        "no_order_placement",
        "no_message_sent",
    ]
    for column in bool_columns:
        output[column] = output[column].map(_to_bool).astype(object)
    return output[PIT_UNIVERSE_EVIDENCE_COMPLETION_HELPER_INDEX_COLUMNS].sort_values(
        ["created_at", "helper_id"]
    ).reset_index(drop=True)


def _needs_evidence_count(frame: pd.DataFrame) -> int:
    gap_columns = [
        "missing_reviewer",
        "missing_reviewed_at",
        "missing_review_reason",
        "missing_evidence_source",
        "missing_evidence_path_or_reference",
        "missing_listed_date_evidence",
        "missing_is_active_evidence",
        "missing_survivorship_bias_resolution",
    ]
    available = [column for column in gap_columns if column in frame.columns]
    if frame.empty or not available:
        return 0
    return int(frame[available].apply(lambda row: any(_to_bool(value) for value in row), axis=1).sum())


def _approved_count(frame: pd.DataFrame) -> int:
    if frame.empty or "current_review_status" not in frame.columns:
        return 0
    return int(frame["current_review_status"].map(_string_or_empty).str.upper().eq("APPROVED_FOR_PIT_UNIVERSE").sum())


def _present_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_string_or_empty).ne("").sum())


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].map(_to_bool).sum())


def _all_true(frame: pd.DataFrame, column: str) -> bool:
    if frame.empty or column not in frame.columns:
        return False
    return bool(frame[column].map(_to_bool).all())


def _first_text(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return ""
    values = [_string_or_empty(value) for value in frame[column].tolist()]
    return next((value for value in values if value), "")


def _metadata_created_at(frame: pd.DataFrame) -> str:
    if frame.empty or "created_at" not in frame:
        return "1970-01-01T00:00:00+00:00"
    values = [str(value) for value in frame["created_at"].dropna().tolist() if str(value).strip()]
    return max(values) if values else "1970-01-01T00:00:00+00:00"


def _artifact_mtime(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return ""


def _to_int(value: Any) -> int:
    try:
        if pd.isna(value):
            return 0
    except (TypeError, ValueError):
        pass
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y", "t"}


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return "" if text.lower() in {"nan", "nat", "none", "null"} else text


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item") and value.__class__.__module__.startswith("numpy"):
        return _json_safe(value.item())
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _dict_table(values: dict[str, Any]) -> str:
    return "\n".join(f"- {key}: {value}" for key, value in values.items())


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 100) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "No rows."
    return frame[available].head(max_rows).to_markdown(index=False)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)
