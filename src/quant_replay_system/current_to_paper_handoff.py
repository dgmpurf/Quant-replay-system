"""Local-only handoff from current-candidate artifacts to daily paper trading."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_replay_system.config import CurrentToPaperHandoffSettings, Settings, load_settings
from quant_replay_system.current_candidate_artifact_health import check_current_candidate_artifact_health
from quant_replay_system.current_candidate_artifact_index import (
    CURRENT_CANDIDATE_INDEX_COLUMNS,
    scan_current_candidate_artifacts,
)
from quant_replay_system.daily_paper_runner import DailyPaperRunResult, run_daily_paper_trading


CURRENT_TO_PAPER_HANDOFF_LIMITATIONS = [
    "Uses local CSV/mock data only.",
    "Selects current-candidate artifacts already written by the local current-candidates workflow.",
    "Runs daily paper trading only; it does not place live orders or call broker APIs.",
    "Direct candidates_path handoff skips artifact health checks unless an index/root is supplied.",
    "Health checks validate local artifact files but do not regenerate candidates or repair paths.",
]


@dataclass(frozen=True)
class SelectedCurrentCandidateArtifact:
    source_type: str
    candidates_path: Path
    report_path: Path | None
    metadata_path: Path | None
    decision_date: pd.Timestamp | None
    universe_name: str
    run_id: str
    candidate_count: int | None
    health_status: str | None
    index_row: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "candidates_path": self.candidates_path,
            "report_path": self.report_path,
            "metadata_path": self.metadata_path,
            "decision_date": self.decision_date,
            "universe_name": self.universe_name,
            "run_id": self.run_id,
            "candidate_count": self.candidate_count,
            "health_status": self.health_status,
            "index_row": self.index_row,
        }


@dataclass(frozen=True)
class CurrentToPaperHandoffArtifactPaths:
    artifact_dir: Path
    handoff_report: Path
    selected_current_candidate: Path
    handoff_metadata: Path
    paper_daily_artifacts: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "artifact_dir": self.artifact_dir,
            "handoff_report": self.handoff_report,
            "selected_current_candidate": self.selected_current_candidate,
            "handoff_metadata": self.handoff_metadata,
            "paper_daily_artifacts": self.paper_daily_artifacts,
        }


@dataclass(frozen=True)
class CurrentToPaperHandoffResult:
    handoff_id: str
    paper_date: pd.Timestamp
    selected_candidates_path: Path
    selected_current_candidate_report_path: Path | None
    selected_current_candidate_metadata_path: Path | None
    selected_decision_date: pd.Timestamp | None
    selected_universe_name: str
    selected_run_id: str
    health_status: str | None
    paper_journal_id: str
    paper_artifact_paths: dict[str, Path]
    handoff_artifact_paths: dict[str, Path]
    warnings: list[str]
    known_limitations: list[str]
    selected_artifact: SelectedCurrentCandidateArtifact
    paper_result: DailyPaperRunResult
    audit_metadata: dict[str, Any]


def select_current_candidate_artifact_for_paper(
    *,
    current_candidate_index_path: str | Path | None = None,
    current_candidate_root: str | Path | None = None,
    candidates_path: str | Path | None = None,
    decision_date: str | pd.Timestamp | None = None,
    universe_name: str | None = None,
    run_id: str | None = None,
    require_health_pass: bool | None = None,
    allow_health_warn: bool | None = None,
    skip_health_check: bool = False,
    config: Settings | str | Path | None = None,
) -> tuple[SelectedCurrentCandidateArtifact, list[str]]:
    """Select one current-candidate candidates.csv artifact for paper trading."""

    settings = _load_project_settings(config)
    handoff_settings = settings.current_to_paper_handoff
    if handoff_settings.enable_live_trading or handoff_settings.enable_broker_api:
        raise ValueError("Current-to-paper handoff cannot enable live trading or broker API access")

    effective_require_health = (
        handoff_settings.require_health_pass if require_health_pass is None else bool(require_health_pass)
    )
    effective_allow_warn = handoff_settings.allow_health_warn if allow_health_warn is None else bool(allow_health_warn)

    if candidates_path is not None:
        selected = _selected_from_direct_candidates_path(
            Path(candidates_path),
            decision_date=decision_date,
            universe_name=universe_name,
            run_id=run_id,
        )
        warnings = []
        if not skip_health_check:
            warnings.append("Health check skipped for direct candidates_path handoff.")
        return selected, warnings

    index_frame, index_source = _load_candidate_index_frame(
        current_candidate_index_path=current_candidate_index_path,
        current_candidate_root=current_candidate_root,
    )
    filtered = _filter_index_frame(
        index_frame,
        decision_date=decision_date,
        universe_name=universe_name,
        run_id=run_id,
    )
    if filtered.empty:
        raise ValueError("No current-candidate artifacts matched the requested selection criteria")

    warnings: list[str] = []
    if not skip_health_check:
        filtered, health_warnings = _attach_health_status(filtered, settings=settings)
        warnings.extend(health_warnings)
        filtered = _filter_by_health_requirement(
            filtered,
            require_health_pass=effective_require_health,
            allow_health_warn=effective_allow_warn,
        )
        if filtered.empty:
            raise ValueError(
                "No current-candidate artifacts passed health requirements "
                f"(require_health_pass={effective_require_health}, allow_health_warn={effective_allow_warn})"
            )
    else:
        filtered = filtered.copy(deep=True)
        filtered["health_status"] = ""
        warnings.append("Current-candidate artifact health check skipped by configuration.")

    sorted_frame = _sort_candidate_index(filtered, prefer_latest=handoff_settings.prefer_latest)
    selected = _selected_from_index_row(sorted_frame.iloc[0].to_dict(), index_source=index_source)
    _assert_selected_candidates_exists(selected)
    if selected.health_status == "WARN":
        warnings.append(f"Selected current-candidate artifact has health status WARN: {selected.run_id}")
    return selected, warnings


def run_current_to_paper_handoff(
    paper_date: str | pd.Timestamp | None = None,
    *,
    current_candidate_index_path: str | Path | None = None,
    current_candidate_root: str | Path | None = None,
    candidates_path: str | Path | None = None,
    decision_date: str | pd.Timestamp | None = None,
    universe_name: str | None = None,
    run_id: str | None = None,
    fills_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    journal_id: str | None = None,
    require_health_pass: bool | None = None,
    allow_health_warn: bool | None = None,
    skip_health_check: bool = False,
    config: Settings | str | Path | None = None,
) -> CurrentToPaperHandoffResult:
    """Select a current-candidate artifact and launch daily paper trading."""

    settings = _load_project_settings(config)
    handoff_settings = settings.current_to_paper_handoff
    if handoff_settings.enable_live_trading or handoff_settings.enable_broker_api:
        raise ValueError("Current-to-paper handoff cannot enable live trading or broker API access")
    if output_dir is not None:
        settings = settings.model_copy(
            update={
                "current_to_paper_handoff": handoff_settings.model_copy(update={"output_dir": Path(output_dir)})
            }
        )
        handoff_settings = settings.current_to_paper_handoff

    selected, warnings = select_current_candidate_artifact_for_paper(
        current_candidate_index_path=current_candidate_index_path,
        current_candidate_root=current_candidate_root,
        candidates_path=candidates_path,
        decision_date=decision_date,
        universe_name=universe_name,
        run_id=run_id,
        require_health_pass=require_health_pass,
        allow_health_warn=allow_health_warn,
        skip_health_check=skip_health_check,
        config=settings,
    )
    effective_paper_date = _resolve_paper_date(
        paper_date,
        selected.decision_date,
        default_from_decision_date=handoff_settings.default_paper_date_from_decision_date,
    )
    handoff_id = generate_current_to_paper_handoff_id(
        paper_date=effective_paper_date,
        selected_candidates_path=selected.candidates_path,
        selected_run_id=selected.run_id,
        fills_path=fills_path,
        config_version=handoff_settings.config_version,
    )
    paper_result = run_daily_paper_trading(
        effective_paper_date,
        candidates_path=selected.candidates_path,
        fills_path=fills_path,
        journal_id=journal_id,
        config=settings,
    )
    paths = resolve_current_to_paper_handoff_paths(handoff_settings.output_dir, handoff_id)
    audit_metadata = _build_audit_metadata(
        handoff_id=handoff_id,
        paper_date=effective_paper_date,
        selected=selected,
        paper_result=paper_result,
        settings=handoff_settings,
        fills_path=fills_path,
        skip_health_check=skip_health_check,
    )
    result = CurrentToPaperHandoffResult(
        handoff_id=handoff_id,
        paper_date=effective_paper_date,
        selected_candidates_path=selected.candidates_path,
        selected_current_candidate_report_path=selected.report_path,
        selected_current_candidate_metadata_path=selected.metadata_path,
        selected_decision_date=selected.decision_date,
        selected_universe_name=selected.universe_name,
        selected_run_id=selected.run_id,
        health_status=selected.health_status,
        paper_journal_id=paper_result.journal_id,
        paper_artifact_paths=paper_result.artifact_paths,
        handoff_artifact_paths=paths.as_dict(),
        warnings=[*warnings, *paper_result.warnings],
        known_limitations=CURRENT_TO_PAPER_HANDOFF_LIMITATIONS,
        selected_artifact=selected,
        paper_result=paper_result,
        audit_metadata=audit_metadata,
    )
    _augment_paper_daily_metadata(result)
    if handoff_settings.write_artifacts:
        write_current_to_paper_handoff_artifacts(result)
    return result


def generate_current_to_paper_handoff_id(
    *,
    paper_date: str | pd.Timestamp,
    selected_candidates_path: str | Path,
    selected_run_id: str,
    fills_path: str | Path | None = None,
    config_version: str = "mvp",
) -> str:
    """Generate a deterministic id for a current-to-paper handoff."""

    payload = {
        "paper_date": str(_normalize_date(paper_date).date()),
        "selected_candidates_path": str(selected_candidates_path),
        "selected_run_id": str(selected_run_id),
        "fills_path": str(fills_path) if fills_path is not None else "",
        "config_version": config_version,
    }
    return _hash_payload(payload, length=12)


def resolve_current_to_paper_handoff_paths(
    output_dir: str | Path,
    handoff_id: str,
) -> CurrentToPaperHandoffArtifactPaths:
    """Resolve stable current-to-paper handoff artifact paths."""

    artifact_dir = Path(output_dir) / handoff_id
    return CurrentToPaperHandoffArtifactPaths(
        artifact_dir=artifact_dir,
        handoff_report=artifact_dir / "handoff_report.md",
        selected_current_candidate=artifact_dir / "selected_current_candidate.json",
        handoff_metadata=artifact_dir / "handoff_metadata.json",
        paper_daily_artifacts=artifact_dir / "paper_daily_artifacts.json",
    )


def build_current_to_paper_metadata(result: CurrentToPaperHandoffResult) -> dict[str, Any]:
    """Build handoff metadata JSON."""

    return {
        "handoff_id": result.handoff_id,
        "paper_date": result.paper_date,
        "selected_candidates_path": result.selected_candidates_path,
        "selected_current_candidate_report_path": result.selected_current_candidate_report_path,
        "selected_current_candidate_metadata_path": result.selected_current_candidate_metadata_path,
        "selected_decision_date": result.selected_decision_date,
        "selected_universe_name": result.selected_universe_name,
        "selected_run_id": result.selected_run_id,
        "health_status": result.health_status,
        "paper_journal_id": result.paper_journal_id,
        "paper_artifact_paths": result.paper_artifact_paths,
        "handoff_artifact_paths": result.handoff_artifact_paths,
        "warnings": result.warnings,
        "known_limitations": result.known_limitations,
        "audit_metadata": result.audit_metadata,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "no_live_trading_statement": "No broker or live trading integration was invoked.",
    }


def write_current_to_paper_handoff_artifacts(result: CurrentToPaperHandoffResult) -> dict[str, Path]:
    """Write handoff report, selected artifact metadata, and JSON pointers."""

    paths = CurrentToPaperHandoffArtifactPaths(**result.handoff_artifact_paths)
    paths.artifact_dir.mkdir(parents=True, exist_ok=True)
    selected_payload = _selected_payload(result.selected_artifact)
    paths.selected_current_candidate.write_text(
        json.dumps(_json_safe(selected_payload), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    metadata = build_current_to_paper_metadata(result)
    metadata["output_files"] = {key: str(value) for key, value in paths.as_dict().items() if key != "artifact_dir"}
    paths.handoff_metadata.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")
    paths.paper_daily_artifacts.write_text(
        json.dumps(_json_safe(result.paper_artifact_paths), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    paths.handoff_report.write_text(render_current_to_paper_handoff_report(result, metadata), encoding="utf-8")
    return paths.as_dict()


def render_current_to_paper_handoff_report(
    result: CurrentToPaperHandoffResult,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render a markdown current-to-paper handoff report."""

    _ = metadata
    lines = [
        f"# Current Candidate To Paper Handoff: {result.handoff_id}",
        "",
        "No broker or live trading integration was invoked. This handoff selects local candidate artifacts and launches local paper reporting only.",
        "",
        "## Handoff Metadata",
        "",
        _dict_table(
            {
                "handoff_id": result.handoff_id,
                "paper_date": result.paper_date,
                "selected_decision_date": result.selected_decision_date,
                "selected_universe_name": result.selected_universe_name,
                "selected_run_id": result.selected_run_id,
                "health_status": result.health_status,
                "paper_journal_id": result.paper_journal_id,
            }
        ),
        "",
        "## Selected Current Candidate Artifact",
        "",
        _dict_table(
            {
                "source_type": result.selected_artifact.source_type,
                "candidates_path": result.selected_candidates_path,
                "report_path": result.selected_current_candidate_report_path,
                "metadata_path": result.selected_current_candidate_metadata_path,
                "candidate_count": result.selected_artifact.candidate_count,
            }
        ),
        "",
        "## Paper Daily Artifacts",
        "",
        _dict_table(result.paper_artifact_paths),
        "",
        "## Handoff Artifacts",
        "",
        _dict_table(result.handoff_artifact_paths),
        "",
        "## Warnings",
        "",
        _warnings_section(result.warnings),
        "",
        "## Known MVP Limitations",
        "",
        "\n".join(f"- {item}" for item in result.known_limitations),
        "",
    ]
    return "\n".join(str(line) for line in lines)


def _load_candidate_index_frame(
    *,
    current_candidate_index_path: str | Path | None,
    current_candidate_root: str | Path | None,
) -> tuple[pd.DataFrame, str]:
    if current_candidate_index_path is not None:
        path = Path(current_candidate_index_path)
        if not path.exists():
            raise FileNotFoundError(f"Current-candidate artifact index CSV not found: {path}")
        return _prepare_index_frame(pd.read_csv(path)), str(path)
    if current_candidate_root is not None:
        root = Path(current_candidate_root)
        return _prepare_index_frame(scan_current_candidate_artifacts(root)), str(root)
    raise ValueError("Provide candidates_path, current_candidate_index_path, or current_candidate_root")


def _filter_index_frame(
    frame: pd.DataFrame,
    *,
    decision_date: str | pd.Timestamp | None,
    universe_name: str | None,
    run_id: str | None,
) -> pd.DataFrame:
    filtered = _prepare_index_frame(frame)
    if decision_date is not None:
        target_date = str(_normalize_date(decision_date).date())
        dates = pd.to_datetime(filtered["decision_date"], errors="coerce").dt.date.astype(str)
        filtered = filtered.loc[dates == target_date]
    if universe_name is not None:
        filtered = filtered.loc[filtered["universe_name"].astype(str) == str(universe_name)]
    if run_id is not None:
        filtered = filtered.loc[filtered["run_id"].astype(str) == str(run_id)]
    filtered = filtered.loc[filtered["candidates_path"].map(_present)]
    return filtered.reset_index(drop=True)


def _attach_health_status(frame: pd.DataFrame, *, settings: Settings) -> tuple[pd.DataFrame, list[str]]:
    health_result = check_current_candidate_artifact_health(index_df=frame, settings=settings)
    status_by_run = _health_status_by_run(frame, health_result.health_frame)
    checked = frame.copy(deep=True)
    checked["health_status"] = [status_by_run.get(str(row["run_id"]), "PASS") for _, row in checked.iterrows()]
    warnings = list(health_result.warnings)
    if health_result.status == "WARN":
        warnings.append("Current-candidate artifact health check produced warnings.")
    if health_result.status == "FAIL":
        warnings.append("Current-candidate artifact health check produced errors.")
    return checked, warnings


def _health_status_by_run(index_frame: pd.DataFrame, health_frame: pd.DataFrame) -> dict[str, str]:
    status_by_run = {str(value): "PASS" for value in index_frame["run_id"].astype(str).tolist()}
    if health_frame.empty:
        return status_by_run
    for run_id, issues in health_frame.groupby("run_id", dropna=False):
        severities = set(issues["severity"].astype(str).str.upper())
        if "ERROR" in severities:
            status_by_run[str(run_id)] = "FAIL"
        elif "WARN" in severities:
            status_by_run[str(run_id)] = "WARN"
        else:
            status_by_run[str(run_id)] = "PASS"
    return status_by_run


def _filter_by_health_requirement(
    frame: pd.DataFrame,
    *,
    require_health_pass: bool,
    allow_health_warn: bool,
) -> pd.DataFrame:
    if not require_health_pass:
        return frame.reset_index(drop=True)
    allowed = {"PASS", "WARN"} if allow_health_warn else {"PASS"}
    return frame.loc[frame["health_status"].astype(str).str.upper().isin(allowed)].reset_index(drop=True)


def _sort_candidate_index(frame: pd.DataFrame, *, prefer_latest: bool) -> pd.DataFrame:
    sortable = frame.copy(deep=True)
    sortable["_decision_date_sort"] = pd.to_datetime(sortable["decision_date"], errors="coerce")
    sortable["_candidate_count_sort"] = pd.to_numeric(sortable["candidate_count"], errors="coerce").fillna(-1)
    sortable["_path_sort"] = sortable["candidates_path"].astype(str)
    if prefer_latest:
        sorted_frame = sortable.sort_values(
            ["_decision_date_sort", "_candidate_count_sort", "_path_sort"],
            ascending=[False, False, True],
            na_position="last",
        )
    else:
        sorted_frame = sortable.sort_values(["_path_sort"], ascending=True, na_position="last")
    return sorted_frame.drop(columns=["_decision_date_sort", "_candidate_count_sort", "_path_sort"]).reset_index(drop=True)


def _selected_from_index_row(row: dict[str, Any], *, index_source: str) -> SelectedCurrentCandidateArtifact:
    return SelectedCurrentCandidateArtifact(
        source_type="CURRENT_CANDIDATE_INDEX",
        candidates_path=Path(str(row.get("candidates_path", ""))),
        report_path=_path_or_none(row.get("report_path")),
        metadata_path=_path_or_none(row.get("metadata_path")),
        decision_date=_date_or_none(row.get("decision_date")),
        universe_name=_string_or_empty(row.get("universe_name")),
        run_id=_string_or_empty(row.get("run_id")),
        candidate_count=_int_or_none(row.get("candidate_count")),
        health_status=_string_or_none(row.get("health_status")),
        index_row={**row, "index_source": index_source},
    )


def _selected_from_direct_candidates_path(
    path: Path,
    *,
    decision_date: str | pd.Timestamp | None,
    universe_name: str | None,
    run_id: str | None,
) -> SelectedCurrentCandidateArtifact:
    if not path.exists():
        raise FileNotFoundError(f"Candidate CSV not found: {path}")
    candidates = pd.read_csv(path)
    metadata_path = path.parent / "metadata.json"
    metadata = _load_json_if_exists(metadata_path)
    output_files = metadata.get("output_files") if isinstance(metadata.get("output_files"), dict) else {}
    report_path = _path_or_none(output_files.get("current_candidates_report")) or _existing_path_or_none(
        path.parent / "current_candidates_report.md"
    )
    selected_decision_date = (
        _date_or_none(decision_date)
        or _date_or_none(metadata.get("decision_date"))
        or _first_date_from_candidates(candidates)
    )
    selected_universe = str(universe_name or metadata.get("universe_name") or "").strip()
    selected_run_id = (
        str(run_id or metadata.get("run_id") or _first_present(candidates, "current_candidate_run_id", "source_run_id", "run_id") or path.parent.name)
    )
    return SelectedCurrentCandidateArtifact(
        source_type="DIRECT_CANDIDATES_PATH",
        candidates_path=path,
        report_path=report_path,
        metadata_path=metadata_path if metadata_path.exists() else None,
        decision_date=selected_decision_date,
        universe_name=selected_universe,
        run_id=selected_run_id,
        candidate_count=len(candidates),
        health_status=None,
        index_row={
            "artifact_type": "CURRENT_CANDIDATES",
            "run_id": selected_run_id,
            "decision_date": str(selected_decision_date.date()) if selected_decision_date is not None else "",
            "universe_name": selected_universe,
            "candidate_count": len(candidates),
            "candidates_path": str(path),
            "report_path": str(report_path) if report_path is not None else "",
            "metadata_path": str(metadata_path) if metadata_path.exists() else "",
        },
    )


def _resolve_paper_date(
    paper_date: str | pd.Timestamp | None,
    selected_decision_date: pd.Timestamp | None,
    *,
    default_from_decision_date: bool,
) -> pd.Timestamp:
    if paper_date is not None:
        return _normalize_date(paper_date)
    if default_from_decision_date and selected_decision_date is not None:
        return _normalize_date(selected_decision_date)
    raise ValueError("paper_date is required when it cannot be inferred from the selected current-candidate artifact")


def _build_audit_metadata(
    *,
    handoff_id: str,
    paper_date: pd.Timestamp,
    selected: SelectedCurrentCandidateArtifact,
    paper_result: DailyPaperRunResult,
    settings: CurrentToPaperHandoffSettings,
    fills_path: str | Path | None,
    skip_health_check: bool,
) -> dict[str, Any]:
    return {
        "handoff_id": handoff_id,
        "paper_date": paper_date,
        "source_type": selected.source_type,
        "selected_candidates_path": selected.candidates_path,
        "selected_current_candidate_report_path": selected.report_path,
        "selected_current_candidate_metadata_path": selected.metadata_path,
        "selected_decision_date": selected.decision_date,
        "selected_universe_name": selected.universe_name,
        "selected_run_id": selected.run_id,
        "selected_candidate_count": selected.candidate_count,
        "health_status": selected.health_status,
        "health_check_skipped": skip_health_check,
        "fills_path": Path(fills_path) if fills_path is not None else None,
        "paper_journal_id": paper_result.journal_id,
        "paper_report_path": paper_result.artifact_paths.get("paper_report"),
        "paper_decision_count": paper_result.decision_count,
        "paper_fill_count": paper_result.fill_count,
        "config_version": settings.config_version,
        "live_trading_enabled": False,
        "broker_api_invoked": False,
        "current_to_paper_handoff_only": True,
    }


def _augment_paper_daily_metadata(result: CurrentToPaperHandoffResult) -> None:
    metadata_path = result.paper_artifact_paths.get("metadata")
    if metadata_path is None or not Path(metadata_path).exists():
        return
    path = Path(metadata_path)
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    metadata["current_to_paper_handoff"] = {
        "handoff_id": result.handoff_id,
        "selected_candidates_path": str(result.selected_candidates_path),
        "selected_current_candidate_report_path": (
            str(result.selected_current_candidate_report_path)
            if result.selected_current_candidate_report_path is not None
            else ""
        ),
        "selected_current_candidate_metadata_path": (
            str(result.selected_current_candidate_metadata_path)
            if result.selected_current_candidate_metadata_path is not None
            else ""
        ),
        "selected_run_id": result.selected_run_id,
        "selected_decision_date": (
            str(result.selected_decision_date.date()) if result.selected_decision_date is not None else ""
        ),
        "selected_universe_name": result.selected_universe_name,
        "health_status": result.health_status,
        "source_type": result.selected_artifact.source_type,
    }
    path.write_text(json.dumps(_json_safe(metadata), indent=2, sort_keys=True), encoding="utf-8")


def _selected_payload(selected: SelectedCurrentCandidateArtifact) -> dict[str, Any]:
    payload = selected.as_dict()
    if selected.metadata_path is not None and selected.metadata_path.exists():
        payload["source_metadata"] = _load_json_if_exists(selected.metadata_path)
    return payload


def _assert_selected_candidates_exists(selected: SelectedCurrentCandidateArtifact) -> None:
    if not selected.candidates_path.exists():
        raise FileNotFoundError(f"Selected candidates.csv does not exist: {selected.candidates_path}")


def _prepare_index_frame(frame: pd.DataFrame) -> pd.DataFrame:
    index = frame.copy(deep=True)
    for column in CURRENT_CANDIDATE_INDEX_COLUMNS:
        if column not in index.columns:
            index[column] = ""
    if "health_status" not in index.columns:
        index["health_status"] = ""
    return index[[*CURRENT_CANDIDATE_INDEX_COLUMNS, "health_status"]].reset_index(drop=True)


def _load_project_settings(config: Settings | str | Path | None) -> Settings:
    if config is None:
        return load_settings(Path("config/default.yaml"))
    if isinstance(config, Settings):
        return config
    return load_settings(Path(config))


def _normalize_date(value: str | pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_localize(None)
    return timestamp.normalize()


def _date_or_none(value: Any) -> pd.Timestamp | None:
    if not _present(value):
        return None
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        return None
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_localize(None)
    return timestamp.normalize()


def _path_or_none(value: Any) -> Path | None:
    if not _present(value):
        return None
    return Path(str(value))


def _existing_path_or_none(value: Path) -> Path | None:
    return value if value.exists() else None


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _first_date_from_candidates(candidates: pd.DataFrame) -> pd.Timestamp | None:
    for column in ["decision_date", "paper_date"]:
        if column in candidates.columns:
            values = pd.to_datetime(candidates[column], errors="coerce").dropna()
            if not values.empty:
                return pd.Timestamp(values.iloc[0]).normalize()
    return None


def _first_present(frame: pd.DataFrame, *columns: str) -> str:
    for column in columns:
        if column in frame.columns:
            values = frame[column].dropna()
            if not values.empty and str(values.iloc[0]).strip():
                return str(values.iloc[0])
    return ""


def _int_or_none(value: Any) -> int | None:
    if not _present(value):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _string_or_none(value: Any) -> str | None:
    return str(value).strip() if _present(value) else None


def _string_or_empty(value: Any) -> str:
    return str(value).strip() if _present(value) else ""


def _present(value: Any) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    return str(value).strip() != ""


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


def _hash_payload(payload: dict[str, Any], length: int) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


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
