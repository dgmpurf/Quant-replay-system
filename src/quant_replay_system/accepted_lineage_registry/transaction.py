"""Byte-verified, single-writer atomic materialization for authorized modes."""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .canonical import canonical_json_bytes, fsync_directory, sha256_bytes, sha256_file, write_bytes_fsync
from .index import mark_index_stale, regenerate_index
from .locking import RegistryWriteLock
from .models import (
    GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE,
    REGISTRY_POLICY_VERSION,
    REGISTRY_SCHEMA_VERSION,
    SYNTHETIC_MODE,
    GovernedCandidateRegistryPolicy,
    HumanReviewPayload,
    MaterializationResult,
    RegistryError,
    RegistryPolicy,
    RegistrySchema,
    ReviewReceiptReference,
    SubjectArtifactManifest,
)
from .path_safety import (
    assert_regular_single_link_file,
    capture_directory_chain_snapshot,
    capture_path_snapshot,
    derive_receipt_key,
    derive_subject_key,
    revalidate_directory_chain_snapshot,
    revalidate_path_snapshot,
    same_filesystem,
    validate_registry_root_authority,
    validate_safe_directory_chain,
)
from .subject_verification import SubjectInputVerification, revalidate_subject_inputs, validate_subject_inputs
from .verification import entry_path, load_registry_configuration, verify_entry


def _timestamp(value: datetime | None) -> str:
    instant = value or datetime.now(timezone.utc)
    return instant.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _authority_kwargs(
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path],
    expected_registry_root: str | Path | None,
    registry_mode: str,
) -> dict[str, Any]:
    return {
        "approved_admin_root": approved_admin_root,
        "repository_root": repository_root,
        "protected_roots": protected_roots,
        "expected_registry_root": expected_registry_root,
        "registry_mode": registry_mode,
    }


def initialize_synthetic_registry(
    root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expected_registry_root: str | Path | None = None,
) -> Path:
    authority = _authority_kwargs(
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        protected_roots=protected_roots,
        expected_registry_root=expected_registry_root,
        registry_mode=SYNTHETIC_MODE,
    )
    return _initialize_registry(root, policy=RegistryPolicy(), **authority)


def _initialize_registry(
    root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path],
    expected_registry_root: str | Path | None,
    registry_mode: str,
    policy: RegistryPolicy | GovernedCandidateRegistryPolicy,
) -> Path:
    authority = _authority_kwargs(
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        protected_roots=protected_roots,
        expected_registry_root=expected_registry_root,
        registry_mode=registry_mode,
    )
    registry_root = validate_registry_root_authority(root, create=False, **authority)
    if registry_root.exists():
        if registry_mode == GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE:
            try:
                load_registry_configuration(registry_root, **authority)
            except RegistryError as exc:
                raise RegistryError(
                    "REAL_CANDIDATE_MATERIALIZATION_ROOT_ALREADY_EXISTS_STOP",
                    "Existing candidate root is not the expected initialized candidate registry",
                ) from exc
        else:
            validate_registry_root_authority(root, create=True, **authority)
    else:
        if registry_mode == GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE:
            try:
                registry_root.mkdir()
            except FileExistsError as exc:
                raise RegistryError(
                    "REAL_CANDIDATE_MATERIALIZATION_ROOT_ALREADY_EXISTS_STOP",
                    "Candidate root appeared before initialization",
                ) from exc
            registry_root = validate_registry_root_authority(root, create=False, **authority)
        else:
            registry_root = validate_registry_root_authority(root, create=True, **authority)
    if any(registry_root.iterdir()):
        load_registry_configuration(registry_root, **authority)
        for directory in ("entries", "derived", ".staging"):
            validate_safe_directory_chain(
                registry_root / directory,
                containment_root=registry_root,
                create=False,
                classification="DERIVED_INDEX_PATH_SAFETY_STOP" if directory == "derived" else "PATH_KEY_DERIVATION_OR_VALIDATION_STOP",
            )
        return registry_root
    for directory in ("entries", "derived", ".staging"):
        validate_safe_directory_chain(registry_root / directory, containment_root=registry_root, create=True)
    policy_bytes = canonical_json_bytes(policy.to_dict())
    schema_bytes = canonical_json_bytes(RegistrySchema().to_dict())
    write_bytes_fsync(registry_root / "registry_policy.json", policy_bytes)
    write_bytes_fsync(registry_root / "registry_schema.json", schema_bytes)
    fsync_directory(registry_root)
    load_registry_configuration(registry_root, **authority)
    return registry_root


def initialize_governed_candidate_registry(
    root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expected_registry_root: str | Path | None = None,
) -> Path:
    return _initialize_registry(
        root,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        protected_roots=protected_roots,
        expected_registry_root=expected_registry_root,
        registry_mode=GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE,
        policy=GovernedCandidateRegistryPolicy(),
    )


def _immutable_identity(
    payload: HumanReviewPayload,
    subject_manifest: SubjectArtifactManifest,
    receipt: ReviewReceiptReference,
) -> dict[str, Any]:
    return {
        "subject_phase_id": payload.subject_phase_id,
        "receipt_id": payload.receipt_id,
        "human_review_payload_sha256": payload.exact_sha256,
        "subject_artifact_manifest_sha256": subject_manifest.exact_sha256,
        "review_receipt_sha256": receipt.exact_sha256,
        "registry_schema_version": REGISTRY_SCHEMA_VERSION,
        "registry_policy_version": REGISTRY_POLICY_VERSION,
    }


def _existing_identity(verified: dict[str, Any]) -> dict[str, Any]:
    return {
        key: verified[key]
        for key in (
            "subject_phase_id",
            "receipt_id",
            "human_review_payload_sha256",
            "subject_artifact_manifest_sha256",
            "review_receipt_sha256",
            "registry_schema_version",
            "registry_policy_version",
        )
    }


def _raise_identity_conflict(expected: dict[str, Any], actual: dict[str, Any]) -> None:
    if expected["human_review_payload_sha256"] != actual["human_review_payload_sha256"]:
        classification = "HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP"
    elif expected["subject_artifact_manifest_sha256"] != actual["subject_artifact_manifest_sha256"]:
        classification = "SUBJECT_ARTIFACT_MANIFEST_MISMATCH_STOP"
    else:
        classification = "ACCEPTANCE_RECEIPT_ID_COLLISION_STOP"
    raise RegistryError(classification, "Existing receipt key has conflicting immutable review identity")


def _safe_remove_known_directory(path: Path, *, containment_root: Path, expected_files: Sequence[str]) -> None:
    if not path.exists():
        return
    validate_safe_directory_chain(path, containment_root=containment_root, create=False)
    children = list(path.iterdir())
    unexpected = [child.name for child in children if child.name not in expected_files or not child.is_file()]
    if unexpected:
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "Refusing to remove directory with unexpected content")
    for child in children:
        assert_regular_single_link_file(child)
        child.unlink()
    path.rmdir()


def _validate_cross_contracts(
    payload: HumanReviewPayload,
    subject_manifest: SubjectArtifactManifest,
) -> None:
    if subject_manifest.data["subject_phase_id"] != payload.subject_phase_id:
        raise RegistryError("SUBJECT_ARTIFACT_MANIFEST_MISMATCH_STOP", "Subject phase mismatch")
    if subject_manifest.data["subject_packet_identifier"] != payload.data["subject_packet_identifier"]:
        raise RegistryError("SUBJECT_PACKET_HASH_MISMATCH_STOP", "Subject packet identifier mismatch")
    if subject_manifest.data["subject_packet_sha256"] != payload.data["subject_packet_sha256"]:
        raise RegistryError("SUBJECT_PACKET_HASH_MISMATCH_STOP", "Subject packet hash mismatch")
    if subject_manifest.exact_sha256 != payload.data["subject_artifact_manifest_sha256"]:
        raise RegistryError("SUBJECT_ARTIFACT_MANIFEST_MISMATCH_STOP", "Subject artifact manifest hash mismatch")


def _revalidate_actual_subject(
    baseline: SubjectInputVerification,
    *,
    payload: HumanReviewPayload,
    subject_manifest: SubjectArtifactManifest,
    subject_packet_path: str | Path,
    subject_artifact_root: str | Path,
    registry_root: Path,
    authority: dict[str, Any],
) -> SubjectInputVerification:
    return revalidate_subject_inputs(
        baseline,
        payload=payload,
        manifest=subject_manifest,
        subject_packet_path=subject_packet_path,
        subject_artifact_root=subject_artifact_root,
        approved_admin_root=authority["approved_admin_root"],
        repository_root=authority["repository_root"],
        registry_root=registry_root,
        protected_roots=authority["protected_roots"],
    )


def _materialize(
    root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    subject_packet_path: str | Path | None,
    subject_artifact_root: str | Path | None,
    human_review_payload_bytes: bytes,
    subject_artifact_manifest_bytes: bytes,
    review_receipt_bytes: bytes,
    materialization_authorization_id: str | None,
    protected_roots: Sequence[str | Path] = (),
    expected_registry_root: str | Path | None = None,
    operator_alias: str = "synthetic-codex",
    operation_id: str | None = None,
    materialized_at: datetime | None = None,
    lock_timeout_seconds: float = 5.0,
    stale_lock_seconds: float = 300.0,
    failure_injection: str | None = None,
    registry_mode: str = SYNTHETIC_MODE,
    enforce_synthetic_identifiers: bool = True,
    success_classification: str = "NEW_ENTRY_MATERIALIZED_SUCCESSFULLY",
    idempotent_classification: str = "IDEMPOTENT_PASS_EXISTING_IDENTICAL_ENTRY",
    collision_classification: str | None = None,
    registry_status: str = "SYNTHETIC_ACCEPTED_REVIEW_MATERIALIZED",
    seal_status: str = "SYNTHETIC_ENTRY_SEALED",
    validation_result: dict[str, Any] | None = None,
    runtime_manifest_extra: dict[str, Any] | None = None,
) -> MaterializationResult:
    if not materialization_authorization_id or not materialization_authorization_id.strip():
        classification = (
            "REAL_CANDIDATE_MATERIALIZATION_EXACT_APPROVAL_MISSING_STOP"
            if registry_mode == GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE
            else "MATERIALIZATION_EXACT_APPROVAL_MISSING_STOP"
        )
        raise RegistryError(
            classification,
            "Separate exact materialization approval is required",
        )
    authority = _authority_kwargs(
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        protected_roots=protected_roots,
        expected_registry_root=expected_registry_root,
        registry_mode=registry_mode,
    )
    prospective_root = validate_registry_root_authority(root, create=False, **authority)
    payload = HumanReviewPayload.from_bytes(human_review_payload_bytes)
    if enforce_synthetic_identifiers:
        payload.assert_synthetic_only()
    subject_manifest = SubjectArtifactManifest.from_bytes(subject_artifact_manifest_bytes)
    receipt = ReviewReceiptReference.from_bytes(
        review_receipt_bytes,
        receipt_id=payload.receipt_id,
        subject_phase_id=payload.subject_phase_id,
    )
    _validate_cross_contracts(payload, subject_manifest)
    baseline_subject = validate_subject_inputs(
        payload=payload,
        manifest=subject_manifest,
        subject_packet_path=subject_packet_path,
        subject_artifact_root=subject_artifact_root,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        registry_root=prospective_root,
        protected_roots=protected_roots,
    )
    assert subject_packet_path is not None
    assert subject_artifact_root is not None

    if registry_mode == SYNTHETIC_MODE:
        registry_root = initialize_synthetic_registry(
            root,
            approved_admin_root=approved_admin_root,
            repository_root=repository_root,
            protected_roots=protected_roots,
            expected_registry_root=expected_registry_root,
        )
    elif registry_mode == GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE:
        registry_root = initialize_governed_candidate_registry(
            root,
            approved_admin_root=approved_admin_root,
            repository_root=repository_root,
            protected_roots=protected_roots,
            expected_registry_root=expected_registry_root,
        )
    else:
        raise RegistryError("LIVE_REGISTRY_MODE_NOT_AUTHORIZED_STOP", "Registry mode is not authorized")
    policy, schema = load_registry_configuration(registry_root, **authority)
    if policy["registry_mode"] != registry_mode:
        raise RegistryError("LIVE_REGISTRY_MODE_NOT_AUTHORIZED_STOP", "Registry policy mode differs from requested mode")
    subject_key = derive_subject_key(payload.subject_phase_id)
    receipt_key = derive_receipt_key(payload.receipt_id)
    operation = operation_id or hashlib.sha256(
        f"{subject_key}|{receipt_key}|{materialization_authorization_id}".encode("utf-8")
    ).hexdigest()[:16]
    root_snapshot = capture_path_snapshot(registry_root, registry_mode=registry_mode)
    entries_root = validate_safe_directory_chain(registry_root / "entries", containment_root=registry_root, create=False)
    staging_root = validate_safe_directory_chain(registry_root / ".staging", containment_root=registry_root, create=False)
    derived_root = validate_safe_directory_chain(
        registry_root / "derived",
        containment_root=registry_root,
        create=False,
        classification="DERIVED_INDEX_PATH_SAFETY_STOP",
    )
    if not same_filesystem(staging_root, entries_root):
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "Staging and target filesystems differ")

    lock = RegistryWriteLock(
        registry_root=registry_root,
        operator_alias=operator_alias,
        operation_id=operation,
        approved_admin_root=Path(approved_admin_root),
        repository_root=Path(repository_root),
        protected_roots=tuple(Path(item) for item in protected_roots),
        expected_registry_root=Path(expected_registry_root) if expected_registry_root is not None else None,
        registry_mode=registry_mode,
        timeout_seconds=lock_timeout_seconds,
        stale_after_seconds=stale_lock_seconds,
    )
    with lock:
        target = entry_path(registry_root, subject_key, receipt_key)
        expected_identity = _immutable_identity(payload, subject_manifest, receipt)
        if target.exists():
            verified = verify_entry(registry_root, subject_key, receipt_key, **authority)
            actual_identity = _existing_identity(verified)
            if actual_identity == expected_identity:
                _revalidate_actual_subject(
                    baseline_subject,
                    payload=payload,
                    subject_manifest=subject_manifest,
                    subject_packet_path=subject_packet_path,
                    subject_artifact_root=subject_artifact_root,
                    registry_root=registry_root,
                    authority=authority,
                )
                return MaterializationResult(
                    classification=idempotent_classification,
                    subject_key=subject_key,
                    receipt_key=receipt_key,
                    entry_created=False,
                    idempotent_replay=True,
                    entry_verified=True,
                    derived_index_status="UNCHANGED",
                    entry_verification_started=True,
                    entry_verification_completed=True,
                    entry_verification_passed=True,
                    materialization_verified=True,
                )
            if collision_classification is not None:
                raise RegistryError(
                    collision_classification,
                    "Existing receipt key has conflicting immutable review identity",
                )
            _raise_identity_conflict(expected_identity, actual_identity)

        subject_parent = validate_safe_directory_chain(
            entries_root / subject_key,
            containment_root=registry_root,
            create=True,
        )
        stage_name = f".tmp-{receipt_key}-{hashlib.sha256(operation.encode('utf-8')).hexdigest()[:12]}"
        stage = staging_root / stage_name
        if stage.exists():
            raise RegistryError("ATOMIC_WRITE_FAILED_NO_AUTHORITATIVE_ENTRY_CREATED", "Staging path already exists")
        validate_safe_directory_chain(stage, containment_root=registry_root, create=True)
        descendant_snapshot = capture_directory_chain_snapshot(
            (registry_root, entries_root, staging_root, derived_root, subject_parent, stage),
            containment_root=registry_root,
        )
        renamed = False
        authoritative_entry_created = False
        entry_verification_started = False
        entry_verification_completed = False
        entry_verification_passed = False
        entry_verification_failure: str | None = None
        try:
            if failure_injection == "after_stage_created":
                raise OSError("injected failure after staging directory creation")
            immutable_files = {
                "human_review_payload.json": payload.exact_bytes,
                "subject_artifact_manifest.json": subject_manifest.exact_bytes,
                "review_receipt.md": receipt.exact_bytes,
            }
            for filename, exact_bytes in immutable_files.items():
                write_bytes_fsync(stage / filename, exact_bytes)
            if failure_injection == "after_immutable_files":
                raise OSError("injected failure after immutable files")
            timestamp = _timestamp(materialized_at)
            runtime_manifest = {
                "actual_subject_bytes_verified": True,
                "entry_file_count": 5,
                "entry_relative_path": f"entries/{subject_key}/{receipt_key}/",
                "human_review_payload_filename": "human_review_payload.json",
                "human_review_payload_sha256": payload.exact_sha256,
                "idempotency_result": "NEW_ENTRY",
                "materialization_authorization_id": materialization_authorization_id,
                "materialized_at": timestamp,
                "materialized_by": operator_alias,
                "operation_identifier": operation,
                "receipt_key": receipt_key,
                "registry_policy_version": policy["registry_policy_version"],
                "registry_schema_version": schema["registry_schema_version"],
                "registry_status": registry_status,
                "review_receipt_filename": "review_receipt.md",
                "review_receipt_sha256": receipt.exact_sha256,
                "subject_artifact_count": len(baseline_subject.artifacts),
                "subject_artifact_manifest_filename": "subject_artifact_manifest.json",
                "subject_artifact_manifest_sha256": subject_manifest.exact_sha256,
                "subject_input_rehash": {
                    "initial": "PASS",
                    "post_output": "PASS",
                    "pre_rename": "PASS",
                },
                "subject_key": subject_key,
                "subject_packet_byte_length": baseline_subject.packet.byte_length,
                "subject_packet_sha256": baseline_subject.packet.sha256,
                "validation_result": validation_result or {"status": "PASS", "synthetic_only": True},
            }
            runtime_manifest.update(runtime_manifest_extra or {})
            manifest_bytes = canonical_json_bytes(runtime_manifest)
            write_bytes_fsync(stage / "entry_manifest.json", manifest_bytes)
            if failure_injection == "after_manifest":
                raise OSError("injected failure after entry manifest")
            seal = {
                "entry_manifest_filename": "entry_manifest.json",
                "entry_manifest_sha256": sha256_bytes(manifest_bytes),
                "receipt_key": receipt_key,
                "registry_policy_version": policy["registry_policy_version"],
                "registry_schema_version": schema["registry_schema_version"],
                "seal_created_at": timestamp,
                "seal_created_by": operator_alias,
                "seal_status": seal_status,
                "subject_key": subject_key,
            }
            write_bytes_fsync(stage / "entry_seal.json", canonical_json_bytes(seal))
            if failure_injection == "after_seal":
                raise OSError("injected failure after entry seal")
            for filename in RegistrySchema().entry_files:
                assert_regular_single_link_file(stage / filename)
            _revalidate_actual_subject(
                baseline_subject,
                payload=payload,
                subject_manifest=subject_manifest,
                subject_packet_path=subject_packet_path,
                subject_artifact_root=subject_artifact_root,
                registry_root=registry_root,
                authority=authority,
            )
            if failure_injection == "mutate_human_payload_before_rename":
                (stage / "human_review_payload.json").write_bytes(payload.exact_bytes + b" ")
            if sha256_file(stage / "human_review_payload.json") != payload.exact_sha256:
                raise RegistryError("HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP", "Reviewer payload changed before rename")
            if sha256_file(stage / "subject_artifact_manifest.json") != subject_manifest.exact_sha256:
                raise RegistryError("SUBJECT_ARTIFACT_MANIFEST_MISMATCH_STOP", "Subject manifest changed before rename")
            if sha256_file(stage / "review_receipt.md") != receipt.exact_sha256:
                raise RegistryError("HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP", "Review receipt changed before rename")
            _revalidate_actual_subject(
                baseline_subject,
                payload=payload,
                subject_manifest=subject_manifest,
                subject_packet_path=subject_packet_path,
                subject_artifact_root=subject_artifact_root,
                registry_root=registry_root,
                authority=authority,
            )
            revalidate_path_snapshot(registry_root, root_snapshot, registry_mode=registry_mode)
            revalidate_directory_chain_snapshot(
                (registry_root, entries_root, staging_root, derived_root, subject_parent, stage),
                descendant_snapshot,
                containment_root=registry_root,
            )
            if failure_injection == "before_rename":
                raise OSError("injected failure before atomic rename")
            if target.exists():
                raise RegistryError("ACCEPTANCE_RECEIPT_ID_COLLISION_STOP", "Target appeared before rename")
            if not same_filesystem(stage, subject_parent):
                raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "Staging and target device changed")
            fsync_directory(stage)
            os.rename(stage, target)
            renamed = True
            authoritative_entry_created = True
            if failure_injection == "after_authoritative_rename":
                raise OSError("injected failure immediately after authoritative rename")
            validate_safe_directory_chain(target, containment_root=registry_root, create=False)
            fsync_directory(target.parent)
            if failure_injection == "before_entry_verification":
                raise OSError("injected failure before entry verification")
            entry_verification_started = True
            verified = verify_entry(
                registry_root,
                subject_key,
                receipt_key,
                subject_packet_path=subject_packet_path,
                subject_artifact_root=subject_artifact_root,
                **authority,
            )
            entry_verification_completed = True
            entry_verification_passed = verified.get("status") == "PASS"
            if not entry_verification_passed:
                entry_verification_failure = "VERIFY_ENTRY_RETURNED_NON_PASS"
        except RegistryError as exc:
            if not renamed:
                _safe_remove_known_directory(stage, containment_root=registry_root, expected_files=RegistrySchema().entry_files)
                raise
            entry_verification_failure = exc.classification
        except Exception as exc:
            if not renamed:
                _safe_remove_known_directory(stage, containment_root=registry_root, expected_files=RegistrySchema().entry_files)
                raise RegistryError(
                    "ATOMIC_WRITE_FAILED_NO_AUTHORITATIVE_ENTRY_CREATED",
                    "Atomic materialization failed before authoritative rename",
                ) from exc
            entry_verification_failure = type(exc).__name__

        if not entry_verification_passed:
            classification = (
                "ENTRY_VERIFICATION_FAILED_AFTER_AUTHORITATIVE_RENAME"
                if entry_verification_started
                else "ENTRY_CREATED_VERIFICATION_INCOMPLETE_REVIEW_REQUIRED"
            )
            try:
                mark_index_stale(registry_root, classification, **authority)
            except RegistryError:
                pass
            return MaterializationResult(
                classification=classification,
                subject_key=subject_key,
                receipt_key=receipt_key,
                entry_created=True,
                idempotent_replay=False,
                entry_verified=False,
                derived_index_status="NOT_ATTEMPTED_STALE",
                authoritative_entry_created=authoritative_entry_created,
                entry_verification_started=entry_verification_started,
                entry_verification_completed=entry_verification_completed,
                entry_verification_passed=False,
                materialization_verified=False,
                entry_verification_failure=entry_verification_failure,
            )

        derived_index_attempted = False
        derived_index_completed = False
        derived_index_passed = False
        try:
            if failure_injection == "after_rename_before_index":
                raise RegistryError(
                    "DERIVED_INDEX_REGENERATION_FAILED_ENTRY_VERIFIED_INDEX_STALE",
                    "Injected post-rename index failure",
                )
            derived_index_attempted = True
            index_result = regenerate_index(
                registry_root,
                failure_injection=failure_injection,
                lock_held=True,
                **authority,
            )
            derived_index_completed = True
            derived_index_passed = index_result.get("status") == "PASS"
            if not derived_index_passed:
                raise RegistryError(
                    "DERIVED_INDEX_REGENERATION_FAILED_ENTRY_VERIFIED_INDEX_STALE",
                    "Derived index regeneration returned a non-PASS result",
                )
            index_status = str(index_result["status"])
            classification = success_classification
        except Exception:
            try:
                mark_index_stale(registry_root, "DERIVED_INDEX_REGENERATION_FAILED_ENTRY_VERIFIED_INDEX_STALE", **authority)
            except RegistryError:
                pass
            index_status = "STALE"
            classification = "DERIVED_INDEX_REGENERATION_FAILED_ENTRY_VERIFIED_INDEX_STALE"
        return MaterializationResult(
            classification=classification,
            subject_key=subject_key,
            receipt_key=receipt_key,
            entry_created=True,
            idempotent_replay=False,
            entry_verified=entry_verification_passed,
            derived_index_status=index_status,
            authoritative_entry_created=authoritative_entry_created,
            entry_verification_started=entry_verification_started,
            entry_verification_completed=entry_verification_completed,
            entry_verification_passed=entry_verification_passed,
            derived_index_attempted=derived_index_attempted,
            derived_index_completed=derived_index_completed,
            derived_index_passed=derived_index_passed,
            materialization_verified=entry_verification_passed and derived_index_passed,
            entry_verification_failure=entry_verification_failure,
        )


def materialize_synthetic(
    root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    subject_packet_path: str | Path | None,
    subject_artifact_root: str | Path | None,
    human_review_payload_bytes: bytes,
    subject_artifact_manifest_bytes: bytes,
    review_receipt_bytes: bytes,
    materialization_authorization_id: str | None,
    protected_roots: Sequence[str | Path] = (),
    expected_registry_root: str | Path | None = None,
    operator_alias: str = "synthetic-codex",
    operation_id: str | None = None,
    materialized_at: datetime | None = None,
    lock_timeout_seconds: float = 5.0,
    stale_lock_seconds: float = 300.0,
    failure_injection: str | None = None,
) -> MaterializationResult:
    """Materialize an explicitly synthetic fixture using the shared transaction."""

    return _materialize(
        root,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        subject_packet_path=subject_packet_path,
        subject_artifact_root=subject_artifact_root,
        human_review_payload_bytes=human_review_payload_bytes,
        subject_artifact_manifest_bytes=subject_artifact_manifest_bytes,
        review_receipt_bytes=review_receipt_bytes,
        materialization_authorization_id=materialization_authorization_id,
        protected_roots=protected_roots,
        expected_registry_root=expected_registry_root,
        operator_alias=operator_alias,
        operation_id=operation_id,
        materialized_at=materialized_at,
        lock_timeout_seconds=lock_timeout_seconds,
        stale_lock_seconds=stale_lock_seconds,
        failure_injection=failure_injection,
    )
