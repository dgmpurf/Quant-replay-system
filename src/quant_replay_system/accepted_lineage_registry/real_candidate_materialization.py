"""Governed, non-live materialization of an exact reviewed candidate."""

from __future__ import annotations

import os
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from .canonical import sha256_bytes
from .models import (
    GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE,
    SHA256_RE,
    MaterializationResult,
    RegistryError,
)
from .path_safety import validate_registry_root_authority
from .real_candidate import (
    ARTIFACT_SET_STOP,
    AUTHORITY_PRESENT_STOP,
    MANIFEST_HASH_STOP,
    PACKET_HASH_STOP,
    PAYLOAD_HASH_STOP,
    REVIEW_DECISION_STOP,
    REVIEW_RECEIPT_HASH_STOP,
    REVIEW_RECEIPT_STOP,
    RUNTIME_FIELD_STOP,
    _cross_contracts,
    _manifest,
    _payload,
    _receipt,
    _subject_inputs,
)
from .transaction import _materialize
from .verification import load_registry_configuration


AUTHORIZATION_MISSING_STOP = "REAL_CANDIDATE_MATERIALIZATION_EXACT_APPROVAL_MISSING_STOP"
AUTHORIZATION_MISMATCH_STOP = "REAL_CANDIDATE_MATERIALIZATION_AUTHORIZATION_MISMATCH_STOP"
AUTHORIZATION_NOT_DISTINCT_STOP = "REAL_CANDIDATE_MATERIALIZATION_AUTHORIZATION_NOT_DISTINCT_STOP"
REVIEW_DECISION_MISMATCH_STOP = "REAL_CANDIDATE_MATERIALIZATION_REVIEW_DECISION_MISMATCH_STOP"
REVIEWER_INPUT_HASH_MISMATCH_STOP = "REAL_CANDIDATE_MATERIALIZATION_REVIEWER_INPUT_HASH_MISMATCH_STOP"
PACKET_HASH_MISMATCH_STOP = "REAL_CANDIDATE_MATERIALIZATION_PACKET_HASH_MISMATCH_STOP"
ARTIFACT_SET_MISMATCH_STOP = "REAL_CANDIDATE_MATERIALIZATION_ARTIFACT_SET_MISMATCH_STOP"
ROOT_UNSAFE_STOP = "REAL_CANDIDATE_MATERIALIZATION_ROOT_UNSAFE_STOP"
ROOT_ALREADY_EXISTS_STOP = "REAL_CANDIDATE_MATERIALIZATION_ROOT_ALREADY_EXISTS_STOP"
LIVE_ROOT_COLLISION_STOP = "REAL_CANDIDATE_MATERIALIZATION_LIVE_ROOT_COLLISION_STOP"
RUNTIME_FIELD_PRESENT_STOP = "REAL_CANDIDATE_MATERIALIZATION_RUNTIME_FIELD_PRESENT_STOP"
RECEIPT_COLLISION_STOP = "REAL_CANDIDATE_MATERIALIZATION_RECEIPT_COLLISION_STOP"

SUCCESS_CLASSIFICATION = "NEW_REAL_CANDIDATE_ENTRY_MATERIALIZED_SUCCESSFULLY"
IDEMPOTENT_CLASSIFICATION = "IDEMPOTENT_PASS_EXISTING_IDENTICAL_REAL_CANDIDATE_ENTRY"


def _absolute(value: str | Path) -> Path:
    return Path(os.path.abspath(os.fspath(value)))


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(os.path.normpath(os.fspath(left))) == os.path.normcase(
        os.path.normpath(os.fspath(right))
    )


def _within(path: Path, parent: Path, *, strict: bool = False) -> bool:
    try:
        common = os.path.commonpath((os.fspath(path), os.fspath(parent)))
    except ValueError:
        return False
    same = os.path.normcase(common) == os.path.normcase(os.fspath(parent))
    return same and (not strict or not _same_path(path, parent))


def _overlaps(left: Path, right: Path) -> bool:
    return _same_path(left, right) or _within(left, right, strict=True) or _within(right, left, strict=True)


def _validate_expected_hashes(values: dict[str, str]) -> None:
    invalid = [name for name, value in values.items() if not isinstance(value, str) or not SHA256_RE.fullmatch(value)]
    if invalid:
        raise RegistryError(
            REVIEWER_INPUT_HASH_MISMATCH_STOP,
            "Expected reviewer-input hashes must be lowercase SHA-256 hexadecimal",
            details={"invalid_fields": invalid},
        )


def _validate_reviewer_hashes(
    *,
    human_review_payload_bytes: bytes,
    subject_artifact_manifest_bytes: bytes,
    review_receipt_bytes: bytes,
    expected_payload_sha256: str,
    expected_subject_manifest_sha256: str,
    expected_review_receipt_sha256: str,
) -> None:
    expected = {
        "expected_payload_sha256": expected_payload_sha256,
        "expected_subject_manifest_sha256": expected_subject_manifest_sha256,
        "expected_review_receipt_sha256": expected_review_receipt_sha256,
    }
    _validate_expected_hashes(expected)
    actual = {
        "expected_payload_sha256": sha256_bytes(human_review_payload_bytes),
        "expected_subject_manifest_sha256": sha256_bytes(subject_artifact_manifest_bytes),
        "expected_review_receipt_sha256": sha256_bytes(review_receipt_bytes),
    }
    mismatched = [name for name in expected if actual[name] != expected[name]]
    if mismatched:
        raise RegistryError(
            REVIEWER_INPUT_HASH_MISMATCH_STOP,
            "Reviewer-authority input bytes differ from their exact approved hashes",
            details={"mismatched_fields": mismatched},
        )


def _validate_authorization(
    current: str | None,
    expected: str | None,
    *,
    review_decision_id: str,
    receipt_id: str,
) -> str:
    if not isinstance(current, str) or not current.strip() or not isinstance(expected, str) or not expected.strip():
        raise RegistryError(AUTHORIZATION_MISSING_STOP, "Two separately supplied materialization authorization IDs are required")
    for value in (current, expected):
        try:
            stable = value.encode("utf-8").decode("utf-8") == value and unicodedata.normalize("NFC", value) == value
        except UnicodeError:
            stable = False
        if not stable:
            raise RegistryError(AUTHORIZATION_MISMATCH_STOP, "Materialization authorization ID is not UTF-8/NFC stable")
    if current != expected:
        raise RegistryError(AUTHORIZATION_MISMATCH_STOP, "Current and expected materialization authorization IDs differ")
    if current == review_decision_id or current == receipt_id:
        raise RegistryError(
            AUTHORIZATION_NOT_DISTINCT_STOP,
            "Materialization authorization ID must be distinct from reviewer identities",
        )
    return current


def _map_contract_error(exc: RegistryError) -> RegistryError:
    mapping = {
        PAYLOAD_HASH_STOP: REVIEWER_INPUT_HASH_MISMATCH_STOP,
        MANIFEST_HASH_STOP: REVIEWER_INPUT_HASH_MISMATCH_STOP,
        REVIEW_RECEIPT_HASH_STOP: REVIEWER_INPUT_HASH_MISMATCH_STOP,
        REVIEW_DECISION_STOP: REVIEW_DECISION_MISMATCH_STOP,
        REVIEW_RECEIPT_STOP: REVIEW_DECISION_MISMATCH_STOP,
        RUNTIME_FIELD_STOP: RUNTIME_FIELD_PRESENT_STOP,
        AUTHORITY_PRESENT_STOP: RUNTIME_FIELD_PRESENT_STOP,
        PACKET_HASH_STOP: PACKET_HASH_MISMATCH_STOP,
        ARTIFACT_SET_STOP: ARTIFACT_SET_MISMATCH_STOP,
    }
    classification = mapping.get(exc.classification, exc.classification)
    return RegistryError(classification, str(exc), details=exc.details)


def _validate_candidate_root(
    candidate_root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    expected_candidate_root: str | Path,
    future_live_registry_root: str | Path,
    subject_packet_path: str | Path,
    subject_artifact_root: str | Path,
    protected_roots: Sequence[str | Path],
) -> Path:
    candidate = _absolute(candidate_root)
    expected = _absolute(expected_candidate_root)
    admin = _absolute(approved_admin_root)
    repository = _absolute(repository_root)
    future_live = _absolute(future_live_registry_root)
    packet = _absolute(subject_packet_path)
    artifact_root = _absolute(subject_artifact_root)

    if not _same_path(candidate, expected):
        raise RegistryError(ROOT_UNSAFE_STOP, "Candidate root differs from the exact expected candidate root")
    if not _within(candidate, admin, strict=True) or _same_path(candidate, repository) or _within(candidate, repository, strict=True):
        raise RegistryError(ROOT_UNSAFE_STOP, "Candidate root is not repo-external below the approved administration root")
    if not _within(future_live, admin, strict=True) or _same_path(future_live, repository) or _within(future_live, repository, strict=True):
        raise RegistryError(LIVE_ROOT_COLLISION_STOP, "Future live registry root is outside its bounded administration surface")
    if _overlaps(candidate, future_live) or os.path.lexists(future_live):
        raise RegistryError(LIVE_ROOT_COLLISION_STOP, "Candidate root collides with the future live registry root")
    for immutable in (packet, artifact_root, *(_absolute(item) for item in protected_roots)):
        if _overlaps(candidate, immutable):
            raise RegistryError(ROOT_UNSAFE_STOP, "Candidate root overlaps an immutable or protected input root")

    try:
        validated = validate_registry_root_authority(
            candidate,
            approved_admin_root=admin,
            repository_root=repository,
            protected_roots=(*protected_roots, future_live),
            expected_registry_root=expected,
            registry_mode=GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE,
            create=False,
        )
    except RegistryError as exc:
        if exc.classification == LIVE_ROOT_COLLISION_STOP:
            raise
        raise RegistryError(ROOT_UNSAFE_STOP, "Candidate root authority validation failed") from exc

    if os.path.lexists(validated):
        if not validated.is_dir():
            raise RegistryError(ROOT_ALREADY_EXISTS_STOP, "Candidate root exists but is not a directory")
        try:
            load_registry_configuration(
                validated,
                approved_admin_root=admin,
                repository_root=repository,
                protected_roots=(*protected_roots, future_live),
                expected_registry_root=expected,
                registry_mode=GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE,
            )
        except RegistryError as exc:
            raise RegistryError(ROOT_ALREADY_EXISTS_STOP, "Candidate root already exists unexpectedly") from exc
        expected_children = {"entries", "derived", ".staging", "registry_policy.json", "registry_schema.json"}
        if {item.name for item in validated.iterdir()} != expected_children:
            raise RegistryError(ROOT_ALREADY_EXISTS_STOP, "Initialized candidate root contains an unexpected child")
    return validated


def materialize_real_candidate(
    root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    expected_candidate_root: str | Path,
    future_live_registry_root: str | Path,
    human_review_payload_bytes: bytes,
    subject_artifact_manifest_bytes: bytes,
    subject_packet_path: str | Path,
    subject_artifact_root: str | Path,
    review_receipt_bytes: bytes,
    expected_review_decision_id: str,
    expected_payload_sha256: str,
    expected_subject_manifest_sha256: str,
    expected_review_receipt_sha256: str,
    materialization_authorization_id: str | None,
    expected_materialization_authorization_id: str | None,
    protected_roots: Sequence[str | Path] = (),
    operator_alias: str = "governed-real-candidate-operator",
    operation_id: str | None = None,
    materialized_at: datetime | None = None,
    lock_timeout_seconds: float = 5.0,
    stale_lock_seconds: float = 300.0,
    failure_injection: str | None = None,
) -> MaterializationResult:
    """Materialize a reviewed candidate into a non-live candidate registry."""

    _validate_reviewer_hashes(
        human_review_payload_bytes=human_review_payload_bytes,
        subject_artifact_manifest_bytes=subject_artifact_manifest_bytes,
        review_receipt_bytes=review_receipt_bytes,
        expected_payload_sha256=expected_payload_sha256,
        expected_subject_manifest_sha256=expected_subject_manifest_sha256,
        expected_review_receipt_sha256=expected_review_receipt_sha256,
    )
    try:
        payload = _payload(
            human_review_payload_bytes,
            expected_sha256=expected_payload_sha256,
            expected_review_decision_id=expected_review_decision_id,
        )
        manifest = _manifest(subject_artifact_manifest_bytes, expected_sha256=expected_subject_manifest_sha256)
        _cross_contracts(payload, manifest)
        _receipt(
            review_receipt_bytes,
            payload=payload,
            expected_review_decision_id=expected_review_decision_id,
            expected_sha256=expected_review_receipt_sha256,
        )
    except RegistryError as exc:
        raise _map_contract_error(exc) from exc

    authorization_id = _validate_authorization(
        materialization_authorization_id,
        expected_materialization_authorization_id,
        review_decision_id=payload.data["review_decision_id"],
        receipt_id=payload.data["receipt_id"],
    )

    try:
        _subject_inputs(
            payload=payload,
            manifest=manifest,
            subject_packet_path=subject_packet_path,
            subject_artifact_root=subject_artifact_root,
            approved_admin_root=approved_admin_root,
            repository_root=repository_root,
            candidate_root=root,
        )
    except RegistryError as exc:
        raise _map_contract_error(exc) from exc

    candidate_root = _validate_candidate_root(
        root,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        expected_candidate_root=expected_candidate_root,
        future_live_registry_root=future_live_registry_root,
        subject_packet_path=subject_packet_path,
        subject_artifact_root=subject_artifact_root,
        protected_roots=protected_roots,
    )
    candidate_protected_roots = (*protected_roots, future_live_registry_root)
    return _materialize(
        candidate_root,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        subject_packet_path=subject_packet_path,
        subject_artifact_root=subject_artifact_root,
        human_review_payload_bytes=human_review_payload_bytes,
        subject_artifact_manifest_bytes=subject_artifact_manifest_bytes,
        review_receipt_bytes=review_receipt_bytes,
        materialization_authorization_id=authorization_id,
        protected_roots=candidate_protected_roots,
        expected_registry_root=expected_candidate_root,
        operator_alias=operator_alias,
        operation_id=operation_id,
        materialized_at=materialized_at,
        lock_timeout_seconds=lock_timeout_seconds,
        stale_lock_seconds=stale_lock_seconds,
        failure_injection=failure_injection,
        registry_mode=GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE,
        enforce_synthetic_identifiers=False,
        success_classification=SUCCESS_CLASSIFICATION,
        idempotent_classification=IDEMPOTENT_CLASSIFICATION,
        collision_classification=RECEIPT_COLLISION_STOP,
        registry_status="GOVERNED_REAL_CANDIDATE_NON_LIVE_MATERIALIZED",
        seal_status="GOVERNED_REAL_CANDIDATE_NON_LIVE_ENTRY_SEALED",
        validation_result={
            "status": "PASS",
            "governed_real_candidate": True,
            "live_registry": False,
            "next_task_authorized_by_registry": False,
        },
        runtime_manifest_extra={
            "mode": GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE,
            "candidate_registry": True,
            "live_registry": False,
            "artifact_verification_result": "PASS",
            "review_decision_id": payload.data["review_decision_id"],
        },
    )
