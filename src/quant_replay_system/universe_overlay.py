"""Reviewed local universe overlay merge helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import Settings, UniverseOverlaySettings, load_settings
from quant_replay_system.data import (
    UNIVERSE_SNAPSHOT_SCHEMA,
    normalize_symbol_column,
    normalize_symbol_series,
    read_csv_preserve_symbol_columns,
)


UNIVERSE_OVERLAY_LIMITATIONS = [
    "Uses reviewed local CSV files only.",
    "Does not call market data APIs or require API tokens.",
    "Does not connect to brokers, place orders, or automate execution.",
    "Does not infer missing ETF coverage; overlay rows must be reviewed by the user.",
]


@dataclass(frozen=True)
class UniverseOverlayArtifactPaths:
    artifact_dir: Path
    raw_data: Path
    universe_overlay_report: Path
    overlay_metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "raw_data": self.raw_data,
            "universe_overlay_report": self.universe_overlay_report,
            "overlay_metadata": self.overlay_metadata,
        }


@dataclass(frozen=True)
class UniverseOverlayResult:
    overlay_run_id: str
    base_universe_path: Path
    overlay_path: Path
    row_count: int
    base_row_count: int
    overlay_row_count: int
    added_symbol_count: int
    overridden_symbol_count: int
    added_symbols: list[str]
    overridden_symbols: list[str]
    merged_universe: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]


def run_universe_overlay(
    base_universe_path: str | Path,
    overlay_path: str | Path,
    *,
    output_dir: str | Path | None = None,
    allow_override_existing: bool | None = None,
    settings: Settings | UniverseOverlaySettings | dict[str, Any] | None = None,
) -> UniverseOverlayResult:
    """Merge reviewed ETF overlay rows into a local canonical universe CSV."""

    project_settings, overlay_settings = _resolve_settings(settings)
    if overlay_settings.enable_live_trading or overlay_settings.enable_broker_api:
        raise ValueError("Universe overlay cannot enable live trading or broker API access")

    effective_settings = overlay_settings
    if output_dir is not None:
        effective_settings = effective_settings.model_copy(update={"output_dir": Path(output_dir)})
    effective_allow_override = (
        effective_settings.allow_override_existing
        if allow_override_existing is None
        else bool(allow_override_existing)
    )

    base_path = Path(base_universe_path)
    overlay_csv_path = Path(overlay_path)
    base = load_universe_overlay_csv(base_path, label="base_universe")
    overlay = load_universe_overlay_csv(overlay_csv_path, label="overlay")
    validate_universe_overlay(overlay, base_universe=base, allow_override_existing=effective_allow_override)
    merge_result = merge_universe_overlay(
        base,
        overlay,
        allow_override_existing=effective_allow_override,
    )
    overlay_run_id = generate_universe_overlay_run_id(
        base_path,
        overlay_csv_path,
        overlay,
        allow_override_existing=effective_allow_override,
        config_version=effective_settings.config_version,
    )
    paths = resolve_universe_overlay_artifact_paths(effective_settings.output_dir, overlay_run_id)
    result = UniverseOverlayResult(
        overlay_run_id=overlay_run_id,
        base_universe_path=base_path,
        overlay_path=overlay_csv_path,
        row_count=len(merge_result["merged"]),
        base_row_count=len(base),
        overlay_row_count=len(overlay),
        added_symbol_count=len(merge_result["added_symbols"]),
        overridden_symbol_count=len(merge_result["overridden_symbols"]),
        added_symbols=merge_result["added_symbols"],
        overridden_symbols=merge_result["overridden_symbols"],
        merged_universe=merge_result["merged"],
        artifact_paths=paths.as_dict(),
        warnings=[],
        known_limitations=UNIVERSE_OVERLAY_LIMITATIONS,
        audit_metadata={
            "overlay_run_id": overlay_run_id,
            "base_universe_path": str(base_path),
            "overlay_path": str(overlay_csv_path),
            "base_row_count": len(base),
            "overlay_row_count": len(overlay),
            "merged_row_count": len(merge_result["merged"]),
            "added_symbols": merge_result["added_symbols"],
            "overridden_symbols": merge_result["overridden_symbols"],
            "allow_override_existing": effective_allow_override,
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "network_api_calls_used_in_tests": False,
            "universe_overlay_only": True,
            "config_version": effective_settings.config_version,
        },
    )
    if effective_settings.write_artifacts:
        write_universe_overlay_artifacts(result)
    _ = project_settings
    return result


def load_universe_overlay_csv(path: str | Path, *, label: str = "universe") -> pd.DataFrame:
    """Load a local canonical universe CSV while preserving symbol strings."""

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"{label} CSV not found: {file_path}")
    frame = read_csv_preserve_symbol_columns(file_path, keep_default_na=False)
    missing = sorted(set(UNIVERSE_SNAPSHOT_SCHEMA).difference(frame.columns))
    if missing:
        raise ValueError(f"{label} CSV missing canonical universe columns: {missing}")
    return _normalize_universe_frame(frame[UNIVERSE_SNAPSHOT_SCHEMA])


def validate_universe_overlay(
    overlay: pd.DataFrame,
    *,
    base_universe: pd.DataFrame | None = None,
    allow_override_existing: bool = False,
) -> None:
    """Validate reviewed overlay rows before they can affect the base universe."""

    missing = sorted(set(UNIVERSE_SNAPSHOT_SCHEMA).difference(overlay.columns))
    if missing:
        raise ValueError(f"Overlay CSV missing canonical universe columns: {missing}")
    if overlay.empty:
        raise ValueError("Overlay CSV must contain at least one reviewed row")

    frame = _normalize_universe_frame(overlay)
    blank_symbols = frame["symbol"].astype(str).str.strip().eq("")
    if blank_symbols.any():
        raise ValueError("Overlay validation failed: symbol is required")

    duplicates = frame["symbol"].duplicated(keep=False)
    if duplicates.any():
        symbols = sorted(set(frame.loc[duplicates, "symbol"]))
        raise ValueError(f"Overlay validation failed: duplicate overlay symbols: {symbols}")

    for column in ["instrument_type", "as_of_date", "available_time", "is_active", "min_lot", "t_plus_rule"]:
        blank = frame[column].map(_is_blank)
        if blank.any():
            raise ValueError(f"Overlay validation failed: {column} is required")

    parsed_as_of = pd.to_datetime(frame["as_of_date"], errors="coerce")
    if parsed_as_of.isna().any():
        raise ValueError("Overlay validation failed: as_of_date contains invalid dates")
    parsed_available = pd.to_datetime(frame["available_time"], errors="coerce")
    if parsed_available.isna().any():
        raise ValueError("Overlay validation failed: available_time contains invalid timestamps")

    invalid_bool = _invalid_bool_values(frame["is_active"])
    if invalid_bool:
        raise ValueError(f"Overlay validation failed: is_active contains invalid boolean values: {invalid_bool}")

    min_lot = pd.to_numeric(frame["min_lot"], errors="coerce")
    if min_lot.isna().any() or (min_lot <= 0).any():
        raise ValueError("Overlay validation failed: min_lot must be positive numeric values")

    if base_universe is not None and not allow_override_existing:
        base_symbols = set(normalize_symbol_series(base_universe["symbol"]))
        existing = sorted(symbol for symbol in frame["symbol"] if symbol in base_symbols)
        if existing:
            raise ValueError(
                "Overlay validation failed: overlay symbols already exist in base universe. "
                f"Use allow_override_existing=true only after review. existing_symbols={existing}"
            )


def merge_universe_overlay(
    base_universe: pd.DataFrame,
    overlay: pd.DataFrame,
    *,
    allow_override_existing: bool = False,
) -> dict[str, Any]:
    """Return a merged universe frame plus added/overridden symbol metadata."""

    base = _normalize_universe_frame(base_universe)
    reviewed_overlay = _normalize_universe_frame(overlay)
    validate_universe_overlay(
        reviewed_overlay,
        base_universe=base,
        allow_override_existing=allow_override_existing,
    )

    base_symbols = set(base["symbol"])
    overlay_symbols = set(reviewed_overlay["symbol"])
    existing = sorted(base_symbols & overlay_symbols)
    added = sorted(overlay_symbols - base_symbols)
    if existing and not allow_override_existing:
        raise ValueError(f"Overlay symbols already exist in base universe: {existing}")

    if existing:
        base = base.loc[~base["symbol"].isin(existing)].copy()
    merged = pd.concat([base, reviewed_overlay], ignore_index=True)
    merged = _sort_universe_frame(merged)
    return {
        "merged": merged,
        "added_symbols": added,
        "overridden_symbols": existing,
    }


def generate_universe_overlay_run_id(
    base_universe_path: str | Path,
    overlay_path: str | Path,
    overlay: pd.DataFrame,
    *,
    allow_override_existing: bool,
    config_version: str,
) -> str:
    """Generate a deterministic id for a reviewed overlay merge."""

    normalized_overlay = _normalize_universe_frame(overlay)
    payload = {
        "base_universe_path": str(base_universe_path),
        "overlay_path": str(overlay_path),
        "overlay_symbols": sorted(normalized_overlay["symbol"].tolist()),
        "overlay_row_count": len(normalized_overlay),
        "allow_override_existing": bool(allow_override_existing),
        "config_version": config_version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def resolve_universe_overlay_artifact_paths(
    output_dir: str | Path,
    overlay_run_id: str,
) -> UniverseOverlayArtifactPaths:
    """Resolve stable output paths for a universe overlay run."""

    artifact_dir = Path(output_dir) / overlay_run_id
    return UniverseOverlayArtifactPaths(
        artifact_dir=artifact_dir,
        raw_data=artifact_dir / "raw_data.csv",
        universe_overlay_report=artifact_dir / "universe_overlay_report.md",
        overlay_metadata=artifact_dir / "overlay_metadata.json",
    )


def write_universe_overlay_artifacts(result: UniverseOverlayResult) -> dict[str, Path]:
    """Write merged universe CSV, markdown report, and metadata."""

    paths = UniverseOverlayArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.merged_universe, paths.raw_data)
    metadata = build_universe_overlay_metadata(result, paths)
    paths.overlay_metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.universe_overlay_report.write_text(render_universe_overlay_report(result, paths, metadata), encoding="utf-8")
    return paths.as_dict()


def build_universe_overlay_metadata(
    result: UniverseOverlayResult,
    paths: UniverseOverlayArtifactPaths,
) -> dict[str, Any]:
    """Build metadata for an overlay run."""

    return {
        "overlay_run_id": result.overlay_run_id,
        "base_universe_path": str(result.base_universe_path),
        "overlay_path": str(result.overlay_path),
        "row_counts": {
            "base_universe": result.base_row_count,
            "overlay": result.overlay_row_count,
            "merged_universe": result.row_count,
        },
        "added_symbol_count": result.added_symbol_count,
        "overridden_symbol_count": result.overridden_symbol_count,
        "added_symbols": result.added_symbols,
        "overridden_symbols": result.overridden_symbols,
        "output_files": {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def render_universe_overlay_report(
    result: UniverseOverlayResult,
    paths: UniverseOverlayArtifactPaths,
    metadata: dict[str, Any],
) -> str:
    """Render a markdown report for a reviewed universe overlay merge."""

    lines = [
        f"# Universe Overlay Report: {result.overlay_run_id}",
        "",
        "No broker or live trading integration was invoked. This is a local reviewed universe data preparation report only.",
        "",
        "## Summary",
        "",
        _dict_table(
            {
                "overlay_run_id": result.overlay_run_id,
                "base_universe_path": result.base_universe_path,
                "overlay_path": result.overlay_path,
                "merged_universe_path": paths.raw_data,
                "base_row_count": result.base_row_count,
                "overlay_row_count": result.overlay_row_count,
                "merged_row_count": result.row_count,
                "added_symbol_count": result.added_symbol_count,
                "overridden_symbol_count": result.overridden_symbol_count,
            }
        ),
        "",
        "## Added Symbols",
        "",
        _list_or_none(result.added_symbols),
        "",
        "## Overridden Symbols",
        "",
        _list_or_none(result.overridden_symbols),
        "",
        "## Output Files",
        "",
        _dict_table(metadata["output_files"]),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in result.known_limitations),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def _normalize_universe_frame(frame: pd.DataFrame) -> pd.DataFrame:
    output = normalize_symbol_column(frame.copy(deep=True))
    for column in UNIVERSE_SNAPSHOT_SCHEMA:
        if column not in output.columns:
            output[column] = ""
    return output[UNIVERSE_SNAPSHOT_SCHEMA]


def _sort_universe_frame(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy(deep=True)
    sort_frame = output.assign(
        _as_of_sort=pd.to_datetime(output["as_of_date"], errors="coerce"),
        _available_sort=pd.to_datetime(output["available_time"], errors="coerce"),
    )
    sort_frame = sort_frame.sort_values(["_as_of_sort", "symbol", "_available_sort", "revision_id"], na_position="last")
    return sort_frame.drop(columns=["_as_of_sort", "_available_sort"]).reset_index(drop=True)


def _invalid_bool_values(series: pd.Series) -> list[str]:
    normalized = series.astype(str).str.strip().str.lower()
    valid = {"true", "1", "yes", "y", "false", "0", "no", "n"}
    return sorted(set(normalized.loc[~normalized.isin(valid)]))


def _is_blank(value: object) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip() == ""


def _resolve_settings(
    settings: Settings | UniverseOverlaySettings | dict[str, Any] | None,
) -> tuple[Settings, UniverseOverlaySettings]:
    if settings is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.universe_overlay
    if isinstance(settings, Settings):
        return settings, settings.universe_overlay
    project = load_settings(Path("config/default.yaml"))
    if isinstance(settings, UniverseOverlaySettings):
        return project, settings
    if isinstance(settings, dict):
        payload = dict(project.universe_overlay.model_dump())
        for key, value in settings.items():
            if key == "universe_overlay" and isinstance(value, dict):
                payload.update(value)
            elif key in payload:
                payload[key] = value
        return project, UniverseOverlaySettings(**payload)
    raise TypeError("settings must be Settings, UniverseOverlaySettings, dict, or None")


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    export = _normalize_universe_temporal_columns_for_export(frame.copy(deep=True))
    for column in export.columns:
        if pd.api.types.is_datetime64_any_dtype(export[column]):
            export[column] = export[column].dt.strftime("%Y-%m-%d %H:%M:%S")
        elif export[column].dtype == "object":
            export[column] = export[column].map(_cell_to_export_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(path, index=False)


def _normalize_universe_temporal_columns_for_export(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy(deep=True)
    if "as_of_date" in output.columns:
        output["as_of_date"] = _format_temporal_series(output["as_of_date"], "%Y-%m-%d %H:%M:%S")
    if "available_time" in output.columns:
        output["available_time"] = _format_temporal_series(output["available_time"], "%Y-%m-%d %H:%M:%S")
    for column in ["listed_date", "delisted_date"]:
        if column in output.columns:
            output[column] = _format_temporal_series(output[column], "%Y-%m-%d")
    return output


def _format_temporal_series(series: pd.Series, fmt: str) -> pd.Series:
    missing = series.map(_is_missing_temporal_token)
    parsed = _parse_mixed_datetime_series(series.where(~missing, pd.NA))
    output = series.astype(str)
    output.loc[missing] = ""
    valid = parsed.notna()
    output.loc[valid] = parsed.loc[valid].dt.strftime(fmt)
    return output


def _parse_mixed_datetime_series(series: pd.Series) -> pd.Series:
    try:
        return pd.to_datetime(series, errors="coerce", format="mixed")
    except TypeError:
        return pd.to_datetime(series, errors="coerce")


def _is_missing_temporal_token(value: object) -> bool:
    if _is_blank(value):
        return True
    return str(value).strip().lower() in {"nan", "nat", "none", "null", "-", "--"}


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


def _dict_table(values: dict[str, Any]) -> str:
    rows = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        rows.append(f"| {key} | {_format_markdown_value(value)} |")
    return "\n".join(rows)


def _list_or_none(values: list[str]) -> str:
    if not values:
        return "- None"
    return "\n".join(f"- {value}" for value in values)


def _format_markdown_value(value: Any) -> str:
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
