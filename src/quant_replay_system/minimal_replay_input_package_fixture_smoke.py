"""Report-only smoke for a minimal replay input package.

This workflow creates a tiny local package under manual diagnostics and runs
the existing historical replay input gate validator against it. It is a
contract smoke only: it never creates active replay input, labels, trained
weights, stock profiles, buy-review eligibility, current-candidates, snapshots,
orders, messages, API calls, data-store writes, or cache mutation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.historical_replay_input_gate_validator import (
    REPLAY_INPUT_GATE_PASS_CANDIDATE,
    HistoricalReplayInputGateValidatorResult,
    run_historical_replay_input_gate_validator,
)


SMOKE_VERSION = "v0.1"
DEFAULT_OUTPUT_DIR = Path(
    "outputs/reports/manual_diagnostics/minimal_replay_input_package_fixture_smoke_v0_1"
)
DEFAULT_VALIDATOR_OUTPUT_DIR = Path(
    "outputs/reports/manual_diagnostics/historical_replay_input_gate_validator_v0_1"
)
PACKAGE_FILES = [
    "replay_input_manifest.json",
    "source_registry.csv",
    "pit_universe.csv",
    "raw_document_store.csv",
    "factor_definition.csv",
    "factor_observation.csv",
    "event_structured.csv",
    "company_exposure.csv",
]
UNSAFE_FALSE_FIELDS = [
    "active_replay_input_ready",
    "active_replay_input",
    "forward_labels_exist",
    "weights_trained",
    "active_stock_profile_exists",
    "real_buy_review_eligible",
    "approval_applied",
    "order_placed",
    "llm_api_called",
    "external_api_called",
    "cache_mutated",
    "current_candidates_run",
    "snapshot_built",
    "signal_semantics_changed",
]


@dataclass(frozen=True)
class MinimalReplayInputPackageFixtureSmokeSettings:
    output_dir: Path = DEFAULT_OUTPUT_DIR
    validator_output_dir: Path = DEFAULT_VALIDATOR_OUTPUT_DIR
    as_of_date: str = "2024-04-02"
    replay_decision_time: str = "2024-04-02T16:00:00+08:00"
    created_at: str = "2024-04-02T16:05:00+08:00"
    symbol: str = "000001"
    write_artifacts: bool = True
    report_only: bool = True
    diagnostic_only: bool = True


@dataclass(frozen=True)
class MinimalReplayInputPackageFixtureSmokeResult:
    smoke_run_id: str
    generated_at: str
    artifact_path: Path
    package_path: Path
    validator_run_id: str
    validator_status: str
    pass_candidate: bool
    active_replay_input_ready: bool
    active_replay_input: bool
    forward_labels_exist: bool
    weights_trained: bool
    active_stock_profile_exists: bool
    real_buy_review_eligible: bool
    approval_applied: bool
    order_placed: bool
    llm_api_called: bool
    external_api_called: bool
    cache_mutated: bool
    current_candidates_run: bool
    snapshot_built: bool
    signal_semantics_changed: bool
    report_only: bool
    diagnostic_only: bool
    no_live_trading: bool
    no_broker_api: bool
    no_order_placement: bool
    no_message_sent: bool
    validator_artifact_path: Path
    artifact_paths: dict[str, Path]
    validation_status: str
    diagnostic_reason: str


def run_minimal_replay_input_package_fixture_smoke(
    settings: MinimalReplayInputPackageFixtureSmokeSettings | None = None,
) -> MinimalReplayInputPackageFixtureSmokeResult:
    resolved = settings or MinimalReplayInputPackageFixtureSmokeSettings()
    _assert_settings_safe(resolved)

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    smoke_run_id = _smoke_run_id(resolved)
    paths = resolve_minimal_replay_input_package_fixture_smoke_paths(resolved.output_dir, smoke_run_id)
    create_minimal_replay_input_package(paths["input_package"], resolved)

    validator_result = run_historical_replay_input_gate_validator(
        input_package=paths["input_package"],
        output_dir=resolved.validator_output_dir,
    )
    diagnostic_reason = _diagnostic_reason(validator_result)
    validation_status = "PASS" if not diagnostic_reason else "FAIL"
    result = _build_result(
        smoke_run_id=smoke_run_id,
        generated_at=generated_at,
        paths=paths,
        validator_result=validator_result,
        validation_status=validation_status,
        diagnostic_reason=diagnostic_reason,
    )

    if resolved.write_artifacts:
        write_minimal_replay_input_package_fixture_smoke_artifacts(result=result, settings=resolved)
    if validation_status != "PASS":
        raise RuntimeError(f"Minimal replay input package fixture smoke failed closed: {diagnostic_reason}")
    return result


def create_minimal_replay_input_package(
    package_path: str | Path,
    settings: MinimalReplayInputPackageFixtureSmokeSettings | None = None,
) -> Path:
    resolved = settings or MinimalReplayInputPackageFixtureSmokeSettings()
    package_dir = Path(package_path)
    _assert_manual_diagnostics_path(package_dir)
    _assert_no_data_store_path(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)

    manifest = _manifest(resolved)
    (package_dir / "replay_input_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    for file_name, row in _package_rows(resolved).items():
        pd.DataFrame([row], dtype=object).to_csv(package_dir / file_name, index=False)
    return package_dir


def write_minimal_replay_input_package_fixture_smoke_artifacts(
    *,
    result: MinimalReplayInputPackageFixtureSmokeResult,
    settings: MinimalReplayInputPackageFixtureSmokeSettings,
) -> dict[str, Path]:
    paths = result.artifact_paths
    paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    paths["smoke_metadata"].write_text(
        json.dumps(_metadata(result), indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    paths["smoke_report"].write_text(_render_report(result), encoding="utf-8")
    paths["validator_result_ref"].write_text(
        json.dumps(_validator_ref(result), indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    _expected_conditions(result).to_csv(paths["expected_pass_candidate_conditions"], index=False)
    _safety_flag_report(result).to_csv(paths["safety_flag_report"], index=False)
    paths["recommended_next_task"].write_text(_recommended_next_task(), encoding="utf-8")
    return paths


def resolve_minimal_replay_input_package_fixture_smoke_paths(
    output_dir: str | Path,
    smoke_run_id: str,
) -> dict[str, Path]:
    artifact_dir = Path(output_dir) / smoke_run_id
    input_package = artifact_dir / "input_package"
    return {
        "artifact_dir": artifact_dir,
        "input_package": input_package,
        "smoke_metadata": artifact_dir / "smoke_metadata.json",
        "smoke_report": artifact_dir / "smoke_report.md",
        "validator_result_ref": artifact_dir / "validator_result_ref.json",
        "expected_pass_candidate_conditions": artifact_dir / "expected_pass_candidate_conditions.csv",
        "safety_flag_report": artifact_dir / "safety_flag_report.csv",
        "recommended_next_task": artifact_dir / "recommended_next_task.md",
    }


def _manifest(settings: MinimalReplayInputPackageFixtureSmokeSettings) -> dict[str, Any]:
    manifest = {
        "package_id": "minimal_replay_input_package_fixture_smoke_000001_20240402",
        "package_type": "historical_replay_input_package",
        "as_of_date": settings.as_of_date,
        "replay_decision_time": settings.replay_decision_time,
        "created_at": settings.created_at,
        "accepted_pit_universe": True,
        "approval_artifact_ref": "diagnostic_accepted_pit_universe_contract_ref_only",
        "report_only": True,
        "diagnostic_only": True,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_order_placement": True,
        "no_message_sent": True,
    }
    manifest.update({field: False for field in UNSAFE_FALSE_FIELDS})
    return manifest


def _package_rows(settings: MinimalReplayInputPackageFixtureSmokeSettings) -> dict[str, dict[str, Any]]:
    symbol = settings.symbol
    signal_date = settings.as_of_date
    decision_safe_time = "2024-04-02T15:30:00+08:00"
    publish_time = "2024-04-02T15:00:00+08:00"
    return {
        "source_registry.csv": {
            "source_id": "src_diagnostic_official_001",
            "source_hash": "hash_src_diagnostic_official_001",
            "revision_id": "rev_source_diagnostic_001",
            "permission_status": "ACCEPTED_FOR_REPLAY_RESEARCH",
            "source_type": "OFFICIAL_PUBLIC_DIAGNOSTIC_CONTEXT",
            "report_only": "true",
            "diagnostic_only": "true",
        },
        "pit_universe.csv": {
            "signal_date": signal_date,
            "symbol": symbol,
            "universe_name": "stock_core",
            "available_time": decision_safe_time,
            "source_id": "src_diagnostic_official_001",
            "source_hash": "hash_pit_universe_diagnostic_001",
            "revision_id": "rev_pit_universe_diagnostic_001",
        },
        "raw_document_store.csv": {
            "document_id": "doc_000001_20240402_diagnostic_status",
            "publish_time": publish_time,
            "available_time": decision_safe_time,
            "evidence_type": "OFFICIAL_STATUS_DIAGNOSTIC_CONTEXT",
            "source_id": "src_diagnostic_official_001",
            "source_hash": "hash_doc_diagnostic_001",
            "revision_id": "rev_doc_diagnostic_001",
        },
        "factor_definition.csv": {
            "factor_id": "event_context_quality_score",
            "factor_layer": "L4",
            "factor_layer_name": "event_driven_context",
            "definition_revision_id": "rev_factor_definition_diagnostic_001",
            "fixed_12_only": "false",
            "source_id": "src_diagnostic_official_001",
            "source_hash": "hash_factor_definition_diagnostic_001",
            "revision_id": "rev_factor_definition_diagnostic_001",
        },
        "factor_observation.csv": {
            "factor_id": "event_context_quality_score",
            "signal_date": signal_date,
            "symbol": symbol,
            "observation_value": "0.50",
            "available_time": decision_safe_time,
            "source_id": "src_diagnostic_official_001",
            "source_hash": "hash_factor_observation_diagnostic_001",
            "revision_id": "rev_factor_observation_diagnostic_001",
        },
        "event_structured.csv": {
            "event_id": "event_000001_20240402_diagnostic_status",
            "event_type": "STATUS_CONTEXT",
            "publish_time": publish_time,
            "available_time": decision_safe_time,
            "source_id": "src_diagnostic_official_001",
            "source_hash": "hash_event_diagnostic_001",
            "revision_id": "rev_event_diagnostic_001",
        },
        "company_exposure.csv": {
            "exposure_id": "exposure_000001_20240402_diagnostic_industry",
            "symbol": symbol,
            "exposure_type": "industry",
            "exposure_value": "bank",
            "available_time": decision_safe_time,
            "source_id": "src_diagnostic_official_001",
            "source_hash": "hash_company_exposure_diagnostic_001",
            "revision_id": "rev_company_exposure_diagnostic_001",
        },
    }


def _build_result(
    *,
    smoke_run_id: str,
    generated_at: str,
    paths: dict[str, Path],
    validator_result: HistoricalReplayInputGateValidatorResult,
    validation_status: str,
    diagnostic_reason: str,
) -> MinimalReplayInputPackageFixtureSmokeResult:
    return MinimalReplayInputPackageFixtureSmokeResult(
        smoke_run_id=smoke_run_id,
        generated_at=generated_at,
        artifact_path=paths["artifact_dir"],
        package_path=paths["input_package"],
        validator_run_id=validator_result.validator_run_id,
        validator_status=validator_result.status,
        pass_candidate=validator_result.pass_candidate,
        active_replay_input_ready=validator_result.active_replay_input_ready,
        active_replay_input=validator_result.active_replay_input,
        forward_labels_exist=validator_result.forward_labels_exist,
        weights_trained=validator_result.weights_trained,
        active_stock_profile_exists=validator_result.active_stock_profile_exists,
        real_buy_review_eligible=validator_result.real_buy_review_eligible,
        approval_applied=validator_result.approval_applied,
        order_placed=validator_result.order_placed,
        llm_api_called=validator_result.llm_api_called,
        external_api_called=validator_result.external_api_called,
        cache_mutated=validator_result.cache_mutated,
        current_candidates_run=validator_result.current_candidates_run,
        snapshot_built=validator_result.snapshot_built,
        signal_semantics_changed=validator_result.signal_semantics_changed,
        report_only=validator_result.report_only,
        diagnostic_only=validator_result.diagnostic_only,
        no_live_trading=validator_result.no_live_trading,
        no_broker_api=validator_result.no_broker_api,
        no_order_placement=validator_result.no_order_placement,
        no_message_sent=validator_result.no_message_sent,
        validator_artifact_path=validator_result.artifact_path,
        artifact_paths=paths,
        validation_status=validation_status,
        diagnostic_reason=diagnostic_reason,
    )


def _diagnostic_reason(validator_result: HistoricalReplayInputGateValidatorResult) -> str:
    checks = {
        "validator_status_is_pass_candidate": validator_result.status == REPLAY_INPUT_GATE_PASS_CANDIDATE,
        "pass_candidate_true": validator_result.pass_candidate is True,
        "active_replay_input_ready_false": validator_result.active_replay_input_ready is False,
        "active_replay_input_false": validator_result.active_replay_input is False,
        "forward_labels_exist_false": validator_result.forward_labels_exist is False,
        "weights_trained_false": validator_result.weights_trained is False,
        "active_stock_profile_exists_false": validator_result.active_stock_profile_exists is False,
        "real_buy_review_eligible_false": validator_result.real_buy_review_eligible is False,
        "approval_applied_false": validator_result.approval_applied is False,
        "order_placed_false": validator_result.order_placed is False,
        "llm_api_called_false": validator_result.llm_api_called is False,
        "external_api_called_false": validator_result.external_api_called is False,
        "cache_mutated_false": validator_result.cache_mutated is False,
        "current_candidates_run_false": validator_result.current_candidates_run is False,
        "snapshot_built_false": validator_result.snapshot_built is False,
        "signal_semantics_changed_false": validator_result.signal_semantics_changed is False,
        "report_only_true": validator_result.report_only is True,
        "diagnostic_only_true": validator_result.diagnostic_only is True,
    }
    failed = [name for name, passed in checks.items() if not passed]
    return "; ".join(failed)


def _metadata(result: MinimalReplayInputPackageFixtureSmokeResult) -> dict[str, Any]:
    return {
        "smoke_run_id": result.smoke_run_id,
        "generated_at": result.generated_at,
        "smoke_version": SMOKE_VERSION,
        "artifact_path": str(result.artifact_path),
        "package_path": str(result.package_path),
        "validator_run_id": result.validator_run_id,
        "validator_status": result.validator_status,
        "pass_candidate": result.pass_candidate,
        "active_replay_input_ready": result.active_replay_input_ready,
        "active_replay_input": result.active_replay_input,
        "forward_labels_exist": result.forward_labels_exist,
        "weights_trained": result.weights_trained,
        "active_stock_profile_exists": result.active_stock_profile_exists,
        "real_buy_review_eligible": result.real_buy_review_eligible,
        "approval_applied": result.approval_applied,
        "order_placed": result.order_placed,
        "llm_api_called": result.llm_api_called,
        "external_api_called": result.external_api_called,
        "cache_mutated": result.cache_mutated,
        "current_candidates_run": result.current_candidates_run,
        "snapshot_built": result.snapshot_built,
        "signal_semantics_changed": result.signal_semantics_changed,
        "report_only": result.report_only,
        "diagnostic_only": result.diagnostic_only,
        "no_live_trading": result.no_live_trading,
        "no_broker_api": result.no_broker_api,
        "no_order_placement": result.no_order_placement,
        "no_message_sent": result.no_message_sent,
        "validator_artifact_path": str(result.validator_artifact_path),
        "validation_status": result.validation_status,
        "diagnostic_reason": result.diagnostic_reason,
        "artifact_paths": {key: str(value) for key, value in result.artifact_paths.items()},
    }


def _validator_ref(result: MinimalReplayInputPackageFixtureSmokeResult) -> dict[str, Any]:
    return {
        "validator_run_id": result.validator_run_id,
        "validator_status": result.validator_status,
        "validator_artifact_path": str(result.validator_artifact_path),
        "metadata_path": str(result.validator_artifact_path / "metadata.json"),
        "input_gate_report_path": str(result.validator_artifact_path / "input_gate_report.md"),
        "pass_candidate": result.pass_candidate,
        "active_replay_input_ready": result.active_replay_input_ready,
        "active_replay_input": result.active_replay_input,
    }


def _expected_conditions(result: MinimalReplayInputPackageFixtureSmokeResult) -> pd.DataFrame:
    conditions = [
        ("validator_status", REPLAY_INPUT_GATE_PASS_CANDIDATE, result.validator_status),
        ("pass_candidate", True, result.pass_candidate),
        ("active_replay_input_ready", False, result.active_replay_input_ready),
        ("active_replay_input", False, result.active_replay_input),
        ("real_buy_review_eligible", False, result.real_buy_review_eligible),
        ("report_only", True, result.report_only),
        ("diagnostic_only", True, result.diagnostic_only),
    ]
    return pd.DataFrame(
        [
            {
                "condition_name": name,
                "expected_value": expected,
                "observed_value": observed,
                "passed": expected == observed,
            }
            for name, expected, observed in conditions
        ]
    )


def _safety_flag_report(result: MinimalReplayInputPackageFixtureSmokeResult) -> pd.DataFrame:
    fields = {
        "active_replay_input_ready": result.active_replay_input_ready,
        "active_replay_input": result.active_replay_input,
        "forward_labels_exist": result.forward_labels_exist,
        "weights_trained": result.weights_trained,
        "active_stock_profile_exists": result.active_stock_profile_exists,
        "real_buy_review_eligible": result.real_buy_review_eligible,
        "approval_applied": result.approval_applied,
        "order_placed": result.order_placed,
        "llm_api_called": result.llm_api_called,
        "external_api_called": result.external_api_called,
        "cache_mutated": result.cache_mutated,
        "current_candidates_run": result.current_candidates_run,
        "snapshot_built": result.snapshot_built,
        "signal_semantics_changed": result.signal_semantics_changed,
    }
    rows = [
        {"flag_name": name, "expected_value": False, "observed_value": value, "passed": value is False}
        for name, value in fields.items()
    ]
    rows.extend(
        [
            {"flag_name": "report_only", "expected_value": True, "observed_value": result.report_only, "passed": result.report_only is True},
            {"flag_name": "diagnostic_only", "expected_value": True, "observed_value": result.diagnostic_only, "passed": result.diagnostic_only is True},
            {"flag_name": "no_live_trading", "expected_value": True, "observed_value": result.no_live_trading, "passed": result.no_live_trading is True},
            {"flag_name": "no_broker_api", "expected_value": True, "observed_value": result.no_broker_api, "passed": result.no_broker_api is True},
            {"flag_name": "no_order_placement", "expected_value": True, "observed_value": result.no_order_placement, "passed": result.no_order_placement is True},
            {"flag_name": "no_message_sent", "expected_value": True, "observed_value": result.no_message_sent, "passed": result.no_message_sent is True},
        ]
    )
    return pd.DataFrame(rows)


def _render_report(result: MinimalReplayInputPackageFixtureSmokeResult) -> str:
    return "\n".join(
        [
            "# Minimal Replay Input Package Fixture Smoke",
            "",
            "Report-only smoke that creates a tiny local replay input package and runs the existing historical replay input gate validator.",
            "",
            f"- smoke_run_id: {result.smoke_run_id}",
            f"- validation_status: {result.validation_status}",
            f"- package_path: {result.package_path}",
            f"- validator_run_id: {result.validator_run_id}",
            f"- validator_status: {result.validator_status}",
            f"- pass_candidate: {result.pass_candidate}",
            f"- active_replay_input_ready: {result.active_replay_input_ready}",
            f"- active_replay_input: {result.active_replay_input}",
            f"- real_buy_review_eligible: {result.real_buy_review_eligible}",
            "",
            "## Safety",
            "",
            "This smoke does not create active replay input, run replay, run current-candidates, build snapshots, compute forward labels, train weights, create stock profiles, create buy-review eligibility, place orders, send messages, call APIs, write data/raw, write data/processed, write data/cache, or mutate cache.",
        ]
    )


def _recommended_next_task() -> str:
    return "\n".join(
        [
            "# Recommended Next Task",
            "",
            "Add artifact views for the minimal replay input package fixture smoke only after the smoke remains stable.",
            "",
            "Keep the smoke separate from research-status until index, health, and status views are intentionally scoped.",
        ]
    )


def _smoke_run_id(settings: MinimalReplayInputPackageFixtureSmokeSettings) -> str:
    payload = {
        "version": SMOKE_VERSION,
        "as_of_date": settings.as_of_date,
        "replay_decision_time": settings.replay_decision_time,
        "symbol": settings.symbol,
        "package_type": "historical_replay_input_package",
    }
    return hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _assert_settings_safe(settings: MinimalReplayInputPackageFixtureSmokeSettings) -> None:
    if not settings.report_only or not settings.diagnostic_only:
        raise ValueError("Minimal replay input package fixture smoke must remain report-only and diagnostic-only.")
    _assert_manual_diagnostics_path(settings.output_dir)
    _assert_manual_diagnostics_path(settings.validator_output_dir)
    _assert_no_data_store_path(settings.output_dir)
    _assert_no_data_store_path(settings.validator_output_dir)


def _assert_manual_diagnostics_path(path: str | Path) -> None:
    normalized = str(Path(path)).replace("\\", "/").lower()
    if "outputs/reports/manual_diagnostics" not in normalized:
        raise ValueError("Minimal replay input package fixture smoke outputs must stay under outputs/reports/manual_diagnostics.")


def _assert_no_data_store_path(path: str | Path) -> None:
    normalized = str(Path(path)).replace("\\", "/").lower()
    if any(part in normalized for part in ["data/raw", "data/processed", "data/cache"]):
        raise ValueError("Minimal replay input package fixture smoke must not write data/raw, data/processed, or data/cache.")


__all__ = [
    "MinimalReplayInputPackageFixtureSmokeResult",
    "MinimalReplayInputPackageFixtureSmokeSettings",
    "create_minimal_replay_input_package",
    "resolve_minimal_replay_input_package_fixture_smoke_paths",
    "run_minimal_replay_input_package_fixture_smoke",
    "write_minimal_replay_input_package_fixture_smoke_artifacts",
]
