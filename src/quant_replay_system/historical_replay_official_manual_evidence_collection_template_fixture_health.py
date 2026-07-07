"""Health view for official manual evidence collection template fixture artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.historical_replay_official_manual_evidence_collection_template_fixture import (
    OUTPUT_FILES,
    SAFETY_FALSE_FIELDS,
)
from quant_replay_system.historical_replay_official_manual_evidence_collection_template_fixture_index import (
    DEFAULT_ROOT,
    VIEW_DIR_NAMES,
    build_historical_replay_official_manual_evidence_collection_template_fixture_index,
)


STATUS_HEALTH_PASS = "OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_HEALTH_PASS_REPORT_ONLY"
STATUS_HEALTH_FAIL = "OFFICIAL_MANUAL_EVIDENCE_COLLECTION_TEMPLATE_FIXTURE_HEALTH_FAIL_UNSAFE"
HEALTH_COLUMNS = ["run_id", "status", "severity", "issue_code", "message", "artifact_path"]
EXPECTED_SYMBOLS = ["000001", "000002", "159915", "300750", "510300", "600000", "600519", "601318", "688981"]
FORBIDDEN_READINESS_WORDING = [
    "PIT_ADMISSIBLE",
    "PIT_APPROVED",
    "READY_FOR_REPLAY",
    "ACTIVE_REPLAY_INPUT_READY",
    "BUY_REVIEW_READY",
    "TRADING_READY",
    "APPROVED_FOR_PAPER",
    "PERFORMANCE_VALIDATED",
]


@dataclass(frozen=True)
class HistoricalReplayOfficialManualEvidenceCollectionTemplateFixtureHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    rows: list[dict[str, str]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def check_historical_replay_official_manual_evidence_collection_template_fixture_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path | None = None,
) -> HistoricalReplayOfficialManualEvidenceCollectionTemplateFixtureHealthResult:
    root_path = Path(root)
    out_dir = Path(output_dir) if output_dir is not None else root_path / "health"
    build_historical_replay_official_manual_evidence_collection_template_fixture_index(
        root=root_path, output_dir=out_dir.parent / "index"
    )
    issues: list[dict[str, str]] = []
    candidate_dirs = _candidate_dirs(root_path)
    if not root_path.exists():
        issues.append(_issue("", "WARNING", "ARTIFACT_ROOT_MISSING", "Artifact root is missing.", root_path))
    for artifact_dir in candidate_dirs:
        issues.extend(_issues_for_artifact_dir(artifact_dir))
    rows = [{column: row.get(column, "") for column in HEALTH_COLUMNS} for row in issues]
    error_count = sum(row["severity"] == "ERROR" for row in rows)
    warning_count = sum(row["severity"] == "WARNING" for row in rows)
    status = STATUS_HEALTH_FAIL if error_count else STATUS_HEALTH_PASS
    paths = _paths(out_dir)
    result = HistoricalReplayOfficialManualEvidenceCollectionTemplateFixtureHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(rows),
        error_count=error_count,
        warning_count=warning_count,
        rows=rows,
        artifact_paths=paths,
        warnings=[] if status == STATUS_HEALTH_PASS else [f"Official manual evidence template fixture health is {status}."],
    )
    _write(result)
    return result


def _candidate_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    candidates: set[Path] = set()
    for filename in OUTPUT_FILES.values():
        for path in root.rglob(filename):
            artifact_dir = path.parent
            try:
                relative_parts = artifact_dir.relative_to(root).parts
            except ValueError:
                continue
            if any(part in VIEW_DIR_NAMES or part.startswith("_") for part in relative_parts):
                continue
            candidates.add(artifact_dir)
    return sorted(candidates)


def _issues_for_artifact_dir(artifact_dir: Path) -> list[dict[str, str]]:
    run_id = artifact_dir.name
    paths = {key: artifact_dir / filename for key, filename in OUTPUT_FILES.items()}
    issues: list[dict[str, str]] = []
    for key, path in paths.items():
        if not path.exists():
            issues.append(_issue(run_id, "ERROR", "MISSING_REQUIRED_ARTIFACT", f"Missing required {key}.", path))
    metadata = _read_json(paths["metadata"])
    safety = _read_json(paths["safety_flags"])
    evidence_rows = _read_csv(paths["evidence_collection_template"]) if paths["evidence_collection_template"].exists() else []
    lineage_rows = _read_csv(paths["source_lineage_template"]) if paths["source_lineage_template"].exists() else []
    no_hit_rows = _read_csv(paths["no_hit_query_handoff_template"]) if paths["no_hit_query_handoff_template"].exists() else []
    survivorship_rows = _read_csv(paths["survivorship_rationale_template"]) if paths["survivorship_rationale_template"].exists() else []
    reviewer_rows = _read_csv(paths["reviewer_notes_template"]) if paths["reviewer_notes_template"].exists() else []
    if metadata is not None:
        run_id = _text(metadata.get("run_id") or run_id)
        issues.extend(_metadata_issues(run_id, metadata, evidence_rows, lineage_rows, no_hit_rows, survivorship_rows, reviewer_rows, paths["metadata"]))
    if safety is not None:
        issues.extend(_safety_issues(run_id, safety, paths["safety_flags"]))
    issues.extend(_evidence_issues(run_id, evidence_rows, paths["evidence_collection_template"]))
    issues.extend(_lineage_issues(run_id, lineage_rows, paths["source_lineage_template"]))
    issues.extend(_no_hit_issues(run_id, no_hit_rows, paths["no_hit_query_handoff_template"]))
    issues.extend(_survivorship_issues(run_id, survivorship_rows, paths["survivorship_rationale_template"]))
    issues.extend(_reviewer_issues(run_id, reviewer_rows, paths["reviewer_notes_template"]))
    for key in ("report", "validation_checklist"):
        if paths[key].exists():
            issues.extend(_public_text_issues(run_id, paths[key]))
    return issues


def _metadata_issues(
    run_id: str,
    metadata: dict[str, Any],
    evidence_rows: list[dict[str, str]],
    lineage_rows: list[dict[str, str]],
    no_hit_rows: list[dict[str, str]],
    survivorship_rows: list[dict[str, str]],
    reviewer_rows: list[dict[str, str]],
    path: Path,
) -> list[dict[str, str]]:
    checks = [
        ("row_count", 9, "ROW_COUNT_MISMATCH"),
        ("stock_row_count", 7, "INSTRUMENT_COUNT_MISMATCH"),
        ("etf_row_count", 2, "INSTRUMENT_COUNT_MISMATCH"),
        ("evidence_collection_template_row_count", 72, "EVIDENCE_TEMPLATE_COUNT_MISMATCH"),
        ("source_lineage_template_row_count", 72, "SOURCE_LINEAGE_TEMPLATE_COUNT_MISMATCH"),
        ("no_hit_template_row_count", 9, "NO_HIT_COUNT_MISMATCH"),
        ("survivorship_template_row_count", 9, "SURVIVORSHIP_COUNT_MISMATCH"),
        ("reviewer_notes_template_row_count", 9, "REVIEWER_NOTES_COUNT_MISMATCH"),
        ("profile_conflict_count", 7, "PROFILE_CONFLICT_COUNT_MISMATCH"),
        ("survivorship_warning_count", 9, "SURVIVORSHIP_COUNT_MISMATCH"),
    ]
    issues = [
        _issue(run_id, "ERROR", code, f"{field} must be {expected}.", path)
        for field, expected, code in checks
        if _int(metadata.get(field)) != expected
    ]
    if evidence_rows and len(evidence_rows) != 72:
        issues.append(_issue(run_id, "ERROR", "EVIDENCE_TEMPLATE_COUNT_MISMATCH", "Evidence template rows must be 72.", path))
    if lineage_rows and len(lineage_rows) != 72:
        issues.append(_issue(run_id, "ERROR", "SOURCE_LINEAGE_TEMPLATE_COUNT_MISMATCH", "Source lineage template rows must be 72.", path))
    for rows, expected, code in [
        (no_hit_rows, 9, "NO_HIT_COUNT_MISMATCH"),
        (survivorship_rows, 9, "SURVIVORSHIP_COUNT_MISMATCH"),
        (reviewer_rows, 9, "REVIEWER_NOTES_COUNT_MISMATCH"),
    ]:
        if rows and len(rows) != expected:
            issues.append(_issue(run_id, "ERROR", code, f"Template row count must be {expected}.", path))
    for field in SAFETY_FALSE_FIELDS:
        if _to_bool(metadata.get(field)):
            issues.append(_issue(run_id, "ERROR", "FORBIDDEN_METADATA_FLAG_TRUE", f"{field} must remain false.", path))
    status_text = " ".join(_text(metadata.get(key)) for key in ("runtime_status", "workflow_stage", "health_status"))
    if any(word in status_text for word in FORBIDDEN_READINESS_WORDING):
        issues.append(_issue(run_id, "ERROR", "UNSAFE_READINESS_WORDING", "Metadata contains forbidden readiness wording.", path))
    return issues


def _safety_issues(run_id: str, safety: dict[str, Any], path: Path) -> list[dict[str, str]]:
    return [
        _issue(run_id, "ERROR", "FORBIDDEN_SAFETY_FLAG_TRUE", f"{field} must remain false.", path)
        for field in SAFETY_FALSE_FIELDS
        if _to_bool(safety.get(field))
    ]


def _evidence_issues(run_id: str, rows: list[dict[str, str]], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    symbols = list(dict.fromkeys(_text(row.get("symbol")) for row in rows))
    if rows and symbols != EXPECTED_SYMBOLS:
        issues.append(_issue(run_id, "ERROR", "SYMBOL_SET_MISMATCH", "Selected sample symbol set/order must be exact.", path))
    for row in rows:
        if _text(row.get("evidence_collection_status")) != "not_collected":
            issues.append(_issue(run_id, "ERROR", "EVIDENCE_COLLECTION_STARTED_UNSAFE", "Evidence collection must remain not_collected.", path))
        if _text(row.get("symbol")).isdigit() and len(_text(row.get("symbol"))) < 6:
            issues.append(_issue(run_id, "ERROR", "SYMBOL_LEADING_ZERO_LOST", "Symbol appears to have lost leading zeros.", path))
    return issues


def _lineage_issues(run_id: str, rows: list[dict[str, str]], path: Path) -> list[dict[str, str]]:
    return [
        _issue(run_id, "ERROR", "FULL_HASH_OR_SOURCE_CONTENT_EXPOSED", "Lineage row exposes forbidden source content or full hash.", path)
        for row in rows
        for value in row.values()
        if _looks_like_full_hash_or_content(value)
    ]


def _no_hit_issues(run_id: str, rows: list[dict[str, str]], path: Path) -> list[dict[str, str]]:
    return [
        _issue(run_id, "ERROR", "NO_HIT_ACCEPTED_UNSAFE", "No-hit handoff must remain not accepted.", path)
        for row in rows
        if _text(row.get("no_hit_acceptance_status")) != "not_accepted"
    ]


def _survivorship_issues(run_id: str, rows: list[dict[str, str]], path: Path) -> list[dict[str, str]]:
    return [
        _issue(run_id, "ERROR", "SURVIVORSHIP_REVIEW_CLOSED_UNSAFE", "Survivorship review must remain not_reviewed.", path)
        for row in rows
        if _text(row.get("survivorship_review_status")) != "not_reviewed"
    ]


def _reviewer_issues(run_id: str, rows: list[dict[str, str]], path: Path) -> list[dict[str, str]]:
    return [
        _issue(run_id, "ERROR", "PRIVATE_REVIEWER_IDENTITY_DISCLOSED", "Reviewer private identity must not be disclosed.", path)
        for row in rows
        if _text(row.get("reviewer_private_identity_disclosed")) != "no"
    ]


def _public_text_issues(run_id: str, path: Path) -> list[dict[str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    return [
        _issue(run_id, "ERROR", "UNSAFE_READINESS_WORDING", f"Artifact contains {word}.", path)
        for word in FORBIDDEN_READINESS_WORDING
        if word in text
    ]


def _paths(output_dir: Path) -> dict[str, Path]:
    return {
        "artifact_dir": output_dir,
        "health_csv": output_dir / "historical_replay_official_manual_evidence_collection_template_fixture_health.csv",
        "health_md": output_dir / "historical_replay_official_manual_evidence_collection_template_fixture_health.md",
        "metadata_json": output_dir / "metadata.json",
    }


def _write(result: HistoricalReplayOfficialManualEvidenceCollectionTemplateFixtureHealthResult) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    with result.artifact_paths["health_csv"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEALTH_COLUMNS)
        writer.writeheader()
        writer.writerows(result.rows)
    result.artifact_paths["health_md"].write_text(_render_markdown(result), encoding="utf-8")
    result.artifact_paths["metadata_json"].write_text(
        json.dumps(
            {
                "status": result.status,
                "checked_artifact_count": result.checked_artifact_count,
                "issue_count": result.issue_count,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "warnings": result.warnings,
                "report_only": True,
                "diagnostic_only": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _render_markdown(result: HistoricalReplayOfficialManualEvidenceCollectionTemplateFixtureHealthResult) -> str:
    return "\n".join(
        [
            "# Historical Replay Official Manual Evidence Collection Template Fixture Health",
            "",
            f"- Status: `{result.status}`",
            f"- Checked artifact count: `{result.checked_artifact_count}`",
            f"- Issue count: `{result.issue_count}`",
            "- Report-only health; no evidence collection, acceptance, closure, PIT approval, replay, buy-review, or trading is authorized.",
            "",
        ]
    )


def _issue(run_id: str, severity: str, code: str, message: str, path: Path) -> dict[str, str]:
    return {
        "run_id": run_id,
        "status": STATUS_HEALTH_FAIL if severity == "ERROR" else STATUS_HEALTH_PASS,
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_path": str(path),
    }


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except OSError:
        return []


def _looks_like_full_hash_or_content(value: Any) -> bool:
    text = str(value)
    return (len(text) >= 64 and all(ch in "0123456789abcdefABCDEF" for ch in text[:64])) or "source bytes" in text.lower()


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)
