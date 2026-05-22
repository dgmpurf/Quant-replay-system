"""Optional snapshot quality preflight for replay-like workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.config import Settings, SnapshotQualityPreflightSettings
from quant_replay_system.snapshot_quality_gate import SnapshotQualityGateResult, run_snapshot_quality_gate


@dataclass(frozen=True)
class SnapshotQualityPreflightResult:
    enabled: bool
    status: str | None = None
    manifest_path: Path | None = None
    report_path: Path | None = None
    quality_gate_id: str | None = None
    artifact_paths: dict[str, Path] | None = None
    warnings: list[str] | None = None
    gate_result: SnapshotQualityGateResult | None = None

    def metadata_fields(self) -> dict[str, Any]:
        """Return stable metadata fields for downstream workflow results."""

        fields: dict[str, Any] = {
            "snapshot_quality_preflight_enabled": self.enabled,
            "snapshot_quality_status": self.status,
            "snapshot_quality_report_path": self.report_path,
            "snapshot_quality_gate_id": self.quality_gate_id,
            "snapshot_quality_warnings": list(self.warnings or []),
        }
        if self.manifest_path is not None:
            fields["snapshot_quality_manifest_path"] = self.manifest_path
        if self.artifact_paths:
            fields["snapshot_quality_artifact_paths"] = dict(self.artifact_paths)
        return fields


class SnapshotQualityPreflightError(ValueError):
    """Raised when an enabled snapshot quality preflight blocks a workflow."""

    def __init__(self, message: str, preflight_result: SnapshotQualityPreflightResult | None = None) -> None:
        super().__init__(message)
        self.preflight_result = preflight_result


def run_snapshot_quality_preflight(
    settings: Settings,
    *,
    snapshot_manifest_path: str | Path | None = None,
    context: str = "workflow",
) -> SnapshotQualityPreflightResult:
    """Run the optional snapshot quality gate and apply blocking rules."""

    preflight_settings = settings.snapshot_quality_preflight
    if preflight_settings.enable_live_trading or preflight_settings.enable_broker_api:
        raise ValueError("Snapshot quality preflight cannot enable live trading or broker API access")
    if not preflight_settings.enabled:
        return SnapshotQualityPreflightResult(enabled=False)

    manifest_path = _resolve_manifest_path(preflight_settings, snapshot_manifest_path, context)
    gate_result = run_snapshot_quality_gate(manifest_path, settings=settings)
    report_path = gate_result.artifact_paths.get("snapshot_quality_gate_report")
    warnings = list(gate_result.warnings)
    if gate_result.status == "WARN":
        warnings.append(f"Snapshot quality preflight warning for {context}: status=WARN")

    preflight_result = SnapshotQualityPreflightResult(
        enabled=True,
        status=gate_result.status,
        manifest_path=manifest_path,
        report_path=report_path if preflight_settings.attach_report_paths else None,
        quality_gate_id=gate_result.quality_gate_id,
        artifact_paths=gate_result.artifact_paths if preflight_settings.attach_report_paths else {},
        warnings=warnings,
        gate_result=gate_result,
    )

    if gate_result.status == "FAIL" and preflight_settings.block_on_fail:
        raise SnapshotQualityPreflightError(
            _block_message(context, "FAIL", manifest_path, report_path),
            preflight_result,
        )
    if gate_result.status == "WARN" and preflight_settings.block_on_warn:
        raise SnapshotQualityPreflightError(
            _block_message(context, "WARN", manifest_path, report_path),
            preflight_result,
        )
    return preflight_result


def disable_snapshot_quality_preflight(settings: Settings) -> Settings:
    """Return a settings copy with preflight disabled for nested workflow calls."""

    return settings.model_copy(
        update={
            "snapshot_quality_preflight": settings.snapshot_quality_preflight.model_copy(
                update={"enabled": False}
            )
        }
    )


def _resolve_manifest_path(
    settings: SnapshotQualityPreflightSettings,
    snapshot_manifest_path: str | Path | None,
    context: str,
) -> Path:
    value = snapshot_manifest_path if snapshot_manifest_path is not None else settings.manifest_path
    if value is None:
        raise SnapshotQualityPreflightError(
            f"Snapshot quality preflight is enabled for {context}, but no manifest_path was provided."
        )
    path = Path(value)
    if str(path).strip() == "":
        raise SnapshotQualityPreflightError(
            f"Snapshot quality preflight is enabled for {context}, but manifest_path is empty."
        )
    return path


def _block_message(context: str, status: str, manifest_path: Path, report_path: Path | None) -> str:
    report = f" Report: {report_path}." if report_path is not None else ""
    return (
        f"Snapshot quality preflight blocked {context}: status={status}, "
        f"manifest={manifest_path}.{report}"
    )
