"""Integrity health view for source/evidence sufficiency policy fixtures."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_replay_system.historical_replay_source_evidence_sufficiency_policy_contract_fixture import (
    BLOCKER_VOCABULARY,
    EVIDENCE_FAMILIES,
    EVIDENCE_FAMILY_CONTRACT_FIELDS,
    OUTPUT_FILES,
    SAFETY_FALSE_FIELDS,
    SELECTED_ROW_FIELDS,
    STATUS_CREATED as CORE_STATUS_CREATED,
    STATUS_VOCABULARY,
    WORKFLOW_STAGE,
    _validate_output_root,
)
from quant_replay_system.historical_replay_source_evidence_sufficiency_policy_contract_fixture_index import (
    DEFAULT_ROOT,
    VIEW_DIR_NAMES,
    _view_dir,
    build_historical_replay_source_evidence_sufficiency_policy_contract_fixture_index,
)


STATUS_HEALTH_PASS = (
    "SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_HEALTH_PASS_REPORT_ONLY"
)
STATUS_HEALTH_WARN = (
    "SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_HEALTH_WARN_REPORT_ONLY"
)
STATUS_HEALTH_FAIL = (
    "SOURCE_EVIDENCE_SUFFICIENCY_POLICY_CONTRACT_FIXTURE_HEALTH_FAIL_UNSAFE"
)
HEALTH_COLUMNS = [
    "run_id",
    "status",
    "severity",
    "issue_code",
    "message",
    "artifact_reference",
]
EXPECTED_SYMBOLS = [
    "000001",
    "000002",
    "159915",
    "300750",
    "510300",
    "600000",
    "600519",
    "601318",
    "688981",
]
STATE_FALSE_FIELDS = [
    "evidence_presence",
    "sufficiency_candidate",
    "evidence_accepted",
    "evidence_closed",
    "pit_admissible",
    "replay_ready",
]
PUBLIC_FILE_KEYS = [
    "metadata",
    "selected_rows",
    "evidence_family_contract",
    "required_fields",
    "status_vocabulary",
    "blocker_vocabulary",
    "timing_revision_matrix",
    "stock_etf_matrix",
    "safety_flags",
    "report",
]
FULL_HASH_RE = re.compile(r"(?i)(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")
PRIVATE_WINDOWS_PATH_RE = re.compile(r"(?i)\b[a-z]:\\users\\[^\\\s]+")
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(?:secret|credential|token|password|api[_-]?key)\s*[:=]\s*[^\s,;}]+"
)


@dataclass(frozen=True)
class HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureHealthResult:
    status: str
    checked_artifact_count: int
    issue_count: int
    error_count: int
    warning_count: int
    rows: list[dict[str, str]]
    artifact_paths: dict[str, Path]
    warnings: list[str]


def check_historical_replay_source_evidence_sufficiency_policy_contract_fixture_health(
    *,
    root: str | Path = DEFAULT_ROOT,
    output_dir: str | Path | None = None,
) -> HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureHealthResult:
    root_path = _validate_output_root(Path(root))
    out_dir = _view_dir(root_path, output_dir, "health")
    build_historical_replay_source_evidence_sufficiency_policy_contract_fixture_index(
        root=root_path, output_dir=out_dir.parent / "index"
    )
    candidate_dirs = _candidate_dirs(root_path)
    issues: list[dict[str, str]] = []
    if not candidate_dirs:
        issues.append(
            _issue(
                "",
                "WARNING",
                "NO_FIXTURE_ARTIFACTS",
                "No source/evidence sufficiency policy fixture artifacts were found.",
                "",
            )
        )
    for artifact_dir in candidate_dirs:
        issues.extend(_issues_for_artifact_dir(root_path, artifact_dir))
    error_count = sum(issue["severity"] == "ERROR" for issue in issues)
    warning_count = sum(issue["severity"] == "WARNING" for issue in issues)
    if error_count:
        status = STATUS_HEALTH_FAIL
    elif warning_count:
        status = STATUS_HEALTH_WARN
    else:
        status = STATUS_HEALTH_PASS
    rows = []
    for issue in issues:
        row = dict(issue)
        row["status"] = status
        rows.append({column: row.get(column, "") for column in HEALTH_COLUMNS})
    result = HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureHealthResult(
        status=status,
        checked_artifact_count=len(candidate_dirs),
        issue_count=len(rows),
        error_count=error_count,
        warning_count=warning_count,
        rows=rows,
        artifact_paths=_paths(out_dir),
        warnings=[row["message"] for row in rows],
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
                parts = artifact_dir.relative_to(root).parts
            except ValueError:
                continue
            if any(part in VIEW_DIR_NAMES or part.startswith("_") for part in parts):
                continue
            candidates.add(artifact_dir)
    return sorted(candidates)


def _issues_for_artifact_dir(root: Path, artifact_dir: Path) -> list[dict[str, str]]:
    relative_dir = artifact_dir.relative_to(root).as_posix()
    paths = {key: artifact_dir / filename for key, filename in OUTPUT_FILES.items()}
    issues: list[dict[str, str]] = []
    for key, path in paths.items():
        if not path.is_file():
            issues.append(
                _issue(
                    artifact_dir.name,
                    "ERROR",
                    "MISSING_REQUIRED_ARTIFACT",
                    f"Missing required core artifact: {key}.",
                    f"{relative_dir}/{path.name}",
                )
            )
    metadata = _read_json(paths["metadata"])
    safety = _read_json(paths["safety_flags"])
    selected_rows, selected_fields = _read_csv(paths["selected_rows"])
    contract_rows, contract_fields = _read_csv(paths["evidence_family_contract"])
    required_rows, _ = _read_csv(paths["required_fields"])
    status_rows, _ = _read_csv(paths["status_vocabulary"])
    blocker_rows, _ = _read_csv(paths["blocker_vocabulary"])
    timing_rows, _ = _read_csv(paths["timing_revision_matrix"])
    stock_etf_rows, _ = _read_csv(paths["stock_etf_matrix"])
    run_id = _text((metadata or {}).get("run_id") or artifact_dir.name)
    if metadata is None:
        issues.append(
            _issue(run_id, "ERROR", "METADATA_INVALID", "metadata.json must contain one object.", f"{relative_dir}/{OUTPUT_FILES['metadata']}")
        )
    else:
        issues.extend(_metadata_issues(run_id, metadata, relative_dir))
    if safety is None:
        issues.append(
            _issue(run_id, "ERROR", "SAFETY_FLAGS_INVALID", "Safety flags must contain one object.", f"{relative_dir}/{OUTPUT_FILES['safety_flags']}")
        )
    else:
        issues.extend(_flag_issues(run_id, safety, relative_dir, "safety flags"))
    issues.extend(
        _schema_count_issues(
            run_id,
            relative_dir,
            selected_rows,
            selected_fields,
            contract_rows,
            contract_fields,
            required_rows,
            status_rows,
            blocker_rows,
            timing_rows,
            stock_etf_rows,
        )
    )
    issues.extend(_selected_row_issues(run_id, relative_dir, selected_rows))
    issues.extend(_contract_row_issues(run_id, relative_dir, contract_rows))
    issues.extend(_vocabulary_issues(run_id, relative_dir, status_rows, blocker_rows))
    issues.extend(_public_disclosure_issues(run_id, relative_dir, paths))
    return issues


def _metadata_issues(
    run_id: str, metadata: dict[str, Any], relative_dir: str
) -> list[dict[str, str]]:
    expected_counts = {
        "row_count": 9,
        "stock_row_count": 7,
        "etf_row_count": 2,
        "profile_conflict_count": 7,
        "profile_aligned_context_count": 2,
        "unresolved_profile_conflict_count": 7,
        "selected_row_with_blocker_count": 9,
        "evidence_family_count": 17,
        "row_evidence_family_contract_count": 153,
        "applicable_contract_row_count": 144,
        "instrument_not_applicable_context_row_count": 9,
        "core_artifact_count": 10,
        "required_field_row_count": 45,
        "status_vocabulary_row_count": 17,
        "blocker_vocabulary_row_count": 28,
        "timing_revision_rule_count": 18,
        "stock_etf_matrix_row_count": 4,
        "sufficiency_candidate_count": 0,
        "evidence_accepted_count": 0,
        "evidence_closed_count": 0,
        "pit_admissible_count": 0,
        "replay_ready_count": 0,
        "safety_true_count": 0,
    }
    reference = f"{relative_dir}/{OUTPUT_FILES['metadata']}"
    issues = [
        _issue(
            run_id,
            "ERROR",
            "METADATA_COUNT_MISMATCH",
            f"{field} must equal {expected}.",
            reference,
        )
        for field, expected in expected_counts.items()
        if _int(metadata.get(field)) != expected
    ]
    for field in ("report_only", "diagnostic_only", "local_only", "synthetic_only"):
        if not _to_bool(metadata.get(field)):
            issues.append(
                _issue(run_id, "ERROR", "SCOPE_FLAG_FALSE", f"{field} must remain true.", reference)
            )
    if metadata.get("runtime_status") != CORE_STATUS_CREATED:
        issues.append(_issue(run_id, "ERROR", "RUNTIME_STATUS_MISMATCH", "Runtime status is not the fixture-created report-only status.", reference))
    if metadata.get("workflow_stage") != WORKFLOW_STAGE:
        issues.append(_issue(run_id, "ERROR", "WORKFLOW_STAGE_MISMATCH", "Workflow stage is not the fixture-created report-only stage.", reference))
    issues.extend(_flag_issues(run_id, metadata, relative_dir, "metadata"))
    limitation = _text(metadata.get("optional_context_limitation"))
    if limitation:
        issues.append(
            _issue(run_id, "WARNING", "OPTIONAL_CONTEXT_LIMITATION", "Optional policy context limitation requires review.", reference)
        )
    return issues


def _flag_issues(
    run_id: str,
    payload: dict[str, Any],
    relative_dir: str,
    surface: str,
) -> list[dict[str, str]]:
    reference = f"{relative_dir}/{OUTPUT_FILES['metadata' if surface == 'metadata' else 'safety_flags']}"
    return [
        _issue(run_id, "ERROR", "FORBIDDEN_FLAG_TRUE", f"{field} must remain false on {surface}.", reference)
        for field in SAFETY_FALSE_FIELDS
        if _to_bool(payload.get(field))
    ]


def _schema_count_issues(
    run_id: str,
    relative_dir: str,
    selected_rows: list[dict[str, str]],
    selected_fields: list[str],
    contract_rows: list[dict[str, str]],
    contract_fields: list[str],
    required_rows: list[dict[str, str]],
    status_rows: list[dict[str, str]],
    blocker_rows: list[dict[str, str]],
    timing_rows: list[dict[str, str]],
    stock_etf_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    checks = [
        (len(selected_rows), 9, "SELECTED_ROW_COUNT_MISMATCH", OUTPUT_FILES["selected_rows"]),
        (len(contract_rows), 153, "CONTRACT_ROW_COUNT_MISMATCH", OUTPUT_FILES["evidence_family_contract"]),
        (len(required_rows), 45, "REQUIRED_FIELD_COUNT_MISMATCH", OUTPUT_FILES["required_fields"]),
        (len(status_rows), 17, "STATUS_COUNT_MISMATCH", OUTPUT_FILES["status_vocabulary"]),
        (len(blocker_rows), 28, "BLOCKER_COUNT_MISMATCH", OUTPUT_FILES["blocker_vocabulary"]),
        (len(timing_rows), 18, "TIMING_REVISION_COUNT_MISMATCH", OUTPUT_FILES["timing_revision_matrix"]),
        (len(stock_etf_rows), 4, "STOCK_ETF_MATRIX_COUNT_MISMATCH", OUTPUT_FILES["stock_etf_matrix"]),
    ]
    for observed, expected, code, filename in checks:
        if observed != expected:
            issues.append(_issue(run_id, "ERROR", code, f"Expected {expected} rows; observed {observed}.", f"{relative_dir}/{filename}"))
    if selected_fields != SELECTED_ROW_FIELDS:
        issues.append(_issue(run_id, "ERROR", "SELECTED_ROW_SCHEMA_MISMATCH", "Selected-row schema must match the 15-field contract.", f"{relative_dir}/{OUTPUT_FILES['selected_rows']}"))
    if contract_fields != EVIDENCE_FAMILY_CONTRACT_FIELDS:
        issues.append(_issue(run_id, "ERROR", "CONTRACT_SCHEMA_MISMATCH", "Evidence-family schema must match the 30-field contract.", f"{relative_dir}/{OUTPUT_FILES['evidence_family_contract']}"))
    return issues


def _selected_row_issues(
    run_id: str, relative_dir: str, rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    reference = f"{relative_dir}/{OUTPUT_FILES['selected_rows']}"
    issues: list[dict[str, str]] = []
    symbols = [_text(row.get("symbol")) for row in rows]
    if symbols != EXPECTED_SYMBOLS:
        issues.append(_issue(run_id, "ERROR", "SYMBOL_SET_OR_ORDER_MISMATCH", "Selected symbols must preserve exact six-character identity and order.", reference))
    if sum(row.get("instrument_type") == "STOCK" for row in rows) != 7 or sum(row.get("instrument_type") == "ETF" for row in rows) != 2:
        issues.append(_issue(run_id, "ERROR", "INSTRUMENT_SPLIT_MISMATCH", "Instrument split must remain 7 STOCK and 2 ETF.", reference))
    for row in rows:
        if not _text(row.get("selected_row_blockers")):
            issues.append(_issue(run_id, "ERROR", "SELECTED_ROW_BLOCKERS_MISSING", "Every selected row must retain blockers.", reference))
        if row.get("instrument_type") == "STOCK" and (
            row.get("profile_conflict") != "true"
            or row.get("profile_policy_status") != "unresolved_profile_conflict"
        ):
            issues.append(_issue(run_id, "ERROR", "PROFILE_CONFLICT_STATE_MISMATCH", "STOCK profile conflicts must remain unresolved.", reference))
        for field in (
            "selected_row_sufficiency_candidate",
            "selected_row_evidence_accepted",
            "selected_row_evidence_closed",
            "selected_row_pit_admissible",
            "selected_row_replay_ready",
        ):
            if _to_bool(row.get(field)):
                issues.append(_issue(run_id, "ERROR", "FORBIDDEN_SELECTED_ROW_STATE_TRUE", f"{field} must remain false.", reference))
    return issues


def _contract_row_issues(
    run_id: str, relative_dir: str, rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    reference = f"{relative_dir}/{OUTPUT_FILES['evidence_family_contract']}"
    issues: list[dict[str, str]] = []
    applicable = sum(row.get("instrument_applicability") == "applies" for row in rows)
    not_applicable = sum(row.get("instrument_applicability") == "not_applicable_context_only" for row in rows)
    if applicable != 144 or not_applicable != 9:
        issues.append(_issue(run_id, "ERROR", "APPLICABILITY_SPLIT_MISMATCH", "Contract rows must split into 144 applicable and 9 explicit N/A context rows.", reference))
    families = {row.get("evidence_family_id") for row in rows}
    if families != {family["evidence_family_id"] for family in EVIDENCE_FAMILIES}:
        issues.append(_issue(run_id, "ERROR", "EVIDENCE_FAMILY_SET_MISMATCH", "All 17 evidence families must be present.", reference))
    for row in rows:
        for field in STATE_FALSE_FIELDS:
            if _to_bool(row.get(field)):
                issues.append(_issue(run_id, "ERROR", "FORBIDDEN_CONTRACT_STATE_TRUE", f"{field} must remain false.", reference))
    return issues


def _vocabulary_issues(
    run_id: str,
    relative_dir: str,
    status_rows: list[dict[str, str]],
    blocker_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if {row.get("status") for row in status_rows} != set(STATUS_VOCABULARY):
        issues.append(_issue(run_id, "ERROR", "STATUS_VOCABULARY_MISMATCH", "Status vocabulary must match the 17 accepted definitions.", f"{relative_dir}/{OUTPUT_FILES['status_vocabulary']}"))
    if {row.get("blocker_id") for row in blocker_rows} != set(BLOCKER_VOCABULARY):
        issues.append(_issue(run_id, "ERROR", "BLOCKER_VOCABULARY_MISMATCH", "Blocker vocabulary must match the 28 accepted definitions.", f"{relative_dir}/{OUTPUT_FILES['blocker_vocabulary']}"))
    return issues


def _public_disclosure_issues(
    run_id: str, relative_dir: str, paths: dict[str, Path]
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for key in PUBLIC_FILE_KEYS:
        path = paths[key]
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        reference = f"{relative_dir}/{path.name}"
        for code, pattern, message in [
            ("FULL_HASH_DISCLOSURE", FULL_HASH_RE, "Public artifact contains a full hash."),
            ("PRIVATE_PATH_DISCLOSURE", PRIVATE_WINDOWS_PATH_RE, "Public artifact contains a private absolute Windows path."),
            ("SECRET_DISCLOSURE", SECRET_ASSIGNMENT_RE, "Public artifact contains secret-like assigned content."),
        ]:
            if pattern.search(text):
                issues.append(_issue(run_id, "ERROR", code, message, reference))
    return issues


def _paths(output_dir: Path) -> dict[str, Path]:
    stem = "historical_replay_source_evidence_sufficiency_policy_contract_fixture_health"
    return {
        "artifact_dir": output_dir,
        "health_csv": output_dir / f"{stem}.csv",
        "health_md": output_dir / f"{stem}.md",
        "metadata_json": output_dir / "metadata.json",
    }


def _write(
    result: HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureHealthResult,
) -> None:
    result.artifact_paths["artifact_dir"].mkdir(parents=True, exist_ok=True)
    with result.artifact_paths["health_csv"].open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=HEALTH_COLUMNS)
        writer.writeheader()
        writer.writerows(result.rows)
    result.artifact_paths["health_md"].write_text(
        _render_markdown(result), encoding="utf-8"
    )
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


def _render_markdown(
    result: HistoricalReplaySourceEvidenceSufficiencyPolicyContractFixtureHealthResult,
) -> str:
    return "\n".join(
        [
            "# Historical Replay Source / Evidence Sufficiency Policy Contract Fixture Health",
            "",
            f"- Status: `{result.status}`",
            f"- Checked fixture runs: `{result.checked_artifact_count}`",
            f"- Errors: `{result.error_count}`",
            f"- Warnings: `{result.warning_count}`",
            "- Health evaluates synthetic artifact integrity only. PASS is not evidence sufficiency, acceptance, closure, PIT approval, or replay readiness.",
            "",
        ]
    )


def _issue(
    run_id: str,
    severity: str,
    code: str,
    message: str,
    artifact_reference: str,
) -> dict[str, str]:
    return {
        "run_id": run_id,
        "status": "",
        "severity": severity,
        "issue_code": code,
        "message": message,
        "artifact_reference": artifact_reference,
    }


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            return list(reader), list(reader.fieldnames or [])
    except (OSError, csv.Error):
        return [], []


def _text(value: Any) -> str:
    return "" if value is None else str(value)


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
