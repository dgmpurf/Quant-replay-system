"""Local-only data source availability and route health checks."""

from __future__ import annotations

import hashlib
import ast
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import DataSourceHealthSettings, DataSourceSettings, Settings, load_settings
from quant_replay_system.data_sources import (
    DataSourceRequest,
    REAL_DATA_SOURCES,
    infer_akshare_market_symbol_type,
    run_data_source_fetch,
)


DATA_SOURCE_HEALTH_LIMITATIONS = [
    "Health checks verify local adapter availability and route behavior only.",
    "A PASS result is not data certification; raw files must still pass data-pipeline, data-quality, and snapshot-quality.",
    "Real/network health checks are manual-only and require explicit --allow-real-data.",
    "Automated tests use fake/local data and must not call real data APIs.",
    "No broker API, live trading, or order automation is invoked.",
]

DATA_SOURCE_HEALTH_COLUMNS = [
    "source",
    "dataset_type",
    "symbol",
    "start_date",
    "end_date",
    "requested_upstream",
    "attempted_upstreams",
    "successful_upstream",
    "attempted_functions",
    "successful_function",
    "status",
    "row_count",
    "latency_ms",
    "error_type",
    "safe_error_message",
    "recommended_fallback",
    "raw_data_path",
    "metadata_path",
    "no_live_trading",
    "no_broker_api",
]

DATA_SOURCE_HEALTH_SUMMARY_COLUMNS = [
    "health_check_id",
    "status",
    "check_count",
    "configured_route_status",
    "pass_count",
    "warn_count",
    "fail_count",
    "row_count",
    "recommended_fallback",
    "no_live_trading",
    "no_broker_api",
]


@dataclass(frozen=True)
class DataSourceHealthCheckRequest:
    source: str
    dataset_type: str
    input_path: str | Path | None = None
    raw_output_dir: str | Path | None = None
    revision_id: str | None = None
    allow_real_data: bool = False
    symbol: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    requested_upstream: str | None = None
    as_of_date: str | None = None
    market_type: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DataSourceHealthCheckResult:
    source: str
    dataset_type: str
    symbol: str
    start_date: str
    end_date: str
    requested_upstream: str
    attempted_upstreams: list[str]
    successful_upstream: str
    attempted_functions: list[str]
    successful_function: str
    status: str
    row_count: int
    latency_ms: int
    error_type: str
    safe_error_message: str
    recommended_fallback: str
    raw_data_path: str
    metadata_path: str
    no_live_trading: bool = True
    no_broker_api: bool = True


@dataclass(frozen=True)
class DataSourceHealthArtifactPaths:
    artifact_dir: Path
    data_source_health_report: Path
    data_source_health_results: Path
    data_source_health_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "data_source_health_report": self.data_source_health_report,
            "data_source_health_results": self.data_source_health_results,
            "data_source_health_summary": self.data_source_health_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class DataSourceHealthResult:
    health_check_id: str
    status: str
    check_results: list[DataSourceHealthCheckResult]
    health_frame: pd.DataFrame
    summary_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]

    @property
    def issue_count(self) -> int:
        return int((self.health_frame["status"] != "PASS").sum()) if not self.health_frame.empty else 0

    @property
    def warning_count(self) -> int:
        return int((self.health_frame["status"] == "WARN").sum()) if not self.health_frame.empty else 0

    @property
    def error_count(self) -> int:
        return int((self.health_frame["status"] == "FAIL").sum()) if not self.health_frame.empty else 0


def run_data_source_health_check(
    requests: list[DataSourceHealthCheckRequest] | DataSourceHealthCheckRequest | None = None,
    *,
    source: str | None = None,
    dataset_type: str | None = None,
    input_path: str | Path | None = None,
    raw_output_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    revision_id: str | None = None,
    allow_real_data: bool = False,
    symbol: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    requested_upstream: str | None = None,
    as_of_date: str | None = None,
    market_type: str | None = None,
    config: Settings | DataSourceHealthSettings | dict[str, Any] | None = None,
) -> DataSourceHealthResult:
    """Run one or more local data source health checks and write artifacts."""

    project_settings, health_settings = _resolve_settings(config)
    if health_settings.enable_live_trading or health_settings.enable_broker_api:
        raise ValueError("Data source health check cannot enable live trading or broker API access")

    check_requests = _coerce_requests(
        requests,
        source=source,
        dataset_type=dataset_type,
        input_path=input_path,
        raw_output_dir=raw_output_dir,
        revision_id=revision_id,
        allow_real_data=allow_real_data,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        requested_upstream=requested_upstream,
        as_of_date=as_of_date,
        market_type=market_type,
    )
    expanded_requests = _expand_health_requests(check_requests, project_settings, health_settings)
    check_results = [
        run_single_source_health_check(request, settings=project_settings, health_settings=health_settings)
        for request in expanded_requests
    ]
    health_frame = build_data_source_health_frame(check_results)
    health_check_id = generate_data_source_health_check_id(check_requests, project_settings, health_settings)
    summary_frame = summarize_data_source_health(health_frame, health_check_id=health_check_id)
    status = str(summary_frame.iloc[0]["status"]) if not summary_frame.empty else "PASS"
    paths = resolve_data_source_health_artifact_paths(
        Path(output_dir) if output_dir is not None else health_settings.output_dir,
        health_check_id,
    )
    warnings = _health_warnings(health_frame)
    audit_metadata = {
        "health_check_id": health_check_id,
        "status": status,
        "check_count": len(check_results),
        "source": check_requests[0].source if check_requests else "",
        "dataset_type": check_requests[0].dataset_type if check_requests else "",
        "allow_real_data": any(request.allow_real_data for request in check_requests),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "network_api_calls_used_in_tests": False,
        "data_source_health_only": True,
        "config_version": health_settings.config_version,
    }
    result = DataSourceHealthResult(
        health_check_id=health_check_id,
        status=status,
        check_results=check_results,
        health_frame=health_frame,
        summary_frame=summary_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=DATA_SOURCE_HEALTH_LIMITATIONS,
        audit_metadata=audit_metadata,
    )
    if health_settings.write_artifacts:
        write_data_source_health_artifacts(result)
    return result


def run_single_source_health_check(
    request: DataSourceHealthCheckRequest,
    *,
    settings: Settings | None = None,
    health_settings: DataSourceHealthSettings | None = None,
) -> DataSourceHealthCheckResult:
    """Run one source/route probe and return a normalized health row."""

    project_settings = settings or load_settings(Path("config/default.yaml"))
    health_cfg = health_settings or project_settings.data_source_health
    normalized_source = _normalize_source(request.source)
    normalized_dataset = str(request.dataset_type).strip().lower()
    requested_upstream = _normalize_requested_upstream(request.requested_upstream)

    if normalized_source in REAL_DATA_SOURCES and not request.allow_real_data:
        return _blocked_real_data_result(request, requested_upstream=requested_upstream)

    source_settings = _source_settings_for_health_request(project_settings.data_sources, request)
    project_settings = project_settings.model_copy(update={"data_sources": source_settings})
    fetch_request = DataSourceRequest(
        source=normalized_source,
        dataset_type=normalized_dataset,
        input_path=request.input_path,
        output_dir=request.raw_output_dir or source_settings.raw_output_dir,
        revision_id=request.revision_id,
        allow_real_data=bool(request.allow_real_data),
        symbol=request.symbol,
        start_date=request.start_date,
        end_date=request.end_date,
        as_of_date=request.as_of_date,
        market_type=request.market_type,
        params=_source_request_params_for_health(request),
    )
    started = time.perf_counter()
    try:
        fetch_result = run_data_source_fetch(fetch_request, settings=project_settings)
        latency_ms = _elapsed_ms(started)
    except Exception as exc:
        latency_ms = _elapsed_ms(started)
        safe_message = _safe_error_message(exc)
        return DataSourceHealthCheckResult(
            source=normalized_source,
            dataset_type=normalized_dataset,
            symbol=request.symbol or "",
            start_date=request.start_date or "",
            end_date=request.end_date or "",
            requested_upstream=requested_upstream,
            attempted_upstreams=_attempted_upstreams_from_message(safe_message),
            successful_upstream="",
            attempted_functions=_attempted_functions_from_message(safe_message),
            successful_function="",
            status="FAIL",
            row_count=0,
            latency_ms=latency_ms,
            error_type=type(exc).__name__,
            safe_error_message=safe_message,
            recommended_fallback=_recommended_fallback(normalized_source, normalized_dataset, request, failed=True),
            raw_data_path="",
            metadata_path="",
        )

    adapter_metadata = fetch_result.audit_metadata.get("adapter_metadata", {})
    status = "PASS" if fetch_result.row_count > 0 else "WARN"
    error_type = "" if status == "PASS" else "EMPTY_RESULT"
    safe_error_message = "" if status == "PASS" else "Adapter returned zero rows."
    recommended_fallback = (
        "Proceed to data-pipeline, data-quality, and snapshot-quality before research use."
        if status == "PASS"
        else _recommended_fallback(normalized_source, normalized_dataset, request, failed=False)
    )
    if health_cfg.fail_empty_result and fetch_result.row_count == 0:
        status = "FAIL"
        recommended_fallback = _recommended_fallback(normalized_source, normalized_dataset, request, failed=True)
    return DataSourceHealthCheckResult(
        source=fetch_result.source,
        dataset_type=fetch_result.dataset_type,
        symbol=str(fetch_result.audit_metadata.get("request", {}).get("symbol", request.symbol or "")),
        start_date=str(fetch_result.audit_metadata.get("request", {}).get("start_date", request.start_date or "")),
        end_date=str(fetch_result.audit_metadata.get("request", {}).get("end_date", request.end_date or "")),
        requested_upstream=requested_upstream,
        attempted_upstreams=list(adapter_metadata.get("attempted_upstreams", [])),
        successful_upstream=str(adapter_metadata.get("upstream_source", "")),
        attempted_functions=list(adapter_metadata.get("attempted_functions", [])),
        successful_function=str(adapter_metadata.get("successful_function", "")),
        status=status,
        row_count=int(fetch_result.row_count),
        latency_ms=latency_ms,
        error_type=error_type,
        safe_error_message=safe_error_message,
        recommended_fallback=recommended_fallback,
        raw_data_path=str(fetch_result.artifact_paths.get("raw_data", "")),
        metadata_path=str(fetch_result.artifact_paths.get("metadata", "")),
    )


def build_data_source_health_frame(
    results: list[DataSourceHealthCheckResult] | pd.DataFrame,
) -> pd.DataFrame:
    """Build a CSV-friendly data source health result frame."""

    if isinstance(results, pd.DataFrame):
        frame = results.copy(deep=True)
    else:
        frame = pd.DataFrame([_health_result_row(result) for result in results])
    for column in DATA_SOURCE_HEALTH_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    frame = frame[DATA_SOURCE_HEALTH_COLUMNS]
    return frame.fillna("")


def summarize_data_source_health(
    health_frame: pd.DataFrame,
    *,
    health_check_id: str,
) -> pd.DataFrame:
    """Summarize data source health rows into one overall status row."""

    frame = build_data_source_health_frame(health_frame)
    check_count = len(frame)
    pass_count = int((frame["status"] == "PASS").sum()) if check_count else 0
    warn_count = int((frame["status"] == "WARN").sum()) if check_count else 0
    fail_count = int((frame["status"] == "FAIL").sum()) if check_count else 0
    configured = frame[frame["requested_upstream"].isin(["", "CONFIGURED_ORDER"])]
    configured_status = str(configured.iloc[0]["status"]) if not configured.empty else ""
    numeric_row_counts = pd.to_numeric(frame["row_count"], errors="coerce").fillna(0)
    if not configured.empty:
        summary_row_count = int(pd.to_numeric(configured.iloc[[0]]["row_count"], errors="coerce").fillna(0).iloc[0])
    else:
        summary_row_count = int(numeric_row_counts.max()) if check_count else 0
    if configured_status:
        status = configured_status
    elif pass_count:
        status = "PASS"
    elif warn_count:
        status = "WARN"
    elif fail_count:
        status = "FAIL"
    else:
        status = "PASS"
    recommended = _overall_recommended_fallback(frame, status)
    summary = pd.DataFrame(
        [
            {
                "health_check_id": health_check_id,
                "status": status,
                "check_count": check_count,
                "configured_route_status": configured_status,
                "pass_count": pass_count,
                "warn_count": warn_count,
                "fail_count": fail_count,
                "row_count": summary_row_count,
                "recommended_fallback": recommended,
                "no_live_trading": True,
                "no_broker_api": True,
            }
        ],
        columns=DATA_SOURCE_HEALTH_SUMMARY_COLUMNS,
    )
    return summary


def write_data_source_health_artifacts(result: DataSourceHealthResult) -> dict[str, Path]:
    """Write data source health markdown, CSV, summary, and metadata artifacts."""

    paths = DataSourceHealthArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.health_frame.to_csv(paths.data_source_health_results, index=False)
    result.summary_frame.to_csv(paths.data_source_health_summary, index=False)
    paths.data_source_health_report.write_text(render_data_source_health_report(result), encoding="utf-8")
    metadata = {
        "health_check_id": result.health_check_id,
        "status": result.status,
        "issue_count": result.issue_count,
        "warning_count": result.warning_count,
        "error_count": result.error_count,
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
        "summary": result.summary_frame.to_dict("records"),
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "created_at": "1970-01-01T00:00:00+00:00",
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    return paths.as_dict()


def render_data_source_health_report(result: DataSourceHealthResult) -> str:
    """Render a concise markdown data source health report."""

    summary = result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}
    lines = [
        "# Data Source Health Check",
        "",
        f"- health_check_id: {result.health_check_id}",
        f"- status: {result.status}",
        f"- check_count: {summary.get('check_count', 0)}",
        f"- pass_count: {summary.get('pass_count', 0)}",
        f"- warn_count: {summary.get('warn_count', 0)}",
        f"- fail_count: {summary.get('fail_count', 0)}",
        f"- recommended_fallback: {summary.get('recommended_fallback', '')}",
        "",
        "No live trading or broker API was invoked.",
        "",
        "## Route Results",
        "",
    ]
    if result.health_frame.empty:
        lines.append("No route checks were run.")
    else:
        visible = result.health_frame.copy(deep=True)
        lines.append(visible.to_markdown(index=False))
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in result.known_limitations)
    return "\n".join(lines) + "\n"


def resolve_data_source_health_artifact_paths(
    output_dir: str | Path,
    health_check_id: str,
) -> DataSourceHealthArtifactPaths:
    artifact_dir = Path(output_dir) / str(health_check_id)
    return DataSourceHealthArtifactPaths(
        artifact_dir=artifact_dir,
        data_source_health_report=artifact_dir / "data_source_health_report.md",
        data_source_health_results=artifact_dir / "data_source_health_results.csv",
        data_source_health_summary=artifact_dir / "data_source_health_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def generate_data_source_health_check_id(
    requests: list[DataSourceHealthCheckRequest],
    project_settings: Settings,
    health_settings: DataSourceHealthSettings,
) -> str:
    payload = {
        "requests": [_request_payload(request) for request in requests],
        "data_sources_config_version": project_settings.data_sources.config_version,
        "health_config_version": health_settings.config_version,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _coerce_requests(
    requests: list[DataSourceHealthCheckRequest] | DataSourceHealthCheckRequest | None,
    *,
    source: str | None,
    dataset_type: str | None,
    input_path: str | Path | None,
    raw_output_dir: str | Path | None,
    revision_id: str | None,
    allow_real_data: bool,
    symbol: str | None,
    start_date: str | None,
    end_date: str | None,
    requested_upstream: str | None,
    as_of_date: str | None,
    market_type: str | None,
) -> list[DataSourceHealthCheckRequest]:
    if isinstance(requests, DataSourceHealthCheckRequest):
        return [requests]
    if requests is not None:
        return list(requests)
    if source is None or dataset_type is None:
        raise ValueError("data-source-health requires source and dataset_type")
    return [
        DataSourceHealthCheckRequest(
            source=source,
            dataset_type=dataset_type,
            input_path=input_path,
            raw_output_dir=raw_output_dir,
            revision_id=revision_id,
            allow_real_data=allow_real_data,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            requested_upstream=requested_upstream,
            as_of_date=as_of_date,
            market_type=market_type,
        )
    ]


def _expand_health_requests(
    requests: list[DataSourceHealthCheckRequest],
    project_settings: Settings,
    health_settings: DataSourceHealthSettings,
) -> list[DataSourceHealthCheckRequest]:
    expanded: list[DataSourceHealthCheckRequest] = []
    for request in requests:
        source = _normalize_source(request.source)
        dataset_type = str(request.dataset_type).strip().lower()
        if request.requested_upstream or source != "AKSHARE_OPTIONAL" or dataset_type not in {"market", "benchmark"}:
            expanded.append(request)
            continue
        configured = _replace_request(request, requested_upstream="CONFIGURED_ORDER")
        expanded.append(configured)
        if not health_settings.check_individual_akshare_upstreams:
            continue
        symbol_type = "INDEX" if dataset_type == "benchmark" else infer_akshare_market_symbol_type(request.symbol)
        for upstream in _akshare_upstream_order_for_symbol_type(symbol_type, project_settings.data_sources):
            expanded.append(_replace_request(request, requested_upstream=upstream))
    return expanded


def _replace_request(request: DataSourceHealthCheckRequest, **updates: Any) -> DataSourceHealthCheckRequest:
    payload = dict(request.__dict__)
    payload.update(updates)
    return DataSourceHealthCheckRequest(**payload)


def _source_settings_for_health_request(
    source_settings: DataSourceSettings,
    request: DataSourceHealthCheckRequest,
) -> DataSourceSettings:
    updates: dict[str, Any] = {}
    source = _normalize_source(request.source)
    if source in REAL_DATA_SOURCES and request.allow_real_data:
        updates.update({"allow_network_sources": True, "allow_real_data_fetch": True})
    requested_upstream = _normalize_requested_upstream(request.requested_upstream)
    if source == "AKSHARE_OPTIONAL" and requested_upstream not in {"", "CONFIGURED_ORDER"}:
        symbol_type = "INDEX" if request.dataset_type == "benchmark" else infer_akshare_market_symbol_type(request.symbol)
        updates["akshare_market_enable_curl_cffi_fallback"] = False
        if symbol_type == "ETF":
            updates["akshare_market_etf_fallback_order"] = [requested_upstream]
        elif symbol_type == "INDEX":
            updates["akshare_market_index_fallback_order"] = [requested_upstream]
        elif symbol_type == "STOCK":
            updates["akshare_market_stock_fallback_order"] = [requested_upstream]
        else:
            updates["akshare_market_stock_fallback_order"] = [requested_upstream]
            updates["akshare_market_etf_fallback_order"] = [requested_upstream]
            updates["akshare_market_index_fallback_order"] = [requested_upstream]
    return source_settings.model_copy(update=updates) if updates else source_settings


def _source_request_params_for_health(request: DataSourceHealthCheckRequest) -> dict[str, Any]:
    params = dict(request.params or {})
    requested_upstream = _normalize_requested_upstream(request.requested_upstream)
    if requested_upstream not in {"", "CONFIGURED_ORDER"}:
        params["enable_curl_cffi_fallback"] = False
    return params


def _akshare_upstream_order_for_symbol_type(symbol_type: str, settings: DataSourceSettings) -> list[str]:
    if symbol_type == "ETF":
        return _unique_upstreams(settings.akshare_market_etf_fallback_order)
    if symbol_type == "INDEX":
        return _unique_upstreams(settings.akshare_market_index_fallback_order)
    if symbol_type == "STOCK":
        return _unique_upstreams(settings.akshare_market_stock_fallback_order)
    return _unique_upstreams(
        [
            *settings.akshare_market_stock_fallback_order,
            *settings.akshare_market_etf_fallback_order,
            *settings.akshare_market_index_fallback_order,
        ]
    )


def _unique_upstreams(values: list[str] | tuple[str, ...]) -> list[str]:
    output: list[str] = []
    for value in values:
        upstream = str(value).strip().upper()
        if upstream in {"TENCENT", "SINA", "EASTMONEY"} and upstream not in output:
            output.append(upstream)
    return output


def _blocked_real_data_result(
    request: DataSourceHealthCheckRequest,
    *,
    requested_upstream: str,
) -> DataSourceHealthCheckResult:
    source = _normalize_source(request.source)
    return DataSourceHealthCheckResult(
        source=source,
        dataset_type=str(request.dataset_type).strip().lower(),
        symbol=request.symbol or "",
        start_date=request.start_date or "",
        end_date=request.end_date or "",
        requested_upstream=requested_upstream,
        attempted_upstreams=[],
        successful_upstream="",
        attempted_functions=[],
        successful_function="",
        status="WARN",
        row_count=0,
        latency_ms=0,
        error_type="BLOCKED_REAL_DATA",
        safe_error_message=f"{source} real data health check requires --allow-real-data.",
        recommended_fallback="Rerun manually with --allow-real-data, or use LOCAL_CSV fallback.",
        raw_data_path="",
        metadata_path="",
    )


def _health_result_row(result: DataSourceHealthCheckResult) -> dict[str, Any]:
    return {
        "source": result.source,
        "dataset_type": result.dataset_type,
        "symbol": result.symbol,
        "start_date": result.start_date,
        "end_date": result.end_date,
        "requested_upstream": result.requested_upstream,
        "attempted_upstreams": json.dumps(result.attempted_upstreams, ensure_ascii=True),
        "successful_upstream": result.successful_upstream,
        "attempted_functions": json.dumps(result.attempted_functions, ensure_ascii=True),
        "successful_function": result.successful_function,
        "status": result.status,
        "row_count": result.row_count,
        "latency_ms": result.latency_ms,
        "error_type": result.error_type,
        "safe_error_message": result.safe_error_message,
        "recommended_fallback": result.recommended_fallback,
        "raw_data_path": result.raw_data_path,
        "metadata_path": result.metadata_path,
        "no_live_trading": result.no_live_trading,
        "no_broker_api": result.no_broker_api,
    }


def _health_warnings(frame: pd.DataFrame) -> list[str]:
    warnings: list[str] = []
    if frame.empty:
        return warnings
    for row in frame.to_dict("records"):
        if row.get("status") == "WARN":
            warnings.append(f"{row.get('source')} {row.get('requested_upstream')}: {row.get('safe_error_message')}")
        elif row.get("status") == "FAIL":
            warnings.append(f"{row.get('source')} {row.get('requested_upstream')}: {row.get('error_type')} {row.get('safe_error_message')}")
    return [warning.strip() for warning in warnings if warning.strip()]


def _overall_recommended_fallback(frame: pd.DataFrame, status: str) -> str:
    if status == "PASS":
        return "At least one configured route is usable. Continue with data-source-fetch, then data-pipeline and quality gates."
    if status == "WARN":
        return "Review warnings, then rerun with --allow-real-data or use LOCAL_CSV fallback."
    if frame.empty:
        return "No checks were run."
    fallbacks = [str(value) for value in frame["recommended_fallback"].tolist() if str(value).strip()]
    return fallbacks[0] if fallbacks else "Use LOCAL_CSV fallback or retry upstream later."


def _recommended_fallback(
    source: str,
    dataset_type: str,
    request: DataSourceHealthCheckRequest,
    *,
    failed: bool,
) -> str:
    _ = dataset_type
    requested_upstream = _normalize_requested_upstream(request.requested_upstream)
    if source == "AKSHARE_OPTIONAL":
        if failed and requested_upstream not in {"", "CONFIGURED_ORDER"}:
            return "Try the configured AKShare fallback order, then use LOCAL_CSV if every upstream fails."
        if failed:
            return "Retry later, check VPN/proxy/upstream changes, or use reviewed LOCAL_CSV fallback."
        return "Review row count and upstream, then run data-pipeline and quality gates."
    if source == "LOCAL_CSV":
        return "Check that the local CSV path exists and is readable."
    if source == "MOCK":
        return "Check configured mock CSV paths."
    return "Review adapter diagnostics or use LOCAL_CSV fallback."


def _elapsed_ms(started: float) -> int:
    return max(0, int(round((time.perf_counter() - started) * 1000)))


def _normalize_source(source: str) -> str:
    return str(source).strip().upper()


def _normalize_requested_upstream(value: str | None) -> str:
    return str(value or "").strip().upper()


def _request_payload(request: DataSourceHealthCheckRequest) -> dict[str, Any]:
    return {
        "source": request.source,
        "dataset_type": request.dataset_type,
        "input_path": str(request.input_path) if request.input_path is not None else "",
        "raw_output_dir": str(request.raw_output_dir) if request.raw_output_dir is not None else "",
        "revision_id": request.revision_id or "",
        "allow_real_data": bool(request.allow_real_data),
        "symbol": request.symbol or "",
        "start_date": request.start_date or "",
        "end_date": request.end_date or "",
        "requested_upstream": request.requested_upstream or "",
        "as_of_date": request.as_of_date or "",
        "market_type": request.market_type or "",
        "params": request.params,
    }


def _safe_error_message(exc: Exception) -> str:
    message = str(exc)
    message = re.sub(
        r"(?i)(token|api[_-]?key|secret|password)\s*[:=]\s*['\"]?[^'\"\s,;]+",
        r"\1=<redacted>",
        message,
    )
    message = re.sub(r"(?i)TUSHARE_TOKEN\s*[:=]\s*[^,\s;]+", "TUSHARE_TOKEN=<redacted>", message)
    return message[:1000]


def _attempted_functions_from_message(message: str) -> list[str]:
    match = re.search(r"attempted_functions=(\[[^\]]*\])", message)
    if not match:
        return []
    try:
        values = ast.literal_eval(match.group(1))
    except (SyntaxError, ValueError):
        return []
    return [str(value) for value in values if str(value).strip()]


def _attempted_upstreams_from_message(message: str) -> list[str]:
    values: list[str] = []
    for match in re.finditer(r"['\"]upstream_source['\"]:\s*['\"]([^'\"]+)['\"]", message):
        upstream = match.group(1).strip().upper()
        if upstream and upstream not in values:
            values.append(upstream)
    return values


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.isoformat()
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _resolve_settings(
    settings: Settings | DataSourceHealthSettings | dict[str, Any] | None,
) -> tuple[Settings, DataSourceHealthSettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.data_source_health
    if isinstance(settings, Settings):
        return settings, settings.data_source_health
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, DataSourceHealthSettings):
        return project, settings
    if isinstance(settings, dict):
        health_payload = dict(project.data_source_health.model_dump())
        project_updates: dict[str, Any] = {}
        for key, value in settings.items():
            if key == "data_source_health" and isinstance(value, dict):
                health_payload.update(value)
            elif key == "data_sources" and isinstance(value, dict):
                project_updates["data_sources"] = project.data_sources.model_copy(update=value)
            elif key in health_payload:
                health_payload[key] = value
        if project_updates:
            project = project.model_copy(update=project_updates)
        return project, DataSourceHealthSettings(**health_payload)
    raise TypeError("settings must be Settings, DataSourceHealthSettings, dict, or None")
