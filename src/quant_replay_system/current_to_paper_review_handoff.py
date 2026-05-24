"""Local-only handoff from paper decisions to manual review update templates."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_replay_system.config import CurrentToPaperReviewHandoffSettings, Settings, load_settings
from quant_replay_system.data import read_csv_preserve_symbol_columns


CURRENT_TO_PAPER_REVIEW_HANDOFF_LIMITATIONS = [
    "Uses local CSV/mock data only.",
    "Creates manual review update templates only; it does not approve trades automatically.",
    "Does not place live orders or call broker APIs.",
    "Suggested statuses are advisory and are kept separate from manual_review_status.",
    "The user must manually review and edit review_updates_template.csv before applying it.",
]

REVIEW_TEMPLATE_COLUMNS = [
    "decision_id",
    "symbol",
    "name",
    "candidate_rank",
    "final_score",
    "action",
    "risk_precheck_status",
    "risk_precheck_reason",
    "suggested_manual_review_status",
    "manual_review_status",
    "manual_review_notes",
    "reviewer_id",
    "review_reason_code",
]


@dataclass(frozen=True)
class CurrentToPaperReviewHandoffArtifactPaths:
    artifact_dir: Path
    review_updates_template: Path
    review_handoff_report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "review_updates_template": self.review_updates_template,
            "review_handoff_report": self.review_handoff_report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CurrentToPaperReviewHandoffResult:
    review_handoff_id: str
    decision_count: int
    template_path: Path
    report_path: Path
    metadata_path: Path
    warnings: list[str]
    known_limitations: list[str]
    decisions: pd.DataFrame
    review_updates_template: pd.DataFrame
    artifact_paths: dict[str, Path]
    audit_metadata: dict[str, Any]


def run_current_to_paper_review_handoff(
    *,
    decisions_path: str | Path | None = None,
    decisions: pd.DataFrame | Any | None = None,
    handoff_artifact_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    reviewer_id: str | None = None,
    config: Settings | str | Path | None = None,
) -> CurrentToPaperReviewHandoffResult:
    """Create a manual review update template from paper decisions."""

    settings = _load_project_settings(config)
    review_handoff_settings = settings.current_to_paper_review_handoff
    if review_handoff_settings.enable_live_trading or review_handoff_settings.enable_broker_api:
        raise ValueError("Current-to-paper review handoff cannot enable live trading or broker API access")
    if output_dir is not None:
        settings = settings.model_copy(
            update={
                "current_to_paper_review_handoff": review_handoff_settings.model_copy(
                    update={"output_dir": Path(output_dir)}
                )
            }
        )
        review_handoff_settings = settings.current_to_paper_review_handoff

    decisions_frame, source_metadata, load_warnings = load_paper_decisions_for_review_handoff(
        decisions_path=decisions_path,
        decisions=decisions,
        handoff_artifact_dir=handoff_artifact_dir,
    )
    effective_reviewer = reviewer_id if reviewer_id is not None else review_handoff_settings.default_reviewer_id
    template = build_review_updates_template(
        decisions_frame,
        reviewer_id=effective_reviewer,
        settings=review_handoff_settings,
    )
    review_handoff_id = generate_current_to_paper_review_handoff_id(
        decisions_frame,
        source_id=_source_identity(source_metadata, decisions_path, handoff_artifact_dir),
        config_version=review_handoff_settings.config_version,
    )
    paths = resolve_current_to_paper_review_handoff_paths(
        review_handoff_settings.output_dir,
        review_handoff_id,
    )
    warnings = list(load_warnings)
    if decisions_frame.empty:
        warnings.append("No decisions were found for review handoff.")
    audit_metadata = {
        "review_handoff_id": review_handoff_id,
        "decision_count": len(decisions_frame),
        "source_metadata": source_metadata,
        "reviewer_id": effective_reviewer,
        "manual_review_status_default": review_handoff_settings.default_manual_review_status,
        "suggestions_only": True,
        "config_version": review_handoff_settings.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "current_to_paper_review_handoff_only": True,
    }
    result = CurrentToPaperReviewHandoffResult(
        review_handoff_id=review_handoff_id,
        decision_count=len(decisions_frame),
        template_path=paths.review_updates_template,
        report_path=paths.review_handoff_report,
        metadata_path=paths.metadata,
        warnings=warnings,
        known_limitations=CURRENT_TO_PAPER_REVIEW_HANDOFF_LIMITATIONS,
        decisions=decisions_frame,
        review_updates_template=template,
        artifact_paths=paths.as_dict(),
        audit_metadata=audit_metadata,
    )
    if review_handoff_settings.write_artifacts:
        write_current_to_paper_review_handoff_artifacts(result)
    return result


def load_paper_decisions_for_review_handoff(
    *,
    decisions_path: str | Path | None = None,
    decisions: pd.DataFrame | Any | None = None,
    handoff_artifact_dir: str | Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any], list[str]]:
    """Load paper decisions from a DataFrame, decisions CSV, handoff dir, or daily paper artifact dir."""

    supplied = sum(value is not None for value in [decisions_path, decisions, handoff_artifact_dir])
    if supplied != 1:
        raise ValueError("Provide exactly one of decisions, decisions_path, or handoff_artifact_dir")
    if isinstance(decisions, pd.DataFrame):
        return _prepare_decisions(decisions), {"source_type": "DECISIONS_DATAFRAME"}, []
    if decisions is not None:
        for attr in ["decisions", "decision_log", "paper_decisions"]:
            if hasattr(decisions, attr):
                value = getattr(decisions, attr)
                if isinstance(value, pd.DataFrame):
                    return _prepare_decisions(value), {"source_type": "DECISIONS_OBJECT"}, []
        raise TypeError("decisions must be a DataFrame or object with decisions/decision_log")
    if decisions_path is not None:
        path = Path(decisions_path)
        if not path.exists():
            raise FileNotFoundError(f"Paper decisions CSV not found: {path}")
        return _prepare_decisions(read_csv_preserve_symbol_columns(path)), {
            "source_type": "DECISIONS_CSV",
            "decisions_path": str(path),
        }, []

    artifact_dir = Path(handoff_artifact_dir) if handoff_artifact_dir is not None else Path()
    decisions_csv, source_metadata, warnings = _resolve_decisions_from_artifact_dir(artifact_dir)
    if not decisions_csv.exists():
        raise FileNotFoundError(f"Paper decisions CSV not found from artifact directory: {decisions_csv}")
    return _prepare_decisions(read_csv_preserve_symbol_columns(decisions_csv)), source_metadata, warnings


def build_review_updates_template(
    decisions: pd.DataFrame,
    *,
    reviewer_id: str | None = None,
    settings: CurrentToPaperReviewHandoffSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Build a review updates CSV template without auto-approving actual statuses."""

    cfg = _coerce_review_handoff_settings(settings)
    frame = _prepare_decisions(decisions)
    rows: list[dict[str, Any]] = []
    for row in frame.to_dict("records"):
        suggested_status = suggest_manual_review_status(row, settings=cfg) if cfg.include_suggested_status else ""
        rows.append(
            {
                "decision_id": _string_or_empty(row.get("decision_id")),
                "symbol": _string_or_empty(row.get("symbol")),
                "name": _string_or_empty(row.get("name")),
                "candidate_rank": row.get("candidate_rank", ""),
                "final_score": row.get("final_score", ""),
                "action": _string_or_empty(row.get("action")),
                "risk_precheck_status": _string_or_empty(row.get("risk_precheck_status")),
                "risk_precheck_reason": _string_or_empty(row.get("risk_precheck_reason")),
                "suggested_manual_review_status": suggested_status,
                "manual_review_status": cfg.default_manual_review_status,
                "manual_review_notes": "",
                "reviewer_id": reviewer_id if reviewer_id is not None else cfg.default_reviewer_id,
                "review_reason_code": suggest_review_reason_code(row, suggested_status=suggested_status),
            }
        )
    return _finalize_template(pd.DataFrame(rows))


def suggest_manual_review_status(
    decision_row: dict[str, Any],
    *,
    settings: CurrentToPaperReviewHandoffSettings | dict[str, Any] | None = None,
) -> str:
    """Suggest a review status while leaving actual manual_review_status unchanged."""

    cfg = _coerce_review_handoff_settings(settings)
    risk_status = _string_or_empty(decision_row.get("risk_precheck_status")).upper()
    action = _string_or_empty(decision_row.get("action")).upper()
    score = _float_or_none(decision_row.get("final_score"))
    if risk_status == "BLOCK":
        return "REJECTED"
    if cfg.auto_reject_below_score is not None and score is not None and score < cfg.auto_reject_below_score:
        return "REJECTED"
    if cfg.auto_approve_above_score is not None and score is not None and score >= cfg.auto_approve_above_score:
        return "APPROVED_FOR_PAPER"
    if action in {"OBSERVE", "WATCH"}:
        return "WATCH_ONLY"
    return "PENDING_REVIEW"


def suggest_review_reason_code(decision_row: dict[str, Any], *, suggested_status: str | None = None) -> str:
    """Suggest a paper-review reason code from score, action, and risk fields."""

    risk_status = _string_or_empty(decision_row.get("risk_precheck_status")).upper()
    risk_reason = _string_or_empty(decision_row.get("risk_precheck_reason")).upper()
    action = _string_or_empty(decision_row.get("action")).upper()
    suggested = _string_or_empty(suggested_status).upper()
    if risk_status == "BLOCK" or "RISK" in risk_reason:
        return "RISK_TOO_HIGH"
    if "LIQUID" in risk_reason:
        return "LIQUIDITY_TOO_LOW"
    if suggested == "APPROVED_FOR_PAPER":
        return "SCORE_CONFIRMED"
    if suggested == "WATCH_ONLY" or action in {"OBSERVE", "WATCH"}:
        return "WATCHLIST_ONLY"
    if suggested == "REJECTED":
        return "RISK_TOO_HIGH"
    return "OTHER"


def generate_current_to_paper_review_handoff_id(
    decisions: pd.DataFrame,
    *,
    source_id: str = "",
    config_version: str = "mvp",
) -> str:
    """Generate a deterministic review handoff id."""

    frame = _prepare_decisions(decisions)
    payload = {
        "decision_ids": sorted(str(value) for value in frame.get("decision_id", pd.Series(dtype="object")).dropna()),
        "source_id": source_id,
        "config_version": config_version,
    }
    return _hash_payload(payload, length=12)


def resolve_current_to_paper_review_handoff_paths(
    output_dir: str | Path,
    review_handoff_id: str,
) -> CurrentToPaperReviewHandoffArtifactPaths:
    """Resolve stable current-to-paper review handoff artifact paths."""

    artifact_dir = Path(output_dir) / review_handoff_id
    return CurrentToPaperReviewHandoffArtifactPaths(
        artifact_dir=artifact_dir,
        review_updates_template=artifact_dir / "review_updates_template.csv",
        review_handoff_report=artifact_dir / "review_handoff_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def write_current_to_paper_review_handoff_artifacts(
    result: CurrentToPaperReviewHandoffResult,
) -> dict[str, Path]:
    """Write review handoff template, report, and metadata."""

    paths = CurrentToPaperReviewHandoffArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.review_updates_template, paths.review_updates_template)
    metadata = build_current_to_paper_review_handoff_metadata(result)
    metadata["output_files"] = {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"}
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.review_handoff_report.write_text(
        render_current_to_paper_review_handoff_report(result, metadata),
        encoding="utf-8",
    )
    return paths.as_dict()


def build_current_to_paper_review_handoff_metadata(
    result: CurrentToPaperReviewHandoffResult,
) -> dict[str, Any]:
    """Build metadata for review handoff artifacts."""

    return {
        "review_handoff_id": result.review_handoff_id,
        "decision_count": result.decision_count,
        "template_path": result.template_path,
        "report_path": result.report_path,
        "metadata_path": result.metadata_path,
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_current_to_paper_review_handoff_report(
    result: CurrentToPaperReviewHandoffResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render a markdown review handoff report."""

    _ = metadata
    lines = [
        f"# Current Candidate To Paper Review Handoff: {result.review_handoff_id}",
        "",
        "No broker or live trading integration was invoked. This report creates a manual review update template only.",
        "",
        "## Review Handoff Metadata",
        "",
        _dict_table(
            {
                "review_handoff_id": result.review_handoff_id,
                "decision_count": result.decision_count,
                "template_path": result.template_path,
                "report_path": result.report_path,
                "suggestions_only": True,
            }
        ),
        "",
        "## Template Preview",
        "",
        _markdown_table(
            result.review_updates_template,
            [
                "decision_id",
                "symbol",
                "candidate_rank",
                "final_score",
                "suggested_manual_review_status",
                "manual_review_status",
                "review_reason_code",
            ],
            max_rows=50,
        ),
        "",
        "## How To Apply After Manual Editing",
        "",
        f"`python -m quant_replay_system.cli paper-review-decisions --decisions <decisions.csv> --updates {result.template_path}`",
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


def _resolve_decisions_from_artifact_dir(artifact_dir: Path) -> tuple[Path, dict[str, Any], list[str]]:
    if not artifact_dir.exists():
        raise FileNotFoundError(f"Artifact directory not found: {artifact_dir}")
    warnings: list[str] = []
    direct_decisions = artifact_dir / "decisions.csv"
    if direct_decisions.exists():
        return direct_decisions, {"source_type": "DAILY_PAPER_ARTIFACT_DIR", "artifact_dir": str(artifact_dir)}, warnings

    metadata_path = artifact_dir / "handoff_metadata.json"
    if metadata_path.exists():
        metadata = _load_json(metadata_path)
        paper_paths = metadata.get("paper_artifact_paths") if isinstance(metadata.get("paper_artifact_paths"), dict) else {}
        decisions_path = _path_or_none(paper_paths.get("decisions"))
        if decisions_path is not None:
            return decisions_path, {
                "source_type": "CURRENT_TO_PAPER_HANDOFF_DIR",
                "artifact_dir": str(artifact_dir),
                "handoff_id": metadata.get("handoff_id", ""),
                "handoff_metadata_path": str(metadata_path),
            }, warnings
        warnings.append(f"handoff_metadata.json did not include paper_artifact_paths.decisions: {metadata_path}")

    paper_daily_artifacts = artifact_dir / "paper_daily_artifacts.json"
    if paper_daily_artifacts.exists():
        paths = _load_json(paper_daily_artifacts)
        decisions_path = _path_or_none(paths.get("decisions"))
        if decisions_path is not None:
            return decisions_path, {
                "source_type": "CURRENT_TO_PAPER_HANDOFF_DIR",
                "artifact_dir": str(artifact_dir),
                "paper_daily_artifacts_path": str(paper_daily_artifacts),
            }, warnings
    raise FileNotFoundError(f"Could not resolve decisions.csv from artifact directory: {artifact_dir}")


def _source_identity(
    source_metadata: dict[str, Any],
    decisions_path: str | Path | None,
    handoff_artifact_dir: str | Path | None,
) -> str:
    if source_metadata.get("handoff_id"):
        return str(source_metadata["handoff_id"])
    if decisions_path is not None:
        return str(decisions_path)
    if handoff_artifact_dir is not None:
        return str(handoff_artifact_dir)
    return str(source_metadata.get("source_type", ""))


def _prepare_decisions(decisions: pd.DataFrame) -> pd.DataFrame:
    frame = decisions.copy(deep=True)
    for column in ["decision_date", "planned_buy_date", "planned_sell_date"]:
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce").dt.normalize()
    for column in ["decision_id", "symbol", "manual_review_status"]:
        if column not in frame.columns:
            frame[column] = ""
    if "candidate_rank" not in frame.columns:
        frame["candidate_rank"] = pd.NA
    sort_columns = [column for column in ["decision_date", "candidate_rank", "symbol"] if column in frame.columns]
    if sort_columns and not frame.empty:
        frame = frame.sort_values(sort_columns, na_position="last")
    return frame.reset_index(drop=True)


def _finalize_template(frame: pd.DataFrame) -> pd.DataFrame:
    template = frame.copy(deep=True)
    for column in REVIEW_TEMPLATE_COLUMNS:
        if column not in template.columns:
            template[column] = ""
    if template.empty:
        return template[REVIEW_TEMPLATE_COLUMNS]
    return template[REVIEW_TEMPLATE_COLUMNS].sort_values(
        ["candidate_rank", "symbol"],
        na_position="last",
    ).reset_index(drop=True)


def _coerce_review_handoff_settings(
    settings: CurrentToPaperReviewHandoffSettings | dict[str, Any] | None,
) -> CurrentToPaperReviewHandoffSettings:
    if settings is None:
        return CurrentToPaperReviewHandoffSettings()
    if isinstance(settings, CurrentToPaperReviewHandoffSettings):
        return settings
    if isinstance(settings, dict):
        return CurrentToPaperReviewHandoffSettings(**settings)
    if hasattr(settings, "model_dump"):
        return CurrentToPaperReviewHandoffSettings(**settings.model_dump())
    raise TypeError("settings must be CurrentToPaperReviewHandoffSettings, dict, or None")


def _load_project_settings(config: Settings | str | Path | None) -> Settings:
    if config is None:
        return load_settings(Path("config/default.yaml"))
    if isinstance(config, Settings):
        return config
    return load_settings(Path(config))


def _path_or_none(value: Any) -> Path | None:
    if not _present(value):
        return None
    return Path(str(value))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _float_or_none(value: Any) -> float | None:
    if not _present(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


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
