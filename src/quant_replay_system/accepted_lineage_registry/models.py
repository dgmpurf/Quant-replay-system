"""Validated models and explicit registry classifications."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from .canonical import decode_json_object, sha256_bytes


REGISTRY_SCHEMA_VERSION = "accepted-lineage-registry-v0.1"
REGISTRY_POLICY_VERSION = "accepted-lineage-registry-policy-v0.1"
SYNTHETIC_MODE = "SYNTHETIC_FIXTURE_ONLY_NOT_A_PILOT"
LIVE_MODE_STOP = "LIVE_REGISTRY_MODE_NOT_AUTHORIZED_STOP"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_REVIEW_STATUSES = {
    "ACCEPTED",
    "ACCEPTED_WITH_LIMITATIONS",
    "REJECTED",
    "NEEDS_ADJUSTMENT_BEFORE_IMPLEMENTATION",
}

HUMAN_REVIEW_REQUIRED_FIELDS = (
    "schema",
    "review_decision_id",
    "receipt_id",
    "subject_phase_id",
    "subject_packet_identifier",
    "subject_packet_sha256",
    "subject_artifact_manifest_sha256",
    "review_status",
    "accepted_classification",
    "accepted_verdict",
    "operational_result",
    "needs_fix",
    "privacy_issue_stop",
    "authority_effects",
    "evidence_state_before",
    "evidence_state_after",
    "blocker_effects",
    "PIT_effect",
    "replay_effect",
    "S5_WP04_effect",
    "prompt_accounting",
    "reviewer_alias",
    "review_surface",
    "reviewed_at",
    "review_limitations",
)

RUNTIME_ONLY_FIELDS = {
    "registry_schema_version",
    "registry_policy_version",
    "materialization_authorization_id",
    "materialized_by",
    "materialized_at",
    "operation_identifier",
    "entry_relative_path",
    "registry_status",
    "validation_result",
    "idempotency_result",
    "human_review_payload_sha256",
    "entry_manifest_sha256",
    "entry_seal_sha256",
}


class RegistryError(RuntimeError):
    """A bounded stop with a machine-readable classification."""

    def __init__(self, classification: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.classification = classification
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "message": str(self),
            "details": self.details,
        }


def _require_string(data: Mapping[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RegistryError(
            "REVIEW_PAYLOAD_REQUIRED_FIELD_MISSING_STOP",
            f"{field} must be a non-empty reviewer-authored string",
        )
    return value


def _require_sha256(data: Mapping[str, Any], field: str) -> str:
    value = _require_string(data, field)
    if not SHA256_RE.fullmatch(value):
        raise RegistryError(
            "HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP",
            f"{field} must be lowercase SHA-256 hexadecimal",
        )
    return value


@dataclass(frozen=True)
class HumanReviewPayload:
    exact_bytes: bytes
    data: dict[str, Any]
    exact_sha256: str

    @classmethod
    def from_bytes(cls, exact_bytes: bytes) -> "HumanReviewPayload":
        try:
            data = decode_json_object(exact_bytes, label="human_review_payload")
        except ValueError as exc:
            raise RegistryError("HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP", str(exc)) from exc
        missing = [field for field in HUMAN_REVIEW_REQUIRED_FIELDS if field not in data]
        if missing:
            raise RegistryError(
                "REVIEW_PAYLOAD_REQUIRED_FIELD_MISSING_STOP",
                "Reviewer-authored payload is missing required fields",
                details={"missing_fields": missing},
            )
        leaked = sorted(RUNTIME_ONLY_FIELDS.intersection(data))
        if leaked:
            raise RegistryError(
                "HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP",
                "Reviewer-authored payload contains runtime-only fields",
                details={"runtime_fields": leaked},
            )
        for field in (
            "review_decision_id",
            "receipt_id",
            "subject_phase_id",
            "subject_packet_identifier",
            "accepted_classification",
            "accepted_verdict",
            "operational_result",
            "reviewer_alias",
            "review_surface",
            "reviewed_at",
        ):
            _require_string(data, field)
        _require_sha256(data, "subject_packet_sha256")
        _require_sha256(data, "subject_artifact_manifest_sha256")
        if data["review_status"] not in ALLOWED_REVIEW_STATUSES:
            raise RegistryError(
                "HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP",
                "review_status is outside the constrained vocabulary",
            )
        for field in ("needs_fix", "privacy_issue_stop"):
            if not isinstance(data[field], bool):
                raise RegistryError("HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP", f"{field} must be boolean")
        for field in ("authority_effects", "blocker_effects", "prompt_accounting"):
            if not isinstance(data[field], dict):
                raise RegistryError("HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP", f"{field} must be an object")
        if not isinstance(data["review_limitations"], list):
            raise RegistryError("HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP", "review_limitations must be an array")
        for supersession_field in ("supersedes_receipt_id", "superseded_by_receipt_id"):
            if data.get(supersession_field) is not None:
                raise RegistryError(
                    "SUPERSESSION_NOT_SUPPORTED_V0_1_STOP",
                    "Registry v0.1 does not support supersession",
                )
        return cls(exact_bytes=exact_bytes, data=data, exact_sha256=sha256_bytes(exact_bytes))

    @property
    def receipt_id(self) -> str:
        return str(self.data["receipt_id"])

    @property
    def subject_phase_id(self) -> str:
        return str(self.data["subject_phase_id"])

    def assert_synthetic_only(self) -> None:
        for field in ("subject_phase_id", "receipt_id", "subject_packet_identifier", "review_decision_id"):
            if not str(self.data[field]).upper().startswith("SYNTHETIC-"):
                raise RegistryError(
                    LIVE_MODE_STOP,
                    f"{field} is not an explicitly synthetic identifier",
                )


@dataclass(frozen=True)
class SubjectArtifactManifest:
    exact_bytes: bytes
    data: dict[str, Any]
    exact_sha256: str

    @classmethod
    def from_bytes(cls, exact_bytes: bytes) -> "SubjectArtifactManifest":
        try:
            data = decode_json_object(exact_bytes, label="subject_artifact_manifest")
        except ValueError as exc:
            raise RegistryError("SUBJECT_ARTIFACT_MANIFEST_MISMATCH_STOP", str(exc)) from exc
        required = (
            "schema",
            "subject_phase_id",
            "subject_packet_identifier",
            "subject_packet_sha256",
            "artifact_count",
            "allow_empty_artifacts",
            "artifacts",
        )
        missing = [field for field in required if field not in data]
        if missing:
            raise RegistryError(
                "SUBJECT_ARTIFACT_MANIFEST_MISMATCH_STOP",
                "Subject artifact manifest is missing fields",
                details={"missing_fields": missing},
            )
        for field in ("schema", "subject_phase_id", "subject_packet_identifier"):
            if not isinstance(data[field], str) or not data[field]:
                raise RegistryError("SUBJECT_ARTIFACT_MANIFEST_MISMATCH_STOP", f"{field} must be non-empty")
        if not isinstance(data["subject_packet_sha256"], str) or not SHA256_RE.fullmatch(data["subject_packet_sha256"]):
            raise RegistryError("SUBJECT_ARTIFACT_MANIFEST_MISMATCH_STOP", "subject_packet_sha256 is invalid")
        if not isinstance(data["artifact_count"], int) or isinstance(data["artifact_count"], bool) or data["artifact_count"] < 0:
            raise RegistryError("SUBJECT_ARTIFACT_RECORD_INVALID_STOP", "artifact_count must be a non-negative integer")
        if not isinstance(data["allow_empty_artifacts"], bool):
            raise RegistryError("SUBJECT_ARTIFACT_RECORD_INVALID_STOP", "allow_empty_artifacts must be boolean")
        if not isinstance(data["artifacts"], list):
            raise RegistryError("SUBJECT_ARTIFACT_RECORD_INVALID_STOP", "artifacts must be an array")
        if data["artifact_count"] != len(data["artifacts"]):
            raise RegistryError("SUBJECT_ARTIFACT_SET_MISMATCH_STOP", "artifact_count differs from artifact records")
        if not data["artifacts"] and not data["allow_empty_artifacts"]:
            raise RegistryError("SUBJECT_ARTIFACT_SET_MISMATCH_STOP", "Empty artifact set is not explicitly permitted")
        for index, record in enumerate(data["artifacts"]):
            if not isinstance(record, dict):
                raise RegistryError("SUBJECT_ARTIFACT_RECORD_INVALID_STOP", "Artifact record must be an object")
            missing_record_fields = [field for field in ("relative_path", "byte_length", "sha256") if field not in record]
            if missing_record_fields:
                raise RegistryError(
                    "SUBJECT_ARTIFACT_RECORD_INVALID_STOP",
                    "Artifact record is missing required fields",
                    details={"record_index": index, "missing_fields": missing_record_fields},
                )
            if not isinstance(record["relative_path"], str) or not record["relative_path"]:
                raise RegistryError("SUBJECT_ARTIFACT_RECORD_INVALID_STOP", "Artifact relative_path must be non-empty")
            if not isinstance(record["byte_length"], int) or isinstance(record["byte_length"], bool) or record["byte_length"] < 0:
                raise RegistryError("SUBJECT_ARTIFACT_RECORD_INVALID_STOP", "Artifact byte_length must be non-negative")
            if not isinstance(record["sha256"], str) or not SHA256_RE.fullmatch(record["sha256"]):
                raise RegistryError("SUBJECT_ARTIFACT_RECORD_INVALID_STOP", "Artifact SHA-256 must be lowercase hexadecimal")
        return cls(exact_bytes=exact_bytes, data=data, exact_sha256=sha256_bytes(exact_bytes))


@dataclass(frozen=True)
class ReviewReceiptReference:
    exact_bytes: bytes
    exact_sha256: str

    @classmethod
    def from_bytes(cls, exact_bytes: bytes, *, receipt_id: str, subject_phase_id: str) -> "ReviewReceiptReference":
        if not exact_bytes or b"\x00" in exact_bytes:
            raise RegistryError("HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP", "Review receipt bytes are empty or invalid")
        try:
            text = exact_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RegistryError("HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP", "Review receipt must be UTF-8") from exc
        if receipt_id not in text or subject_phase_id not in text:
            raise RegistryError(
                "HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP",
                "Review receipt does not name the exact receipt and subject",
            )
        return cls(exact_bytes=exact_bytes, exact_sha256=sha256_bytes(exact_bytes))


@dataclass(frozen=True)
class RuntimeEntryManifest:
    data: dict[str, Any]


@dataclass(frozen=True)
class EntrySeal:
    data: dict[str, Any]


@dataclass(frozen=True)
class RegistryPolicy:
    registry_policy_version: str = REGISTRY_POLICY_VERSION
    registry_mode: str = SYNTHETIC_MODE
    single_writer: bool = True
    supersession_enabled: bool = False
    live_registry_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RegistrySchema:
    registry_schema_version: str = REGISTRY_SCHEMA_VERSION
    entry_file_count: int = 5
    entry_files: tuple[str, ...] = (
        "human_review_payload.json",
        "subject_artifact_manifest.json",
        "review_receipt.md",
        "entry_manifest.json",
        "entry_seal.json",
    )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["entry_files"] = list(self.entry_files)
        return value


@dataclass(frozen=True)
class DerivedIndexRecord:
    subject_key: str
    receipt_key: str
    subject_phase_id: str
    receipt_id: str
    review_status: str
    accepted_classification: str
    registry_schema_version: str
    registry_policy_version: str
    entry_seal_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RegistryHealthResult:
    registry_mode: str
    registry_schema_version: str
    registry_policy_version: str
    root_safety: str
    lock_status: str
    authoritative_entry_count: int
    entry_verification_status: str
    derived_index_status: str
    stale_index_status: bool
    orphan_temporary_directories: int
    path_safety_warnings: tuple[str, ...]
    platform_limitations: tuple[str, ...]
    privacy_warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        for field in ("path_safety_warnings", "platform_limitations", "privacy_warnings"):
            value[field] = list(value[field])
        return value


@dataclass(frozen=True)
class MaterializationResult:
    classification: str
    subject_key: str
    receipt_key: str
    entry_created: bool
    idempotent_replay: bool
    entry_verified: bool
    derived_index_status: str
    authoritative_entry_created: bool = False
    entry_verification_started: bool = False
    entry_verification_completed: bool = False
    entry_verification_passed: bool = False
    derived_index_attempted: bool = False
    derived_index_completed: bool = False
    derived_index_passed: bool = False
    materialization_verified: bool = False
    entry_verification_failure: str | None = None
    execution_packet_modified: bool = False
    live_registry_created: bool = False
    Stage1B_A_materialized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LineagePreflightResult:
    classification: str
    predecessor_review_state: dict[str, Any]
    next_task_authorized_by_registry: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
