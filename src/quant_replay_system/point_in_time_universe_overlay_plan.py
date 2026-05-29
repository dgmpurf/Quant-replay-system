"""Plan-only point-in-time universe overlay review templates."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns


OVERLAY_PLAN_COLUMNS = [
    "overlay_plan_id",
    "signal_date",
    "symbol",
    "universe_name",
    "proposed_as_of_date",
    "proposed_available_time",
    "base_universe_path",
    "base_universe_as_of_date",
    "base_universe_available_time",
    "include_flag",
    "review_status",
    "review_reason",
    "source",
    "upstream_source",
    "survivorship_bias_warning",
    "manual_review_required",
    "valid_for_signal_date",
    "blocker_reason",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "plan_only",
]

EXECUTION_MANIFEST_REQUIRED_COLUMNS = [
    "execution_manifest_id",
    "plan_id",
    "signal_date",
    "universe",
    "readiness_status",
    "blocker_reason",
    "universe_dataset_path",
    "universe_as_of_date",
]

SAFETY_STATEMENT = (
    "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
    "order placement, message delivery, LLM API, or external API was invoked."
)


@dataclass(frozen=True)
class PointInTimeUniverseOverlayPlanSettings:
    output_dir: Path = Path("outputs/reports/point_in_time_universe_overlay_plan")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    enable_live_trading: bool = False
    enable_broker_api: bool = False
    enable_order_placement: bool = False
    enable_message_delivery: bool = False
    enable_external_api: bool = False
    enable_llm_api: bool = False


@dataclass(frozen=True)
class PointInTimeUniverseOverlayPlanRequest:
    execution_manifest: Path
    base_universe: Path | None
    universe_name: str
    allow_template_include: bool


@dataclass(frozen=True)
class PointInTimeUniverseOverlayPlanRow:
    overlay_plan_id: str
    signal_date: str
    symbol: str
    universe_name: str
    proposed_as_of_date: str
    proposed_available_time: str
    base_universe_path: str
    base_universe_as_of_date: str
    base_universe_available_time: str
    include_flag: bool | str
    review_status: str
    review_reason: str
    source: str
    upstream_source: str
    survivorship_bias_warning: bool
    manual_review_required: bool
    valid_for_signal_date: bool
    blocker_reason: str
    no_live_trading: bool = True
    no_broker_api: bool = True
    no_order_placement: bool = True
    no_message_sent: bool = True
    plan_only: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "overlay_plan_id": self.overlay_plan_id,
            "signal_date": self.signal_date,
            "symbol": self.symbol,
            "universe_name": self.universe_name,
            "proposed_as_of_date": self.proposed_as_of_date,
            "proposed_available_time": self.proposed_available_time,
            "base_universe_path": self.base_universe_path,
            "base_universe_as_of_date": self.base_universe_as_of_date,
            "base_universe_available_time": self.base_universe_available_time,
            "include_flag": self.include_flag,
            "review_status": self.review_status,
            "review_reason": self.review_reason,
            "source": self.source,
            "upstream_source": self.upstream_source,
            "survivorship_bias_warning": self.survivorship_bias_warning,
            "manual_review_required": self.manual_review_required,
            "valid_for_signal_date": self.valid_for_signal_date,
            "blocker_reason": self.blocker_reason,
            "no_live_trading": self.no_live_trading,
            "no_broker_api": self.no_broker_api,
            "no_order_placement": self.no_order_placement,
            "no_message_sent": self.no_message_sent,
            "plan_only": self.plan_only,
        }


@dataclass(frozen=True)
class PointInTimeUniverseOverlayPlanArtifactPaths:
    artifact_dir: Path
    overlay_plan_csv: Path
    overlay_template_csv: Path
    report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "overlay_plan_csv": self.overlay_plan_csv,
            "overlay_template_csv": self.overlay_template_csv,
            "report": self.report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PointInTimeUniverseOverlayPlanResult:
    overlay_plan_id: str
    status: str
    request: PointInTimeUniverseOverlayPlanRequest
    row_count: int
    signal_date_count: int
    symbol_count: int
    review_status_counts: dict[str, int]
    survivorship_bias_warning_count: int
    valid_for_signal_date_count: int
    plan_frame: pd.DataFrame
    warnings: list[str]
    artifact_paths: dict[str, Path]
    audit_metadata: dict[str, Any]


def load_backfill_execution_manifest_for_universe_plan(path: str | Path) -> pd.DataFrame:
    """Load an execution manifest CSV while preserving symbol-like strings."""

    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Current-candidates backfill execution manifest not found: {manifest_path}")
    frame = read_csv_preserve_symbol_columns(manifest_path, keep_default_na=False)
    missing = [column for column in EXECUTION_MANIFEST_REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Execution manifest missing required columns: {', '.join(missing)}")
    return frame


def build_point_in_time_universe_overlay_plan(
    *,
    execution_manifest: str | Path,
    base_universe: str | Path | None = None,
    universe_name: str = "",
    allow_template_include: bool = False,
    output_dir: str | Path | None = None,
    settings: PointInTimeUniverseOverlayPlanSettings | None = None,
) -> PointInTimeUniverseOverlayPlanResult:
    """Build a manual-review PIT universe overlay plan without generating snapshots or candidates."""

    resolved_settings = settings or PointInTimeUniverseOverlayPlanSettings()
    if output_dir is not None:
        resolved_settings = PointInTimeUniverseOverlayPlanSettings(
            output_dir=Path(output_dir),
            config_version=resolved_settings.config_version,
            write_artifacts=resolved_settings.write_artifacts,
            enable_live_trading=resolved_settings.enable_live_trading,
            enable_broker_api=resolved_settings.enable_broker_api,
            enable_order_placement=resolved_settings.enable_order_placement,
            enable_message_delivery=resolved_settings.enable_message_delivery,
            enable_external_api=resolved_settings.enable_external_api,
            enable_llm_api=resolved_settings.enable_llm_api,
        )
    _assert_settings_safe(resolved_settings)

    request = PointInTimeUniverseOverlayPlanRequest(
        execution_manifest=Path(execution_manifest),
        base_universe=Path(base_universe) if base_universe else None,
        universe_name=str(universe_name or "").strip(),
        allow_template_include=bool(allow_template_include),
    )
    manifest_frame = load_backfill_execution_manifest_for_universe_plan(request.execution_manifest)
    overlay_plan_id = generate_point_in_time_universe_overlay_plan_id(request, manifest_frame, resolved_settings)
    plan_symbols_by_date = _load_plan_symbols_by_signal_date(request.execution_manifest)
    rows = _build_overlay_rows(overlay_plan_id, request, manifest_frame, plan_symbols_by_date)
    plan_frame = build_point_in_time_universe_overlay_plan_table([row.as_dict() for row in rows])
    status = "WARN"
    warnings = _build_warnings(request, manifest_frame, plan_frame)
    paths = resolve_point_in_time_universe_overlay_plan_paths(resolved_settings.output_dir, overlay_plan_id)
    result = PointInTimeUniverseOverlayPlanResult(
        overlay_plan_id=overlay_plan_id,
        status=status,
        request=request,
        row_count=len(plan_frame),
        signal_date_count=_nunique(plan_frame, "signal_date"),
        symbol_count=_nunique(plan_frame, "symbol"),
        review_status_counts=_value_counts(plan_frame, "review_status"),
        survivorship_bias_warning_count=_true_count(plan_frame, "survivorship_bias_warning"),
        valid_for_signal_date_count=_true_count(plan_frame, "valid_for_signal_date"),
        plan_frame=plan_frame,
        warnings=warnings,
        artifact_paths=paths.as_dict(),
        audit_metadata=_audit_metadata(request, resolved_settings),
    )
    if resolved_settings.write_artifacts:
        write_point_in_time_universe_overlay_plan_artifacts(result)
    return result


def build_point_in_time_universe_overlay_plan_table(rows: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=OVERLAY_PLAN_COLUMNS)
    for column in _BOOLEAN_COLUMNS:
        if column in frame:
            frame[column] = frame[column].astype(object)
    return frame


def write_point_in_time_universe_overlay_plan_artifacts(
    result: PointInTimeUniverseOverlayPlanResult,
) -> dict[str, Path]:
    """Write overlay plan, template, report, and metadata artifacts."""

    paths = PointInTimeUniverseOverlayPlanArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.plan_frame.to_csv(paths.overlay_plan_csv, index=False)
    result.plan_frame.to_csv(paths.overlay_template_csv, index=False)
    paths.metadata.write_text(
        json.dumps(_json_safe(build_point_in_time_universe_overlay_plan_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    paths.report.write_text(render_point_in_time_universe_overlay_plan_report(result), encoding="utf-8")
    return paths.as_dict()


def render_point_in_time_universe_overlay_plan_report(result: PointInTimeUniverseOverlayPlanResult) -> str:
    lines = [
        f"# Point-in-Time Universe Overlay Plan: {result.overlay_plan_id}",
        "",
        SAFETY_STATEMENT,
        "This is a plan/template-only artifact. It does not claim any generated row is point-in-time valid until manual review is completed.",
        "",
        "## Summary",
        "",
        _dict_table(_summary_dict(result)),
        "",
        "## Review Status Counts",
        "",
        _dict_table(result.review_status_counts),
        "",
        "## Plan Rows",
        "",
        _markdown_table(result.plan_frame, OVERLAY_PLAN_COLUMNS),
        "",
        "## Warnings",
        "",
        "\n".join(f"- {warning}" for warning in result.warnings) if result.warnings else "No warnings.",
        "",
    ]
    return "\n".join(str(line) for line in lines)


def build_point_in_time_universe_overlay_plan_metadata(
    result: PointInTimeUniverseOverlayPlanResult,
) -> dict[str, Any]:
    return {
        "overlay_plan_id": result.overlay_plan_id,
        "status": result.status,
        "created_at": "",
        "execution_manifest": str(result.request.execution_manifest),
        "base_universe": str(result.request.base_universe) if result.request.base_universe else "",
        "universe_name": result.request.universe_name,
        "allow_template_include": result.request.allow_template_include,
        "row_count": result.row_count,
        "signal_date_count": result.signal_date_count,
        "symbol_count": result.symbol_count,
        "review_status_counts": result.review_status_counts,
        "survivorship_bias_warning_count": result.survivorship_bias_warning_count,
        "valid_for_signal_date_count": result.valid_for_signal_date_count,
        "warnings": result.warnings,
        "output_files": {
            key: str(value)
            for key, value in result.artifact_paths.items()
            if key != "artifact_dir"
        },
        **result.audit_metadata,
        "known_limitations": [
            "This workflow creates manual-review templates only.",
            "Rows derived from a future universe are not point-in-time valid until independently reviewed.",
            "It does not create snapshot manifests.",
            "It does not run current-candidates or compute forward-return labels.",
        ],
    }


def generate_point_in_time_universe_overlay_plan_id(
    request: PointInTimeUniverseOverlayPlanRequest,
    manifest_frame: pd.DataFrame,
    settings: PointInTimeUniverseOverlayPlanSettings,
) -> str:
    payload = {
        "execution_manifest": str(request.execution_manifest),
        "execution_manifest_digest": _frame_digest(manifest_frame),
        "base_universe": str(request.base_universe) if request.base_universe else "",
        "universe_name": request.universe_name,
        "allow_template_include": request.allow_template_include,
        "config_version": settings.config_version,
    }
    return _hash_payload(payload, length=12)


def resolve_point_in_time_universe_overlay_plan_paths(
    output_dir: str | Path,
    overlay_plan_id: str,
) -> PointInTimeUniverseOverlayPlanArtifactPaths:
    artifact_dir = Path(output_dir) / overlay_plan_id
    return PointInTimeUniverseOverlayPlanArtifactPaths(
        artifact_dir=artifact_dir,
        overlay_plan_csv=artifact_dir / "point_in_time_universe_overlay_plan.csv",
        overlay_template_csv=artifact_dir / "point_in_time_universe_overlay_template.csv",
        report=artifact_dir / "point_in_time_universe_overlay_plan_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def _build_overlay_rows(
    overlay_plan_id: str,
    request: PointInTimeUniverseOverlayPlanRequest,
    manifest_frame: pd.DataFrame,
    plan_symbols_by_date: dict[str, list[str]],
) -> list[PointInTimeUniverseOverlayPlanRow]:
    blocked = manifest_frame.loc[
        manifest_frame["readiness_status"].map(_text).str.upper() == "BLOCKED_UNIVERSE_AS_OF"
    ].copy()
    rows: list[PointInTimeUniverseOverlayPlanRow] = []
    for _, manifest_row in blocked.iterrows():
        base_path = _resolve_base_universe_path(request.base_universe, manifest_row.to_dict())
        if base_path is None or not base_path.exists():
            continue
        base_frame = _load_base_universe(base_path)
        candidate_symbols = _candidate_symbols(manifest_row.to_dict(), base_frame, plan_symbols_by_date)
        scoped = _latest_universe_rows_by_symbol(base_frame, candidate_symbols)
        for _, universe_row in scoped.iterrows():
            rows.append(
                _overlay_row_from_universe_row(
                    overlay_plan_id,
                    request,
                    manifest_row.to_dict(),
                    universe_row.to_dict(),
                    base_path,
                )
            )
    return rows


def _overlay_row_from_universe_row(
    overlay_plan_id: str,
    request: PointInTimeUniverseOverlayPlanRequest,
    manifest_row: dict[str, Any],
    universe_row: dict[str, Any],
    base_path: Path,
) -> PointInTimeUniverseOverlayPlanRow:
    signal_date = _date_text(manifest_row.get("signal_date"))
    base_as_of_date = _date_text(universe_row.get("as_of_date"))
    base_available_time = _datetime_text(universe_row.get("available_time"))
    survivorship_warning = _is_future_universe(signal_date, base_as_of_date, base_available_time)
    future_reason = (
        "Base universe is later than the signal date; manual point-in-time review is required before inclusion."
        if survivorship_warning
        else "Manual point-in-time review is required before inclusion."
    )
    blocker_parts = [future_reason, "Template row is not reviewed and is not valid for execution."]
    manifest_blocker = _text(manifest_row.get("blocker_reason"))
    if manifest_blocker:
        blocker_parts.insert(0, manifest_blocker)
    return PointInTimeUniverseOverlayPlanRow(
        overlay_plan_id=overlay_plan_id,
        signal_date=signal_date,
        symbol=normalize_symbol_value(universe_row.get("symbol")),
        universe_name=request.universe_name or _text(manifest_row.get("universe")),
        proposed_as_of_date=signal_date,
        proposed_available_time=f"{signal_date} 08:00:00" if signal_date else "",
        base_universe_path=str(base_path),
        base_universe_as_of_date=base_as_of_date,
        base_universe_available_time=base_available_time,
        include_flag=True if request.allow_template_include else "",
        review_status="NEEDS_MANUAL_REVIEW",
        review_reason=future_reason,
        source=_text(universe_row.get("source")) or _text(manifest_row.get("recommended_source_filter")),
        upstream_source=_text(universe_row.get("upstream_source")) or _text(
            manifest_row.get("recommended_upstream_filter")
        ),
        survivorship_bias_warning=survivorship_warning,
        manual_review_required=True,
        valid_for_signal_date=False,
        blocker_reason=" ".join(blocker_parts),
    )


def _load_base_universe(path: Path) -> pd.DataFrame:
    frame = read_csv_preserve_symbol_columns(path, keep_default_na=False)
    if "symbol" not in frame.columns:
        raise ValueError(f"Base universe missing symbol column: {path}")
    frame = frame.copy()
    frame["symbol"] = frame["symbol"].map(normalize_symbol_value)
    return frame


def _candidate_symbols(
    manifest_row: dict[str, Any],
    base_frame: pd.DataFrame,
    plan_symbols_by_date: dict[str, list[str]],
) -> list[str]:
    signal_date = _date_text(manifest_row.get("signal_date"))
    if signal_date in plan_symbols_by_date and plan_symbols_by_date[signal_date]:
        return plan_symbols_by_date[signal_date]
    for column in ["symbols", "planned_symbols"]:
        symbols = _split_symbols(manifest_row.get(column))
        if symbols:
            return symbols
    market_path = _path_or_none(manifest_row.get("market_dataset_path"))
    if market_path is not None and market_path.exists():
        try:
            market = read_csv_preserve_symbol_columns(market_path, keep_default_na=False)
        except Exception:
            market = pd.DataFrame()
        if {"symbol", "trade_date"}.issubset(market.columns):
            market = market.copy()
            market["symbol"] = market["symbol"].map(normalize_symbol_value)
            market_dates = pd.to_datetime(market["trade_date"], errors="coerce").dt.strftime("%Y-%m-%d")
            scoped = market.loc[market_dates == _date_text(manifest_row.get("signal_date"))]
            symbols = sorted({symbol for symbol in scoped["symbol"].tolist() if symbol})
            if symbols:
                return symbols
    return sorted({symbol for symbol in base_frame["symbol"].tolist() if symbol})


def _load_plan_symbols_by_signal_date(execution_manifest_path: Path) -> dict[str, list[str]]:
    metadata_path = execution_manifest_path.parent / "metadata.json"
    if not metadata_path.exists():
        return {}
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    plan_path = _path_or_none(metadata.get("plan"))
    if plan_path is None or not plan_path.exists():
        return {}
    try:
        plan_frame = read_csv_preserve_symbol_columns(plan_path, keep_default_na=False)
    except Exception:
        return {}
    if "signal_date" not in plan_frame or "symbols" not in plan_frame:
        return {}
    by_date: dict[str, list[str]] = {}
    for _, row in plan_frame.iterrows():
        signal_date = _date_text(row.get("signal_date"))
        symbols = _split_symbols(row.get("symbols"))
        if signal_date and symbols:
            by_date[signal_date] = symbols
    return by_date


def _resolve_base_universe_path(explicit_base: Path | None, manifest_row: dict[str, Any]) -> Path | None:
    if explicit_base is not None:
        return explicit_base
    local_overlay = _latest_local_universe_overlay()
    if local_overlay is not None:
        return local_overlay
    return _path_or_none(manifest_row.get("universe_dataset_path"))


def _latest_local_universe_overlay() -> Path | None:
    root = Path("data/raw/LOCAL_CSV/universe_overlay")
    if not root.exists():
        return None
    candidates = [path for path in root.rglob("raw_data.csv") if path.is_file()]
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: (path.stat().st_mtime, str(path)))[-1]


def _latest_universe_rows_by_symbol(base_frame: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    scoped = base_frame.loc[base_frame["symbol"].isin(symbols)].copy() if symbols else base_frame.copy()
    if scoped.empty:
        return scoped
    for column in ["as_of_date", "available_time", "revision_id"]:
        if column not in scoped.columns:
            scoped[column] = ""
    scoped["_as_of_sort"] = pd.to_datetime(scoped["as_of_date"], errors="coerce")
    scoped["_available_sort"] = pd.to_datetime(scoped["available_time"], errors="coerce")
    scoped["_revision_sort"] = scoped["revision_id"].map(_text)
    scoped = scoped.sort_values(["symbol", "_as_of_sort", "_available_sort", "_revision_sort"])
    latest = scoped.groupby("symbol", as_index=False, sort=True).tail(1)
    return latest.drop(columns=["_as_of_sort", "_available_sort", "_revision_sort"]).sort_values("symbol")


def _is_future_universe(signal_date: str, base_as_of_date: str, base_available_time: str) -> bool:
    signal = pd.Timestamp(signal_date).normalize() if signal_date else pd.NaT
    decision_time = signal + pd.Timedelta(hours=15, minutes=30) if not pd.isna(signal) else pd.NaT
    as_of = pd.to_datetime(base_as_of_date, errors="coerce")
    available = pd.to_datetime(base_available_time, errors="coerce")
    if pd.isna(signal) or pd.isna(as_of) or pd.isna(available):
        return True
    return bool(as_of.normalize() > signal or available > decision_time)


def _build_warnings(
    request: PointInTimeUniverseOverlayPlanRequest,
    manifest_frame: pd.DataFrame,
    plan_frame: pd.DataFrame,
) -> list[str]:
    blocked_count = int(
        (
            manifest_frame["readiness_status"].map(_text).str.upper()
            == "BLOCKED_UNIVERSE_AS_OF"
        ).sum()
    )
    warnings = [
        "Plan/template-only artifact: no point-in-time universe was approved.",
        "Current-candidates were not generated.",
        "Snapshot manifests were not built.",
        "Forward-return labels were not computed.",
    ]
    if blocked_count == 0:
        warnings.append("No BLOCKED_UNIVERSE_AS_OF rows were found in the execution manifest.")
    if plan_frame.empty:
        warnings.append("No overlay template rows were generated.")
    if _true_count(plan_frame, "survivorship_bias_warning") > 0:
        warnings.append("Rows derived from a future universe carry survivorship-bias warnings.")
    if request.allow_template_include:
        warnings.append("Template include flags were prefilled by explicit request; rows still require manual review.")
    return warnings


def _audit_metadata(
    request: PointInTimeUniverseOverlayPlanRequest,
    settings: PointInTimeUniverseOverlayPlanSettings,
) -> dict[str, Any]:
    return {
        "plan_only": True,
        "current_candidates_executed": False,
        "data_pipeline_executed": False,
        "snapshot_manifest_built": False,
        "snapshot_manifests_built": False,
        "forward_returns_computed": False,
        "cache_mutated": False,
        "network_api_called": False,
        "external_api_called": False,
        "llm_api_called": False,
        "reviewed_execution_required": True,
        "requires_manual_review": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "order_placement_enabled": False,
        "message_sent": False,
        "message_delivery_enabled": False,
        "approved_for_paper_applied": False,
        "output_dir": str(settings.output_dir),
        "config_version": settings.config_version,
    }


def _summary_dict(result: PointInTimeUniverseOverlayPlanResult) -> dict[str, Any]:
    return {
        "overlay_plan_id": result.overlay_plan_id,
        "status": result.status,
        "execution_manifest": result.request.execution_manifest,
        "base_universe": result.request.base_universe or "",
        "row_count": result.row_count,
        "signal_date_count": result.signal_date_count,
        "symbol_count": result.symbol_count,
        "survivorship_bias_warning_count": result.survivorship_bias_warning_count,
        "valid_for_signal_date_count": result.valid_for_signal_date_count,
        "overlay_plan_csv": result.artifact_paths["overlay_plan_csv"],
        "overlay_template_csv": result.artifact_paths["overlay_template_csv"],
    }


def _assert_settings_safe(settings: PointInTimeUniverseOverlayPlanSettings) -> None:
    if settings.enable_live_trading:
        raise ValueError("PIT universe overlay plan cannot enable live trading.")
    if settings.enable_broker_api:
        raise ValueError("PIT universe overlay plan cannot enable broker API access.")
    if settings.enable_order_placement:
        raise ValueError("PIT universe overlay plan cannot enable order placement.")
    if settings.enable_message_delivery:
        raise ValueError("PIT universe overlay plan cannot enable message delivery.")
    if settings.enable_external_api:
        raise ValueError("PIT universe overlay plan cannot enable external API calls.")
    if settings.enable_llm_api:
        raise ValueError("PIT universe overlay plan cannot enable LLM API calls.")


def _frame_digest(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "empty"
    return hashlib.sha256(frame.astype(str).to_csv(index=False).encode("utf-8")).hexdigest()


def _hash_payload(payload: dict[str, Any], *, length: int = 12) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def _date_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return ""
    return str(pd.Timestamp(timestamp).normalize().date())


def _datetime_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return ""
    return pd.Timestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def _text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    if text.lower() in {"nan", "nat", "none", "null"}:
        return ""
    return text


def _split_symbols(value: Any) -> list[str]:
    text = _text(value)
    if not text:
        return []
    tokens = [token.strip() for token in text.replace(",", ";").split(";")]
    return sorted({normalize_symbol_value(token) for token in tokens if normalize_symbol_value(token)})


def _path_or_none(value: Any) -> Path | None:
    text = _text(value)
    return Path(text) if text else None


def _nunique(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame:
        return 0
    return int(frame[column].nunique())


def _value_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if frame.empty or column not in frame:
        return {}
    return {
        str(value): int(count)
        for value, count in frame[column].value_counts().sort_index().items()
    }


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame:
        return 0
    return int(sum(_bool_from_value(value) for value in frame[column]))


def _bool_from_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    return str(value).strip().lower() in {"true", "1", "yes", "y", "pass", "ready"}


def _dict_table(values: dict[str, Any]) -> str:
    if not values:
        return "No data."
    return "\n".join(f"- {key}: {value}" for key, value in values.items())


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "No rows."
    available = [column for column in columns if column in frame.columns]
    if not available:
        return "No columns."
    return frame[available].to_markdown(index=False)


_BOOLEAN_COLUMNS = [
    "survivorship_bias_warning",
    "manual_review_required",
    "valid_for_signal_date",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "plan_only",
]
