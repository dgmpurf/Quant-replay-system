"""Local-only review workflow for paper-trading decisions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_replay_system.config import PaperReviewSettings, Settings, load_settings


REVIEW_STATUSES = {"PENDING_REVIEW", "APPROVED_FOR_PAPER", "REJECTED", "WATCH_ONLY"}
REVIEW_REASON_CODES = {
    "SCORE_CONFIRMED",
    "RISK_TOO_HIGH",
    "LIQUIDITY_TOO_LOW",
    "TECHNICAL_WEAK",
    "OVERHEATED",
    "MANUAL_OVERRIDE",
    "WATCHLIST_ONLY",
    "OTHER",
}

REVIEW_LIMITATIONS = [
    "Uses local CSV/mock data only.",
    "Does not place live orders or call broker APIs.",
    "Review updates are manual audit records, not order instructions.",
    "Does not enforce portfolio sizing, cash checks, or execution feasibility.",
]

REQUIRED_UPDATE_COLUMNS = ["decision_id", "manual_review_status"]
OPTIONAL_UPDATE_COLUMNS = ["manual_review_notes", "reviewer_id", "review_reason_code"]
REVIEWED_DECISION_EXTRA_COLUMNS = ["reviewer_id", "review_time", "review_reason_code"]
AUDIT_COLUMNS = [
    "audit_id",
    "decision_id",
    "old_status",
    "new_status",
    "old_notes",
    "new_notes",
    "reviewer_id",
    "review_reason_code",
    "review_time",
]


@dataclass(frozen=True)
class PaperReviewUpdate:
    decision_id: str
    manual_review_status: str
    manual_review_notes: str = ""
    reviewer_id: str = ""
    review_reason_code: str = "OTHER"


@dataclass(frozen=True)
class PaperReviewArtifactPaths:
    artifact_dir: Path
    reviewed_decisions: Path
    review_audit_log: Path
    review_summary: Path
    paper_review_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "reviewed_decisions": self.reviewed_decisions,
            "review_audit_log": self.review_audit_log,
            "review_summary": self.review_summary,
            "paper_review_report": self.paper_review_report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PaperReviewResult:
    review_id: str
    reviewed_decisions: pd.DataFrame
    review_audit_log: pd.DataFrame
    review_summary: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def load_paper_decisions(path: str | Path) -> pd.DataFrame:
    """Load a local paper decisions CSV."""

    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Paper decisions CSV not found: {csv_path}")
    return _prepare_decisions(pd.read_csv(csv_path))


def apply_paper_review_updates(
    decisions: pd.DataFrame | str | Path,
    updates: pd.DataFrame | list[PaperReviewUpdate] | str | Path,
    *,
    reviewer_id: str | None = None,
    review_time: str | pd.Timestamp | None = None,
    settings: Settings | PaperReviewSettings | dict[str, Any] | None = None,
) -> PaperReviewResult:
    """Apply manual review updates to paper decisions and write optional artifacts."""

    project_settings, review_settings = _resolve_settings(settings)
    if review_settings.enable_live_trading or review_settings.enable_broker_api:
        raise ValueError("Paper review cannot enable live trading or broker API access")

    decisions_frame = _prepare_decisions(_load_frame(decisions))
    updates_raw = _load_updates(updates)
    validate_review_updates(decisions_frame, updates_raw, settings=review_settings)
    updates_frame = _prepare_updates(updates_raw, reviewer_id=reviewer_id)
    normalized_review_time = _normalize_review_time(review_time)

    reviewed = decisions_frame.copy(deep=True)
    for column in REVIEWED_DECISION_EXTRA_COLUMNS:
        if column not in reviewed.columns:
            reviewed[column] = ""
    audit_log = build_review_audit_log(
        reviewed,
        updates_frame,
        reviewer_id=reviewer_id,
        review_time=normalized_review_time,
        settings=review_settings,
    )
    updates_by_id = {
        str(row["decision_id"]): row
        for row in updates_frame.to_dict("records")
        if _present(row.get("decision_id"))
    }
    for idx, row in reviewed.iterrows():
        decision_id = str(row.get("decision_id", "")).strip()
        update = updates_by_id.get(decision_id)
        if update is None:
            continue
        reviewed.at[idx, "manual_review_status"] = str(update["manual_review_status"]).upper().strip()
        reviewed.at[idx, "manual_review_notes"] = _string_or_empty(update.get("manual_review_notes"))
        reviewed.at[idx, "reviewer_id"] = _string_or_empty(update.get("reviewer_id"))
        reviewed.at[idx, "review_time"] = normalized_review_time
        reviewed.at[idx, "review_reason_code"] = _reason_code(update.get("review_reason_code"))

    reviewed = _finalize_reviewed_decisions(reviewed)
    summary = summarize_review_status(reviewed)
    review_id = generate_paper_review_id(
        decisions_frame,
        updates_frame,
        reviewer_id=reviewer_id,
        review_time=review_time,
        config_version=review_settings.config_version,
    )
    paths = resolve_paper_review_artifact_paths(review_settings.output_dir, review_id)
    warnings = _review_warnings(reviewed, updates_frame, review_settings)
    audit_metadata = {
        "review_id": review_id,
        "decision_rows": len(decisions_frame),
        "update_rows": len(updates_frame),
        "audit_rows": len(audit_log),
        "reviewer_id": reviewer_id or "",
        "review_time": normalized_review_time,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
    }
    result = PaperReviewResult(
        review_id=review_id,
        reviewed_decisions=reviewed,
        review_audit_log=audit_log,
        review_summary=summary,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=REVIEW_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if review_settings.write_artifacts:
        write_paper_review_artifacts(result)
    _ = project_settings
    return result


def validate_review_updates(
    decisions: pd.DataFrame,
    updates: pd.DataFrame,
    *,
    settings: PaperReviewSettings | dict[str, Any] | None = None,
) -> None:
    """Validate a manual review update frame, raising ValueError on failure."""

    cfg = _coerce_review_settings(settings)
    decision_frame = _prepare_decisions(decisions)
    updates_frame = _prepare_updates(updates)
    errors: list[str] = []
    missing_columns = [column for column in REQUIRED_UPDATE_COLUMNS if column not in updates.columns]
    if missing_columns:
        errors.append(f"Missing required review update columns: {', '.join(missing_columns)}")
    if updates_frame.empty:
        errors.append("Review updates are empty")
    if "decision_id" in updates_frame.columns:
        decision_ids = updates_frame["decision_id"].astype(str).str.strip()
        duplicated = decision_ids[decision_ids != ""].duplicated(keep=False)
        if duplicated.any():
            duplicates = sorted(decision_ids[duplicated].unique())
            errors.append(f"Duplicate review updates for decision_id: {', '.join(duplicates)}")
        known_ids = set(str(value).strip() for value in decision_frame["decision_id"].dropna())
        unknown = sorted(set(decision_ids[decision_ids != ""]) - known_ids)
        if unknown:
            errors.append(f"Unknown decision_id in review updates: {', '.join(unknown)}")
    if "manual_review_status" in updates_frame.columns:
        statuses = updates_frame["manual_review_status"].astype(str).str.upper().str.strip()
        invalid = sorted(set(statuses) - REVIEW_STATUSES)
        if invalid:
            errors.append(f"Invalid manual_review_status: {', '.join(invalid)}")
        if not cfg.allow_pending_reviews and "PENDING_REVIEW" in set(statuses):
            errors.append("PENDING_REVIEW updates are not allowed by settings")
    if "review_reason_code" in updates_frame.columns:
        reasons = updates_frame["review_reason_code"].map(_reason_code)
        invalid_reasons = sorted(set(reasons) - REVIEW_REASON_CODES)
        if invalid_reasons:
            errors.append(f"Invalid review_reason_code: {', '.join(invalid_reasons)}")
    if errors:
        raise ValueError("; ".join(errors))


def build_review_audit_log(
    decisions: pd.DataFrame,
    updates: pd.DataFrame,
    *,
    reviewer_id: str | None = None,
    review_time: str | pd.Timestamp | None = None,
    settings: PaperReviewSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Build an audit log for review status and note changes."""

    cfg = _coerce_review_settings(settings)
    decision_frame = _prepare_decisions(decisions)
    updates_frame = _prepare_updates(updates, reviewer_id=reviewer_id)
    validate_review_updates(decision_frame, updates_frame, settings=cfg)
    normalized_review_time = _normalize_review_time(review_time)
    decision_by_id = {
        str(row["decision_id"]): row
        for row in decision_frame.to_dict("records")
        if _present(row.get("decision_id"))
    }
    rows = []
    for update in updates_frame.to_dict("records"):
        decision_id = str(update["decision_id"]).strip()
        decision = decision_by_id[decision_id]
        new_status = str(update["manual_review_status"]).upper().strip()
        reviewer = _string_or_empty(update.get("reviewer_id")) or _string_or_empty(reviewer_id)
        reason = _reason_code(update.get("review_reason_code"))
        payload = {
            "decision_id": decision_id,
            "old_status": _string_or_empty(decision.get("manual_review_status")),
            "new_status": new_status,
            "new_notes": _string_or_empty(update.get("manual_review_notes")),
            "reviewer_id": reviewer,
            "review_reason_code": reason,
            "review_time": normalized_review_time,
            "config_version": cfg.config_version,
        }
        rows.append(
            {
                "audit_id": _hash_payload(payload, length=12),
                "decision_id": decision_id,
                "old_status": _string_or_empty(decision.get("manual_review_status")),
                "new_status": new_status,
                "old_notes": _string_or_empty(decision.get("manual_review_notes")),
                "new_notes": _string_or_empty(update.get("manual_review_notes")),
                "reviewer_id": reviewer,
                "review_reason_code": reason,
                "review_time": normalized_review_time,
            }
        )
    return _finalize_audit_log(pd.DataFrame(rows))


def summarize_review_status(decisions: pd.DataFrame) -> pd.DataFrame:
    """Summarize reviewed decision statuses."""

    frame = _prepare_decisions(decisions)
    total = len(frame)
    statuses = frame["manual_review_status"].astype(str).str.upper().str.strip() if total else pd.Series(dtype="object")
    approved = int((statuses == "APPROVED_FOR_PAPER").sum())
    rejected = int((statuses == "REJECTED").sum())
    watch_only = int((statuses == "WATCH_ONLY").sum())
    pending = int((statuses == "PENDING_REVIEW").sum())
    denominator = float(total) if total else 0.0
    return pd.DataFrame(
        [
            {
                "total_decisions": total,
                "approved_count": approved,
                "rejected_count": rejected,
                "watch_only_count": watch_only,
                "pending_count": pending,
                "approval_rate": approved / denominator if denominator else 0.0,
                "rejected_rate": rejected / denominator if denominator else 0.0,
                "watch_only_rate": watch_only / denominator if denominator else 0.0,
            }
        ]
    )


def generate_paper_review_id(
    decisions: pd.DataFrame,
    updates: pd.DataFrame,
    *,
    reviewer_id: str | None = None,
    review_time: str | pd.Timestamp | None = None,
    config_version: str = "mvp",
) -> str:
    """Generate a deterministic review id."""

    decision_frame = _prepare_decisions(decisions)
    updates_frame = _prepare_updates(updates, reviewer_id=reviewer_id)
    payload = {
        "decision_ids": sorted(str(value) for value in decision_frame["decision_id"].dropna().unique()),
        "updates": _stable_records(updates_frame),
        "reviewer_id": reviewer_id or "",
        "review_time": _normalize_review_time(review_time) if review_time is not None else "",
        "config_version": config_version,
    }
    return _hash_payload(payload, length=10)


def resolve_paper_review_artifact_paths(output_dir: str | Path, review_id: str) -> PaperReviewArtifactPaths:
    """Resolve artifact paths for a paper review run."""

    artifact_dir = Path(output_dir) / review_id
    return PaperReviewArtifactPaths(
        artifact_dir=artifact_dir,
        reviewed_decisions=artifact_dir / "reviewed_decisions.csv",
        review_audit_log=artifact_dir / "review_audit_log.csv",
        review_summary=artifact_dir / "review_summary.csv",
        paper_review_report=artifact_dir / "paper_review_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def write_paper_review_artifacts(result: PaperReviewResult) -> dict[str, Path]:
    """Write reviewed decisions, audit log, summary, report, and metadata."""

    paths = PaperReviewArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.reviewed_decisions, paths.reviewed_decisions)
    _export_dataframe(result.review_audit_log, paths.review_audit_log)
    _export_dataframe(result.review_summary, paths.review_summary)
    metadata = build_paper_review_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.paper_review_report.write_text(render_paper_review_report(result, paths, metadata), encoding="utf-8")
    return paths.as_dict()


def build_paper_review_metadata(result: PaperReviewResult, paths: PaperReviewArtifactPaths) -> dict[str, Any]:
    """Build metadata for a paper review run."""

    return {
        "review_id": result.review_id,
        "created_at": _metadata_created_at(result.audit_metadata.get("review_time")),
        "row_counts": {
            "reviewed_decisions": len(result.reviewed_decisions),
            "review_audit_log": len(result.review_audit_log),
            "review_summary": len(result.review_summary),
        },
        "review_summary": result.review_summary.to_dict("records")[0] if not result.review_summary.empty else {},
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "paper_trading_only": True,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_paper_review_report(
    result: PaperReviewResult,
    paths: PaperReviewArtifactPaths,
    metadata: dict[str, Any],
) -> str:
    """Render the markdown paper review report."""

    lines = [
        f"# Paper Trading Review Report: {result.review_id}",
        "",
        "No broker or live trading integration was invoked. This is a local manual paper-review report only.",
        "",
        "## Review Metadata",
        "",
        _dict_table(
            {
                "review_id": result.review_id,
                "artifact_dir": paths.artifact_dir,
                "reviewed_decisions": len(result.reviewed_decisions),
                "audit_rows": len(result.review_audit_log),
            }
        ),
        "",
        "## Approval / Rejection Summary",
        "",
        _markdown_table(
            result.review_summary,
            [
                "total_decisions",
                "approved_count",
                "rejected_count",
                "watch_only_count",
                "pending_count",
                "approval_rate",
                "rejected_rate",
                "watch_only_rate",
            ],
        ),
        "",
        "## Review Audit Log",
        "",
        _markdown_table(
            result.review_audit_log,
            [
                "audit_id",
                "decision_id",
                "old_status",
                "new_status",
                "reviewer_id",
                "review_reason_code",
                "review_time",
            ],
        ),
        "",
        "## Reviewed Decisions",
        "",
        _markdown_table(
            result.reviewed_decisions,
            [
                "decision_id",
                "symbol",
                "name",
                "candidate_rank",
                "final_score",
                "manual_review_status",
                "manual_review_notes",
                "reviewer_id",
                "review_reason_code",
            ],
        ),
        "",
        "## Warnings",
        "",
        _warnings_section(result.warnings),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in metadata["known_limitations"]),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def _resolve_settings(settings: Settings | PaperReviewSettings | dict[str, Any] | None) -> tuple[Settings, PaperReviewSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.paper_review
    if isinstance(settings, Settings):
        return settings, settings.paper_review
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, PaperReviewSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.paper_review.model_dump())
        for key, value in settings.items():
            if key == "paper_review" and isinstance(value, dict):
                payload.update(value)
            elif key in payload:
                payload[key] = value
        return project, PaperReviewSettings(**payload)
    raise TypeError("settings must be Settings, PaperReviewSettings, dict, or None")


def _coerce_review_settings(settings: PaperReviewSettings | dict[str, Any] | None) -> PaperReviewSettings:
    if settings is None:
        return PaperReviewSettings()
    if isinstance(settings, PaperReviewSettings):
        return settings
    if isinstance(settings, dict):
        return PaperReviewSettings(**settings)
    if hasattr(settings, "model_dump"):
        return PaperReviewSettings(**settings.model_dump())
    raise TypeError("settings must be PaperReviewSettings, dict, or None")


def _load_frame(value: pd.DataFrame | str | Path) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value.copy(deep=True)
    path = Path(value)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    return pd.read_csv(path)


def _load_updates(value: pd.DataFrame | list[PaperReviewUpdate] | str | Path) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value.copy(deep=True)
    if isinstance(value, list):
        return pd.DataFrame([update.__dict__ if isinstance(update, PaperReviewUpdate) else update for update in value])
    path = Path(value)
    if not path.exists():
        raise FileNotFoundError(f"Review updates CSV not found: {path}")
    return pd.read_csv(path)


def _prepare_decisions(decisions: pd.DataFrame) -> pd.DataFrame:
    frame = decisions.copy(deep=True)
    for column in ["decision_date", "planned_buy_date", "planned_sell_date", "review_time"]:
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce")
            if column != "review_time":
                frame[column] = frame[column].dt.normalize()
    for column in ["decision_id", "manual_review_status", "manual_review_notes"]:
        if column not in frame.columns:
            frame[column] = ""
        frame[column] = frame[column].map(_string_or_empty)
    for column in ["reviewer_id", "review_reason_code"]:
        if column in frame.columns:
            frame[column] = frame[column].map(_string_or_empty)
    if frame.empty:
        return frame
    return frame.reset_index(drop=True)


def _prepare_updates(updates: pd.DataFrame, *, reviewer_id: str | None = None) -> pd.DataFrame:
    frame = updates.copy(deep=True)
    for column in REQUIRED_UPDATE_COLUMNS + OPTIONAL_UPDATE_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    if frame.empty:
        return frame[REQUIRED_UPDATE_COLUMNS + OPTIONAL_UPDATE_COLUMNS]
    frame["decision_id"] = frame["decision_id"].map(_string_or_empty)
    frame["manual_review_status"] = frame["manual_review_status"].astype(str).str.upper().str.strip()
    frame["manual_review_notes"] = frame["manual_review_notes"].map(_string_or_empty)
    frame["reviewer_id"] = frame["reviewer_id"].map(_string_or_empty)
    if reviewer_id:
        frame.loc[frame["reviewer_id"] == "", "reviewer_id"] = reviewer_id
    frame["review_reason_code"] = frame["review_reason_code"].map(_reason_code)
    return frame[REQUIRED_UPDATE_COLUMNS + OPTIONAL_UPDATE_COLUMNS].reset_index(drop=True)


def _finalize_reviewed_decisions(frame: pd.DataFrame) -> pd.DataFrame:
    reviewed = frame.copy(deep=True)
    for column in REVIEWED_DECISION_EXTRA_COLUMNS:
        if column not in reviewed.columns:
            reviewed[column] = ""
    if "decision_id" not in reviewed.columns:
        reviewed["decision_id"] = ""
    if "candidate_rank" not in reviewed.columns:
        reviewed["candidate_rank"] = pd.NA
    if "symbol" not in reviewed.columns:
        reviewed["symbol"] = ""
    sort_columns = [column for column in ["decision_date", "candidate_rank", "symbol"] if column in reviewed.columns]
    return reviewed.sort_values(sort_columns, na_position="last").reset_index(drop=True) if sort_columns else reviewed.reset_index(drop=True)


def _finalize_audit_log(frame: pd.DataFrame) -> pd.DataFrame:
    audit = frame.copy(deep=True)
    for column in AUDIT_COLUMNS:
        if column not in audit.columns:
            audit[column] = pd.NA
    if audit.empty:
        return audit[AUDIT_COLUMNS]
    return audit[AUDIT_COLUMNS].sort_values(["review_time", "decision_id"], na_position="last").reset_index(drop=True)


def _review_warnings(decisions: pd.DataFrame, updates: pd.DataFrame, settings: PaperReviewSettings) -> list[str]:
    warnings = []
    pending = int((decisions["manual_review_status"].astype(str).str.upper() == "PENDING_REVIEW").sum()) if not decisions.empty else 0
    if pending:
        warnings.append(f"{pending} decision(s) remain pending review.")
    if updates.empty:
        warnings.append("No review updates were applied.")
    if settings.enable_live_trading or settings.enable_broker_api:
        warnings.append("Invalid live/broker setting detected.")
    return warnings


def _normalize_review_time(value: str | pd.Timestamp | None) -> str:
    if value is None:
        return "1970-01-01T00:00:00+00:00"
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize(timezone.utc)
    return timestamp.isoformat()


def _metadata_created_at(review_time: Any) -> str:
    if _present(review_time):
        return str(review_time)
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _reason_code(value: Any) -> str:
    text = _string_or_empty(value).upper().strip()
    return text if text else "OTHER"


def _string_or_empty(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _present(value: Any) -> bool:
    return _string_or_empty(value) != ""


def _stable_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    export = frame.copy(deep=True).sort_values([column for column in ["decision_id", "manual_review_status"] if column in frame.columns])
    return [_json_safe(record) for record in export.to_dict("records")]


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    export = _sanitize_dataframe_for_export(frame)
    path.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(path, index=False)


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
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if np.isnan(value):
            return None
        return float(value)
    if isinstance(value, float) and np.isnan(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
