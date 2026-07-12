"""Authoritative entry and predecessor-lineage verification."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from .canonical import decode_json_object, sha256_file
from .models import (
    REGISTRY_POLICY_VERSION,
    REGISTRY_SCHEMA_VERSION,
    SYNTHETIC_MODE,
    HumanReviewPayload,
    LineagePreflightResult,
    RegistryError,
    ReviewReceiptReference,
    SubjectArtifactManifest,
)
from .path_safety import (
    assert_regular_single_link_file,
    derive_receipt_key,
    derive_subject_key,
    ensure_descendant,
    validate_receipt_key,
    validate_registry_root_authority,
    validate_safe_directory_chain,
    validate_subject_key,
)
from .subject_verification import revalidate_subject_inputs, validate_subject_inputs


ENTRY_FILES = (
    "human_review_payload.json",
    "subject_artifact_manifest.json",
    "review_receipt.md",
    "entry_manifest.json",
    "entry_seal.json",
)


def _authority_kwargs(
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path],
    expected_registry_root: str | Path | None,
) -> dict[str, Any]:
    return {
        "approved_admin_root": approved_admin_root,
        "repository_root": repository_root,
        "protected_roots": protected_roots,
        "expected_registry_root": expected_registry_root,
    }


def load_registry_configuration(
    root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expected_registry_root: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    authority = _authority_kwargs(
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        protected_roots=protected_roots,
        expected_registry_root=expected_registry_root,
    )
    registry_root = validate_registry_root_authority(root, create=False, **authority)
    validate_safe_directory_chain(registry_root, containment_root=approved_admin_root, create=False)
    policy_path = registry_root / "registry_policy.json"
    schema_path = registry_root / "registry_schema.json"
    for path in (policy_path, schema_path):
        assert_regular_single_link_file(path, classification="REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP")
    policy = decode_json_object(policy_path.read_bytes(), label="registry_policy")
    schema = decode_json_object(schema_path.read_bytes(), label="registry_schema")
    if policy.get("registry_policy_version") != REGISTRY_POLICY_VERSION:
        raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "Registry policy version mismatch")
    if schema.get("registry_schema_version") != REGISTRY_SCHEMA_VERSION:
        raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "Registry schema version mismatch")
    if policy.get("registry_mode") != SYNTHETIC_MODE or policy.get("live_registry_allowed") is not False:
        raise RegistryError("LIVE_REGISTRY_MODE_NOT_AUTHORIZED_STOP", "Registry is not synthetic-only")
    if schema.get("entry_files") != list(ENTRY_FILES) or schema.get("entry_file_count") != len(ENTRY_FILES):
        raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "Five-file schema mismatch")
    return policy, schema


def entry_path(root: str | Path, subject_key: str, receipt_key: str) -> Path:
    validate_subject_key(subject_key)
    validate_receipt_key(receipt_key)
    registry_root = Path(root).absolute()
    return ensure_descendant(registry_root / "entries" / subject_key / receipt_key, registry_root, strict=True)


def verify_entry(
    root: str | Path,
    subject_key: str,
    receipt_key: str,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expected_registry_root: str | Path | None = None,
    subject_packet_path: str | Path | None = None,
    subject_artifact_root: str | Path | None = None,
) -> dict[str, Any]:
    authority = _authority_kwargs(
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        protected_roots=protected_roots,
        expected_registry_root=expected_registry_root,
    )
    registry_root = validate_registry_root_authority(root, create=False, **authority)
    policy, schema = load_registry_configuration(registry_root, **authority)
    target = entry_path(registry_root, subject_key, receipt_key)
    if not target.is_dir():
        raise RegistryError("REGISTRY_ENTRY_NOT_FOUND_STOP", "Registry entry does not exist")
    validate_safe_directory_chain(target, containment_root=registry_root, create=False)
    children = list(target.iterdir())
    if sorted(child.name for child in children) != sorted(ENTRY_FILES):
        raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "Entry file set is not exactly five files")
    for child in children:
        assert_regular_single_link_file(child)

    payload = HumanReviewPayload.from_bytes((target / "human_review_payload.json").read_bytes())
    subject_manifest = SubjectArtifactManifest.from_bytes((target / "subject_artifact_manifest.json").read_bytes())
    receipt = ReviewReceiptReference.from_bytes(
        (target / "review_receipt.md").read_bytes(),
        receipt_id=payload.receipt_id,
        subject_phase_id=payload.subject_phase_id,
    )
    expected_subject_key = derive_subject_key(payload.subject_phase_id)
    expected_receipt_key = derive_receipt_key(payload.receipt_id)
    if (
        subject_key != expected_subject_key
        or target.parent.name != expected_subject_key
        or receipt_key != expected_receipt_key
        or target.name != expected_receipt_key
    ):
        raise RegistryError(
            "LOGICAL_ID_OPAQUE_KEY_BINDING_MISMATCH_STOP",
            "Opaque entry keys are not derived from reviewer-authored logical identifiers",
        )
    if subject_manifest.data["subject_phase_id"] != payload.subject_phase_id:
        raise RegistryError("SUBJECT_ARTIFACT_MANIFEST_MISMATCH_STOP", "Subject phase differs across payload and manifest")
    if subject_manifest.exact_sha256 != payload.data["subject_artifact_manifest_sha256"]:
        raise RegistryError("SUBJECT_ARTIFACT_MANIFEST_MISMATCH_STOP", "Reviewer payload names a different manifest hash")
    if subject_manifest.data["subject_packet_sha256"] != payload.data["subject_packet_sha256"]:
        raise RegistryError("SUBJECT_PACKET_HASH_MISMATCH_STOP", "Subject packet hash differs across payload and manifest")

    actual_subject = None
    if subject_packet_path is not None or subject_artifact_root is not None:
        actual_subject = validate_subject_inputs(
            payload=payload,
            manifest=subject_manifest,
            subject_packet_path=subject_packet_path,
            subject_artifact_root=subject_artifact_root,
            approved_admin_root=approved_admin_root,
            repository_root=repository_root,
            registry_root=registry_root,
            protected_roots=protected_roots,
        )
        revalidate_subject_inputs(
            actual_subject,
            payload=payload,
            manifest=subject_manifest,
            subject_packet_path=subject_packet_path,
            subject_artifact_root=subject_artifact_root,
            approved_admin_root=approved_admin_root,
            repository_root=repository_root,
            registry_root=registry_root,
            protected_roots=protected_roots,
        )

    manifest_bytes = (target / "entry_manifest.json").read_bytes()
    runtime_manifest = decode_json_object(manifest_bytes, label="entry_manifest")
    forbidden_manifest_fields = {
        "entry_manifest_sha256",
        "entry_seal_sha256",
        "review_decision_id",
        "reviewed_at",
        "accepted_classification",
        "accepted_verdict",
    }
    if forbidden_manifest_fields.intersection(runtime_manifest):
        raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "Runtime manifest contains forbidden fields")
    if (
        runtime_manifest.get("subject_key") != expected_subject_key
        or runtime_manifest.get("receipt_key") != expected_receipt_key
    ):
        raise RegistryError(
            "LOGICAL_ID_OPAQUE_KEY_BINDING_MISMATCH_STOP",
            "Runtime manifest opaque keys are not bound to reviewer-authored logical identifiers",
        )
    expected_manifest_values = {
        "registry_schema_version": schema["registry_schema_version"],
        "registry_policy_version": policy["registry_policy_version"],
        "human_review_payload_sha256": payload.exact_sha256,
        "subject_artifact_manifest_sha256": subject_manifest.exact_sha256,
        "review_receipt_sha256": receipt.exact_sha256,
        "entry_file_count": 5,
        "subject_artifact_count": subject_manifest.data["artifact_count"],
        "actual_subject_bytes_verified": True,
    }
    for field, expected in expected_manifest_values.items():
        if runtime_manifest.get(field) != expected:
            raise RegistryError("HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP", f"Runtime manifest mismatch: {field}")
    if actual_subject is not None and runtime_manifest.get("subject_packet_byte_length") != actual_subject.packet.byte_length:
        raise RegistryError("SUBJECT_PACKET_HASH_MISMATCH_STOP", "Runtime packet byte length differs from actual packet")

    seal_bytes = (target / "entry_seal.json").read_bytes()
    seal = decode_json_object(seal_bytes, label="entry_seal")
    if "entry_seal_sha256" in seal or "own_sha256" in seal:
        raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "Entry seal contains a self hash")
    if seal.get("entry_manifest_sha256") != sha256_file(target / "entry_manifest.json"):
        raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "Entry seal manifest hash mismatch")
    if seal.get("subject_key") != expected_subject_key or seal.get("receipt_key") != expected_receipt_key:
        raise RegistryError(
            "LOGICAL_ID_OPAQUE_KEY_BINDING_MISMATCH_STOP",
            "Entry seal opaque keys are not bound to reviewer-authored logical identifiers",
        )

    result = {
        "status": "PASS",
        "subject_key": subject_key,
        "receipt_key": receipt_key,
        "subject_phase_id": payload.subject_phase_id,
        "receipt_id": payload.receipt_id,
        "review_status": payload.data["review_status"],
        "accepted_classification": payload.data["accepted_classification"],
        "human_review_payload_sha256": payload.exact_sha256,
        "subject_artifact_manifest_sha256": subject_manifest.exact_sha256,
        "review_receipt_sha256": receipt.exact_sha256,
        "entry_manifest_sha256": sha256_file(target / "entry_manifest.json"),
        "entry_seal_sha256": sha256_file(target / "entry_seal.json"),
        "registry_schema_version": schema["registry_schema_version"],
        "registry_policy_version": policy["registry_policy_version"],
        "materialized_at": runtime_manifest.get("materialized_at"),
        "materialized_by": runtime_manifest.get("materialized_by"),
        "materialization_authorization_id": runtime_manifest.get("materialization_authorization_id"),
        "actual_subject_bytes_verified": actual_subject is not None,
    }
    if actual_subject is not None:
        result["subject_packet_byte_length"] = actual_subject.packet.byte_length
        result["subject_artifact_count"] = len(actual_subject.artifacts)
    return result


def preflight_next_task(
    root: str | Path,
    subject_key: str,
    receipt_key: str,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expected_registry_root: str | Path | None = None,
    current_task_approval_id: str | None,
) -> LineagePreflightResult:
    if not current_task_approval_id or not current_task_approval_id.strip():
        raise RegistryError(
            "NEXT_TASK_EXACT_APPROVAL_MISSING_STOP",
            "A current exact task approval is required; predecessor state is not authority",
        )
    verified = verify_entry(
        root,
        subject_key,
        receipt_key,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        protected_roots=protected_roots,
        expected_registry_root=expected_registry_root,
    )
    predecessor = {
        key: verified[key]
        for key in (
            "subject_phase_id",
            "receipt_id",
            "review_status",
            "accepted_classification",
            "registry_schema_version",
            "registry_policy_version",
        )
    }
    return LineagePreflightResult(
        classification="PREDECESSOR_REVIEW_STATE_VALID_CURRENT_APPROVAL_PRESENT",
        predecessor_review_state=predecessor,
        next_task_authorized_by_registry=False,
    )
