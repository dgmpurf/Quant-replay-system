"""Local-only health checks for market-cache-export policy recommendation plans."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketCacheExportPolicyHealthSettings, Settings, load_settings
from quant_replay_system.data import read_csv_preserve_symbol_columns
from quant_replay_system.market_cache_export import MARKET_CACHE_EXPORT_REQUIRED_COLUMNS
from quant_replay_system.market_cache_export_policy_index import (
    INDEX_COLUMNS,
    NO_LIVE_STATEMENTS,
    build_market_cache_export_policy_index,
)


MARKET_CACHE_EXPORT_POLICY_HEALTH_LIMITATIONS = [
    "Checks local policy recommendation artifacts referenced by the index only.",
    "Does not regenerate plans, run exports, mutate the market cache, or call external APIs.",
    "PROVISIONAL recommendations are reviewable warnings, not hidden or converted to PASS.",
]

HEALTH_COLUMNS = [
    "plan_id",
    "path_field",
    "path_value",
    "severity",
    "issue_code",
    "issue_message",
    "suggested_action",
]


@dataclass(frozen=True)
class MarketCacheExportPolicyHealthArtifactPaths:
    artifact_dir: Path
    market_cache_export_policy_health_report: Path
    market_cache_export_policy_health_issues: Path
    market_cache_export_policy_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_cache_export_policy_health_report": self.market_cache_export_policy_health_report,
            "market_cache_export_policy_health_issues": self.market_cache_export_policy_health_issues,
            "market_cache_export_policy_health_summary": self.market_cache_export_policy_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MarketCacheExportPolicyHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    health_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    health_check_id: str
    audit_metadata: dict[str, Any]


def check_market_cache_export_policy_health(
    *,
    index_df: pd.DataFrame | None = None,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    output_dir: str | Path | None = None,
    settings: Settings | MarketCacheExportPolicyHealthSettings | dict[str, Any] | None = None,
) -> MarketCacheExportPolicyHealthResult:
    project_settings, health_settings = _resolve_settings(settings)
    if health_settings.enable_live_trading or health_settings.enable_broker_api:
        raise ValueError("Market cache export policy health cannot enable live trading or broker API access")

    index_frame, index_source, load_warnings, load_issues = _load_index(
        index_df=index_df,
        index_path=index_path,
        root=root,
        settings=health_settings,
        project_settings=project_settings,
    )
    health_frame = build_market_cache_export_policy_health_frame(index_frame, settings=health_settings)
    if load_issues:
        health_frame = _finalize_health_frame(pd.concat([pd.DataFrame(load_issues), health_frame], ignore_index=True))
    summary_frame = summarize_market_cache_export_policy_health(
        health_frame,
        checked_artifact_count=len(index_frame),
        index_df=index_frame,
    )
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    health_check_id = generate_market_cache_export_policy_health_id(
        index_frame,
        index_source=index_source,
        settings=health_settings,
    )
    paths = resolve_market_cache_export_policy_health_paths(
        Path(output_dir) if output_dir is not None else health_settings.output_dir,
        health_check_id,
    )
    audit_metadata = {
        "health_check_id": health_check_id,
        "index_source": index_source,
        "checked_artifact_count": len(index_frame),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "market_cache_export_policy_health_only": True,
        "config_version": health_settings.config_version,
    }
    result = MarketCacheExportPolicyHealthResult(
        status=status,
        checked_artifact_count=len(index_frame),
        issue_count=int(summary_frame.iloc[0]["issue_count"]) if not summary_frame.empty else 0,
        error_count=int(summary_frame.iloc[0]["error_count"]) if not summary_frame.empty else 0,
        warning_count=int(summary_frame.iloc[0]["warning_count"]) if not summary_frame.empty else 0,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=load_warnings,
        known_limitations=MARKET_CACHE_EXPORT_POLICY_HEALTH_LIMITATIONS,
        health_check_id=health_check_id,
        audit_metadata=audit_metadata,
    )
    if health_settings.write_artifacts:
        write_market_cache_export_policy_health_artifacts(result)
    return result


def build_market_cache_export_policy_health_frame(
    index_df: pd.DataFrame,
    *,
    settings: MarketCacheExportPolicyHealthSettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    cfg = _coerce_settings(settings)
    issues: list[dict[str, Any]] = []
    index_frame = _prepare_index_frame(index_df)
    for row in index_frame.to_dict("records"):
        plan_id = _string(row.get("plan_id"))
        metadata = _check_json_path(row, "metadata_path", issues, required=True, issue_code="MISSING_METADATA")
        report_path = _check_file_path(row, "report_path", issues, required=True, issue_code="MISSING_REPORT")
        _check_no_live_statement(row, "report_path", report_path, issues, cfg)
        recommendations = _check_csv_path(row, "recommendations_path", issues, required=True, issue_code="MISSING_RECOMMENDATIONS")
        _check_csv_path(row, "issues_path", issues, required=False, issue_code="UNREADABLE_RECOMMENDATIONS")
        manifest = _check_generated_manifest(row, issues)
        if recommendations is not None:
            _check_recommendation_counts(row, metadata, recommendations, issues)
            _check_recommendation_warnings(row, recommendations, issues)
            _check_comparison_diagnostics(row, recommendations, issues, cfg)
        if manifest is not None:
            _check_manifest_schema(row, manifest, issues)
            _check_manifest_symbols(row, manifest, issues)
            _check_manifest_source_upstream(row, manifest, issues)
        if _string(row.get("downstream_export_id")):
            _check_file_path(row, "downstream_export_report_path", issues, required=True, issue_code="MISSING_LINKED_EXPORT")
        if _string(row.get("downstream_snapshot_quality_status")):
            _check_file_path(
                row,
                "downstream_snapshot_quality_report_path",
                issues,
                required=True,
                issue_code="MISSING_LINKED_SNAPSHOT",
            )
        _check_metadata_safety(row, metadata, issues)
        if not plan_id:
            issues.append(
                _issue(
                    "",
                    "plan_id",
                    "",
                    "ERROR",
                    "STALE_OR_PARTIAL_ARTIFACT",
                    "Indexed policy plan row is missing a plan_id.",
                    "Regenerate the policy plan artifact or index.",
                )
            )
    return _finalize_health_frame(pd.DataFrame(issues))


def summarize_market_cache_export_policy_health(
    health_frame: pd.DataFrame,
    *,
    checked_artifact_count: int,
    index_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    frame = _finalize_health_frame(health_frame)
    comparison = _comparison_totals(index_df)
    error_count = int((frame["severity"] == "ERROR").sum()) if not frame.empty else 0
    warning_count = int((frame["severity"] == "WARN").sum()) if not frame.empty else 0
    status = "FAIL" if error_count else ("WARN" if warning_count else "PASS")
    return pd.DataFrame(
        [
            {
                "status": status,
                "checked_artifact_count": checked_artifact_count,
                "issue_count": int(len(frame)),
                "error_count": error_count,
                "warning_count": warning_count,
                **comparison,
                "no_live_trading": True,
                "no_broker_api": True,
            }
        ]
    )


def resolve_market_cache_export_policy_health_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> MarketCacheExportPolicyHealthArtifactPaths:
    artifact_dir = Path(output_dir) / health_check_id
    return MarketCacheExportPolicyHealthArtifactPaths(
        artifact_dir=artifact_dir,
        market_cache_export_policy_health_report=artifact_dir / "market_cache_export_policy_health_report.md",
        market_cache_export_policy_health_issues=artifact_dir / "market_cache_export_policy_health_issues.csv",
        market_cache_export_policy_health_summary=artifact_dir / "market_cache_export_policy_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_market_cache_export_policy_health_artifacts(
    result: MarketCacheExportPolicyHealthResult,
) -> dict[str, Path]:
    paths = MarketCacheExportPolicyHealthArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths.market_cache_export_policy_health_issues, index=False)
    result.summary_frame.to_csv(paths.market_cache_export_policy_health_summary, index=False)
    metadata = {
        "health_check_id": result.health_check_id,
        "status": result.status,
        "checked_artifact_count": result.checked_artifact_count,
        "issue_count": result.issue_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "summary": result.summary_frame.to_dict("records")[0] if not result.summary_frame.empty else {},
        "comparison_issue_counts": _issue_code_counts(result.health_frame, prefix="COMPARISON"),
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.market_cache_export_policy_health_report.write_text(
        render_market_cache_export_policy_health_report(result),
        encoding="utf-8",
    )
    return paths.as_dict()


def render_market_cache_export_policy_health_report(
    result: MarketCacheExportPolicyHealthResult,
) -> str:
    lines = [
        "# Market Cache Export Policy Artifact Health",
        "",
        "No live trading or broker API was invoked. This report checks local policy recommendation artifacts only.",
        "",
        "## Summary",
        "",
        result.summary_frame.to_markdown(index=False),
        "",
        "## Issues",
        "",
        result.health_frame.to_markdown(index=False) if not result.health_frame.empty else "No issues.",
    ]
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in result.known_limitations)
    return "\n".join(lines) + "\n"


def _load_index(
    *,
    index_df: pd.DataFrame | None,
    index_path: str | Path | None,
    root: str | Path | None,
    settings: MarketCacheExportPolicyHealthSettings,
    project_settings: Settings,
) -> tuple[pd.DataFrame, str, list[str], list[dict[str, Any]]]:
    if index_df is not None:
        return _prepare_index_frame(index_df), "DATAFRAME", [], []
    if index_path is not None:
        path = Path(index_path)
        if not path.exists():
            issue = _issue(
                "",
                "index_path",
                str(path),
                "ERROR",
                "INDEX_NOT_FOUND",
                "Market cache export policy index CSV was not found.",
                "Run market-cache-export-plan-index or pass --root.",
            )
            return _prepare_index_frame(pd.DataFrame()), str(path), [], [issue]
        return read_csv_preserve_symbol_columns(path, keep_default_na=False), str(path), [], []
    effective_root = Path(root) if root is not None else settings.root_dir
    index = build_market_cache_export_policy_index(
        root=effective_root,
        output_dir=settings.output_dir / "_generated_index",
        include_missing_metadata=True,
        settings=project_settings.model_copy(
            update={
                "market_cache_export_policy_index": project_settings.market_cache_export_policy_index.model_copy(
                    update={"write_artifacts": False}
                )
            }
        ),
    )
    return index.index_frame, str(effective_root), index.warnings, []


def _check_generated_manifest(row: dict[str, Any], issues: list[dict[str, Any]]) -> pd.DataFrame | None:
    path = _check_file_path(
        row,
        "generated_reviewed_manifest_path",
        issues,
        required=True,
        issue_code="MISSING_GENERATED_MANIFEST",
    )
    if path is None or not path.exists():
        return None
    try:
        return read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception as exc:
        issues.append(
            _issue(
                _string(row.get("plan_id")),
                "generated_reviewed_manifest_path",
                str(path),
                "ERROR",
                "UNREADABLE_GENERATED_MANIFEST",
                f"Generated reviewed manifest could not be read safely: {exc}",
                "Inspect or regenerate the policy plan.",
            )
        )
    return None


def _check_recommendation_counts(
    row: dict[str, Any],
    metadata: dict[str, Any],
    recommendations: pd.DataFrame,
    issues: list[dict[str, Any]],
) -> None:
    if recommendations.empty or "status" not in recommendations.columns:
        return
    statuses = recommendations["status"].astype(str).str.upper()
    actual = int(statuses.isin({"RECOMMENDED", "RECOMMENDED_WITH_WARNINGS"}).sum())
    expected = int(_number(metadata.get("recommendation_count", row.get("recommendation_count", actual))))
    if actual != expected:
        issues.append(
            _issue(
                _string(row.get("plan_id")),
                "recommendations_path",
                _string(row.get("recommendations_path")),
                "ERROR",
                "RECOMMENDATION_COUNT_MISMATCH",
                f"Recommendation count mismatch: metadata={expected}, recommendations_csv={actual}.",
                "Regenerate the policy plan artifact.",
            )
        )


def _check_recommendation_warnings(
    row: dict[str, Any],
    recommendations: pd.DataFrame,
    issues: list[dict[str, Any]],
) -> None:
    if recommendations.empty or "status" not in recommendations.columns:
        return
    for item in recommendations.to_dict("records"):
        status = _string(item.get("status")).upper()
        warnings = _string(item.get("warnings"))
        symbol = _string(item.get("symbol"))
        if "PROVISIONAL" in warnings.upper():
            issues.append(
                _issue(
                    _string(row.get("plan_id")),
                    "recommendations_path",
                    _string(row.get("recommendations_path")),
                    "WARN",
                    "PROVISIONAL_RECOMMENDATION",
                    f"Recommendation for {symbol} has reviewable policy warnings: {warnings or status}.",
                    "Review the generated manifest notes before export.",
                )
            )
        elif status == "RECOMMENDED_WITH_WARNINGS":
            issues.append(
                _issue(
                    _string(row.get("plan_id")),
                    "recommendations_path",
                    _string(row.get("recommendations_path")),
                    "WARN",
                    "POLICY_RECOMMENDATION_WARNING",
                    f"Recommendation for {symbol} has reviewable warnings: {warnings or status}.",
                    "Review the generated manifest notes before export.",
                )
            )
        if status == "NO_RELIABLE_SOURCE":
            issues.append(
                _issue(
                    _string(row.get("plan_id")),
                    "recommendations_path",
                    _string(row.get("recommendations_path")),
                    "ERROR",
                    "NO_RELIABLE_SOURCE",
                    f"Recommendation for {symbol} found no reliable source.",
                    "Backfill another source, review policy, or leave the row disabled.",
                )
            )


def _check_comparison_diagnostics(
    row: dict[str, Any],
    recommendations: pd.DataFrame,
    issues: list[dict[str, Any]],
    settings: MarketCacheExportPolicyHealthSettings,
) -> None:
    if recommendations.empty or "status" not in recommendations.columns:
        return
    comparison_columns = [column for column in recommendations.columns if str(column).startswith("comparison_")]
    if not comparison_columns:
        return
    for item in recommendations.to_dict("records"):
        status = _string(item.get("status")).upper()
        if status not in {"RECOMMENDED", "RECOMMENDED_WITH_WARNINGS"}:
            continue
        symbol = _string(item.get("symbol"))
        comparison_status = _string(item.get("comparison_status")).upper()
        security_type = _string(item.get("security_type")).upper()
        warnings = _string(item.get("warnings")).upper()
        if not comparison_status:
            issues.append(
                _issue(
                    _string(row.get("plan_id")),
                    "recommendations_path",
                    _string(row.get("recommendations_path")),
                    "WARN",
                    "COMPARISON_MISSING",
                    f"Recommendation for {symbol} is missing comparison diagnostics.",
                    "Regenerate the policy plan to include source-comparison diagnostics.",
                )
            )
        elif comparison_status == "UNAVAILABLE":
            issue_code = "PROVISIONAL_WITHOUT_REFERENCE" if security_type == "ETF" and "PROVISIONAL" in warnings else "COMPARISON_UNAVAILABLE"
            issues.append(
                _issue(
                    _string(row.get("plan_id")),
                    "recommendations_path",
                    _string(row.get("recommendations_path")),
                    "WARN",
                    issue_code,
                    f"Recommendation for {symbol} has comparison_status=UNAVAILABLE.",
                    "Review source policy warnings; this can be expected for ETF/Sina when no second ETF source exists.",
                )
            )
        elif comparison_status == "WARN":
            issues.append(
                _issue(
                    _string(row.get("plan_id")),
                    "recommendations_path",
                    _string(row.get("recommendations_path")),
                    "WARN",
                    "COMPARISON_WARN",
                    f"Recommendation for {symbol} has comparison warnings.",
                    "Review source-only rows or tolerance warnings before export.",
                )
            )
        elif comparison_status == "FAIL":
            severity = "ERROR" if settings.strict else "WARN"
            issues.append(
                _issue(
                    _string(row.get("plan_id")),
                    "recommendations_path",
                    _string(row.get("recommendations_path")),
                    severity,
                    "ACTIONABLE_COMPARISON_FAILURE",
                    f"Recommendation for {symbol} failed required-field source comparison.",
                    "Review the compared source rows before using the generated manifest.",
                )
            )


def _check_manifest_schema(row: dict[str, Any], manifest: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    missing = [column for column in MARKET_CACHE_EXPORT_REQUIRED_COLUMNS if column not in manifest.columns]
    if missing:
        issues.append(
            _issue(
                _string(row.get("plan_id")),
                "generated_reviewed_manifest_path",
                _string(row.get("generated_reviewed_manifest_path")),
                "ERROR",
                "UNREADABLE_GENERATED_MANIFEST",
                f"Generated manifest missing required market-cache-export columns: {', '.join(missing)}.",
                "Regenerate the policy plan manifest.",
            )
        )


def _check_manifest_symbols(row: dict[str, Any], manifest: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    if "symbol" not in manifest.columns:
        return
    for symbol in manifest["symbol"].astype(str).tolist():
        text = symbol.strip()
        digits = "".join(ch for ch in text if ch.isdigit())
        if digits and len(digits) < 6:
            issues.append(
                _issue(
                    _string(row.get("plan_id")),
                    "generated_reviewed_manifest_path",
                    _string(row.get("generated_reviewed_manifest_path")),
                    "ERROR",
                    "SYMBOL_FORMAT_ERROR",
                    f"Symbol appears to have lost leading zeros: {text}",
                    "Regenerate the manifest with symbol-preserving CSV loading/writing.",
                )
            )


def _check_manifest_source_upstream(row: dict[str, Any], manifest: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    if not {"enabled", "source", "upstream_source"}.issubset(manifest.columns):
        return
    enabled = manifest["enabled"].map(_coerce_bool)
    missing = manifest.loc[
        enabled
        & (
            manifest["source"].astype(str).str.strip().eq("")
            | manifest["upstream_source"].astype(str).str.strip().eq("")
        )
    ]
    if not missing.empty:
        issues.append(
            _issue(
                _string(row.get("plan_id")),
                "generated_reviewed_manifest_path",
                _string(row.get("generated_reviewed_manifest_path")),
                "ERROR",
                "MISSING_SOURCE_UPSTREAM_SELECTION",
                "Generated manifest has enabled rows without explicit source/upstream_source.",
                "Review or regenerate the policy plan before export.",
            )
        )


def _check_file_path(
    row: dict[str, Any],
    field: str,
    issues: list[dict[str, Any]],
    *,
    required: bool,
    issue_code: str,
) -> Path | None:
    value = _string(row.get(field))
    plan_id = _string(row.get("plan_id"))
    if not value:
        if required:
            issues.append(
                _issue(
                    plan_id,
                    field,
                    value,
                    "ERROR",
                    issue_code,
                    f"Required path field {field} is empty.",
                    "Regenerate the policy plan index or source artifact.",
                )
            )
        return None
    path = Path(value)
    if not path.exists():
        issues.append(
            _issue(
                plan_id,
                field,
                value,
                "ERROR" if required else "WARN",
                issue_code,
                f"Referenced file does not exist: {path}",
                "Regenerate or repair the linked local artifact.",
            )
        )
        return path
    return path


def _check_csv_path(
    row: dict[str, Any],
    field: str,
    issues: list[dict[str, Any]],
    *,
    required: bool,
    issue_code: str,
) -> pd.DataFrame | None:
    path = _check_file_path(row, field, issues, required=required, issue_code=issue_code)
    if path is None or not path.exists():
        return None
    try:
        return read_csv_preserve_symbol_columns(path, keep_default_na=False)
    except Exception as exc:
        issues.append(
            _issue(
                _string(row.get("plan_id")),
                field,
                str(path),
                "ERROR",
                issue_code,
                f"CSV could not be read safely: {exc}",
                "Inspect or regenerate the CSV artifact.",
            )
        )
    return None


def _check_json_path(
    row: dict[str, Any],
    field: str,
    issues: list[dict[str, Any]],
    *,
    required: bool,
    issue_code: str,
) -> dict[str, Any]:
    path = _check_file_path(row, field, issues, required=required, issue_code=issue_code)
    if path is None or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        issues.append(
            _issue(
                _string(row.get("plan_id")),
                field,
                str(path),
                "ERROR",
                issue_code,
                f"JSON could not be read safely: {exc}",
                "Inspect or regenerate the JSON artifact.",
            )
        )
    return {}


def _check_no_live_statement(
    row: dict[str, Any],
    field: str,
    path: Path | None,
    issues: list[dict[str, Any]],
    settings: MarketCacheExportPolicyHealthSettings,
) -> None:
    if path is None or not path.exists():
        return
    content = path.read_text(encoding="utf-8", errors="ignore")
    if not any(statement in content for statement in NO_LIVE_STATEMENTS):
        issues.append(
            _issue(
                _string(row.get("plan_id")),
                field,
                str(path),
                settings.missing_no_live_statement_severity,
                "MISSING_NO_LIVE_TRADING_STATEMENT",
                "Report is missing a no-live-trading/no-broker statement.",
                "Regenerate the local artifact with the current report renderer.",
            )
        )


def _check_metadata_safety(row: dict[str, Any], metadata: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    if not metadata:
        return
    plan_id = _string(row.get("plan_id"))
    if metadata.get("live_trading_enabled") not in {False, "False", "false", 0, "0"}:
        issues.append(
            _issue(
                plan_id,
                "metadata_path",
                _string(row.get("metadata_path")),
                "ERROR",
                "MISSING_NO_LIVE_TRADING_STATEMENT",
                "Metadata live_trading_enabled is missing or not false.",
                "Inspect and regenerate the local-only policy plan artifact.",
            )
        )
    if metadata.get("broker_api_invoked") not in {False, "False", "false", 0, "0"}:
        issues.append(
            _issue(
                plan_id,
                "metadata_path",
                _string(row.get("metadata_path")),
                "ERROR",
                "MISSING_NO_LIVE_TRADING_STATEMENT",
                "Metadata broker_api_invoked is missing or not false.",
                "Inspect and regenerate the local-only policy plan artifact.",
            )
        )
    if metadata.get("cache_mutated") not in {False, "False", "false", 0, "0"}:
        issues.append(
            _issue(
                plan_id,
                "metadata_path",
                _string(row.get("metadata_path")),
                "ERROR",
                "STALE_OR_PARTIAL_ARTIFACT",
                "Metadata cache_mutated is missing or not false.",
                "Inspect and regenerate the policy plan; planning must not mutate cache.",
            )
        )


def _issue(
    plan_id: str,
    path_field: str,
    path_value: str,
    severity: str,
    issue_code: str,
    issue_message: str,
    suggested_action: str,
) -> dict[str, Any]:
    return {
        "plan_id": plan_id,
        "path_field": path_field,
        "path_value": path_value,
        "severity": severity.upper(),
        "issue_code": issue_code,
        "issue_message": issue_message,
        "suggested_action": suggested_action,
    }


def _finalize_health_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=HEALTH_COLUMNS)
    output = frame.copy(deep=True)
    for column in HEALTH_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    return output[HEALTH_COLUMNS].reset_index(drop=True)


def _prepare_index_frame(index_df: pd.DataFrame) -> pd.DataFrame:
    frame = index_df.copy(deep=True)
    for column in INDEX_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    return frame[INDEX_COLUMNS].reset_index(drop=True)


def _comparison_totals(index_df: pd.DataFrame | None) -> dict[str, int]:
    columns = [
        "comparison_pass_count",
        "comparison_warn_count",
        "comparison_fail_count",
        "comparison_unavailable_count",
        "comparison_required_but_missing_count",
        "comparison_supported_recommendation_count",
        "comparison_unsupported_recommendation_count",
    ]
    if index_df is None:
        return {column: 0 for column in columns}
    frame = index_df.copy(deep=True)
    return {
        column: int(pd.to_numeric(frame.get(column, pd.Series(dtype="object")), errors="coerce").fillna(0).sum())
        for column in columns
    }


def _issue_code_counts(frame: pd.DataFrame, *, prefix: str) -> dict[str, int]:
    if frame.empty or "issue_code" not in frame.columns:
        return {}
    codes = frame["issue_code"].astype(str)
    filtered = codes.loc[codes.str.startswith(prefix)]
    return {str(key): int(value) for key, value in filtered.value_counts().sort_index().items()}


def _coerce_settings(
    settings: MarketCacheExportPolicyHealthSettings | dict[str, Any] | None,
) -> MarketCacheExportPolicyHealthSettings:
    if settings is None:
        return MarketCacheExportPolicyHealthSettings()
    if isinstance(settings, MarketCacheExportPolicyHealthSettings):
        return settings
    return MarketCacheExportPolicyHealthSettings(**settings)


def _resolve_settings(
    settings: Settings | MarketCacheExportPolicyHealthSettings | dict[str, Any] | None,
) -> tuple[Settings, MarketCacheExportPolicyHealthSettings]:
    project = load_settings(Path("config/default.yaml"))
    if settings is None:
        return project, project.market_cache_export_policy_health
    if isinstance(settings, Settings):
        return settings, settings.market_cache_export_policy_health
    if isinstance(settings, MarketCacheExportPolicyHealthSettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.market_cache_export_policy_health.model_dump())
        payload.update(settings.get("market_cache_export_policy_health", settings))
        return project, MarketCacheExportPolicyHealthSettings(**payload)
    raise TypeError("settings must be Settings, MarketCacheExportPolicyHealthSettings, dict, or None")


def generate_market_cache_export_policy_health_id(
    index_frame: pd.DataFrame,
    *,
    index_source: str,
    settings: MarketCacheExportPolicyHealthSettings,
) -> str:
    payload = {
        "index_source": index_source,
        "plan_ids": sorted(index_frame.get("plan_id", pd.Series(dtype="object")).astype(str).tolist()),
        "config_version": settings.config_version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _string(value).lower()
    return text in {"true", "1", "yes", "y", "enabled"}


def _string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value
