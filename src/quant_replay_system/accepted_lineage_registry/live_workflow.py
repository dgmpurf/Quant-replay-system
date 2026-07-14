"""Bounded prospective-live workflows that do not grant live-entry authority."""

from __future__ import annotations

import os
import unicodedata
from pathlib import Path
from typing import Any, Mapping, Sequence

from .canonical import (
    canonical_json_bytes,
    decode_json_object,
    flush_parent_directory_durable,
    sha256_bytes,
    write_bytes_durable,
)
from .models import (
    GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE,
    GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE,
    SYNTHETIC_MODE,
    GovernedLiveRegistryPolicy,
    HumanReviewPayload,
    RegistryError,
    RegistrySchema,
    SubjectArtifactManifest,
)
from .path_safety import (
    assert_no_filesystem_indirection,
    assert_regular_single_link_file,
    validate_candidate_live_root_separation,
    validate_live_registry_root_authority,
)
from .windows_live_backend import (
    DIRECTORY_DURABILITY_UNPROVEN_STOP,
    WindowsLiveFilesystemBackend,
)
from .subject_verification import validate_live_preflight_immutable_inputs


SUCCESS_CLASSIFICATION = "LIVE_REGISTRY_EMPTY_INITIALIZED_SUCCESSFULLY"
IDEMPOTENT_CLASSIFICATION = "IDEMPOTENT_PASS_EXISTING_IDENTICAL_EMPTY_LIVE_REGISTRY"
PLATFORM_HARDENING_STOP = "LIVE_REGISTRY_PLATFORM_HARDENING_REQUIRED_STOP"
APPROVAL_MISSING_STOP = "LIVE_REGISTRY_ROOT_INITIALIZATION_APPROVAL_MISSING_STOP"
INCOMPLETE_REVIEW_STOP = "LIVE_REGISTRY_ROOT_INITIALIZATION_INCOMPLETE_REVIEW_REQUIRED"
ENTRY_EXISTS_STOP = "LIVE_REGISTRY_ROOT_ALREADY_CONTAINS_ENTRY_STOP"
WRONG_POLICY_STOP = "LIVE_REGISTRY_WRONG_POLICY_STOP"
REPLAY_CONFLICT_STOP = "LIVE_REGISTRY_INITIALIZATION_AUTHORIZATION_REPLAY_CONFLICT_STOP"

LIVE_AUTHORIZATION_STATES = (
    "ISSUED_NOT_ACTIVATED",
    "ACTIVATED_NOT_CONSUMED",
    "CONSUMED_PENDING_HUMAN_LIVE_ENTRY_REVIEW",
    "CONSUMED_ACCEPTED_LIVE_ENTRY",
    "CONSUMED_REVIEW_REQUIRED",
)
LIVE_ENTRY_PREFLIGHT_SUCCESS = "LIVE_ENTRY_PRE_AUTHORITATIVE_RENAME_PREFLIGHT_VALIDATED_NO_WRITE"
LIVE_ENTRY_PREFLIGHT_APPROVAL_MISSING_STOP = "LIVE_ENTRY_PREFLIGHT_APPROVAL_MISSING_STOP"
LIVE_ENTRY_AUTHORIZATION_IDENTITY_COLLISION_STOP = "LIVE_ENTRY_AUTHORIZATION_IDENTITY_COLLISION_STOP"
LIVE_ENTRY_AUTHORIZATION_BINDING_MISMATCH_STOP = "LIVE_ENTRY_AUTHORIZATION_BINDING_MISMATCH_STOP"
LIVE_ENTRY_AUTHORIZATION_STATE_INVALID_STOP = "LIVE_ENTRY_AUTHORIZATION_STATE_INVALID_STOP"
LIVE_ENTRY_AUTHORIZATION_REUSE_STOP = "LIVE_ENTRY_AUTHORIZATION_REUSE_STOP"
LIVE_ENTRY_CANDIDATE_PROVENANCE_MISMATCH_STOP = "LIVE_ENTRY_CANDIDATE_PROVENANCE_MISMATCH_STOP"
LIVE_ENTRY_FORBIDDEN_CANDIDATE_SOURCE_STOP = "LIVE_ENTRY_FORBIDDEN_CANDIDATE_SOURCE_STOP"
LIVE_ENTRY_ROOT_MODE_OR_OVERLAP_STOP = "LIVE_ENTRY_ROOT_MODE_OR_OVERLAP_STOP"
LIVE_ENTRY_SUBJECT_OR_RECEIPT_MISMATCH_STOP = "LIVE_ENTRY_SUBJECT_OR_RECEIPT_MISMATCH_STOP"
NEW_LIVE_ENTRY_MATERIALIZED_PENDING_HUMAN_REVIEW = "NEW_LIVE_ENTRY_MATERIALIZED_PENDING_HUMAN_REVIEW"
IDEMPOTENT_PASS_EXISTING_IDENTICAL_LIVE_ENTRY_PENDING_HUMAN_REVIEW = (
    "IDEMPOTENT_PASS_EXISTING_IDENTICAL_LIVE_ENTRY_PENDING_HUMAN_REVIEW"
)
LIVE_ENTRY_AUTHORIZATION_REPLAY_CONFLICT_STOP = "LIVE_ENTRY_AUTHORIZATION_REPLAY_CONFLICT_STOP"
LIVE_ENTRY_RECEIPT_COLLISION_STOP = "LIVE_ENTRY_RECEIPT_COLLISION_STOP"

_EXPECTED_CHILDREN = {
    ".staging",
    "derived",
    "entries",
    "registry_initialization_seal.json",
    "registry_instance_manifest.json",
    "registry_policy.json",
    "registry_schema.json",
}
_REQUIRED_CAPABILITIES = (
    "windows_backend_available",
    "reparse_safe_handle_open",
    "volume_and_file_identity_queries",
    "hardlink_count_query",
    "file_handle_flush",
    "handle_relative_same_volume_rename",
    "verified_handle_lock_disposition",
)


def _absolute(path: str | Path) -> Path:
    return Path(os.path.abspath(os.fspath(Path(path))))


def _required_nfc(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or unicodedata.normalize("NFC", value) != value:
        raise RegistryError(APPROVAL_MISSING_STOP, f"{field} must be non-empty NFC-stable text")
    return value


def _preflight_nfc(value: object, field: str, *, classification: str) -> str:
    if not isinstance(value, str) or not value.strip() or unicodedata.normalize("NFC", value) != value:
        raise RegistryError(classification, f"{field} must be non-empty NFC-stable text")
    return value


def _preflight_sha256(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or value != value.lower()
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise RegistryError(LIVE_ENTRY_CANDIDATE_PROVENANCE_MISMATCH_STOP, f"{field} must be lowercase SHA-256")
    return value


def _is_within(path: Path, parent: Path, *, strict: bool = False) -> bool:
    try:
        common = Path(os.path.commonpath((os.fspath(path), os.fspath(parent))))
    except ValueError:
        return False
    same = os.path.normcase(os.fspath(common)) == os.path.normcase(os.fspath(parent))
    if strict:
        return same and os.path.normcase(os.fspath(path)) != os.path.normcase(os.fspath(parent))
    return same


def _validate_review_paths(
    review_output_root: str | Path,
    review_zip_path: str | Path,
    *,
    repository_root: Path,
    candidate_root: Path,
    live_root: Path,
) -> tuple[Path, Path]:
    output = _absolute(review_output_root)
    zip_path = _absolute(review_zip_path)
    if not zip_path.name.endswith(".zip") or zip_path.parent != output:
        raise RegistryError(APPROVAL_MISSING_STOP, "Review ZIP must be one direct ZIP child of review_output_root")
    for protected in (repository_root, candidate_root, live_root):
        if _is_within(output, protected) or _is_within(protected, output):
            raise RegistryError(APPROVAL_MISSING_STOP, "Review output must be disjoint from repository and registry roots")
    return output, zip_path


def _validate_candidate_policy(candidate: Path) -> dict[str, Any]:
    if not candidate.is_dir():
        raise RegistryError(WRONG_POLICY_STOP, "Candidate registry root must already exist as a directory")
    assert_no_filesystem_indirection(candidate, classification="LIVE_REGISTRY_REPARSE_OR_INDIRECTION_STOP")
    policy_path = candidate / "registry_policy.json"
    assert_regular_single_link_file(policy_path, classification=WRONG_POLICY_STOP)
    policy = decode_json_object(policy_path.read_bytes(), label="candidate_registry_policy")
    mode = policy.get("registry_mode")
    if mode == GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE:
        raise RegistryError(
            "LIVE_REGISTRY_CANDIDATE_POLICY_RECLASSIFICATION_STOP",
            "A live policy cannot be supplied as the candidate exclusion root",
        )
    if mode == SYNTHETIC_MODE:
        if policy.get("live_registry_allowed") is not False:
            raise RegistryError(WRONG_POLICY_STOP, "Synthetic candidate fixture unexpectedly allows live use")
    elif mode == GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE:
        if policy.get("candidate_registry") is not True or policy.get("live_registry") is not False:
            raise RegistryError(WRONG_POLICY_STOP, "Governed candidate policy fields are inconsistent")
    else:
        raise RegistryError(WRONG_POLICY_STOP, "Candidate exclusion root has an unsupported policy mode")
    return policy


def _validated_backend(backend: WindowsLiveFilesystemBackend | None) -> WindowsLiveFilesystemBackend:
    try:
        selected = backend or WindowsLiveFilesystemBackend()
        report = selected.capability_report()
    except RegistryError as exc:
        raise RegistryError(
            PLATFORM_HARDENING_STOP,
            "Required Windows platform hardening is unavailable",
            details={"underlying_classification": exc.classification},
        ) from exc
    missing = [field for field in _REQUIRED_CAPABILITIES if getattr(report, field, False) is not True]
    if missing or getattr(report, "risk_waiver_granted", False) is not False:
        raise RegistryError(
            PLATFORM_HARDENING_STOP,
            "Required Windows platform controls did not report verified PASS",
            details={"missing_or_unverified_controls": missing},
        )
    return selected


def _flush_directory(path: Path, backend: WindowsLiveFilesystemBackend) -> None:
    if flush_parent_directory_durable(path, backend=backend) is not True:
        raise RegistryError(DIRECTORY_DURABILITY_UNPROVEN_STOP, "Required directory durability was not observed")


def _write(path: Path, exact_bytes: bytes, backend: WindowsLiveFilesystemBackend) -> None:
    write_bytes_durable(path, exact_bytes, backend=backend)
    _flush_directory(path, backend)


def _documents(
    *,
    registry_instance_id: str,
    live_platform_acceptance_id: str,
    authorization_id: str,
    operator_alias: str,
    operation_id: str,
    initialized_at: str,
    review_output_root: Path,
    review_zip_path: Path,
) -> tuple[dict[str, bytes], dict[str, Any], str]:
    policy = GovernedLiveRegistryPolicy().to_dict()
    schema = RegistrySchema().to_dict()
    policy_bytes = canonical_json_bytes(policy)
    schema_bytes = canonical_json_bytes(schema)
    root_mode_identity = sha256_bytes(
        canonical_json_bytes(
            {
                "live_platform_acceptance_id": live_platform_acceptance_id,
                "live_root_initialization_authorization_id": authorization_id,
                "registry_instance_id": registry_instance_id,
                "registry_mode": GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE,
            }
        )
    )
    review_binding = sha256_bytes(
        canonical_json_bytes(
            {
                "review_output_name": review_output_root.name,
                "review_zip_name": review_zip_path.name,
            }
        )
    )
    instance = {
        "business_authority": "none",
        "candidate_registry": False,
        "evidence_acceptance_authority": "none",
        "initialized_at": initialized_at,
        "live_platform_acceptance_id": live_platform_acceptance_id,
        "live_registry": True,
        "live_registry_allowed": True,
        "live_root_initialization_authorization_id": authorization_id,
        "next_task_authorized_by_registry": False,
        "operation_id": operation_id,
        "operator_alias": operator_alias,
        "PIT_authority": "none",
        "registry_instance_id": registry_instance_id,
        "registry_instance_schema": "accepted-lineage-live-registry-instance-v0.1",
        "registry_mode": GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE,
        "replay_authority": "none",
        "research_authority": "none",
        "review_output_binding_sha256": review_binding,
        "root_mode_identity": root_mode_identity,
        "trading_authority": "none",
    }
    instance_bytes = canonical_json_bytes(instance)
    index_bytes = b""
    index_manifest = {
        "entry_count": 0,
        "index_filename": "registry_index.jsonl",
        "registry_index_sha256": sha256_bytes(index_bytes),
        "registry_policy_version": policy["registry_policy_version"],
        "registry_schema_version": schema["registry_schema_version"],
        "status": "DERIVED_NON_AUTHORITATIVE_EMPTY_LIVE_INDEX_VALID",
    }
    index_manifest_bytes = canonical_json_bytes(index_manifest)
    seal = {
        "initialized_at": initialized_at,
        "live_platform_acceptance_id": live_platform_acceptance_id,
        "live_root_initialization_authorization_id": authorization_id,
        "operation_id": operation_id,
        "registry_index_manifest_sha256": sha256_bytes(index_manifest_bytes),
        "registry_index_sha256": sha256_bytes(index_bytes),
        "registry_initialization_status": "EMPTY_LIVE_REGISTRY_INITIALIZATION_SEALED",
        "registry_instance_id": registry_instance_id,
        "registry_instance_manifest_sha256": sha256_bytes(instance_bytes),
        "registry_policy_sha256": sha256_bytes(policy_bytes),
        "registry_schema_sha256": sha256_bytes(schema_bytes),
        "root_mode_identity": root_mode_identity,
    }
    documents = {
        "registry_policy.json": policy_bytes,
        "registry_schema.json": schema_bytes,
        "registry_instance_manifest.json": instance_bytes,
        "derived/registry_index.jsonl": index_bytes,
        "derived/registry_index_manifest.json": index_manifest_bytes,
        "registry_initialization_seal.json": canonical_json_bytes(seal),
    }
    return documents, instance, root_mode_identity


def _health(registry_instance_id: str, root_mode_identity: str) -> dict[str, Any]:
    return {
        "authoritative_entry_count": 0,
        "business_authority": "none",
        "buy_review_authority": "none",
        "candidate_registry": False,
        "derived_index_status": "PASS",
        "entry_verification_status": "PASS_EMPTY",
        "evidence_acceptance_authority": "none",
        "live_platform_hardening_status": "PASS",
        "live_registry": True,
        "live_registry_allowed": True,
        "lock_status": "UNLOCKED",
        "next_task_authorized_by_registry": False,
        "orphan_temporary_directories": 0,
        "PIT_authority": "none",
        "registry_instance_id": registry_instance_id,
        "replay_authority": "none",
        "research_authority": "none",
        "root_mode_binding_status": "PASS",
        "root_mode_identity": root_mode_identity,
        "trading_authority": "none",
    }


def _result(
    classification: str,
    *,
    registry_instance_id: str,
    root_mode_identity: str,
    documents: dict[str, bytes],
) -> dict[str, Any]:
    return {
        "classification": classification,
        "health": _health(registry_instance_id, root_mode_identity),
        "initialization_seal_sha256": sha256_bytes(documents["registry_initialization_seal.json"]),
        "live_entry_materialized": False,
        "materialization_authorized": False,
        "next_task_authorized_by_registry": False,
        "registry_instance_id": registry_instance_id,
        "review_packaging_deferred": True,
        "root_mode_identity": root_mode_identity,
    }


def _existing_result(
    root: Path,
    *,
    expected_root: Path,
    candidate_root: Path,
    approved_admin_root: Path,
    repository_root: Path,
    authorization_id: str,
    registry_instance_id: str,
    documents: dict[str, bytes],
    root_mode_identity: str,
) -> dict[str, Any]:
    try:
        validate_live_registry_root_authority(
            root,
            approved_admin_root=approved_admin_root,
            repository_root=repository_root,
            expected_registry_root=expected_root,
            candidate_root=candidate_root,
            expected_existing_state="INITIALIZED_LIVE",
        )
    except RegistryError as exc:
        if exc.classification == "LIVE_REGISTRY_UNEXPECTED_EXISTING_ROOT_STOP":
            raise RegistryError(INCOMPLETE_REVIEW_STOP, "Existing live root is only partially initialized") from exc
        raise
    entries = root / "entries"
    if entries.is_dir() and any(entries.iterdir()):
        raise RegistryError(ENTRY_EXISTS_STOP, "An empty-root replay cannot target a root containing entries")
    child_names = {item.name for item in root.iterdir()}
    if child_names != _EXPECTED_CHILDREN or not entries.is_dir():
        raise RegistryError(INCOMPLETE_REVIEW_STOP, "Existing live root structure is incomplete or unexpected")
    try:
        instance = decode_json_object((root / "registry_instance_manifest.json").read_bytes(), label="registry_instance_manifest")
    except (OSError, ValueError) as exc:
        raise RegistryError(INCOMPLETE_REVIEW_STOP, "Registry instance manifest is unreadable") from exc
    if instance.get("live_root_initialization_authorization_id") != authorization_id:
        raise RegistryError(REPLAY_CONFLICT_STOP, "Existing empty root used a different initialization authorization")
    if instance.get("registry_instance_id") != registry_instance_id:
        raise RegistryError(WRONG_POLICY_STOP, "Existing empty root uses a different registry instance")
    for relative, expected in documents.items():
        path = root / relative
        if not path.is_file():
            raise RegistryError(INCOMPLETE_REVIEW_STOP, f"Existing empty root is missing {relative}")
        observed = path.read_bytes()
        if observed != expected:
            classification = WRONG_POLICY_STOP if relative in {
                "registry_policy.json",
                "registry_schema.json",
                "registry_instance_manifest.json",
            } else INCOMPLETE_REVIEW_STOP
            raise RegistryError(classification, f"Existing empty root differs at {relative}")
    return _result(
        IDEMPOTENT_CLASSIFICATION,
        registry_instance_id=registry_instance_id,
        root_mode_identity=root_mode_identity,
        documents=documents,
    )


def _remove_exact_empty_root(root: Path, backend: WindowsLiveFilesystemBackend, identity: object) -> bool:
    try:
        observed = backend.verify_committed_directory_identity(root, identity)
        if observed != identity or any(root.iterdir()):
            return False
        root.rmdir()
        return True
    except Exception:
        return False


def preflight_live_accepted_lineage_materialization(
    root: str | Path,
    *,
    expected_live_registry_root: str | Path,
    candidate_registry_root: str | Path,
    expected_candidate_registry_root: str | Path,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    live_registry_mode: str,
    candidate_registry_mode: str,
    registry_instance_id: str,
    expected_registry_instance_id: str,
    logical_subject_identity: str,
    expected_logical_subject_identity: str,
    review_decision_id: str,
    receipt_id: str,
    expected_receipt_id: str,
    candidate_materialization_authorization_id: str,
    live_platform_acceptance_id: str,
    live_root_initialization_authorization_id: str,
    live_materialization_authorization_id: str,
    expected_live_materialization_authorization_id: str,
    live_entry_review_decision_id: str,
    next_task_approval_id: str,
    authorization_state: str,
    execution_approval_id: str | None,
    human_review_payload: HumanReviewPayload,
    subject_artifact_manifest: SubjectArtifactManifest,
    subject_packet_path: str | Path,
    subject_artifact_root: str | Path,
    review_receipt: bytes,
    expected_reviewer_input_hashes: Mapping[str, Any],
    accepted_candidate_entry_seal_sha256: str,
    candidate_entry_seal_sha256: str,
    accepted_pilot_review_zip_sha256: str,
    pilot_review_zip_sha256: str,
    candidate_source_intent: str = "provenance_hashes_only",
    candidate_entry_bytes: bytes | None = None,
    consumed_live_materialization_authorization_ids: Sequence[str] = (),
    prior_live_materialization_authorization_bindings: Mapping[str, Mapping[str, str]] | None = None,
    existing_live_entry_replay: bool = False,
) -> dict[str, Any]:
    """Validate a prospective live materialization and stop before any write."""

    if execution_approval_id is None:
        raise RegistryError(LIVE_ENTRY_PREFLIGHT_APPROVAL_MISSING_STOP, "Explicit execution approval is required")
    _preflight_nfc(
        execution_approval_id,
        "execution_approval_id",
        classification=LIVE_ENTRY_PREFLIGHT_APPROVAL_MISSING_STOP,
    )

    identity_values = {
        "review_decision_id": review_decision_id,
        "receipt_id": receipt_id,
        "candidate_materialization_authorization_id": candidate_materialization_authorization_id,
        "live_platform_acceptance_id": live_platform_acceptance_id,
        "live_root_initialization_authorization_id": live_root_initialization_authorization_id,
        "live_materialization_authorization_id": live_materialization_authorization_id,
        "live_entry_review_decision_id": live_entry_review_decision_id,
        "next_task_approval_id": next_task_approval_id,
    }
    normalized_identities = {
        field: _preflight_nfc(
            value,
            field,
            classification=LIVE_ENTRY_AUTHORIZATION_IDENTITY_COLLISION_STOP,
        )
        for field, value in identity_values.items()
    }
    materialization_authorization = normalized_identities["live_materialization_authorization_id"]
    if materialization_authorization in {
        normalized_identities["candidate_materialization_authorization_id"],
        normalized_identities["live_root_initialization_authorization_id"],
    }:
        raise RegistryError(LIVE_ENTRY_AUTHORIZATION_REUSE_STOP, "Candidate or initialization authority cannot materialize live state")
    authorization_is_consumed = materialization_authorization in set(consumed_live_materialization_authorization_ids)
    if authorization_is_consumed and not existing_live_entry_replay:
        raise RegistryError(LIVE_ENTRY_AUTHORIZATION_REUSE_STOP, "Consumed live materialization authorization cannot be reused")
    prior_bindings = dict(prior_live_materialization_authorization_bindings or {})
    if materialization_authorization in prior_bindings and not existing_live_entry_replay:
        raise RegistryError(LIVE_ENTRY_AUTHORIZATION_REUSE_STOP, "Live materialization authorization already has a receipt or root binding")
    if len(set(normalized_identities.values())) != len(normalized_identities):
        raise RegistryError(LIVE_ENTRY_AUTHORIZATION_IDENTITY_COLLISION_STOP, "Authorization identities must be pairwise distinct")

    replay_state_valid = existing_live_entry_replay and authorization_state in {
        "ISSUED_NOT_ACTIVATED",
        "CONSUMED_PENDING_HUMAN_LIVE_ENTRY_REVIEW",
    }
    if authorization_state not in LIVE_AUTHORIZATION_STATES or (
        authorization_state != "ISSUED_NOT_ACTIVATED" and not replay_state_valid
    ):
        raise RegistryError(LIVE_ENTRY_AUTHORIZATION_STATE_INVALID_STOP, "Preflight requires one issued, unactivated authorization")
    if existing_live_entry_replay and authorization_state.startswith("CONSUMED_") and not authorization_is_consumed:
        raise RegistryError(LIVE_ENTRY_AUTHORIZATION_REUSE_STOP, "Consumed replay authorization lacks consumed-state evidence")
    if live_registry_mode != GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE:
        raise RegistryError(LIVE_ENTRY_ROOT_MODE_OR_OVERLAP_STOP, "Prospective live mode must be explicit")
    if candidate_registry_mode not in {GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE, SYNTHETIC_MODE}:
        raise RegistryError(LIVE_ENTRY_ROOT_MODE_OR_OVERLAP_STOP, "Candidate mode must be explicit and non-live")

    try:
        candidate, live = validate_candidate_live_root_separation(
            candidate_registry_root,
            root,
            approved_admin_root=approved_admin_root,
            repository_root=repository_root,
        )
    except RegistryError as exc:
        raise RegistryError(
            LIVE_ENTRY_ROOT_MODE_OR_OVERLAP_STOP,
            "Prospective live and candidate roots are not safely separated",
            details={"underlying_classification": exc.classification},
        ) from exc
    expected_live = _absolute(expected_live_registry_root)
    expected_candidate = _absolute(expected_candidate_registry_root)
    if os.path.normcase(os.fspath(live)) != os.path.normcase(os.fspath(expected_live)):
        raise RegistryError(LIVE_ENTRY_AUTHORIZATION_BINDING_MISMATCH_STOP, "Live root differs from exact authorization binding")
    if os.path.normcase(os.fspath(candidate)) != os.path.normcase(os.fspath(expected_candidate)):
        raise RegistryError(LIVE_ENTRY_AUTHORIZATION_BINDING_MISMATCH_STOP, "Candidate root differs from exact authorization binding")

    instance_id = _preflight_nfc(
        registry_instance_id,
        "registry_instance_id",
        classification=LIVE_ENTRY_AUTHORIZATION_BINDING_MISMATCH_STOP,
    )
    expected_instance_id = _preflight_nfc(
        expected_registry_instance_id,
        "expected_registry_instance_id",
        classification=LIVE_ENTRY_AUTHORIZATION_BINDING_MISMATCH_STOP,
    )
    expected_authorization = _preflight_nfc(
        expected_live_materialization_authorization_id,
        "expected_live_materialization_authorization_id",
        classification=LIVE_ENTRY_AUTHORIZATION_BINDING_MISMATCH_STOP,
    )
    if instance_id != expected_instance_id or materialization_authorization != expected_authorization:
        raise RegistryError(LIVE_ENTRY_AUTHORIZATION_BINDING_MISMATCH_STOP, "Instance or authorization binding mismatch")

    subject_identity = _preflight_nfc(
        logical_subject_identity,
        "logical_subject_identity",
        classification=LIVE_ENTRY_SUBJECT_OR_RECEIPT_MISMATCH_STOP,
    )
    expected_subject_identity = _preflight_nfc(
        expected_logical_subject_identity,
        "expected_logical_subject_identity",
        classification=LIVE_ENTRY_SUBJECT_OR_RECEIPT_MISMATCH_STOP,
    )
    expected_receipt = _preflight_nfc(
        expected_receipt_id,
        "expected_receipt_id",
        classification=LIVE_ENTRY_SUBJECT_OR_RECEIPT_MISMATCH_STOP,
    )
    if subject_identity != expected_subject_identity or normalized_identities["receipt_id"] != expected_receipt:
        raise RegistryError(LIVE_ENTRY_SUBJECT_OR_RECEIPT_MISMATCH_STOP, "Subject or receipt binding mismatch")

    if candidate_entry_bytes is not None or candidate_source_intent != "provenance_hashes_only":
        raise RegistryError(
            LIVE_ENTRY_FORBIDDEN_CANDIDATE_SOURCE_STOP,
            "Candidate entry bytes, copy, import, rename, or promotion cannot be a live write source",
        )
    accepted_entry_seal = _preflight_sha256(
        accepted_candidate_entry_seal_sha256,
        "accepted_candidate_entry_seal_sha256",
    )
    candidate_entry_seal = _preflight_sha256(candidate_entry_seal_sha256, "candidate_entry_seal_sha256")
    accepted_pilot_zip = _preflight_sha256(
        accepted_pilot_review_zip_sha256,
        "accepted_pilot_review_zip_sha256",
    )
    pilot_zip = _preflight_sha256(pilot_review_zip_sha256, "pilot_review_zip_sha256")
    if accepted_entry_seal != candidate_entry_seal or accepted_pilot_zip != pilot_zip:
        raise RegistryError(
            LIVE_ENTRY_CANDIDATE_PROVENANCE_MISMATCH_STOP,
            "Candidate provenance hashes differ from accepted review evidence",
        )

    immutable_inputs = validate_live_preflight_immutable_inputs(
        payload=human_review_payload,
        manifest=subject_artifact_manifest,
        review_receipt=review_receipt,
        subject_packet_path=subject_packet_path,
        subject_artifact_root=subject_artifact_root,
        expected_reviewer_input_hashes=expected_reviewer_input_hashes,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        registry_root=live,
        protected_roots=(candidate,),
    )

    return {
        "PIT_authority": "none",
        "authorization_consumed": authorization_state.startswith("CONSUMED_"),
        "authorization_state_after": (
            authorization_state if existing_live_entry_replay else "ACTIVATED_NOT_CONSUMED"
        ),
        "authorization_state_before": authorization_state,
        "authorization_state_persisted": False,
        "authoritative_write_performed": False,
        "business_authority": "none",
        "buy_review_authority": "none",
        "candidate_provenance_verified": True,
        "candidate_registry": False,
        "classification": LIVE_ENTRY_PREFLIGHT_SUCCESS,
        "evidence_acceptance_authority": "none",
        "immutable_input_verification": immutable_inputs.safe_report(),
        "live_entry_materialized": False,
        "live_registry": True,
        "next_task_authorized_by_registry": False,
        "replay_authority": "none",
        "research_authority": "none",
        "staging_created": False,
        "terminal_boundary": "STOP_BEFORE_AUTHORITATIVE_STAGED_ENTRY_CREATION_OR_RENAME",
        "trading_authority": "none",
    }


def materialize_live_accepted_lineage_entry(
    root: str | Path,
    *,
    expected_live_registry_root: str | Path,
    candidate_registry_root: str | Path,
    expected_candidate_registry_root: str | Path,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    live_registry_mode: str,
    candidate_registry_mode: str,
    registry_instance_id: str,
    expected_registry_instance_id: str,
    logical_subject_identity: str,
    expected_logical_subject_identity: str,
    review_decision_id: str,
    receipt_id: str,
    expected_receipt_id: str,
    candidate_materialization_authorization_id: str,
    live_platform_acceptance_id: str,
    live_root_initialization_authorization_id: str,
    live_materialization_authorization_id: str,
    expected_live_materialization_authorization_id: str,
    live_entry_review_decision_id: str,
    next_task_approval_id: str,
    authorization_state: str,
    execution_approval_id: str | None,
    human_review_payload: HumanReviewPayload,
    subject_artifact_manifest: SubjectArtifactManifest,
    subject_packet_path: str | Path,
    subject_artifact_root: str | Path,
    review_receipt: bytes,
    expected_reviewer_input_hashes: Mapping[str, Any],
    accepted_candidate_entry_seal_sha256: str,
    candidate_entry_seal_sha256: str,
    accepted_pilot_review_zip_sha256: str,
    pilot_review_zip_sha256: str,
    operator_alias: str,
    operation_id: str,
    materialized_at: str,
    backend: WindowsLiveFilesystemBackend | None = None,
    candidate_source_intent: str = "provenance_hashes_only",
    candidate_entry_bytes: bytes | None = None,
    consumed_live_materialization_authorization_ids: Sequence[str] = (),
    prior_live_materialization_authorization_bindings: Mapping[str, Mapping[str, str]] | None = None,
    failure_injection: str | None = None,
) -> dict[str, Any]:
    """Run full preflight, then materialize one synthetic-test live entry."""

    from .transaction import materialize_live_entry_transaction

    selected_backend = _validated_backend(backend)
    existing_replay = authorization_state == "CONSUMED_PENDING_HUMAN_LIVE_ENTRY_REVIEW"
    preflight = preflight_live_accepted_lineage_materialization(
        root,
        expected_live_registry_root=expected_live_registry_root,
        candidate_registry_root=candidate_registry_root,
        expected_candidate_registry_root=expected_candidate_registry_root,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        live_registry_mode=live_registry_mode,
        candidate_registry_mode=candidate_registry_mode,
        registry_instance_id=registry_instance_id,
        expected_registry_instance_id=expected_registry_instance_id,
        logical_subject_identity=logical_subject_identity,
        expected_logical_subject_identity=expected_logical_subject_identity,
        review_decision_id=review_decision_id,
        receipt_id=receipt_id,
        expected_receipt_id=expected_receipt_id,
        candidate_materialization_authorization_id=candidate_materialization_authorization_id,
        live_platform_acceptance_id=live_platform_acceptance_id,
        live_root_initialization_authorization_id=live_root_initialization_authorization_id,
        live_materialization_authorization_id=live_materialization_authorization_id,
        expected_live_materialization_authorization_id=expected_live_materialization_authorization_id,
        live_entry_review_decision_id=live_entry_review_decision_id,
        next_task_approval_id=next_task_approval_id,
        authorization_state=authorization_state,
        execution_approval_id=execution_approval_id,
        human_review_payload=human_review_payload,
        subject_artifact_manifest=subject_artifact_manifest,
        subject_packet_path=subject_packet_path,
        subject_artifact_root=subject_artifact_root,
        review_receipt=review_receipt,
        expected_reviewer_input_hashes=expected_reviewer_input_hashes,
        accepted_candidate_entry_seal_sha256=accepted_candidate_entry_seal_sha256,
        candidate_entry_seal_sha256=candidate_entry_seal_sha256,
        accepted_pilot_review_zip_sha256=accepted_pilot_review_zip_sha256,
        pilot_review_zip_sha256=pilot_review_zip_sha256,
        candidate_source_intent=candidate_source_intent,
        candidate_entry_bytes=candidate_entry_bytes,
        consumed_live_materialization_authorization_ids=consumed_live_materialization_authorization_ids,
        prior_live_materialization_authorization_bindings=prior_live_materialization_authorization_bindings,
        existing_live_entry_replay=existing_replay,
    )
    operator = _preflight_nfc(operator_alias, "operator_alias", classification=LIVE_ENTRY_PREFLIGHT_APPROVAL_MISSING_STOP)
    operation = _preflight_nfc(operation_id, "operation_id", classification=LIVE_ENTRY_PREFLIGHT_APPROVAL_MISSING_STOP)
    timestamp = _preflight_nfc(materialized_at, "materialized_at", classification=LIVE_ENTRY_PREFLIGHT_APPROVAL_MISSING_STOP)
    result = materialize_live_entry_transaction(
        root,
        expected_live_registry_root=expected_live_registry_root,
        candidate_registry_root=candidate_registry_root,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        registry_instance_id=registry_instance_id,
        logical_subject_identity=logical_subject_identity,
        receipt_id=receipt_id,
        human_review_payload=human_review_payload,
        subject_artifact_manifest=subject_artifact_manifest,
        review_receipt=review_receipt,
        live_materialization_authorization_id=live_materialization_authorization_id,
        accepted_candidate_entry_seal_sha256=accepted_candidate_entry_seal_sha256,
        accepted_pilot_review_zip_sha256=accepted_pilot_review_zip_sha256,
        immutable_input_verification=preflight["immutable_input_verification"],
        existing_live_entry_replay=existing_replay,
        operator_alias=operator,
        operation_id=operation,
        materialized_at=timestamp,
        backend=selected_backend,
        failure_injection=failure_injection,
    )
    result["preflight_classification"] = preflight["classification"]
    return result


def recover_live_accepted_lineage_index(
    root: str | Path,
    *,
    expected_live_registry_root: str | Path,
    candidate_registry_root: str | Path,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    registry_instance_id: str,
    recovery_approval_id: str,
    operator_alias: str,
    operation_id: str,
    backend: WindowsLiveFilesystemBackend | None = None,
    failure_injection: str | None = None,
) -> dict[str, Any]:
    """Recover derived live index state without rematerializing an entry."""

    from .transaction import recover_live_index_transaction

    selected_backend = _validated_backend(backend)
    approval = _preflight_nfc(
        recovery_approval_id,
        "recovery_approval_id",
        classification=LIVE_ENTRY_PREFLIGHT_APPROVAL_MISSING_STOP,
    )
    return recover_live_index_transaction(
        root,
        expected_live_registry_root=expected_live_registry_root,
        candidate_registry_root=candidate_registry_root,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        registry_instance_id=registry_instance_id,
        recovery_approval_id=approval,
        operator_alias=operator_alias,
        operation_id=operation_id,
        backend=selected_backend,
        failure_injection=failure_injection,
    )


def initialize_governed_live_registry(
    root: str | Path,
    *,
    expected_live_registry_root: str | Path,
    candidate_registry_root: str | Path,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    live_platform_acceptance_id: str,
    live_root_initialization_authorization_id: str,
    expected_live_root_initialization_authorization_id: str,
    registry_instance_id: str,
    operator_alias: str,
    operation_id: str,
    initialized_at: str,
    review_output_root: str | Path,
    review_zip_path: str | Path,
    backend: WindowsLiveFilesystemBackend | None = None,
) -> dict[str, Any]:
    """Initialize one empty live registry while granting no entry authority."""

    acceptance_id = _required_nfc(live_platform_acceptance_id, "live_platform_acceptance_id")
    authorization_id = _required_nfc(
        live_root_initialization_authorization_id,
        "live_root_initialization_authorization_id",
    )
    expected_authorization_id = _required_nfc(
        expected_live_root_initialization_authorization_id,
        "expected_live_root_initialization_authorization_id",
    )
    instance_id = _required_nfc(registry_instance_id, "registry_instance_id")
    operator = _required_nfc(operator_alias, "operator_alias")
    operation = _required_nfc(operation_id, "operation_id")
    initialized = _required_nfc(initialized_at, "initialized_at")
    if authorization_id != expected_authorization_id:
        raise RegistryError(APPROVAL_MISSING_STOP, "Initialization authorization does not match exact approval")
    if authorization_id in {acceptance_id, instance_id, operator, operation}:
        raise RegistryError(APPROVAL_MISSING_STOP, "Initialization authorization is not authority-distinct")

    live = _absolute(root)
    expected_live = _absolute(expected_live_registry_root)
    candidate = _absolute(candidate_registry_root)
    admin = _absolute(approved_admin_root)
    repository = _absolute(repository_root)
    validate_candidate_live_root_separation(
        candidate,
        live,
        approved_admin_root=admin,
        repository_root=repository,
    )
    if os.path.normcase(os.fspath(live)) != os.path.normcase(os.fspath(expected_live)):
        raise RegistryError("LIVE_REGISTRY_EXACT_ROOT_MISMATCH_STOP", "Live root differs from exact approved root")
    _validate_candidate_policy(candidate)
    review_output, review_zip = _validate_review_paths(
        review_output_root,
        review_zip_path,
        repository_root=repository,
        candidate_root=candidate,
        live_root=live,
    )
    selected_backend = _validated_backend(backend)
    documents, _, root_mode_identity = _documents(
        registry_instance_id=instance_id,
        live_platform_acceptance_id=acceptance_id,
        authorization_id=authorization_id,
        operator_alias=operator,
        operation_id=operation,
        initialized_at=initialized,
        review_output_root=review_output,
        review_zip_path=review_zip,
    )
    if os.path.lexists(live):
        return _existing_result(
            live,
            expected_root=expected_live,
            candidate_root=candidate,
            approved_admin_root=admin,
            repository_root=repository,
            authorization_id=authorization_id,
            registry_instance_id=instance_id,
            documents=documents,
            root_mode_identity=root_mode_identity,
        )

    validate_live_registry_root_authority(
        live,
        approved_admin_root=admin,
        repository_root=repository,
        expected_registry_root=expected_live,
        candidate_root=candidate,
        expected_existing_state="ABSENT",
    )
    root_created = False
    root_identity: object | None = None
    structure_created = False
    try:
        live.mkdir()
        root_created = True
        with selected_backend.open_directory_no_reparse(live) as handle:
            root_identity = selected_backend.query_handle_identity(handle)
            selected_backend.query_link_count(handle)
        with selected_backend.open_directory_no_reparse(candidate) as handle:
            candidate_identity = selected_backend.query_handle_identity(handle)
            selected_backend.query_link_count(handle)
        if candidate_identity == root_identity:
            raise RegistryError("LIVE_REGISTRY_CANDIDATE_ROOT_OVERLAP_STOP", "Candidate and live handle identities overlap")
        for name in ("entries", "derived", ".staging"):
            (live / name).mkdir()
        structure_created = True
        _flush_directory(live, selected_backend)
        for relative in (
            "registry_policy.json",
            "registry_schema.json",
            "registry_instance_manifest.json",
            "derived/registry_index.jsonl",
            "derived/registry_index_manifest.json",
            "registry_initialization_seal.json",
        ):
            _write(live / relative, documents[relative], selected_backend)
        selected_backend.verify_committed_directory_identity(live, root_identity)
        if any((live / "entries").iterdir()):
            raise RegistryError(ENTRY_EXISTS_STOP, "Fresh empty live root unexpectedly contains an entry")
        return _result(
            SUCCESS_CLASSIFICATION,
            registry_instance_id=instance_id,
            root_mode_identity=root_mode_identity,
            documents=documents,
        )
    except Exception as exc:
        if root_created and not structure_created and root_identity is not None:
            _remove_exact_empty_root(live, selected_backend, root_identity)
        if structure_created:
            underlying = exc.classification if isinstance(exc, RegistryError) else type(exc).__name__
            raise RegistryError(
                INCOMPLETE_REVIEW_STOP,
                "Empty live-root initialization is incomplete and retained for review",
                details={"underlying_classification": underlying},
            ) from exc
        raise
