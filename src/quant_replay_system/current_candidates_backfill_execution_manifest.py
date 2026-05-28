"""Manifest-only readiness checks for reviewed current-candidates backfill execution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.data import normalize_symbol_value, read_csv_preserve_symbol_columns
from quant_replay_system.snapshot_quality_gate import load_snapshot_manifest


MANIFEST_COLUMNS = [
    "execution_manifest_id",
    "plan_id",
    "signal_date",
    "universe",
    "selection_profile",
    "plan_status",
    "warmup_available",
    "candidate_generation_feasible",
    "forward_1d_available",
    "forward_3d_available",
    "forward_5d_available",
    "forward_10d_available",
    "required_snapshot_manifest_path",
    "snapshot_manifest_found",
    "snapshot_quality_status",
    "market_dataset_path",
    "universe_dataset_path",
    "universe_as_of_date",
    "universe_valid_for_signal_date",
    "trading_calendar_path",
    "source_policy",
    "recommended_source_filter",
    "recommended_upstream_filter",
    "readiness_status",
    "blocker_reason",
    "reviewed_execution_required",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "plan_only",
]

READINESS_STATUSES = {
    "READY_FOR_REVIEW",
    "BLOCKED_MISSING_SNAPSHOT",
    "BLOCKED_SNAPSHOT_QUALITY",
    "BLOCKED_UNIVERSE_AS_OF",
    "BLOCKED_PLAN_INFEASIBLE",
    "BLOCKED_MISSING_INPUT",
    "REVIEW_REQUIRED",
}

SAFETY_STATEMENT = (
    "No current-candidates generation, snapshot build, forward labels, live trading, broker API, "
    "order placement, message delivery, or network/API call was invoked."
)


@dataclass(frozen=True)
class CurrentCandidatesBackfillExecutionManifestSettings:
    output_dir: Path = Path("outputs/reports/current_candidates_backfill_execution_manifest")
    config_version: str = "v0.1"
    write_artifacts: bool = True
    enable_live_trading: bool = False
    enable_broker_api: bool = False
    enable_order_placement: bool = False
    enable_message_delivery: bool = False


@dataclass(frozen=True)
class CurrentCandidatesBackfillExecutionManifestRequest:
    plan: Path
    snapshot_root: Path
    snapshot_quality_root: Path
    universe_root: Path
    selection_profile: str | None


@dataclass(frozen=True)
class CurrentCandidatesBackfillExecutionManifestRow:
    execution_manifest_id: str
    plan_id: str
    signal_date: str
    universe: str
    selection_profile: str
    plan_status: str
    warmup_available: bool
    candidate_generation_feasible: bool
    forward_1d_available: bool
    forward_3d_available: bool
    forward_5d_available: bool
    forward_10d_available: bool
    required_snapshot_manifest_path: str
    snapshot_manifest_found: bool
    snapshot_quality_status: str
    market_dataset_path: str
    universe_dataset_path: str
    universe_as_of_date: str
    universe_valid_for_signal_date: bool
    trading_calendar_path: str
    source_policy: str
    recommended_source_filter: str
    recommended_upstream_filter: str
    readiness_status: str
    blocker_reason: str
    reviewed_execution_required: bool = True
    no_live_trading: bool = True
    no_broker_api: bool = True
    no_order_placement: bool = True
    no_message_sent: bool = True
    plan_only: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "execution_manifest_id": self.execution_manifest_id,
            "plan_id": self.plan_id,
            "signal_date": self.signal_date,
            "universe": self.universe,
            "selection_profile": self.selection_profile,
            "plan_status": self.plan_status,
            "warmup_available": self.warmup_available,
            "candidate_generation_feasible": self.candidate_generation_feasible,
            "forward_1d_available": self.forward_1d_available,
            "forward_3d_available": self.forward_3d_available,
            "forward_5d_available": self.forward_5d_available,
            "forward_10d_available": self.forward_10d_available,
            "required_snapshot_manifest_path": self.required_snapshot_manifest_path,
            "snapshot_manifest_found": self.snapshot_manifest_found,
            "snapshot_quality_status": self.snapshot_quality_status,
            "market_dataset_path": self.market_dataset_path,
            "universe_dataset_path": self.universe_dataset_path,
            "universe_as_of_date": self.universe_as_of_date,
            "universe_valid_for_signal_date": self.universe_valid_for_signal_date,
            "trading_calendar_path": self.trading_calendar_path,
            "source_policy": self.source_policy,
            "recommended_source_filter": self.recommended_source_filter,
            "recommended_upstream_filter": self.recommended_upstream_filter,
            "readiness_status": self.readiness_status,
            "blocker_reason": self.blocker_reason,
            "reviewed_execution_required": self.reviewed_execution_required,
            "no_live_trading": self.no_live_trading,
            "no_broker_api": self.no_broker_api,
            "no_order_placement": self.no_order_placement,
            "no_message_sent": self.no_message_sent,
            "plan_only": self.plan_only,
        }


@dataclass(frozen=True)
class CurrentCandidatesBackfillExecutionManifestArtifactPaths:
    artifact_dir: Path
    execution_manifest_csv: Path
    report: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "execution_manifest_csv": self.execution_manifest_csv,
            "report": self.report,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CurrentCandidatesBackfillExecutionManifestResult:
    execution_manifest_id: str
    status: str
    request: CurrentCandidatesBackfillExecutionManifestRequest
    row_count: int
    ready_count: int
    blocked_count: int
    readiness_counts: dict[str, int]
    manifest_frame: pd.DataFrame
    warnings: list[str]
    artifact_paths: dict[str, Path]
    audit_metadata: dict[str, Any]


@dataclass(frozen=True)
class _SnapshotCandidate:
    snapshot_id: str
    manifest_path: Path
    market_dataset_path: str
    universe_dataset_path: str
    trading_calendar_path: str
    snapshot_quality_status: str


def load_backfill_plan_for_execution(plan: str | Path) -> pd.DataFrame:
    """Load a backfill plan CSV while preserving symbol-like text fields."""

    plan_path = Path(plan)
    if not plan_path.exists():
        raise FileNotFoundError(f"Current-candidates backfill plan not found: {plan_path}")
    frame = read_csv_preserve_symbol_columns(plan_path, keep_default_na=False)
    required = {
        "plan_id",
        "signal_date",
        "universe",
        "selection_profile",
        "status",
        "warmup_available",
        "candidate_generation_feasible",
        "forward_1d_available",
        "forward_3d_available",
        "forward_5d_available",
        "forward_10d_available",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Backfill plan missing required columns: {', '.join(missing)}")
    return frame


def build_current_candidates_backfill_execution_manifest(
    *,
    plan: str | Path,
    snapshot_root: str | Path = "outputs/reports/data_pipeline",
    snapshot_quality_root: str | Path = "outputs/reports/snapshot_quality",
    universe_root: str | Path = "data/raw/LOCAL_CSV/universe_overlay",
    selection_profile: str | None = None,
    output_dir: str | Path | None = None,
    settings: CurrentCandidatesBackfillExecutionManifestSettings | None = None,
) -> CurrentCandidatesBackfillExecutionManifestResult:
    """Build a reviewed execution readiness manifest from a warmup-aware plan."""

    resolved_settings = settings or CurrentCandidatesBackfillExecutionManifestSettings()
    if output_dir is not None:
        resolved_settings = CurrentCandidatesBackfillExecutionManifestSettings(
            output_dir=Path(output_dir),
            config_version=resolved_settings.config_version,
            write_artifacts=resolved_settings.write_artifacts,
            enable_live_trading=resolved_settings.enable_live_trading,
            enable_broker_api=resolved_settings.enable_broker_api,
            enable_order_placement=resolved_settings.enable_order_placement,
            enable_message_delivery=resolved_settings.enable_message_delivery,
        )
    _assert_settings_safe(resolved_settings)

    request = CurrentCandidatesBackfillExecutionManifestRequest(
        plan=Path(plan),
        snapshot_root=Path(snapshot_root),
        snapshot_quality_root=Path(snapshot_quality_root),
        universe_root=Path(universe_root),
        selection_profile=str(selection_profile).strip() if selection_profile else None,
    )
    plan_frame = load_backfill_plan_for_execution(request.plan)
    snapshots = _load_snapshot_candidates(request.snapshot_root, request.snapshot_quality_root)
    execution_manifest_id = generate_current_candidates_backfill_execution_manifest_id(
        request,
        plan_frame,
        snapshots,
        resolved_settings,
    )
    rows = [
        evaluate_signal_date_execution_readiness(
            row.to_dict(),
            execution_manifest_id=execution_manifest_id,
            snapshots=snapshots,
            selection_profile_override=request.selection_profile,
        ).as_dict()
        for _, row in plan_frame.iterrows()
    ]
    manifest_frame = build_current_candidates_backfill_execution_manifest_table(rows)
    readiness_counts = _readiness_counts(manifest_frame)
    ready_count = int(readiness_counts.get("READY_FOR_REVIEW", 0))
    blocked_count = int(sum(value for key, value in readiness_counts.items() if key.startswith("BLOCKED_")))
    status = "PASS" if rows and blocked_count == 0 else "WARN"
    warnings = _build_warnings(rows, snapshots)
    paths = resolve_current_candidates_backfill_execution_manifest_paths(
        resolved_settings.output_dir,
        execution_manifest_id,
    )
    result = CurrentCandidatesBackfillExecutionManifestResult(
        execution_manifest_id=execution_manifest_id,
        status=status,
        request=request,
        row_count=len(rows),
        ready_count=ready_count,
        blocked_count=blocked_count,
        readiness_counts=readiness_counts,
        manifest_frame=manifest_frame,
        warnings=warnings,
        artifact_paths=paths.as_dict(),
        audit_metadata=_audit_metadata(request, snapshots, resolved_settings),
    )
    if resolved_settings.write_artifacts:
        write_current_candidates_backfill_execution_manifest_artifacts(result)
    return result


def evaluate_signal_date_execution_readiness(
    plan_row: dict[str, Any],
    *,
    execution_manifest_id: str,
    snapshots: list[_SnapshotCandidate],
    selection_profile_override: str | None = None,
) -> CurrentCandidatesBackfillExecutionManifestRow:
    """Evaluate one planned signal date without executing candidate generation."""

    snapshot = snapshots[0] if snapshots else None
    base = _base_row_fields(plan_row, execution_manifest_id, snapshot, selection_profile_override)
    plan_blocker = _plan_feasibility_blocker(plan_row)
    if plan_blocker:
        return CurrentCandidatesBackfillExecutionManifestRow(
            **base,
            readiness_status="BLOCKED_PLAN_INFEASIBLE",
            blocker_reason=plan_blocker,
        )
    if snapshot is None:
        return CurrentCandidatesBackfillExecutionManifestRow(
            **base,
            readiness_status="BLOCKED_MISSING_SNAPSHOT",
            blocker_reason="No snapshot_manifest.json was found under the configured snapshot root.",
        )
    if snapshot.snapshot_quality_status != "PASS":
        return CurrentCandidatesBackfillExecutionManifestRow(
            **base,
            readiness_status="BLOCKED_SNAPSHOT_QUALITY",
            blocker_reason=f"snapshot_quality_status={snapshot.snapshot_quality_status or 'MISSING'} is not PASS.",
        )
    input_blocker = _missing_input_blocker(snapshot)
    if input_blocker:
        return CurrentCandidatesBackfillExecutionManifestRow(
            **base,
            readiness_status="BLOCKED_MISSING_INPUT",
            blocker_reason=input_blocker,
        )

    universe_check = _evaluate_universe_validity(plan_row, snapshot)
    base["universe_as_of_date"] = universe_check["universe_as_of_date"]
    base["universe_valid_for_signal_date"] = bool(universe_check["universe_valid_for_signal_date"])
    if not universe_check["universe_valid_for_signal_date"]:
        return CurrentCandidatesBackfillExecutionManifestRow(
            **base,
            readiness_status="BLOCKED_UNIVERSE_AS_OF",
            blocker_reason=str(universe_check["reason"]),
        )

    data_blocker = _market_or_calendar_blocker(plan_row, snapshot)
    if data_blocker:
        return CurrentCandidatesBackfillExecutionManifestRow(
            **base,
            readiness_status="BLOCKED_MISSING_INPUT",
            blocker_reason=data_blocker,
        )

    return CurrentCandidatesBackfillExecutionManifestRow(
        **base,
        readiness_status="READY_FOR_REVIEW",
        blocker_reason="",
    )


def build_current_candidates_backfill_execution_manifest_table(rows: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=MANIFEST_COLUMNS)
    for column in _BOOLEAN_COLUMNS:
        if column in frame:
            frame[column] = frame[column].astype(object)
    return frame


def write_current_candidates_backfill_execution_manifest_artifacts(
    result: CurrentCandidatesBackfillExecutionManifestResult,
) -> dict[str, Path]:
    """Write manifest CSV, markdown report, and metadata."""

    paths = CurrentCandidatesBackfillExecutionManifestArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.manifest_frame.to_csv(paths.execution_manifest_csv, index=False)
    paths.metadata.write_text(
        json.dumps(
            _json_safe(build_current_candidates_backfill_execution_manifest_metadata(result)),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    paths.report.write_text(render_current_candidates_backfill_execution_manifest_report(result), encoding="utf-8")
    return paths.as_dict()


def render_current_candidates_backfill_execution_manifest_report(
    result: CurrentCandidatesBackfillExecutionManifestResult,
) -> str:
    lines = [
        f"# Current-Candidates Backfill Execution Manifest: {result.execution_manifest_id}",
        "",
        SAFETY_STATEMENT,
        "This is a manifest-only readiness artifact. It does not run current-candidates, build snapshot manifests, run data-pipeline, or compute forward returns.",
        "",
        "## Summary",
        "",
        _dict_table(_summary_dict(result)),
        "",
        "## Readiness Counts",
        "",
        _dict_table(result.readiness_counts),
        "",
        "## Manifest Rows",
        "",
        _markdown_table(result.manifest_frame, MANIFEST_COLUMNS),
        "",
        "## Warnings",
        "",
        "\n".join(f"- {warning}" for warning in result.warnings) if result.warnings else "No warnings.",
        "",
    ]
    return "\n".join(str(line) for line in lines)


def build_current_candidates_backfill_execution_manifest_metadata(
    result: CurrentCandidatesBackfillExecutionManifestResult,
) -> dict[str, Any]:
    return {
        "execution_manifest_id": result.execution_manifest_id,
        "status": result.status,
        "created_at": "",
        "plan": str(result.request.plan),
        "snapshot_root": str(result.request.snapshot_root),
        "snapshot_quality_root": str(result.request.snapshot_quality_root),
        "universe_root": str(result.request.universe_root),
        "selection_profile": result.request.selection_profile or "",
        "row_count": result.row_count,
        "ready_count": result.ready_count,
        "blocked_count": result.blocked_count,
        "readiness_counts": result.readiness_counts,
        "warnings": result.warnings,
        "output_files": {
            key: str(value)
            for key, value in result.artifact_paths.items()
            if key != "artifact_dir"
        },
        **result.audit_metadata,
        "known_limitations": [
            "This manifest checks readiness only and does not generate current-candidates.",
            "It does not build missing snapshot manifests or universe overlays.",
            "It does not compute forward-return labels.",
            "READY_FOR_REVIEW still requires human review before any later execution step.",
        ],
    }


def generate_current_candidates_backfill_execution_manifest_id(
    request: CurrentCandidatesBackfillExecutionManifestRequest,
    plan_frame: pd.DataFrame,
    snapshots: list[_SnapshotCandidate],
    settings: CurrentCandidatesBackfillExecutionManifestSettings,
) -> str:
    payload = {
        "plan": str(request.plan),
        "plan_digest": _frame_digest(plan_frame),
        "snapshot_root": str(request.snapshot_root),
        "snapshot_quality_root": str(request.snapshot_quality_root),
        "snapshot_inventory": [
            {
                "snapshot_id": snapshot.snapshot_id,
                "manifest_path": str(snapshot.manifest_path),
                "snapshot_quality_status": snapshot.snapshot_quality_status,
            }
            for snapshot in snapshots
        ],
        "selection_profile": request.selection_profile or "",
        "config_version": settings.config_version,
    }
    return _hash_payload(payload, length=12)


def resolve_current_candidates_backfill_execution_manifest_paths(
    output_dir: str | Path,
    execution_manifest_id: str,
) -> CurrentCandidatesBackfillExecutionManifestArtifactPaths:
    artifact_dir = Path(output_dir) / execution_manifest_id
    return CurrentCandidatesBackfillExecutionManifestArtifactPaths(
        artifact_dir=artifact_dir,
        execution_manifest_csv=artifact_dir / "current_candidates_backfill_execution_manifest.csv",
        report=artifact_dir / "current_candidates_backfill_execution_manifest_report.md",
        metadata=artifact_dir / "metadata.json",
    )


def _base_row_fields(
    plan_row: dict[str, Any],
    execution_manifest_id: str,
    snapshot: _SnapshotCandidate | None,
    selection_profile_override: str | None,
) -> dict[str, Any]:
    return {
        "execution_manifest_id": execution_manifest_id,
        "plan_id": _text(plan_row.get("plan_id")),
        "signal_date": _date_text(plan_row.get("signal_date")),
        "universe": _text(plan_row.get("universe")),
        "selection_profile": selection_profile_override or _text(plan_row.get("selection_profile")),
        "plan_status": _text(plan_row.get("status")),
        "warmup_available": _bool_from_value(plan_row.get("warmup_available")),
        "candidate_generation_feasible": _bool_from_value(plan_row.get("candidate_generation_feasible")),
        "forward_1d_available": _bool_from_value(plan_row.get("forward_1d_available")),
        "forward_3d_available": _bool_from_value(plan_row.get("forward_3d_available")),
        "forward_5d_available": _bool_from_value(plan_row.get("forward_5d_available")),
        "forward_10d_available": _bool_from_value(plan_row.get("forward_10d_available")),
        "required_snapshot_manifest_path": str(snapshot.manifest_path) if snapshot is not None else "",
        "snapshot_manifest_found": snapshot is not None,
        "snapshot_quality_status": snapshot.snapshot_quality_status if snapshot is not None else "",
        "market_dataset_path": snapshot.market_dataset_path if snapshot is not None else "",
        "universe_dataset_path": snapshot.universe_dataset_path if snapshot is not None else "",
        "universe_as_of_date": "",
        "universe_valid_for_signal_date": False,
        "trading_calendar_path": snapshot.trading_calendar_path if snapshot is not None else "",
        "source_policy": _text(plan_row.get("source_policy")),
        "recommended_source_filter": _text(plan_row.get("recommended_source_filter")),
        "recommended_upstream_filter": _text(plan_row.get("recommended_upstream_filter")),
    }


def _plan_feasibility_blocker(plan_row: dict[str, Any]) -> str:
    blockers = []
    if _text(plan_row.get("status")).upper() not in {"READY", "PASS"}:
        blockers.append(f"plan_status={_text(plan_row.get('status')) or 'MISSING'}")
    for column in [
        "warmup_available",
        "candidate_generation_feasible",
        "forward_1d_available",
        "forward_3d_available",
        "forward_5d_available",
        "forward_10d_available",
    ]:
        if not _bool_from_value(plan_row.get(column)):
            blockers.append(f"{column}=false")
    return "; ".join(blockers)


def _load_snapshot_candidates(snapshot_root: Path, snapshot_quality_root: Path) -> list[_SnapshotCandidate]:
    if not snapshot_root.exists():
        return []
    quality_by_snapshot = _snapshot_quality_statuses(snapshot_quality_root)
    candidates: list[_SnapshotCandidate] = []
    for manifest_path in sorted(snapshot_root.rglob("snapshot_manifest.json")):
        try:
            manifest = load_snapshot_manifest(manifest_path)
        except Exception:
            continue
        dataset_paths = manifest.get("dataset_paths", {})
        if not isinstance(dataset_paths, dict):
            dataset_paths = {}
        snapshot_id = _text(manifest.get("snapshot_id")) or manifest_path.parent.name
        candidates.append(
            _SnapshotCandidate(
                snapshot_id=snapshot_id,
                manifest_path=Path(manifest.get("manifest_path", manifest_path)),
                market_dataset_path=_text(dataset_paths.get("market")),
                universe_dataset_path=_text(dataset_paths.get("universe")),
                trading_calendar_path=_text(dataset_paths.get("trading_calendar")),
                snapshot_quality_status=_text(quality_by_snapshot.get(snapshot_id)),
            )
        )
    return sorted(
        candidates,
        key=lambda item: (
            item.snapshot_quality_status == "PASS",
            item.market_dataset_path != "",
            item.universe_dataset_path != "",
            item.trading_calendar_path != "",
            str(item.manifest_path),
        ),
        reverse=True,
    )


def _snapshot_quality_statuses(snapshot_quality_root: Path) -> dict[str, str]:
    if not snapshot_quality_root.exists():
        return {}
    statuses: dict[str, str] = {}
    for metadata_path in sorted(snapshot_quality_root.rglob("metadata.json")):
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        snapshot_id = _text(metadata.get("snapshot_id"))
        if snapshot_id:
            statuses[snapshot_id] = _text(metadata.get("status")).upper()
    return statuses


def _missing_input_blocker(snapshot: _SnapshotCandidate) -> str:
    missing = []
    for label, value in [
        ("market", snapshot.market_dataset_path),
        ("universe", snapshot.universe_dataset_path),
        ("trading_calendar", snapshot.trading_calendar_path),
    ]:
        if not value:
            missing.append(f"{label}_dataset_path missing")
        elif not Path(value).exists():
            missing.append(f"{label}_dataset_path does not exist: {value}")
    return "; ".join(missing)


def _evaluate_universe_validity(plan_row: dict[str, Any], snapshot: _SnapshotCandidate) -> dict[str, Any]:
    signal_date = _timestamp(plan_row.get("signal_date"))
    decision_time = signal_date + pd.Timedelta(hours=15, minutes=30)
    try:
        universe = read_csv_preserve_symbol_columns(snapshot.universe_dataset_path, keep_default_na=False)
    except Exception as exc:
        return {
            "universe_as_of_date": "",
            "universe_valid_for_signal_date": False,
            "reason": f"Unable to read universe dataset: {exc}",
        }
    if "symbol" in universe:
        universe["symbol"] = universe["symbol"].map(normalize_symbol_value)
    symbols = _planned_symbols(plan_row)
    scoped = universe.loc[universe["symbol"].isin(symbols)].copy() if symbols and "symbol" in universe else universe.copy()
    if scoped.empty:
        return {
            "universe_as_of_date": "",
            "universe_valid_for_signal_date": False,
            "reason": "Universe dataset has no rows for planned symbols.",
        }
    if "as_of_date" not in scoped or "available_time" not in scoped:
        return {
            "universe_as_of_date": "",
            "universe_valid_for_signal_date": False,
            "reason": "Universe dataset is missing as_of_date or available_time.",
        }
    as_of_dates = pd.to_datetime(scoped["as_of_date"], errors="coerce").dt.normalize()
    available_times = pd.to_datetime(scoped["available_time"], errors="coerce")
    universe_as_of = as_of_dates.max()
    if as_of_dates.isna().any() or available_times.isna().any():
        return {
            "universe_as_of_date": _date_text(universe_as_of),
            "universe_valid_for_signal_date": False,
            "reason": "Universe dataset contains invalid as_of_date or available_time values.",
        }
    if (as_of_dates > signal_date).any():
        return {
            "universe_as_of_date": _date_text(universe_as_of),
            "universe_valid_for_signal_date": False,
            "reason": "Universe as_of_date is later than signal date.",
        }
    if (available_times > decision_time).any():
        return {
            "universe_as_of_date": _date_text(universe_as_of),
            "universe_valid_for_signal_date": False,
            "reason": "Universe available_time is later than signal decision time.",
        }
    return {
        "universe_as_of_date": _date_text(universe_as_of),
        "universe_valid_for_signal_date": True,
        "reason": "",
    }


def _market_or_calendar_blocker(plan_row: dict[str, Any], snapshot: _SnapshotCandidate) -> str:
    signal_date = _date_text(plan_row.get("signal_date"))
    symbols = _planned_symbols(plan_row)
    try:
        market = read_csv_preserve_symbol_columns(snapshot.market_dataset_path, keep_default_na=False)
        calendar = read_csv_preserve_symbol_columns(snapshot.trading_calendar_path, keep_default_na=False)
    except Exception as exc:
        return f"Unable to read market or trading calendar dataset: {exc}"
    if "trade_date" not in market or "symbol" not in market:
        return "Market dataset is missing trade_date or symbol."
    market = market.copy()
    market["symbol"] = market["symbol"].map(normalize_symbol_value)
    market["trade_date"] = pd.to_datetime(market["trade_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    date_market = market.loc[market["trade_date"] == signal_date]
    if symbols:
        missing = sorted(set(symbols).difference(set(date_market["symbol"])))
        if missing:
            return f"Market dataset is missing signal-date rows for planned symbols: {', '.join(missing[:5])}"
    if "trade_date" not in calendar:
        return "Trading calendar dataset is missing trade_date."
    calendar_dates = pd.to_datetime(calendar["trade_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    if signal_date not in set(calendar_dates.dropna()):
        return f"Trading calendar is missing signal_date={signal_date}."
    return ""


def _readiness_counts(frame: pd.DataFrame) -> dict[str, int]:
    if frame.empty or "readiness_status" not in frame:
        return {}
    return {
        str(status): int(count)
        for status, count in frame["readiness_status"].value_counts().sort_index().items()
    }


def _build_warnings(rows: list[dict[str, Any]], snapshots: list[_SnapshotCandidate]) -> list[str]:
    warnings = [
        "Manifest-only artifact: current-candidates were not generated.",
        "Snapshot manifests were not built by this command.",
        "Forward-return labels were not computed.",
    ]
    if not snapshots:
        warnings.append("No existing snapshot manifests were found.")
    blocked = [row for row in rows if str(row.get("readiness_status", "")).startswith("BLOCKED_")]
    if blocked:
        warnings.append(f"{len(blocked)} planned signal date rows are blocked before reviewed execution.")
    return warnings


def _audit_metadata(
    request: CurrentCandidatesBackfillExecutionManifestRequest,
    snapshots: list[_SnapshotCandidate],
    settings: CurrentCandidatesBackfillExecutionManifestSettings,
) -> dict[str, Any]:
    return {
        "snapshot_manifest_count": len(snapshots),
        "snapshot_manifests": [str(snapshot.manifest_path) for snapshot in snapshots],
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
        "universe_root": str(request.universe_root),
    }


def _summary_dict(result: CurrentCandidatesBackfillExecutionManifestResult) -> dict[str, Any]:
    return {
        "execution_manifest_id": result.execution_manifest_id,
        "status": result.status,
        "plan": result.request.plan,
        "row_count": result.row_count,
        "ready_count": result.ready_count,
        "blocked_count": result.blocked_count,
        "snapshot_manifest_count": result.audit_metadata.get("snapshot_manifest_count", 0),
        "execution_manifest_csv": result.artifact_paths["execution_manifest_csv"],
    }


def _planned_symbols(plan_row: dict[str, Any]) -> list[str]:
    text = _text(plan_row.get("symbols"))
    if not text:
        return []
    tokens = [token.strip() for token in text.replace(",", ";").split(";")]
    return sorted({normalize_symbol_value(token) for token in tokens if normalize_symbol_value(token)})


def _assert_settings_safe(settings: CurrentCandidatesBackfillExecutionManifestSettings) -> None:
    if settings.enable_live_trading:
        raise ValueError("Current-candidates backfill execution manifest cannot enable live trading.")
    if settings.enable_broker_api:
        raise ValueError("Current-candidates backfill execution manifest cannot enable broker API access.")
    if settings.enable_order_placement:
        raise ValueError("Current-candidates backfill execution manifest cannot enable order placement.")
    if settings.enable_message_delivery:
        raise ValueError("Current-candidates backfill execution manifest cannot enable message delivery.")


def _frame_digest(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "empty"
    encoded = frame.astype(str).to_csv(index=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
    if value is None or pd.isna(value):
        return ""
    return str(pd.Timestamp(value).normalize().date())


def _timestamp(value: Any) -> pd.Timestamp:
    return pd.Timestamp(_date_text(value)).normalize()


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
    "warmup_available",
    "candidate_generation_feasible",
    "forward_1d_available",
    "forward_3d_available",
    "forward_5d_available",
    "forward_10d_available",
    "snapshot_manifest_found",
    "universe_valid_for_signal_date",
    "reviewed_execution_required",
    "no_live_trading",
    "no_broker_api",
    "no_order_placement",
    "no_message_sent",
    "plan_only",
]
