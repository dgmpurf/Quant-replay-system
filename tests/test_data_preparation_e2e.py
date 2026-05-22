import json
from pathlib import Path

import pandas as pd

from quant_replay_system.config import load_settings
from quant_replay_system.current_candidates import generate_current_candidates
from quant_replay_system.data_pipeline import (
    load_data_pipeline_manifest,
    run_data_source_ingestion_pipeline,
)
from quant_replay_system.snapshot_quality_gate import run_snapshot_quality_gate


def test_data_preparation_e2e_pipeline_snapshot_quality_to_current_candidates(tmp_path: Path) -> None:
    manifest_path = Path("data/mock/data_pipeline_manifest.json")

    pipeline_result = run_data_source_ingestion_pipeline(
        load_data_pipeline_manifest(manifest_path),
        config=_settings(tmp_path),
    )

    assert pipeline_result.status == "PASS"
    assert pipeline_result.snapshot_manifest_path is not None
    assert pipeline_result.snapshot_manifest_path.exists()
    snapshot_payload = json.loads(pipeline_result.snapshot_manifest_path.read_text(encoding="utf-8"))
    assert {"market", "universe", "trading_calendar"}.issubset(snapshot_payload["processed_files"])
    for dataset_type in ["market", "universe", "trading_calendar"]:
        assert Path(snapshot_payload["processed_files"][dataset_type]).exists()

    snapshot_quality = run_snapshot_quality_gate(
        pipeline_result.snapshot_manifest_path,
        settings=_settings(tmp_path),
    )

    assert snapshot_quality.status == "PASS"

    current_result = generate_current_candidates(
        "2024-01-08",
        universe_name="etf_core",
        top_n=5,
        config=_settings(tmp_path),
        snapshot_manifest_path=pipeline_result.snapshot_manifest_path,
    )

    assert current_result.factor_dataset_row_count > 0
    assert current_result.scored_dataset_row_count > 0
    assert current_result.snapshot_quality_status == "PASS"
    assert current_result.artifact_paths["candidates"].exists()
    assert current_result.artifact_paths["current_candidates_report"].exists()
    candidates = pd.read_csv(current_result.artifact_paths["candidates"])
    assert {"symbol", "final_score", "action"}.issubset(candidates.columns)
    assert len(candidates) == current_result.candidate_count
    report = current_result.artifact_paths["current_candidates_report"].read_text(encoding="utf-8")
    assert "No broker or live trading integration was invoked" in report

    assert pipeline_result.audit_metadata["live_trading_enabled"] is False
    assert pipeline_result.audit_metadata["broker_api_invoked"] is False
    assert pipeline_result.audit_metadata["network_api_calls_used_in_tests"] is False
    for dataset_result in pipeline_result.dataset_results:
        assert dataset_result.source_result is not None
        assert dataset_result.source_result.audit_metadata["network_api_calls_used_in_tests"] is False
        assert dataset_result.source_result.audit_metadata["broker_api_invoked"] is False
    assert snapshot_quality.audit_metadata["live_trading_enabled"] is False
    assert snapshot_quality.audit_metadata["broker_api_invoked"] is False
    assert current_result.audit_metadata["live_trading_enabled"] is False
    assert current_result.audit_metadata["broker_api_invoked"] is False
    assert current_result.audit_metadata["current_candidate_generation_only"] is True


def _settings(tmp_path: Path):
    settings = load_settings(Path("config/default.yaml"))
    return settings.model_copy(
        update={
            "data_pipeline": settings.data_pipeline.model_copy(
                update={
                    "output_dir": tmp_path / "reports" / "data_pipeline",
                    "raw_output_dir": tmp_path / "raw",
                    "processed_output_dir": tmp_path / "processed",
                    "snapshot_output_dir": tmp_path / "snapshots",
                    "write_artifacts": True,
                }
            ),
            "data_quality": settings.data_quality.model_copy(
                update={"output_dir": tmp_path / "reports" / "data_quality"}
            ),
            "snapshot_quality_gate": settings.snapshot_quality_gate.model_copy(
                update={"output_dir": tmp_path / "reports" / "snapshot_quality"}
            ),
            "current_candidates": settings.current_candidates.model_copy(
                update={
                    "output_dir": tmp_path / "reports" / "current_candidates",
                    "default_top_n": 5,
                    "min_action": "NO_TRADE",
                    "min_final_score": None,
                    "write_artifacts": True,
                }
            ),
        }
    )
