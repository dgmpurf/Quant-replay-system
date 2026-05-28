"""Read-only proposal report from calibration artifacts to signal semantics."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from quant_replay_system.config import SignalSemanticsSettings, load_settings


PROPOSAL_CATEGORIES = [
    "KEEP_CURRENT_DEFAULTS",
    "CONSIDER_WATCH_EXPANSION",
    "DO_NOT_EXPAND_BUY_REVIEW_YET",
    "REQUIRE_MORE_EVIDENCE",
    "NEED_MULTI_DATE_VALIDATION",
    "NEED_MORE_SYMBOLS",
    "NEED_BACKTEST_OR_PAPER_EVIDENCE",
]

PROFILE_FALLBACK_THRESHOLDS = {
    "conservative": {"reviewed_buy_min_score": 75.0, "watch_min_score": 60.0},
    "balanced": {"reviewed_buy_min_score": 70.0, "watch_min_score": 55.0},
    "experimental": {"reviewed_buy_min_score": 65.0, "watch_min_score": 50.0},
}

SUMMARY_COLUMNS = [
    "proposal_run_id",
    "status",
    "calibration_root",
    "semantics_config",
    "calibration_run_count",
    "calibration_row_count",
    "observed_review_buy_candidate_count",
    "observed_watch_count",
    "observed_no_action_count",
    "observed_blocked_count",
    "observed_demo_only_count",
    "semantics_reviewed_buy_min_score",
    "semantics_watch_min_score",
    "conservative_reviewed_buy_min_score",
    "conservative_watch_min_score",
    "balanced_reviewed_buy_min_score",
    "balanced_watch_min_score",
    "experimental_reviewed_buy_min_score",
    "experimental_watch_min_score",
    "demo_only_run_count",
    "synthetic_review_buy_run_count",
    "data_quality_fail_gate_observed",
    "snapshot_quality_fail_gate_observed",
    "risk_block_gate_observed",
    "keep_current_defaults",
    "defaults_changed",
    "requires_manual_confirmation",
    "auto_order_allowed",
    "no_live_trading",
    "no_broker_api",
    "no_message_sent",
]

PROPOSAL_COLUMNS = [
    "proposal_run_id",
    "category",
    "severity",
    "recommendation",
    "rationale",
    "evidence",
    "changes_defaults",
]


@dataclass(frozen=True)
class CalibrationToSemanticsSettings:
    calibration_root: Path = Path("outputs/reports/advisory_profile_calibration")
    semantics_config: Path = Path("config/default.yaml")
    output_dir: Path = Path("outputs/reports/calibration_to_signal_semantics")
    config_version: str = "mvp"
    write_artifacts: bool = True
    enable_live_trading: bool = False
    enable_broker_api: bool = False
    enable_message_delivery: bool = False
    auto_order_allowed: bool = False


@dataclass(frozen=True)
class CalibrationRunSummary:
    calibration_run_id: str
    profile: str
    row_count: int
    review_buy_candidate_count: int
    watch_count: int
    no_action_count: int
    blocked_count: int
    demo_only_count: int
    issue_count: int
    reviewed_buy_min_score: float | None
    watch_min_score: float | None
    summary_path: Path
    issues_path: Path
    metadata_path: Path
    issue_codes: list[str]
    created_at: str


@dataclass(frozen=True)
class CalibrationToSemanticsInput:
    calibration_root: Path
    semantics_config: Path
    semantics_settings: SignalSemanticsSettings
    calibration_runs: list[CalibrationRunSummary]


@dataclass(frozen=True)
class CalibrationToSemanticsProposal:
    category: str
    severity: str
    recommendation: str
    rationale: str
    evidence: str
    changes_defaults: bool = False

    def as_dict(self, proposal_run_id: str) -> dict[str, Any]:
        return {
            "proposal_run_id": proposal_run_id,
            "category": self.category,
            "severity": self.severity,
            "recommendation": self.recommendation,
            "rationale": self.rationale,
            "evidence": self.evidence,
            "changes_defaults": self.changes_defaults,
        }


@dataclass(frozen=True)
class CalibrationToSemanticsResult:
    proposal_run_id: str
    status: str
    calibration_root: Path
    semantics_config: Path
    semantics_settings: SignalSemanticsSettings
    calibration_runs: list[CalibrationRunSummary]
    comparison: dict[str, Any]
    proposals: list[CalibrationToSemanticsProposal]
    summary_frame: pd.DataFrame
    proposals_frame: pd.DataFrame
    artifact_paths: dict[str, Path]
    warnings: list[str]
    defaults_changed: bool

    @property
    def proposal_categories(self) -> list[str]:
        return [proposal.category for proposal in self.proposals]


@dataclass(frozen=True)
class CalibrationToSemanticsArtifactPaths:
    artifact_dir: Path
    calibration_to_signal_semantics_report: Path
    calibration_to_signal_semantics_summary: Path
    calibration_to_signal_semantics_proposals: Path
    metadata: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "calibration_to_signal_semantics_report": self.calibration_to_signal_semantics_report,
            "calibration_to_signal_semantics_summary": self.calibration_to_signal_semantics_summary,
            "calibration_to_signal_semantics_proposals": self.calibration_to_signal_semantics_proposals,
            "metadata": self.metadata,
        }


def load_calibration_runs_for_proposal(
    *,
    calibration_root: str | Path = "outputs/reports/advisory_profile_calibration",
    semantics_config: str | Path = "config/default.yaml",
) -> CalibrationToSemanticsInput:
    """Load local calibration run summaries and current signal semantics settings."""

    root = Path(calibration_root)
    config_path = Path(semantics_config)
    settings = load_settings(config_path).signal_semantics
    runs = _load_calibration_run_summaries(root)
    return CalibrationToSemanticsInput(
        calibration_root=root,
        semantics_config=config_path,
        semantics_settings=settings,
        calibration_runs=runs,
    )


def compare_calibration_profiles_to_semantics_defaults(
    proposal_input: CalibrationToSemanticsInput,
) -> dict[str, Any]:
    """Compare observed calibration runs to current signal semantics defaults without changing them."""

    runs = proposal_input.calibration_runs
    profile_thresholds = _profile_thresholds(runs)
    issue_codes = [code for run in runs for code in run.issue_codes]
    row_count = sum(run.row_count for run in runs)
    comparison: dict[str, Any] = {
        "calibration_run_count": len(runs),
        "calibration_row_count": row_count,
        "observed_review_buy_candidate_count": sum(run.review_buy_candidate_count for run in runs),
        "observed_watch_count": sum(run.watch_count for run in runs),
        "observed_no_action_count": sum(run.no_action_count for run in runs),
        "observed_blocked_count": sum(run.blocked_count for run in runs),
        "observed_demo_only_count": sum(run.demo_only_count for run in runs),
        "semantics_reviewed_buy_min_score": float(proposal_input.semantics_settings.reviewed_buy_min_score),
        "semantics_watch_min_score": float(proposal_input.semantics_settings.watch_min_score),
        "demo_only_run_count": sum(1 for run in runs if run.demo_only_count > 0),
        "synthetic_review_buy_run_count": sum(
            1 for run in runs if run.review_buy_candidate_count > 0 and run.demo_only_count == 0
        ),
        "data_quality_fail_gate_observed": "DATA_QUALITY_FAILED" in issue_codes,
        "snapshot_quality_fail_gate_observed": "SNAPSHOT_QUALITY_FAILED" in issue_codes,
        "risk_block_gate_observed": "RISK_BLOCKED" in issue_codes,
        "keep_current_defaults": True,
        "defaults_changed": False,
    }
    for profile in ("conservative", "balanced", "experimental"):
        thresholds = profile_thresholds.get(profile, PROFILE_FALLBACK_THRESHOLDS[profile])
        comparison[f"{profile}_reviewed_buy_min_score"] = float(thresholds["reviewed_buy_min_score"])
        comparison[f"{profile}_watch_min_score"] = float(thresholds["watch_min_score"])
    return comparison


def build_calibration_to_semantics_proposal(
    *,
    calibration_root: str | Path = "outputs/reports/advisory_profile_calibration",
    semantics_config: str | Path = "config/default.yaml",
    output_dir: str | Path = "outputs/reports/calibration_to_signal_semantics",
    settings: CalibrationToSemanticsSettings | None = None,
) -> CalibrationToSemanticsResult:
    """Build a read-only profile refinement proposal from calibration artifacts."""

    resolved = _resolve_settings(
        settings,
        calibration_root=calibration_root,
        semantics_config=semantics_config,
        output_dir=output_dir,
    )
    _assert_settings_safe(resolved)
    proposal_input = load_calibration_runs_for_proposal(
        calibration_root=resolved.calibration_root,
        semantics_config=resolved.semantics_config,
    )
    comparison = compare_calibration_profiles_to_semantics_defaults(proposal_input)
    proposals = _build_proposals(comparison)
    proposal_run_id = _proposal_run_id(
        comparison,
        proposals=proposals,
        semantics_config=resolved.semantics_config,
        config_version=resolved.config_version,
    )
    paths = resolve_calibration_to_signal_semantics_artifact_paths(resolved.output_dir, proposal_run_id)
    warnings = _build_warnings(proposal_input, comparison)
    summary_frame = _summary_frame(
        proposal_run_id=proposal_run_id,
        status="WARN",
        proposal_input=proposal_input,
        comparison=comparison,
    )
    proposals_frame = pd.DataFrame(
        [proposal.as_dict(proposal_run_id) for proposal in proposals],
        columns=PROPOSAL_COLUMNS,
    )
    result = CalibrationToSemanticsResult(
        proposal_run_id=proposal_run_id,
        status="WARN",
        calibration_root=resolved.calibration_root,
        semantics_config=resolved.semantics_config,
        semantics_settings=proposal_input.semantics_settings,
        calibration_runs=proposal_input.calibration_runs,
        comparison=comparison,
        proposals=proposals,
        summary_frame=summary_frame,
        proposals_frame=proposals_frame,
        artifact_paths=paths.as_dict(),
        warnings=warnings,
        defaults_changed=False,
    )
    if resolved.write_artifacts:
        write_calibration_to_semantics_artifacts(result)
    return result


def run_calibration_to_signal_semantics(
    *,
    calibration_root: str | Path = "outputs/reports/advisory_profile_calibration",
    semantics_config: str | Path = "config/default.yaml",
    output_dir: str | Path = "outputs/reports/calibration_to_signal_semantics",
    settings: CalibrationToSemanticsSettings | None = None,
) -> CalibrationToSemanticsResult:
    """Run the read-only calibration-to-semantics proposal report."""

    return build_calibration_to_semantics_proposal(
        calibration_root=calibration_root,
        semantics_config=semantics_config,
        output_dir=output_dir,
        settings=settings,
    )


def resolve_calibration_to_signal_semantics_artifact_paths(
    output_dir: str | Path,
    proposal_run_id: str,
) -> CalibrationToSemanticsArtifactPaths:
    artifact_dir = Path(output_dir) / proposal_run_id
    return CalibrationToSemanticsArtifactPaths(
        artifact_dir=artifact_dir,
        calibration_to_signal_semantics_report=artifact_dir / "calibration_to_signal_semantics_report.md",
        calibration_to_signal_semantics_summary=artifact_dir / "calibration_to_signal_semantics_summary.csv",
        calibration_to_signal_semantics_proposals=artifact_dir / "calibration_to_signal_semantics_proposals.csv",
        metadata=artifact_dir / "metadata.json",
    )


def write_calibration_to_semantics_artifacts(result: CalibrationToSemanticsResult) -> dict[str, Path]:
    """Write proposal report, summary, proposals, and metadata artifacts."""

    paths = CalibrationToSemanticsArtifactPaths(**result.artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    _export_dataframe(result.summary_frame, paths.calibration_to_signal_semantics_summary)
    _export_dataframe(result.proposals_frame, paths.calibration_to_signal_semantics_proposals)
    paths.calibration_to_signal_semantics_report.write_text(
        render_calibration_to_semantics_report(result),
        encoding="utf-8",
    )
    paths.metadata.write_text(
        json.dumps(_json_safe(build_calibration_to_semantics_metadata(result)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths.as_dict()


def render_calibration_to_semantics_report(result: CalibrationToSemanticsResult) -> str:
    """Render a local markdown proposal report."""

    lines = [
        f"# Calibration-to-Signal Semantics Proposal: {result.proposal_run_id}",
        "",
        "This is not strategy validation.",
        "This report does not approve non-demo trading.",
        "REVIEW_BUY_CANDIDATE remains human-review-only and is not an order.",
        "No live trading, broker API, automated order placement, message delivery, LLM API, or external API was invoked.",
        "",
        "## Recommendation",
        "",
        "Keep current signal semantics defaults. Use calibration outputs as design evidence only.",
        "The next safe implementation should focus on WATCH semantics or evidence collection, not automatic buy-review expansion.",
        "",
        "## Summary",
        "",
        _dict_table(result.summary_frame.iloc[0].to_dict() if not result.summary_frame.empty else {}),
        "",
        "## Current Signal Semantics Defaults",
        "",
        _dict_table(
            {
                "reviewed_buy_min_score": result.semantics_settings.reviewed_buy_min_score,
                "watch_min_score": result.semantics_settings.watch_min_score,
                "require_data_quality_pass": result.semantics_settings.require_data_quality_pass,
                "require_snapshot_quality_pass": result.semantics_settings.require_snapshot_quality_pass,
                "allow_review_buy_for_demo": result.semantics_settings.allow_review_buy_for_demo,
                "allow_auto_order": result.semantics_settings.allow_auto_order,
            }
        ),
        "",
        "## Calibration Profile Thresholds",
        "",
        _profile_threshold_table(result.comparison),
        "",
        "## Proposal Categories",
        "",
        _markdown_table(result.proposals_frame, PROPOSAL_COLUMNS),
        "",
        "## Calibration Runs Read",
        "",
        _markdown_table(_calibration_runs_frame(result.calibration_runs), _calibration_run_columns()),
        "",
        "## Mandatory Gates",
        "",
        _dict_table(
            {
                "valid_symbol_required": True,
                "risk_precheck_block_is_mandatory": True,
                "data_quality_fail_blocks": True,
                "snapshot_quality_fail_blocks": True,
                "market_or_execution_unavailable_blocks": True,
                "NO_TRADE_does_not_become_buy_review_from_score": True,
            }
        ),
        "",
        "## Safety",
        "",
        _dict_table(
            {
                "requires_manual_confirmation": True,
                "auto_order_allowed": False,
                "no_live_trading": True,
                "no_broker_api": True,
                "no_message_sent": True,
                "external_api_called": False,
                "llm_api_called": False,
                "defaults_changed": False,
            }
        ),
        "",
        "## Warnings",
        "",
        _warnings_section(result.warnings),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def build_calibration_to_semantics_metadata(result: CalibrationToSemanticsResult) -> dict[str, Any]:
    return {
        "proposal_run_id": result.proposal_run_id,
        "status": result.status,
        "created_at": "",
        "calibration_root": str(result.calibration_root),
        "semantics_config": str(result.semantics_config),
        "calibration_run_count": len(result.calibration_runs),
        "proposal_categories": result.proposal_categories,
        "comparison": result.comparison,
        "defaults_changed": False,
        "signal_semantics_defaults_changed": False,
        "config_mutated": False,
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
        "message_sent": False,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "message_delivery_enabled": False,
        "external_api_called": False,
        "llm_api_called": False,
        "approved_for_paper_applied": False,
        "report_only": True,
        "not_strategy_validation": True,
        "review_buy_candidate_is_order": False,
        "recommended_next_focus": "WATCH semantics or evidence collection before non-demo buy-review expansion.",
        "output_files": {
            key: str(path)
            for key, path in result.artifact_paths.items()
            if key != "artifact_dir"
        },
        "known_limitations": [
            "Calibration artifacts are local design evidence only.",
            "Demo artifacts validate workflow safety, not strategy quality.",
            "Synthetic fixtures prove rule behavior, not market edge.",
            "This report does not modify signal_semantics defaults or executable strategy settings.",
        ],
    }


def _load_calibration_run_summaries(root: Path) -> list[CalibrationRunSummary]:
    if not root.exists():
        return []
    runs: list[CalibrationRunSummary] = []
    for metadata_path in sorted(root.glob("*/metadata.json")):
        metadata = _load_json_or_empty(metadata_path)
        calibration_run_id = _text(metadata.get("calibration_run_id")) or metadata_path.parent.name
        if not calibration_run_id:
            continue
        output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
        summary_path = Path(
            output_files.get("advisory_profile_calibration_summary")
            or metadata_path.parent / "advisory_profile_calibration_summary.csv"
        )
        issues_path = Path(
            output_files.get("advisory_profile_calibration_issues")
            or metadata_path.parent / "advisory_profile_calibration_issues.csv"
        )
        summary = _first_csv_record(summary_path)
        profile = _text(summary.get("profile")) or _text(metadata.get("profile"))
        profile_definition = metadata.get("profile_definition") if isinstance(metadata.get("profile_definition"), dict) else {}
        runs.append(
            CalibrationRunSummary(
                calibration_run_id=calibration_run_id,
                profile=profile,
                row_count=_int_or_zero(summary.get("row_count") or metadata.get("row_count")),
                review_buy_candidate_count=_int_or_zero(
                    summary.get("review_buy_candidate_count")
                    or _metadata_label_count(metadata, "REVIEW_BUY_CANDIDATE")
                ),
                watch_count=_int_or_zero(summary.get("watch_count") or _metadata_label_count(metadata, "WATCH")),
                no_action_count=_int_or_zero(summary.get("no_action_count") or _metadata_label_count(metadata, "NO_ACTION")),
                blocked_count=_int_or_zero(summary.get("blocked_count") or _metadata_label_count(metadata, "BLOCKED")),
                demo_only_count=_int_or_zero(summary.get("demo_only_count") or _metadata_label_count(metadata, "DEMO_ONLY")),
                issue_count=_int_or_zero(summary.get("issue_count") or metadata.get("issue_count")),
                reviewed_buy_min_score=_float_or_none(profile_definition.get("reviewed_buy_min_score")),
                watch_min_score=_float_or_none(profile_definition.get("watch_min_score")),
                summary_path=summary_path,
                issues_path=issues_path,
                metadata_path=metadata_path,
                issue_codes=_issue_codes(issues_path),
                created_at=_text(metadata.get("created_at")),
            )
        )
    return sorted(runs, key=lambda run: (run.created_at, run.calibration_run_id))


def _profile_thresholds(runs: list[CalibrationRunSummary]) -> dict[str, dict[str, float]]:
    thresholds = {profile: values.copy() for profile, values in PROFILE_FALLBACK_THRESHOLDS.items()}
    for run in runs:
        profile = run.profile.strip().lower()
        if profile in thresholds and run.reviewed_buy_min_score is not None and run.watch_min_score is not None:
            thresholds[profile] = {
                "reviewed_buy_min_score": float(run.reviewed_buy_min_score),
                "watch_min_score": float(run.watch_min_score),
            }
    return thresholds


def _build_proposals(comparison: dict[str, Any]) -> list[CalibrationToSemanticsProposal]:
    evidence = (
        f"runs={comparison['calibration_run_count']}; rows={comparison['calibration_row_count']}; "
        f"review_buy={comparison['observed_review_buy_candidate_count']}; "
        f"watch={comparison['observed_watch_count']}; demo_only={comparison['observed_demo_only_count']}."
    )
    proposals = [
        CalibrationToSemanticsProposal(
            category="KEEP_CURRENT_DEFAULTS",
            severity="INFO",
            recommendation="Keep current signal_semantics thresholds and safety gates unchanged.",
            rationale="Calibration output is useful for design, but current evidence does not validate strategy quality.",
            evidence=evidence,
        ),
        CalibrationToSemanticsProposal(
            category="CONSIDER_WATCH_EXPANSION",
            severity="INFO",
            recommendation="Explore WATCH semantics before expanding REVIEW_BUY_CANDIDATE.",
            rationale="WATCH is review context and is safer to broaden before buy-review labels.",
            evidence=evidence,
        ),
        CalibrationToSemanticsProposal(
            category="DO_NOT_EXPAND_BUY_REVIEW_YET",
            severity="WARN",
            recommendation="Do not expand non-demo buy-review thresholds from calibration artifacts alone.",
            rationale="Synthetic REVIEW_BUY_CANDIDATE rows prove rule behavior, not market edge.",
            evidence=evidence,
        ),
        CalibrationToSemanticsProposal(
            category="REQUIRE_MORE_EVIDENCE",
            severity="WARN",
            recommendation="Require more real local research evidence before changing signal_semantics defaults.",
            rationale="Demo-only and synthetic runs are insufficient for production-facing threshold changes.",
            evidence=evidence,
        ),
        CalibrationToSemanticsProposal(
            category="NEED_MULTI_DATE_VALIDATION",
            severity="WARN",
            recommendation="Collect multi-date calibration evidence before non-demo semantics changes.",
            rationale="Single-date or fixture-only calibration cannot establish robust behavior.",
            evidence=evidence,
        ),
        CalibrationToSemanticsProposal(
            category="NEED_MORE_SYMBOLS",
            severity="WARN",
            recommendation="Collect broader symbol coverage before changing non-demo thresholds.",
            rationale="Small local samples are vulnerable to overfitting and do not validate strategy quality.",
            evidence=evidence,
        ),
        CalibrationToSemanticsProposal(
            category="NEED_BACKTEST_OR_PAPER_EVIDENCE",
            severity="WARN",
            recommendation="Require backtest, paper review, or comparable evidence before treating labels as calibrated.",
            rationale="Profile thresholds should not become real advisory semantics without audited evidence.",
            evidence=evidence,
        ),
    ]
    return proposals


def _summary_frame(
    *,
    proposal_run_id: str,
    status: str,
    proposal_input: CalibrationToSemanticsInput,
    comparison: dict[str, Any],
) -> pd.DataFrame:
    row = {
        "proposal_run_id": proposal_run_id,
        "status": status,
        "calibration_root": str(proposal_input.calibration_root),
        "semantics_config": str(proposal_input.semantics_config),
        **comparison,
        "requires_manual_confirmation": True,
        "auto_order_allowed": False,
        "no_live_trading": True,
        "no_broker_api": True,
        "no_message_sent": True,
    }
    return pd.DataFrame([row], columns=SUMMARY_COLUMNS)


def _calibration_runs_frame(runs: list[CalibrationRunSummary]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "calibration_run_id": run.calibration_run_id,
                "profile": run.profile,
                "row_count": run.row_count,
                "review_buy_candidate_count": run.review_buy_candidate_count,
                "watch_count": run.watch_count,
                "no_action_count": run.no_action_count,
                "blocked_count": run.blocked_count,
                "demo_only_count": run.demo_only_count,
                "issue_count": run.issue_count,
                "issue_codes": ";".join(run.issue_codes),
            }
            for run in runs
        ],
        columns=_calibration_run_columns(),
    )


def _calibration_run_columns() -> list[str]:
    return [
        "calibration_run_id",
        "profile",
        "row_count",
        "review_buy_candidate_count",
        "watch_count",
        "no_action_count",
        "blocked_count",
        "demo_only_count",
        "issue_count",
        "issue_codes",
    ]


def _profile_threshold_table(comparison: dict[str, Any]) -> str:
    frame = pd.DataFrame(
        [
            {
                "source": "signal_semantics_current",
                "reviewed_buy_min_score": comparison["semantics_reviewed_buy_min_score"],
                "watch_min_score": comparison["semantics_watch_min_score"],
            },
            {
                "source": "conservative",
                "reviewed_buy_min_score": comparison["conservative_reviewed_buy_min_score"],
                "watch_min_score": comparison["conservative_watch_min_score"],
            },
            {
                "source": "balanced",
                "reviewed_buy_min_score": comparison["balanced_reviewed_buy_min_score"],
                "watch_min_score": comparison["balanced_watch_min_score"],
            },
            {
                "source": "experimental",
                "reviewed_buy_min_score": comparison["experimental_reviewed_buy_min_score"],
                "watch_min_score": comparison["experimental_watch_min_score"],
            },
        ]
    )
    return _markdown_table(frame, ["source", "reviewed_buy_min_score", "watch_min_score"])


def _proposal_run_id(
    comparison: dict[str, Any],
    *,
    proposals: list[CalibrationToSemanticsProposal],
    semantics_config: Path,
    config_version: str,
) -> str:
    payload = {
        "comparison": comparison,
        "categories": [proposal.category for proposal in proposals],
        "semantics_config": str(semantics_config),
        "config_version": config_version,
    }
    return _hash_payload(payload, length=12)


def _build_warnings(
    proposal_input: CalibrationToSemanticsInput,
    comparison: dict[str, Any],
) -> list[str]:
    warnings = [
        "Calibration-to-semantics proposal is report-only and does not modify signal_semantics defaults.",
        "REVIEW_BUY_CANDIDATE remains human-review-only and is not an order.",
    ]
    if comparison["observed_demo_only_count"]:
        warnings.append("Demo calibration rows are workflow/safety validation only.")
    if comparison["synthetic_review_buy_run_count"]:
        warnings.append("Synthetic review-buy labels prove rule behavior, not market edge.")
    if not proposal_input.calibration_runs:
        warnings.append("No calibration artifacts were found; collect evidence before changing thresholds.")
    return warnings


def _resolve_settings(
    settings: CalibrationToSemanticsSettings | None,
    *,
    calibration_root: str | Path,
    semantics_config: str | Path,
    output_dir: str | Path,
) -> CalibrationToSemanticsSettings:
    base = settings or CalibrationToSemanticsSettings()
    return CalibrationToSemanticsSettings(
        calibration_root=Path(calibration_root or base.calibration_root),
        semantics_config=Path(semantics_config or base.semantics_config),
        output_dir=Path(output_dir or base.output_dir),
        config_version=base.config_version,
        write_artifacts=base.write_artifacts,
        enable_live_trading=base.enable_live_trading,
        enable_broker_api=base.enable_broker_api,
        enable_message_delivery=base.enable_message_delivery,
        auto_order_allowed=base.auto_order_allowed,
    )


def _assert_settings_safe(settings: CalibrationToSemanticsSettings) -> None:
    if settings.enable_live_trading:
        raise ValueError("Calibration-to-semantics proposal cannot enable live trading.")
    if settings.enable_broker_api:
        raise ValueError("Calibration-to-semantics proposal cannot enable broker API access.")
    if settings.enable_message_delivery:
        raise ValueError("Calibration-to-semantics proposal cannot enable message delivery.")
    if settings.auto_order_allowed:
        raise ValueError("Calibration-to-semantics proposal cannot allow auto-order.")


def _load_json_or_empty(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _first_csv_record(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        frame = pd.read_csv(path)
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError):
        return {}
    if frame.empty:
        return {}
    return frame.iloc[0].to_dict()


def _issue_codes(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        frame = pd.read_csv(path)
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError):
        return []
    if frame.empty or "issue_code" not in frame.columns:
        return []
    return [str(value).strip().upper() for value in frame["issue_code"].dropna().astype(str) if str(value).strip()]


def _metadata_label_count(metadata: dict[str, Any], label: str) -> int:
    label_counts = metadata.get("label_counts")
    if not isinstance(label_counts, dict):
        return 0
    return _int_or_zero(label_counts.get(label))


def _int_or_zero(value: Any) -> int:
    try:
        if pd.isna(value):
            return 0
    except (TypeError, ValueError):
        pass
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _float_or_none(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _export_dataframe(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _dict_table(values: dict[str, Any]) -> str:
    if not values:
        return "_No values._"
    rows = ["| Field | Value |", "| --- | --- |"]
    for key, value in values.items():
        rows.append(f"| `{key}` | `{_format_markdown_value(value)}` |")
    return "\n".join(rows)


def _markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 50) -> str:
    available = [column for column in columns if column in frame.columns]
    if frame.empty or not available:
        return "_No rows._"
    rows = [
        "| " + " | ".join(available) + " |",
        "| " + " | ".join("---" for _ in available) + " |",
    ]
    for record in frame.loc[:, available].head(max_rows).to_dict("records"):
        rows.append("| " + " | ".join(_format_markdown_value(record[column]) for column in available) + " |")
    return "\n".join(rows)


def _warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return "- None"
    return "\n".join(f"- {warning}" for warning in warnings)


def _format_markdown_value(value: Any) -> str:
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        return f"{value:.6g}"
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.DataFrame):
        return [_json_safe(record) for record in value.to_dict("records")]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
