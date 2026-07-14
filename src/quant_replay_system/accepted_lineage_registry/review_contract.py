"""Mode-neutral validation of exact reviewer and immutable subject contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .canonical import decode_json_object, sha256_bytes
from .models import (
    RUNTIME_ONLY_FIELDS,
    SHA256_RE,
    HumanReviewPayload,
    RegistryError,
    ReviewReceiptReference,
    SubjectArtifactManifest,
)


@dataclass(frozen=True)
class ReviewContractClassifications:
    payload_hash: str = "REVIEW_CONTRACT_PAYLOAD_HASH_MISMATCH_STOP"
    manifest_hash: str = "REVIEW_CONTRACT_MANIFEST_HASH_MISMATCH_STOP"
    receipt_hash: str = "REVIEW_CONTRACT_RECEIPT_HASH_MISMATCH_STOP"
    review_decision: str = "REVIEW_CONTRACT_DECISION_MISMATCH_STOP"
    review_receipt: str = "REVIEW_CONTRACT_RECEIPT_MISMATCH_STOP"
    packet_hash: str = "REVIEW_CONTRACT_PACKET_MISMATCH_STOP"
    artifact_set: str = "REVIEW_CONTRACT_ARTIFACT_SET_MISMATCH_STOP"
    authority_present: str = "REVIEW_CONTRACT_AUTHORITY_PRESENT_STOP"
    runtime_field: str = "REVIEW_CONTRACT_RUNTIME_FIELD_PRESENT_STOP"


@dataclass(frozen=True)
class ValidatedReviewedSubject:
    payload: HumanReviewPayload
    manifest: SubjectArtifactManifest
    receipt: ReviewReceiptReference


def _stop(classification: str, message: str, *, cause: Exception | None = None) -> None:
    error = RegistryError(classification, message)
    if cause is None:
        raise error
    raise error from cause


def validate_exact_reviewed_subject(
    *,
    human_review_payload_bytes: bytes,
    subject_artifact_manifest_bytes: bytes,
    review_receipt_bytes: bytes,
    expected_review_decision_id: str,
    expected_payload_sha256: str,
    expected_subject_manifest_sha256: str,
    expected_review_receipt_sha256: str,
    classifications: ReviewContractClassifications | None = None,
) -> ValidatedReviewedSubject:
    """Validate exact reviewer-authored bytes without granting runtime authority."""

    labels = classifications or ReviewContractClassifications()
    if sha256_bytes(human_review_payload_bytes) != expected_payload_sha256:
        _stop(labels.payload_hash, "Reviewer payload differs from the exact approved hash")
    try:
        raw_payload = decode_json_object(
            human_review_payload_bytes,
            label="human_review_payload",
        )
    except ValueError as exc:
        _stop(labels.review_decision, "Reviewer payload is not valid JSON", cause=exc)
    runtime_fields = sorted(RUNTIME_ONLY_FIELDS.intersection(raw_payload))
    if runtime_fields:
        raise RegistryError(
            labels.runtime_field,
            "Reviewer payload contains runtime-only materialization fields",
            details={"runtime_fields": runtime_fields},
        )
    if raw_payload.get("review_decision_id") != expected_review_decision_id:
        _stop(labels.review_decision, "Reviewer decision ID differs from exact authority")
    if not isinstance(raw_payload.get("reviewed_at"), str) or not raw_payload["reviewed_at"].strip():
        _stop(labels.review_decision, "Reviewer authority timestamp is missing")
    try:
        payload = HumanReviewPayload.from_bytes(human_review_payload_bytes)
    except RegistryError as exc:
        _stop(labels.review_decision, "Reviewer payload contract validation failed", cause=exc)
    authority = payload.data.get("authority_effects", {})
    if authority.get("materialization_authority") not in {"NONE", "NONE_BY_THIS_REISSUE"}:
        _stop(labels.authority_present, "Reviewer decision does not provide materialization authority")

    if sha256_bytes(subject_artifact_manifest_bytes) != expected_subject_manifest_sha256:
        _stop(labels.manifest_hash, "Subject manifest differs from the exact approved hash")
    try:
        manifest = SubjectArtifactManifest.from_bytes(subject_artifact_manifest_bytes)
    except RegistryError as exc:
        _stop(labels.artifact_set, "Subject artifact manifest is invalid", cause=exc)

    if not isinstance(expected_review_receipt_sha256, str) or not SHA256_RE.fullmatch(
        expected_review_receipt_sha256
    ):
        _stop(
            labels.receipt_hash,
            "Expected review receipt SHA-256 must be 64 lowercase hexadecimal characters",
        )
    receipt_sha256 = sha256_bytes(review_receipt_bytes)
    if receipt_sha256 != expected_review_receipt_sha256:
        _stop(labels.receipt_hash, "Review receipt differs from the exact approved hash")
    if not review_receipt_bytes or b"\x00" in review_receipt_bytes:
        _stop(labels.review_receipt, "Review receipt bytes are empty or invalid")
    try:
        receipt_text = review_receipt_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        _stop(labels.review_receipt, "Review receipt must be UTF-8", cause=exc)
    required_receipt_fields = {
        "receipt_id": payload.receipt_id,
        "subject_phase_id": payload.subject_phase_id,
        "review_decision_id": expected_review_decision_id,
        "materialization_authorization_id": "null",
    }
    receipt_lines = receipt_text.splitlines()
    for field, expected_value in required_receipt_fields.items():
        expected_line = f"{field} = {expected_value}"
        field_lines = [
            line
            for line in receipt_lines
            if "=" in line and line.split("=", 1)[0].strip() == field
        ]
        if field_lines != [expected_line]:
            _stop(
                labels.review_receipt,
                f"Review receipt must contain exactly one exact {field} field line",
            )
    receipt = ReviewReceiptReference(
        exact_bytes=review_receipt_bytes,
        exact_sha256=receipt_sha256,
    )

    if manifest.data["subject_phase_id"] != payload.subject_phase_id:
        _stop(labels.artifact_set, "Subject phase differs across reviewer contracts")
    if manifest.exact_sha256 != payload.data["subject_artifact_manifest_sha256"]:
        _stop(labels.manifest_hash, "Reviewer payload references a different subject manifest")
    if manifest.data["subject_packet_identifier"] != payload.data["subject_packet_identifier"]:
        _stop(labels.packet_hash, "Subject packet identifier differs across reviewer contracts")
    if manifest.data["subject_packet_sha256"] != payload.data["subject_packet_sha256"]:
        _stop(labels.packet_hash, "Subject packet hash differs across reviewer contracts")
    return ValidatedReviewedSubject(payload=payload, manifest=manifest, receipt=receipt)
