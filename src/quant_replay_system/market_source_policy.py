"""Market source field reliability policy helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import MarketSourcePolicySettings, Settings, load_settings


MARKET_SOURCE_POLICY_TIMESTAMP = "1970-01-01T00:00:00+00:00"

MARKET_POLICY_FIELDS = ["open", "high", "low", "close", "volume", "amount", "pre_close"]
PRICE_POLICY_FIELDS = ["open", "high", "low", "close"]

POLICY_STATUS_RANK = {
    "RELIABLE": 6,
    "PROVISIONAL": 5,
    "CAVEAT_FIRST_WINDOW_ROW": 4,
    "UNKNOWN": 3,
    "UNSTABLE": 2,
    "UNAVAILABLE": 1,
    "DO_NOT_USE": 0,
}

MARKET_SOURCE_POLICY_LIMITATIONS = [
    "The policy records field-level source reliability hints; it does not certify data quality.",
    "The policy does not choose a single trusted source for all workflows.",
    "Cached rows must still pass data-pipeline, data-quality, and snapshot-quality before research use.",
    "No broker API, live trading, or order automation is invoked.",
]


class MarketFieldReliability(str, Enum):
    RELIABLE = "RELIABLE"
    PROVISIONAL = "PROVISIONAL"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"
    UNSTABLE = "UNSTABLE"
    DO_NOT_USE = "DO_NOT_USE"
    CAVEAT_FIRST_WINDOW_ROW = "CAVEAT_FIRST_WINDOW_ROW"


@dataclass(frozen=True)
class MarketSourceFieldPolicy:
    source: str
    upstream_source: str
    security_type: str
    field_reliability: dict[str, MarketFieldReliability]
    notes: list[str]

    def reliability_for(self, field: str) -> MarketFieldReliability:
        return self.field_reliability.get(_normalize_field(field), MarketFieldReliability.UNKNOWN)

    def as_status_dict(self, fields: list[str] | None = None) -> dict[str, str]:
        selected_fields = fields or MARKET_POLICY_FIELDS
        return {field: self.reliability_for(field).value for field in selected_fields}


@dataclass(frozen=True)
class MarketSourcePolicyArtifactPaths:
    artifact_dir: Path
    market_source_policy_report: Path
    market_source_policy_csv: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "market_source_policy_report": self.market_source_policy_report,
            "market_source_policy_csv": self.market_source_policy_csv,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MarketSourcePolicyReportResult:
    policy_report_id: str
    status: str
    policy_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    audit_metadata: dict[str, Any]

    @property
    def row_count(self) -> int:
        return len(self.policy_frame)


def get_market_field_reliability(
    *,
    source: str,
    upstream_source: str,
    security_type: str,
    field: str,
    config: Settings | MarketSourcePolicySettings | dict[str, Any] | None = None,
) -> MarketFieldReliability:
    """Return one policy status, defaulting to UNKNOWN for unconfigured combinations."""

    policy = get_market_source_policy(
        source=source,
        upstream_source=upstream_source,
        security_type=security_type,
        config=config,
    )
    return policy.reliability_for(field)


def get_market_source_policy(
    *,
    source: str,
    upstream_source: str,
    security_type: str,
    config: Settings | MarketSourcePolicySettings | dict[str, Any] | None = None,
) -> MarketSourceFieldPolicy:
    """Return the source/upstream/security policy block with UNKNOWN defaults."""

    _project_settings, policy_settings = _resolve_settings(config)
    normalized_source = _normalize_key(source)
    normalized_upstream = _normalize_key(upstream_source)
    normalized_security = _normalize_key(security_type)
    payload = policy_settings.field_reliability
    block = (
        payload.get(normalized_source, {})
        .get(normalized_upstream, {})
        .get(normalized_security, {})
        if isinstance(payload, dict)
        else {}
    )
    if not isinstance(block, dict):
        block = {}
    reliability = {
        field: _coerce_reliability(block.get(field, MarketFieldReliability.UNKNOWN.value))
        for field in MARKET_POLICY_FIELDS
    }
    notes = block.get("notes", [])
    if not isinstance(notes, list):
        notes = [str(notes)]
    return MarketSourceFieldPolicy(
        source=normalized_source,
        upstream_source=normalized_upstream,
        security_type=normalized_security,
        field_reliability=reliability,
        notes=[str(note) for note in notes],
    )


def summarize_market_source_policy(
    *,
    config: Settings | MarketSourcePolicySettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Flatten the configured policy into a machine-readable table."""

    _project_settings, policy_settings = _resolve_settings(config)
    rows: list[dict[str, Any]] = []
    payload = policy_settings.field_reliability
    for source, upstreams in sorted((payload or {}).items()):
        if not isinstance(upstreams, dict):
            continue
        for upstream_source, securities in sorted(upstreams.items()):
            if not isinstance(securities, dict):
                continue
            for security_type, block in sorted(securities.items()):
                if not isinstance(block, dict):
                    continue
                notes = block.get("notes", [])
                if not isinstance(notes, list):
                    notes = [str(notes)]
                note_text = " | ".join(str(note) for note in notes)
                for field in MARKET_POLICY_FIELDS:
                    rows.append(
                        {
                            "source": _normalize_key(source),
                            "upstream_source": _normalize_key(upstream_source),
                            "security_type": _normalize_key(security_type),
                            "field": field,
                            "reliability": _coerce_reliability(block.get(field, "UNKNOWN")).value,
                            "notes": note_text,
                            "no_live_trading": True,
                            "no_broker_api": True,
                        }
                    )
    return pd.DataFrame(
        rows,
        columns=[
            "source",
            "upstream_source",
            "security_type",
            "field",
            "reliability",
            "notes",
            "no_live_trading",
            "no_broker_api",
        ],
    )


def annotate_market_frame_with_field_reliability(
    frame: pd.DataFrame,
    *,
    source: str,
    upstream_source: str,
    security_type: str,
    fields: list[str] | None = None,
    config: Settings | MarketSourcePolicySettings | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Return a copy with per-field reliability columns for the requested source context."""

    output = frame.copy(deep=True)
    selected_fields = fields or MARKET_POLICY_FIELDS
    policy = get_market_source_policy(
        source=source,
        upstream_source=upstream_source,
        security_type=security_type,
        config=config,
    )
    for field in selected_fields:
        output[f"{field}_reliability"] = policy.reliability_for(field).value
    return output


def select_preferred_source_for_fields(
    *,
    source_a: str,
    upstream_source_a: str,
    source_b: str,
    upstream_source_b: str,
    security_type: str,
    fields: list[str],
    config: Settings | MarketSourcePolicySettings | dict[str, Any] | None = None,
) -> str:
    """Select source(s) with the strongest configured reliability across fields."""

    candidates = [
        (source_a, upstream_source_a),
        (source_b, upstream_source_b),
    ]
    scored: list[tuple[str, int]] = []
    for source, upstream_source in candidates:
        policy = get_market_source_policy(
            source=source,
            upstream_source=upstream_source,
            security_type=security_type,
            config=config,
        )
        score = min(_reliability_rank(policy.reliability_for(field)) for field in fields)
        scored.append((_normalize_key(source), score))
    best_score = max(score for _source, score in scored)
    if best_score <= POLICY_STATUS_RANK["UNAVAILABLE"]:
        return "NONE"
    return ",".join(source for source, score in scored if score == best_score)


def infer_market_security_type(symbol: str) -> str:
    """Infer a broad market security type from a China market symbol."""

    cleaned = str(symbol or "").strip().lower()
    digits = "".join(ch for ch in cleaned if ch.isdigit())
    if len(digits) > 6:
        digits = digits[-6:]
    digits = digits.zfill(6) if digits.isdigit() and 0 < len(digits) < 6 else digits
    if digits in {"000300", "000905", "000852"}:
        return "INDEX"
    if digits.startswith(("510", "511", "512", "513", "515", "516", "159")):
        return "ETF"
    if digits.startswith(("000", "001", "002", "003", "300", "600", "601", "603", "605", "688")):
        return "STOCK"
    return "UNKNOWN"


def build_market_comparison_policy_hints(
    comparison_frame: pd.DataFrame,
    *,
    symbol: str,
    source_a: str,
    source_b: str,
    config: Settings | MarketSourcePolicySettings | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build source field policy hints for one market-cache comparison."""

    security_type = infer_market_security_type(symbol)
    upstream_a = _first_non_empty(comparison_frame.get("upstream_source_a", pd.Series(dtype="object")))
    upstream_b = _first_non_empty(comparison_frame.get("upstream_source_b", pd.Series(dtype="object")))
    policy_a = get_market_source_policy(
        source=source_a,
        upstream_source=upstream_a,
        security_type=security_type,
        config=config,
    )
    policy_b = get_market_source_policy(
        source=source_b,
        upstream_source=upstream_b,
        security_type=security_type,
        config=config,
    )
    pre_close_statuses = {
        policy_a.reliability_for("pre_close").value,
        policy_b.reliability_for("pre_close").value,
    }
    pre_close_caveat = (
        "CAVEAT_FIRST_WINDOW_ROW" if "CAVEAT_FIRST_WINDOW_ROW" in pre_close_statuses else ""
    )
    amount_preferred = select_preferred_source_for_fields(
        source_a=source_a,
        upstream_source_a=upstream_a,
        source_b=source_b,
        upstream_source_b=upstream_b,
        security_type=security_type,
        fields=["amount"],
        config=config,
    )
    return {
        "policy_security_type": security_type,
        "source_a_upstream_source": upstream_a,
        "source_b_upstream_source": upstream_b,
        "source_a_field_reliability": json.dumps(policy_a.as_status_dict(), sort_keys=True),
        "source_b_field_reliability": json.dumps(policy_b.as_status_dict(), sort_keys=True),
        "recommended_for_price": select_preferred_source_for_fields(
            source_a=source_a,
            upstream_source_a=upstream_a,
            source_b=source_b,
            upstream_source_b=upstream_b,
            security_type=security_type,
            fields=PRICE_POLICY_FIELDS,
            config=config,
        ),
        "recommended_for_volume": select_preferred_source_for_fields(
            source_a=source_a,
            upstream_source_a=upstream_a,
            source_b=source_b,
            upstream_source_b=upstream_b,
            security_type=security_type,
            fields=["volume"],
            config=config,
        ),
        "recommended_for_amount": amount_preferred,
        "amount_sensitive_preferred_source": amount_preferred,
        "pre_close_caveat": pre_close_caveat,
        "source_a_policy_notes": " | ".join(policy_a.notes),
        "source_b_policy_notes": " | ".join(policy_b.notes),
    }


def run_market_source_policy_report(
    *,
    output_dir: str | Path | None = None,
    config: Settings | MarketSourcePolicySettings | dict[str, Any] | None = None,
) -> MarketSourcePolicyReportResult:
    """Write a local source field reliability policy report."""

    _project_settings, policy_settings = _resolve_settings(config)
    if policy_settings.enable_live_trading or policy_settings.enable_broker_api:
        raise ValueError("Market source policy cannot enable live trading or broker API access")
    frame = summarize_market_source_policy(config=policy_settings)
    policy_report_id = generate_market_source_policy_report_id(policy_settings)
    artifact_paths = resolve_market_source_policy_artifact_paths(
        Path(output_dir) if output_dir is not None else policy_settings.output_dir,
        policy_report_id,
    )
    result = MarketSourcePolicyReportResult(
        policy_report_id=policy_report_id,
        status="PASS",
        policy_frame=frame,
        artifact_paths=artifact_paths.as_dict(),
        warnings=[],
        known_limitations=MARKET_SOURCE_POLICY_LIMITATIONS,
        audit_metadata={
            "policy_report_id": policy_report_id,
            "operation": "market_source_policy",
            "row_count": len(frame),
            "live_trading_enabled": False,
            "broker_api_invoked": False,
            "market_source_policy_only": True,
            "config_version": policy_settings.config_version,
        },
    )
    if policy_settings.write_artifacts:
        write_market_source_policy_artifacts(result)
    return result


def write_market_source_policy_artifacts(result: MarketSourcePolicyReportResult) -> dict[str, Path]:
    paths = MarketSourcePolicyArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.policy_frame.to_csv(paths.market_source_policy_csv, index=False)
    paths.market_source_policy_report.write_text(render_market_source_policy_report(result), encoding="utf-8")
    metadata = {
        "policy_report_id": result.policy_report_id,
        "status": result.status,
        "row_count": result.row_count,
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "created_at": MARKET_SOURCE_POLICY_TIMESTAMP,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_live_trading_statement": "No live trading or broker API was invoked.",
    }
    paths.metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    return paths.as_dict()


def render_market_source_policy_report(result: MarketSourcePolicyReportResult) -> str:
    lines = [
        "# Market Source Field Reliability Policy",
        "",
        f"- policy_report_id: {result.policy_report_id}",
        f"- status: {result.status}",
        f"- row_count: {result.row_count}",
        "",
        "No live trading or broker API was invoked.",
        "",
        "## Policy Table",
        "",
        result.policy_frame.to_markdown(index=False) if not result.policy_frame.empty else "No policy rows.",
        "",
        "## Interpretation",
        "",
        "- Health checks report whether a route is available.",
        "- Source comparisons report whether overlapping rows agree.",
        "- This policy records field-level reliability hints by source, upstream, and security type.",
        "- Policy hints do not replace data-pipeline, data-quality, or snapshot-quality.",
    ]
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in result.known_limitations)
    return "\n".join(lines) + "\n"


def resolve_market_source_policy_artifact_paths(
    output_dir: str | Path,
    policy_report_id: str,
) -> MarketSourcePolicyArtifactPaths:
    artifact_dir = Path(output_dir) / policy_report_id
    return MarketSourcePolicyArtifactPaths(
        artifact_dir=artifact_dir,
        market_source_policy_report=artifact_dir / "market_source_policy_report.md",
        market_source_policy_csv=artifact_dir / "market_source_policy.csv",
        metadata=artifact_dir / "metadata.json",
    )


def generate_market_source_policy_report_id(settings: MarketSourcePolicySettings) -> str:
    payload = {
        "field_reliability": settings.field_reliability,
        "config_version": settings.config_version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _resolve_settings(
    config: Settings | MarketSourcePolicySettings | dict[str, Any] | None,
) -> tuple[Settings, MarketSourcePolicySettings]:
    if config is None:
        project = load_settings(Path("config/default.yaml"))
        return project, project.market_source_policy
    if isinstance(config, Settings):
        return config, config.market_source_policy
    project = load_settings(Path("config/default.yaml"))
    if isinstance(config, MarketSourcePolicySettings):
        return project, config
    if isinstance(config, dict):
        payload = dict(project.market_source_policy.model_dump())
        if "market_source_policy" in config and isinstance(config["market_source_policy"], dict):
            payload.update(config["market_source_policy"])
        else:
            payload.update(config)
        return project, MarketSourcePolicySettings(**payload)
    raise TypeError("config must be Settings, MarketSourcePolicySettings, dict, or None")


def _coerce_reliability(value: Any) -> MarketFieldReliability:
    normalized = _normalize_key(str(value or "UNKNOWN"))
    try:
        return MarketFieldReliability(normalized)
    except ValueError:
        return MarketFieldReliability.UNKNOWN


def _reliability_rank(value: MarketFieldReliability) -> int:
    return POLICY_STATUS_RANK.get(value.value, POLICY_STATUS_RANK["UNKNOWN"])


def _normalize_key(value: Any) -> str:
    return str(value or "").strip().upper()


def _normalize_field(value: Any) -> str:
    return str(value or "").strip().lower()


def _first_non_empty(series: pd.Series) -> str:
    for value in series.dropna().astype(str):
        normalized = value.strip().upper()
        if normalized:
            return normalized
    return ""


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
