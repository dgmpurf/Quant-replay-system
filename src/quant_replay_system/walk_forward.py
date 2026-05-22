"""Walk-forward validation over parameter calibration results."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from quant_replay_system.calibration import (
    CALIBRATION_LIMITATIONS,
    CalibrationParameterSet,
    CalibrationResult,
    run_parameter_calibration,
)
from quant_replay_system.calendar import TradingCalendar
from quant_replay_system.config import Settings, WalkForwardSettings, load_settings
from quant_replay_system.snapshot_quality_preflight import (
    disable_snapshot_quality_preflight,
    run_snapshot_quality_preflight,
)


WALK_FORWARD_LIMITATIONS = [
    *CALIBRATION_LIMITATIONS,
    "MVP walk-forward validation supports explicit train/validation/test splits.",
    "Rolling-window split generation is not implemented yet.",
    "Diagnostics are simple explainable heuristics, not statistical proof of future robustness.",
]


@dataclass(frozen=True)
class WalkForwardSplit:
    split_name: str
    train_dates: list[pd.Timestamp]
    validation_dates: list[pd.Timestamp]
    test_dates: list[pd.Timestamp]


@dataclass(frozen=True)
class WalkForwardDiagnostics:
    train_objective_score: float | None
    validation_objective_score: float | None
    test_objective_score: float | None
    train_average_return: float | None
    validation_average_return: float | None
    train_portfolio_total_return: float | None
    validation_portfolio_total_return: float | None
    train_max_drawdown: float | None
    validation_max_drawdown: float | None
    objective_decay: float
    return_decay: float
    drawdown_worsening: float
    rank_stability: float | None
    low_trade_count_penalty: float
    overfit_risk_score: float
    overfit_risk_label: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WalkForwardArtifactPaths:
    artifact_dir: Path
    walk_forward_report: Path
    diagnostics: Path
    selected_parameter_set: Path
    train_summary: Path
    validation_summary: Path
    test_summary: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "walk_forward_report": self.walk_forward_report,
            "diagnostics": self.diagnostics,
            "selected_parameter_set": self.selected_parameter_set,
            "train_summary": self.train_summary,
            "validation_summary": self.validation_summary,
            "test_summary": self.test_summary,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class WalkForwardResult:
    walk_forward_id: str
    train_dates: list[pd.Timestamp]
    validation_dates: list[pd.Timestamp]
    test_dates: list[pd.Timestamp]
    train_calibration_result: CalibrationResult
    selected_parameter_set: CalibrationParameterSet | None
    validation_result: CalibrationResult | None
    test_result: CalibrationResult | None
    diagnostics: WalkForwardDiagnostics
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    snapshot_quality_preflight: dict[str, Any] | None = None


def build_walk_forward_splits(
    *,
    train_dates: Iterable[str | pd.Timestamp],
    validation_dates: Iterable[str | pd.Timestamp] | None = None,
    test_dates: Iterable[str | pd.Timestamp] | None = None,
    split_name: str = "explicit",
) -> WalkForwardSplit:
    """Build an explicit train/validation/test split."""

    train = _normalize_date_list(train_dates)
    validation = _normalize_date_list(validation_dates or [])
    test = _normalize_date_list(test_dates or [])
    _ensure_disjoint_dates(train=train, validation=validation, test=test)
    return WalkForwardSplit(
        split_name=split_name,
        train_dates=train,
        validation_dates=validation,
        test_dates=test,
    )


def run_walk_forward_validation(
    *,
    train_dates: Iterable[str | pd.Timestamp],
    validation_dates: Iterable[str | pd.Timestamp] | None = None,
    test_dates: Iterable[str | pd.Timestamp] | None = None,
    universe_name: str = "default",
    parameter_sets: Iterable[CalibrationParameterSet | dict[str, Any]] | None = None,
    config: Settings | str | Path | None = None,
    market_data: pd.DataFrame | None = None,
    universe_snapshot: pd.DataFrame | None = None,
    benchmark_data: pd.DataFrame | None = None,
    corporate_actions: pd.DataFrame | None = None,
    trading_calendar: TradingCalendar | None = None,
    walk_forward_id: str | None = None,
    split_name: str = "explicit",
    snapshot_manifest_path: str | Path | None = None,
) -> WalkForwardResult:
    """Run train calibration, validate selected params, and optionally test them."""

    settings = _load_settings(config)
    preflight = run_snapshot_quality_preflight(
        settings,
        snapshot_manifest_path=snapshot_manifest_path,
        context="run_walk_forward_validation",
    )
    run_settings = disable_snapshot_quality_preflight(settings) if preflight.enabled else settings
    wf_settings = run_settings.walk_forward
    split = build_walk_forward_splits(
        train_dates=train_dates,
        validation_dates=validation_dates,
        test_dates=test_dates,
        split_name=split_name,
    )
    _validate_split_lengths(split, wf_settings)

    parameter_set_list = list(parameter_sets) if parameter_sets is not None else None
    effective_id = walk_forward_id or generate_walk_forward_id(
        universe_name=universe_name,
        split=split,
        parameter_sets=parameter_set_list,
        config_version=wf_settings.config_version,
    )
    paths = resolve_walk_forward_artifact_paths(wf_settings.output_dir, effective_id)
    run_settings = run_settings.model_copy(
        update={
            "calibration": run_settings.calibration.model_copy(update={"output_dir": paths.artifact_dir / "calibrations"})
        }
    )

    train_result = run_parameter_calibration(
        decision_dates=split.train_dates,
        universe_name=universe_name,
        parameter_sets=parameter_set_list,
        config=run_settings,
        market_data=market_data,
        universe_snapshot=universe_snapshot,
        benchmark_data=benchmark_data,
        corporate_actions=corporate_actions,
        trading_calendar=trading_calendar,
        split_name="train",
        train_dates=split.train_dates,
        validation_dates=split.validation_dates,
        test_dates=split.test_dates,
    )
    selected = train_result.best_parameter_set
    warnings = list(preflight.warnings or [])
    warnings.extend(train_result.warnings)

    validation_result: CalibrationResult | None = None
    if selected is not None and split.validation_dates:
        validation_result = run_parameter_calibration(
            decision_dates=split.validation_dates,
            universe_name=universe_name,
            parameter_sets=[selected],
            config=run_settings,
            market_data=market_data,
            universe_snapshot=universe_snapshot,
            benchmark_data=benchmark_data,
            corporate_actions=corporate_actions,
            trading_calendar=trading_calendar,
            split_name="validation",
            train_dates=split.train_dates,
            validation_dates=split.validation_dates,
            test_dates=split.test_dates,
        )
        warnings.extend(f"validation: {warning}" for warning in validation_result.warnings)

    test_result: CalibrationResult | None = None
    if selected is not None and split.test_dates:
        test_result = run_parameter_calibration(
            decision_dates=split.test_dates,
            universe_name=universe_name,
            parameter_sets=[selected],
            config=run_settings,
            market_data=market_data,
            universe_snapshot=universe_snapshot,
            benchmark_data=benchmark_data,
            corporate_actions=corporate_actions,
            trading_calendar=trading_calendar,
            split_name="test",
            train_dates=split.train_dates,
            validation_dates=split.validation_dates,
            test_dates=split.test_dates,
        )
        warnings.extend(f"test: {warning}" for warning in test_result.warnings)

    diagnostics = compute_overfitting_diagnostics(
        train_calibration_result=train_result,
        validation_result=validation_result,
        test_result=test_result,
        selected_parameter_set=selected,
        settings=wf_settings,
        min_trade_count=run_settings.calibration.min_trade_count,
    )

    preflight_metadata = preflight.metadata_fields()
    result = WalkForwardResult(
        walk_forward_id=effective_id,
        train_dates=split.train_dates,
        validation_dates=split.validation_dates,
        test_dates=split.test_dates,
        train_calibration_result=train_result,
        selected_parameter_set=selected,
        validation_result=validation_result,
        test_result=test_result,
        diagnostics=diagnostics,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        known_limitations=WALK_FORWARD_LIMITATIONS,
        snapshot_quality_preflight=preflight_metadata,
    )
    if wf_settings.write_artifacts:
        write_walk_forward_report(result)
    return result


def compute_overfitting_diagnostics(
    *,
    train_calibration_result: Any,
    validation_result: Any | None,
    test_result: Any | None = None,
    selected_parameter_set: CalibrationParameterSet | None = None,
    settings: WalkForwardSettings | dict[str, Any] | None = None,
    min_trade_count: int = 3,
) -> WalkForwardDiagnostics:
    """Compute simple in-sample vs out-of-sample overfitting diagnostics."""

    cfg = _coerce_walk_forward_settings(settings)
    selected_id = (
        selected_parameter_set.parameter_set_id
        if selected_parameter_set is not None
        else _first_parameter_set_id(train_calibration_result)
    )
    train_row = _selected_ranked_row(train_calibration_result, selected_id)
    validation_row = _selected_ranked_row(validation_result, selected_id)
    test_row = _selected_ranked_row(test_result, selected_id)

    train_objective = _row_float(train_row, "ranking_score", "objective_score")
    validation_objective = _row_float(validation_row, "ranking_score", "objective_score")
    test_objective = _row_float(test_row, "ranking_score", "objective_score")

    train_return = _effective_return(train_row)
    validation_return = _effective_return(validation_row)
    train_drawdown = _effective_drawdown(train_row)
    validation_drawdown = _effective_drawdown(validation_row)
    validation_trade_count = _row_float(validation_row, "portfolio_number_of_trades", "total_trades")

    objective_decay = _decay_score(train_objective, validation_objective, floor=1.0)
    return_decay = _decay_score(train_return, validation_return, floor=0.01)
    drawdown_worsening = _drawdown_worsening(train_drawdown, validation_drawdown)
    low_trade_penalty = _low_trade_count_penalty(validation_trade_count, min_trade_count)
    overfit_score = _clip_fraction(
        0.40 * objective_decay
        + 0.25 * return_decay
        + 0.20 * drawdown_worsening
        + 0.15 * low_trade_penalty
    )

    return WalkForwardDiagnostics(
        train_objective_score=train_objective,
        validation_objective_score=validation_objective,
        test_objective_score=test_objective,
        train_average_return=_row_float(train_row, "average_return"),
        validation_average_return=_row_float(validation_row, "average_return"),
        train_portfolio_total_return=_row_float(train_row, "portfolio_total_return"),
        validation_portfolio_total_return=_row_float(validation_row, "portfolio_total_return"),
        train_max_drawdown=train_drawdown,
        validation_max_drawdown=validation_drawdown,
        objective_decay=objective_decay,
        return_decay=return_decay,
        drawdown_worsening=drawdown_worsening,
        rank_stability=None,
        low_trade_count_penalty=low_trade_penalty,
        overfit_risk_score=overfit_score,
        overfit_risk_label=_risk_label(overfit_score, cfg),
    )


def generate_walk_forward_id(
    *,
    universe_name: str,
    split: WalkForwardSplit,
    parameter_sets: Iterable[CalibrationParameterSet | dict[str, Any]] | None,
    config_version: str = "mvp",
) -> str:
    """Generate deterministic walk-forward id from split and parameter candidates."""

    payload = {
        "universe_name": universe_name,
        "split_name": split.split_name,
        "train_dates": split.train_dates,
        "validation_dates": split.validation_dates,
        "test_dates": split.test_dates,
        "parameter_sets": [_parameter_set_payload(item) for item in parameter_sets] if parameter_sets else [],
        "config_version": config_version,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:10]


def resolve_walk_forward_artifact_paths(output_dir: str | Path, walk_forward_id: str) -> WalkForwardArtifactPaths:
    """Resolve stable artifact paths for one walk-forward run."""

    artifact_dir = Path(output_dir) / walk_forward_id
    return WalkForwardArtifactPaths(
        artifact_dir=artifact_dir,
        walk_forward_report=artifact_dir / "walk_forward_report.md",
        diagnostics=artifact_dir / "diagnostics.csv",
        selected_parameter_set=artifact_dir / "selected_parameter_set.json",
        train_summary=artifact_dir / "train_summary.csv",
        validation_summary=artifact_dir / "validation_summary.csv",
        test_summary=artifact_dir / "test_summary.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_walk_forward_report(result: WalkForwardResult, path: str | Path | None = None) -> Path:
    """Write walk-forward report and supporting artifacts."""

    paths = WalkForwardArtifactPaths(**result.artifact_paths)
    if path is not None:
        paths = WalkForwardArtifactPaths(
            artifact_dir=Path(path).parent,
            walk_forward_report=Path(path),
            diagnostics=paths.diagnostics,
            selected_parameter_set=paths.selected_parameter_set,
            train_summary=paths.train_summary,
            validation_summary=paths.validation_summary,
            test_summary=paths.test_summary,
            metadata=paths.metadata,
        )

    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(pd.DataFrame([result.diagnostics.as_dict()]), paths.diagnostics)
    _export_dataframe(_selected_summary_frame(result.train_calibration_result, result.selected_parameter_set), paths.train_summary)
    _export_dataframe(_selected_summary_frame(result.validation_result, result.selected_parameter_set), paths.validation_summary)
    if result.test_dates:
        _export_dataframe(_selected_summary_frame(result.test_result, result.selected_parameter_set), paths.test_summary)

    selected_payload = (
        result.selected_parameter_set.as_dict() if result.selected_parameter_set is not None else {}
    )
    paths.selected_parameter_set.write_text(
        json.dumps(_json_safe(selected_payload), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    metadata = build_walk_forward_metadata(result, paths)
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.walk_forward_report.write_text(render_walk_forward_report(result, paths, metadata), encoding="utf-8")
    return paths.walk_forward_report


def build_walk_forward_metadata(result: WalkForwardResult, paths: WalkForwardArtifactPaths) -> dict[str, Any]:
    """Build metadata.json content for walk-forward validation."""

    output_files = {name: str(path) for name, path in paths.as_dict().items() if name != "artifact_dir"}
    if not result.test_dates:
        output_files.pop("test_summary", None)
    return {
        "walk_forward_id": result.walk_forward_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "train_dates": result.train_dates,
        "validation_dates": result.validation_dates,
        "test_dates": result.test_dates,
        "selected_parameter_set": (
            None if result.selected_parameter_set is None else result.selected_parameter_set.as_dict()
        ),
        "diagnostics": result.diagnostics.as_dict(),
        "output_files": output_files,
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "snapshot_quality_preflight": result.snapshot_quality_preflight or {},
        **(result.snapshot_quality_preflight or {}),
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "contract_note": "Walk-forward validation calls calibration and does not bypass point-in-time or replay contracts.",
    }


def render_walk_forward_report(
    result: WalkForwardResult,
    paths: WalkForwardArtifactPaths,
    metadata: dict[str, Any],
) -> str:
    """Render walk-forward markdown report."""

    selected = result.selected_parameter_set.as_dict() if result.selected_parameter_set is not None else {}
    lines = [
        f"# Walk-Forward Validation Report: {result.walk_forward_id}",
        "",
        "## Walk-Forward Metadata",
        "",
        _dict_table(
            {
                "walk_forward_id": result.walk_forward_id,
                "artifact_dir": paths.artifact_dir,
                "train_dates": len(result.train_dates),
                "validation_dates": len(result.validation_dates),
                "test_dates": len(result.test_dates),
            }
        ),
        "",
        "## Snapshot Quality Preflight",
        "",
        _dict_table(result.snapshot_quality_preflight or {"snapshot_quality_preflight_enabled": False}),
        "",
        "## Date Split Summary",
        "",
        _dict_table(
            {
                "train_dates": result.train_dates,
                "validation_dates": result.validation_dates,
                "test_dates": result.test_dates,
            }
        ),
        "",
        "## Selected Parameter Set",
        "",
        _dict_table(selected) if selected else "_No selected parameter set._",
        "",
        "## Train Performance",
        "",
        _markdown_table(_selected_summary_frame(result.train_calibration_result, result.selected_parameter_set)),
        "",
        "## Validation Performance",
        "",
        _markdown_table(_selected_summary_frame(result.validation_result, result.selected_parameter_set)),
        "",
        "## Test Performance",
        "",
        _markdown_table(_selected_summary_frame(result.test_result, result.selected_parameter_set)) if result.test_dates else "_No test dates supplied._",
        "",
        "## In-Sample vs Out-of-Sample Comparison",
        "",
        _dict_table(
            {
                "train_objective_score": result.diagnostics.train_objective_score,
                "validation_objective_score": result.diagnostics.validation_objective_score,
                "objective_decay": result.diagnostics.objective_decay,
                "return_decay": result.diagnostics.return_decay,
                "drawdown_worsening": result.diagnostics.drawdown_worsening,
            }
        ),
        "",
        "## Overfitting Diagnostics",
        "",
        _dict_table(result.diagnostics.as_dict()),
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


def _validate_split_lengths(split: WalkForwardSplit, settings: WalkForwardSettings) -> None:
    if len(split.train_dates) < settings.min_train_dates:
        raise ValueError(f"train_dates must contain at least {settings.min_train_dates} date(s)")
    if settings.require_validation and len(split.validation_dates) < settings.min_validation_dates:
        raise ValueError(f"validation_dates must contain at least {settings.min_validation_dates} date(s)")
    if settings.require_test and len(split.test_dates) < settings.min_test_dates:
        raise ValueError(f"test_dates must contain at least {settings.min_test_dates} date(s)")


def _selected_summary_frame(result: Any | None, parameter_set: CalibrationParameterSet | None) -> pd.DataFrame:
    if result is None or not hasattr(result, "ranked_results") or result.ranked_results.empty:
        return pd.DataFrame()
    selected_id = parameter_set.parameter_set_id if parameter_set is not None else _first_parameter_set_id(result)
    row = _selected_ranked_row(result, selected_id)
    return pd.DataFrame([row]) if row else pd.DataFrame()


def _selected_ranked_row(result: Any | None, parameter_set_id: str | None) -> dict[str, Any]:
    if result is None or not hasattr(result, "ranked_results"):
        return {}
    frame = result.ranked_results
    if frame is None or frame.empty:
        return {}
    if parameter_set_id is not None and "parameter_set_id" in frame.columns:
        rows = frame.loc[frame["parameter_set_id"] == parameter_set_id]
        if not rows.empty:
            return rows.iloc[0].to_dict()
    return frame.iloc[0].to_dict()


def _first_parameter_set_id(result: Any | None) -> str | None:
    if result is None or not hasattr(result, "ranked_results") or result.ranked_results.empty:
        return None
    return str(result.ranked_results.iloc[0].get("parameter_set_id"))


def _row_float(row: dict[str, Any], *columns: str) -> float | None:
    for column in columns:
        value = row.get(column)
        if value is not None and not pd.isna(value):
            return float(value)
    return None


def _effective_return(row: dict[str, Any]) -> float | None:
    return _row_float(row, "portfolio_total_return", "average_return")


def _effective_drawdown(row: dict[str, Any]) -> float | None:
    return _row_float(row, "portfolio_max_drawdown", "max_drawdown_proxy")


def _decay_score(train_value: float | None, validation_value: float | None, *, floor: float) -> float:
    if train_value is None or validation_value is None:
        return 0.0
    return _clip_fraction(max(0.0, train_value - validation_value) / max(abs(train_value), floor))


def _drawdown_worsening(train_drawdown: float | None, validation_drawdown: float | None) -> float:
    if train_drawdown is None or validation_drawdown is None:
        return 0.0
    train_abs = abs(min(0.0, float(train_drawdown)))
    validation_abs = abs(min(0.0, float(validation_drawdown)))
    return _clip_fraction(max(0.0, validation_abs - train_abs) / max(train_abs, 0.01))


def _low_trade_count_penalty(trade_count: float | None, minimum_trade_count: int) -> float:
    if minimum_trade_count <= 0:
        return 0.0
    count = 0 if trade_count is None or pd.isna(trade_count) else int(trade_count)
    if count >= minimum_trade_count:
        return 0.0
    return _clip_fraction((minimum_trade_count - count) / minimum_trade_count)


def _risk_label(score: float, settings: WalkForwardSettings) -> str:
    if score >= settings.severe_overfit_threshold:
        return "SEVERE"
    if score >= settings.overfit_warning_threshold:
        return "HIGH"
    if score >= settings.overfit_warning_threshold / 2.0:
        return "MEDIUM"
    return "LOW"


def _clip_fraction(value: Any) -> float:
    if value is None or pd.isna(value):
        return 0.0
    return float(np.clip(float(value), 0.0, 1.0))


def _parameter_set_payload(value: CalibrationParameterSet | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, CalibrationParameterSet):
        return value.as_dict()
    return dict(value)


def _ensure_disjoint_dates(
    *,
    train: list[pd.Timestamp],
    validation: list[pd.Timestamp],
    test: list[pd.Timestamp],
) -> None:
    named_sets = {
        "train": set(train),
        "validation": set(validation),
        "test": set(test),
    }
    overlaps = [
        f"{left}/{right}"
        for left, left_values in named_sets.items()
        for right, right_values in named_sets.items()
        if left < right and left_values.intersection(right_values)
    ]
    if overlaps:
        raise ValueError(f"Walk-forward date splits must be disjoint; overlaps: {overlaps}")


def _normalize_date_list(values: Iterable[str | pd.Timestamp]) -> list[pd.Timestamp]:
    return [_normalize_date(value) for value in values]


def _normalize_date(value: str | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_localize(None)
    return timestamp.normalize()


def _load_settings(config: Settings | str | Path | None) -> Settings:
    if config is None:
        return load_settings(Path("config/default.yaml"))
    if isinstance(config, Settings):
        return config
    return load_settings(Path(config))


def _coerce_walk_forward_settings(settings: WalkForwardSettings | dict[str, Any] | None) -> WalkForwardSettings:
    if settings is None:
        return WalkForwardSettings()
    if isinstance(settings, WalkForwardSettings):
        return settings
    if isinstance(settings, dict):
        return WalkForwardSettings(**settings)
    if hasattr(settings, "model_dump"):
        return WalkForwardSettings(**settings.model_dump())
    raise TypeError("settings must be WalkForwardSettings, dict, or None")


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


def _markdown_table(frame: pd.DataFrame, max_rows: int = 50) -> str:
    if frame.empty:
        return "_No rows._"
    table = frame.head(max_rows).copy()
    columns = list(table.columns)
    rows = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for record in table.to_dict("records"):
        rows.append("| " + " | ".join(_format_markdown_value(record[column]) for column in columns) + " |")
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
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
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
