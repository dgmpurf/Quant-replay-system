import json
import sys
from pathlib import Path

import pandas as pd
import yaml

from quant_replay_system import cli
from quant_replay_system.config import load_settings


DECISION_DATE = "2024-01-08"
UNIVERSE = "etf_core"


def test_unified_local_research_workflow_e2e_cli_smoke(tmp_path: Path, capsys) -> None:
    config_path = _write_e2e_config(tmp_path)
    reports_root = tmp_path / "reports"

    outputs = []

    assert _run_cli(
        [
            "data-pipeline",
            "--manifest",
            "data/mock/data_pipeline_manifest.json",
            "--config",
            str(config_path),
        ],
        capsys,
        outputs,
    ) == 0
    snapshot_manifest = _single_artifact_file(reports_root / "data_pipeline", "snapshot_manifest.json")
    snapshot_payload = json.loads(snapshot_manifest.read_text(encoding="utf-8"))
    assert {"market", "universe", "trading_calendar"}.issubset(snapshot_payload["processed_files"])

    assert _run_cli(
        [
            "snapshot-quality",
            "--manifest",
            str(snapshot_manifest),
            "--config",
            str(config_path),
        ],
        capsys,
        outputs,
    ) == 0
    assert "Snapshot quality status: PASS" in outputs[-1]

    assert _run_cli(
        [
            "current-candidates",
            "--date",
            DECISION_DATE,
            "--universe",
            UNIVERSE,
            "--top",
            "5",
            "--snapshot-manifest",
            str(snapshot_manifest),
            "--config",
            str(config_path),
        ],
        capsys,
        outputs,
    ) == 0
    candidates_path = _single_artifact_file(reports_root / "current_candidates", "candidates.csv")
    current_report = candidates_path.parent / "current_candidates_report.md"
    candidates = pd.read_csv(candidates_path)
    assert {"symbol", "final_score", "action"}.issubset(candidates.columns)
    assert not candidates.empty
    assert current_report.exists()

    assert _run_cli(
        [
            "current-candidates-index",
            "--root",
            str(reports_root / "current_candidates"),
            "--config",
            str(config_path),
        ],
        capsys,
        outputs,
    ) == 0
    current_index = reports_root / "current_candidates" / "index" / "current_candidate_artifact_index.csv"
    assert current_index.exists()

    assert _run_cli(
        [
            "current-candidates-health",
            "--index",
            str(current_index),
            "--config",
            str(config_path),
        ],
        capsys,
        outputs,
    ) == 0

    assert _run_cli(
        [
            "current-to-paper",
            "--index",
            str(current_index),
            "--decision-date",
            DECISION_DATE,
            "--universe",
            UNIVERSE,
            "--paper-date",
            DECISION_DATE,
            "--output-dir",
            str(reports_root / "current_to_paper_handoff"),
            "--config",
            str(config_path),
        ],
        capsys,
        outputs,
    ) == 0
    handoff_metadata = _single_artifact_file(reports_root / "current_to_paper_handoff", "handoff_metadata.json")
    handoff_payload = json.loads(handoff_metadata.read_text(encoding="utf-8"))
    initial_decisions = Path(handoff_payload["paper_artifact_paths"]["decisions"])
    assert initial_decisions.exists()

    assert _run_cli(
        [
            "current-to-paper-review",
            "--handoff-dir",
            str(handoff_metadata.parent),
            "--reviewer-id",
            "e2e-reviewer",
            "--config",
            str(config_path),
        ],
        capsys,
        outputs,
    ) == 0
    review_template = _single_artifact_file(reports_root / "current_to_paper_review_handoff", "review_updates_template.csv")
    assert review_template.exists()

    review_updates = tmp_path / "review_updates_e2e.csv"
    _edited_review_updates(review_template).to_csv(review_updates, index=False)
    assert _run_cli(
        [
            "paper-review-decisions",
            "--decisions",
            str(initial_decisions),
            "--updates",
            str(review_updates),
            "--health-check",
            "--reviewer-id",
            "e2e-reviewer",
            "--config",
            str(config_path),
        ],
        capsys,
        outputs,
    ) == 0
    reviewed_decisions = _single_artifact_file(reports_root / "paper_trading" / "reviews", "reviewed_decisions.csv")
    assert reviewed_decisions.exists()

    fills_path = tmp_path / "fills_e2e.csv"
    _approved_fill(reviewed_decisions).to_csv(fills_path, index=False)
    assert _run_cli(
        [
            "paper-daily",
            "--date",
            DECISION_DATE,
            "--reviewed-decisions",
            str(reviewed_decisions),
            "--fills",
            str(fills_path),
            "--journal-id",
            "e2e-final",
            "--config",
            str(config_path),
        ],
        capsys,
        outputs,
    ) == 0
    daily_report = reports_root / "paper_trading" / "daily" / f"{DECISION_DATE}_e2e-final" / "paper_report.md"
    assert daily_report.exists()

    assert _run_cli(
        [
            "paper-reconcile-fills",
            "--decisions",
            str(reviewed_decisions),
            "--fills",
            str(fills_path),
            "--config",
            str(config_path),
        ],
        capsys,
        outputs,
    ) == 0
    reconciliation_report = _single_artifact_file(reports_root / "paper_trading" / "reconciliation", "reconciliation_report.md")
    assert reconciliation_report.exists()

    assert _run_cli(["paper-index", "--root", str(reports_root / "paper_trading"), "--config", str(config_path)], capsys, outputs) == 0
    paper_index = reports_root / "paper_trading" / "index" / "paper_artifact_index.csv"
    assert paper_index.exists()
    assert _run_cli(["paper-health-check", "--index", str(paper_index), "--config", str(config_path)], capsys, outputs) == 0

    assert _run_cli(["data-prep-index", "--root", str(reports_root), "--config", str(config_path)], capsys, outputs) == 0
    data_prep_index = reports_root / "data_preparation" / "index" / "data_preparation_artifact_index.csv"
    assert data_prep_index.exists()
    assert _run_cli(["data-prep-health", "--index", str(data_prep_index), "--config", str(config_path)], capsys, outputs) == 0
    assert _run_cli(
        [
            "data-prep-status",
            "--root",
            str(reports_root),
            "--decision-date",
            DECISION_DATE,
            "--universe",
            UNIVERSE,
            "--config",
            str(config_path),
        ],
        capsys,
        outputs,
    ) == 0
    data_prep_report = _single_artifact_file(reports_root / "data_preparation" / "workflow_status", "data_preparation_workflow_status_report.md")
    assert data_prep_report.exists()

    assert _run_cli(
        [
            "paper-workflow-status",
            "--root",
            str(reports_root),
            "--decision-date",
            DECISION_DATE,
            "--universe",
            UNIVERSE,
            "--config",
            str(config_path),
        ],
        capsys,
        outputs,
    ) == 0
    paper_workflow_report = _single_artifact_file(reports_root / "paper_trading" / "workflow_status", "paper_workflow_status_report.md")
    assert paper_workflow_report.exists()

    assert _run_cli(
        [
            "research-status",
            "--root",
            str(reports_root),
            "--decision-date",
            DECISION_DATE,
            "--universe",
            UNIVERSE,
            "--config",
            str(config_path),
        ],
        capsys,
        outputs,
    ) == 0
    research_output = outputs[-1]
    research_report = _single_artifact_file(reports_root / "local_research_dashboard", "local_research_dashboard.md")
    assert research_report.exists()
    assert "next_manual_action:" in research_output
    assert "## Next Manual Action" in research_report.read_text(encoding="utf-8")
    assert all("No live trading or broker API was invoked." in output for output in outputs)

    assert not any("broker" in module_name.lower() for module_name in sys.modules)


def _run_cli(args: list[str], capsys, outputs: list[str]) -> int:
    code = cli.main(args)
    captured = capsys.readouterr()
    outputs.append(captured.out)
    return code


def _write_e2e_config(tmp_path: Path) -> Path:
    settings = load_settings(Path("config/default.yaml"))
    reports = tmp_path / "reports"
    settings = settings.model_copy(
        update={
            "data_sources": settings.data_sources.model_copy(
                update={
                    "raw_output_dir": tmp_path / "raw",
                    "allow_network_sources": False,
                    "allow_real_data_fetch": False,
                }
            ),
            "data_pipeline": settings.data_pipeline.model_copy(
                update={
                    "output_dir": reports / "data_pipeline",
                    "raw_output_dir": tmp_path / "raw",
                    "processed_output_dir": tmp_path / "processed",
                    "snapshot_output_dir": tmp_path / "snapshots",
                    "write_artifacts": True,
                }
            ),
            "data_quality": settings.data_quality.model_copy(
                update={"output_dir": reports / "data_quality"}
            ),
            "snapshot_quality_gate": settings.snapshot_quality_gate.model_copy(
                update={"output_dir": reports / "snapshot_quality"}
            ),
            "current_candidates": settings.current_candidates.model_copy(
                update={
                    "output_dir": reports / "current_candidates",
                    "default_top_n": 5,
                    "min_action": "NO_TRADE",
                    "min_final_score": None,
                    "write_artifacts": True,
                }
            ),
            "current_candidate_artifact_index": settings.current_candidate_artifact_index.model_copy(
                update={
                    "root_dir": reports / "current_candidates",
                    "output_dir": reports / "current_candidates" / "index",
                }
            ),
            "current_candidate_artifact_health": settings.current_candidate_artifact_health.model_copy(
                update={
                    "index_path": reports / "current_candidates" / "index" / "current_candidate_artifact_index.csv",
                    "root_dir": reports / "current_candidates",
                    "output_dir": reports / "current_candidates" / "health",
                }
            ),
            "current_to_paper_handoff": settings.current_to_paper_handoff.model_copy(
                update={"output_dir": reports / "current_to_paper_handoff"}
            ),
            "current_to_paper_review_handoff": settings.current_to_paper_review_handoff.model_copy(
                update={"output_dir": reports / "current_to_paper_review_handoff"}
            ),
            "paper_review_template_health": settings.paper_review_template_health.model_copy(
                update={"output_dir": reports / "paper_trading" / "review_template_health"}
            ),
            "paper_review": settings.paper_review.model_copy(
                update={"output_dir": reports / "paper_trading" / "reviews"}
            ),
            "daily_paper_runner": settings.daily_paper_runner.model_copy(
                update={"output_dir": reports / "paper_trading" / "daily"}
            ),
            "paper_reconciliation": settings.paper_reconciliation.model_copy(
                update={"output_dir": reports / "paper_trading" / "reconciliation"}
            ),
            "paper_artifact_index": settings.paper_artifact_index.model_copy(
                update={
                    "root_dir": reports / "paper_trading",
                    "output_dir": reports / "paper_trading" / "index",
                }
            ),
            "paper_artifact_health": settings.paper_artifact_health.model_copy(
                update={
                    "index_path": reports / "paper_trading" / "index" / "paper_artifact_index.csv",
                    "root_dir": reports / "paper_trading",
                    "output_dir": reports / "paper_trading" / "health",
                }
            ),
            "paper_workflow_status": settings.paper_workflow_status.model_copy(
                update={
                    "root_dir": reports,
                    "current_candidates_root": reports / "current_candidates",
                    "paper_trading_root": reports / "paper_trading",
                    "output_dir": reports / "paper_trading" / "workflow_status",
                }
            ),
            "data_preparation_artifact_index": settings.data_preparation_artifact_index.model_copy(
                update={
                    "root_dir": reports,
                    "output_dir": reports / "data_preparation" / "index",
                }
            ),
            "data_preparation_artifact_health": settings.data_preparation_artifact_health.model_copy(
                update={
                    "index_path": reports / "data_preparation" / "index" / "data_preparation_artifact_index.csv",
                    "root_dir": reports,
                    "output_dir": reports / "data_preparation" / "health",
                }
            ),
            "data_preparation_workflow_status": settings.data_preparation_workflow_status.model_copy(
                update={
                    "root_dir": reports,
                    "data_pipeline_root": reports / "data_pipeline",
                    "data_quality_root": reports / "data_quality",
                    "snapshot_quality_root": reports / "snapshot_quality",
                    "current_candidates_root": reports / "current_candidates",
                    "output_dir": reports / "data_preparation" / "workflow_status",
                }
            ),
            "local_research_dashboard": settings.local_research_dashboard.model_copy(
                update={
                    "root_dir": reports,
                    "data_preparation_root": reports / "data_preparation",
                    "current_candidates_root": reports / "current_candidates",
                    "paper_trading_root": reports / "paper_trading",
                    "output_dir": reports / "local_research_dashboard",
                }
            ),
        }
    )
    config_path = tmp_path / "e2e_config.yaml"
    config_path.write_text(yaml.safe_dump(settings.model_dump(mode="json"), sort_keys=False), encoding="utf-8")
    return config_path


def _edited_review_updates(template_path: Path) -> pd.DataFrame:
    updates = pd.read_csv(template_path)
    for column in ["manual_review_status", "review_reason_code", "manual_review_notes", "reviewer_id"]:
        updates[column] = updates[column].astype("object")
    for idx in updates.index:
        if idx == 0:
            updates.loc[idx, "manual_review_status"] = "APPROVED_FOR_PAPER"
            updates.loc[idx, "review_reason_code"] = "SCORE_CONFIRMED"
            updates.loc[idx, "manual_review_notes"] = "approved for e2e paper fill"
        else:
            updates.loc[idx, "manual_review_status"] = "WATCH_ONLY"
            updates.loc[idx, "review_reason_code"] = "WATCHLIST_ONLY"
            updates.loc[idx, "manual_review_notes"] = "watch only in e2e smoke test"
        updates.loc[idx, "reviewer_id"] = "e2e-reviewer"
    return updates


def _approved_fill(reviewed_decisions_path: Path) -> pd.DataFrame:
    reviewed = pd.read_csv(reviewed_decisions_path)
    approved = reviewed.loc[reviewed["manual_review_status"] == "APPROVED_FOR_PAPER"]
    assert not approved.empty
    decision = approved.iloc[0]
    quantity = 100
    fill_price = 10.0
    gross = quantity * fill_price
    return pd.DataFrame(
        [
            {
                "fill_id": "local-research-e2e-fill",
                "decision_id": decision["decision_id"],
                "symbol": decision["symbol"],
                "side": "BUY",
                "fill_date": DECISION_DATE,
                "fill_price": fill_price,
                "quantity": quantity,
                "gross_notional": gross,
                "fees": 0.0,
                "slippage": 0.0,
                "net_cash_flow": -gross,
                "fill_source": "MANUAL",
                "manual_notes": "manual local research e2e fill",
            }
        ]
    )


def _single_artifact_file(root: Path, filename: str) -> Path:
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    assert len(matches) == 1, f"expected one {filename} under {root}, found {matches}"
    return matches[0]
