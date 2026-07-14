"""Actual synthetic subject-packet and artifact-byte verification."""

from __future__ import annotations

import os
import stat
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from .canonical import sha256_bytes, sha256_file
from .models import HumanReviewPayload, RegistryError, SubjectArtifactManifest
from .path_safety import (
    FILE_ATTRIBUTE_REPARSE_POINT,
    assert_regular_single_link_file,
    reject_casefold_collisions,
    validate_external_input_path,
    validate_relative_artifact_path,
    validate_safe_directory_chain,
)


@dataclass(frozen=True)
class VerifiedFileBytes:
    relative_path: str
    byte_length: int
    sha256: str
    st_dev: int
    st_ino: int
    st_mode: int
    st_nlink: int
    file_attributes: int

    def safe_report(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "byte_length": self.byte_length,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class SubjectInputVerification:
    packet: VerifiedFileBytes
    artifacts: tuple[VerifiedFileBytes, ...]
    exact_set_result: str

    def safe_report(self) -> dict[str, Any]:
        return {
            "packet": self.packet.safe_report(),
            "artifact_count": len(self.artifacts),
            "artifacts": [artifact.safe_report() for artifact in self.artifacts],
            "exact_set_result": self.exact_set_result,
        }

    def identity(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LivePreflightImmutableInputVerification:
    """Exact immutable-input evidence for the no-write live preflight."""

    human_review_payload_sha256: str
    subject_artifact_manifest_sha256: str
    review_receipt_sha256: str
    subject_inputs: SubjectInputVerification

    def safe_report(self) -> dict[str, Any]:
        return {
            "human_review_payload_sha256": self.human_review_payload_sha256,
            "review_receipt_sha256": self.review_receipt_sha256,
            "subject_artifact_manifest_sha256": self.subject_artifact_manifest_sha256,
            "subject_inputs": self.subject_inputs.safe_report(),
        }


def _attributes(file_stat: os.stat_result) -> int:
    return int(getattr(file_stat, "st_file_attributes", 0) or 0)


def _snapshot(path: Path, *, relative_path: str, classification: str) -> VerifiedFileBytes:
    assert_regular_single_link_file(path, classification=classification)
    before = os.lstat(path)
    digest = sha256_file(path)
    after = os.lstat(path)
    before_identity = (
        int(before.st_dev),
        int(before.st_ino),
        int(before.st_mode),
        int(getattr(before, "st_nlink", 1)),
        int(before.st_size),
        _attributes(before),
    )
    after_identity = (
        int(after.st_dev),
        int(after.st_ino),
        int(after.st_mode),
        int(getattr(after, "st_nlink", 1)),
        int(after.st_size),
        _attributes(after),
    )
    if before_identity != after_identity:
        raise RegistryError("SUBJECT_INPUT_MUTATED_DURING_TRANSACTION_STOP", "Subject input changed while hashing")
    return VerifiedFileBytes(
        relative_path=relative_path,
        byte_length=int(after.st_size),
        sha256=digest,
        st_dev=int(after.st_dev),
        st_ino=int(after.st_ino),
        st_mode=int(after.st_mode),
        st_nlink=int(getattr(after, "st_nlink", 1)),
        file_attributes=_attributes(after),
    )


def _artifact_file_set(root: Path) -> tuple[dict[str, Path], set[str]]:
    files: dict[str, Path] = {}
    directories: set[str] = set()
    stack: list[tuple[Path, PurePosixPath]] = [(root, PurePosixPath("."))]
    while stack:
        directory, relative_directory = stack.pop()
        for child in sorted(directory.iterdir(), key=lambda item: item.name.casefold()):
            file_stat = os.lstat(child)
            if stat.S_ISLNK(file_stat.st_mode) or _attributes(file_stat) & FILE_ATTRIBUTE_REPARSE_POINT:
                raise RegistryError("SUBJECT_ARTIFACT_PATH_UNSAFE_STOP", "Indirect subject artifact path rejected")
            relative = PurePosixPath(child.relative_to(root).as_posix())
            normalized = validate_relative_artifact_path(relative.as_posix())
            if stat.S_ISDIR(file_stat.st_mode):
                directories.add(normalized)
                stack.append((child, relative))
            elif stat.S_ISREG(file_stat.st_mode):
                if int(getattr(file_stat, "st_nlink", 1)) != 1:
                    raise RegistryError("SUBJECT_ARTIFACT_PATH_UNSAFE_STOP", "Hard-linked subject artifact rejected")
                files[normalized] = child
            else:
                raise RegistryError("SUBJECT_ARTIFACT_RECORD_INVALID_STOP", "Unsupported subject artifact file type")
    reject_casefold_collisions((*directories, *files), classification="SUBJECT_ARTIFACT_PATH_UNSAFE_STOP")
    return files, directories


def _expected_directories(relative_paths: Sequence[str]) -> set[str]:
    expected: set[str] = set()
    for value in relative_paths:
        path = PurePosixPath(value)
        parts = path.parts[:-1]
        for index in range(1, len(parts) + 1):
            expected.add(PurePosixPath(*parts[:index]).as_posix())
    return expected


def validate_subject_inputs(
    *,
    payload: HumanReviewPayload,
    manifest: SubjectArtifactManifest,
    subject_packet_path: str | Path | None,
    subject_artifact_root: str | Path | None,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    registry_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
) -> SubjectInputVerification:
    if subject_packet_path is None:
        raise RegistryError("SUBJECT_PACKET_PATH_REQUIRED_STOP", "Actual subject_packet_path is required")
    if subject_artifact_root is None:
        raise RegistryError("SUBJECT_ARTIFACT_MISSING_STOP", "Actual subject_artifact_root is required")
    packet_path = validate_external_input_path(
        subject_packet_path,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        registry_root=registry_root,
        protected_roots=protected_roots,
        expect_directory=False,
        missing_classification="SUBJECT_PACKET_PATH_REQUIRED_STOP",
    )
    artifact_root = validate_external_input_path(
        subject_artifact_root,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        registry_root=registry_root,
        protected_roots=protected_roots,
        expect_directory=True,
        missing_classification="SUBJECT_ARTIFACT_MISSING_STOP",
    )
    try:
        packet_path.relative_to(artifact_root)
    except ValueError:
        pass
    else:
        raise RegistryError("SUBJECT_ARTIFACT_SET_MISMATCH_STOP", "Subject packet must not be inside artifact root")

    packet = _snapshot(packet_path, relative_path="synthetic_subject_packet.zip", classification="SUBJECT_PACKET_NOT_REGULAR_STOP")
    expected_packet_hash = str(payload.data["subject_packet_sha256"])
    if manifest.data["subject_packet_sha256"] != expected_packet_hash:
        raise RegistryError("SUBJECT_PACKET_HASH_MISMATCH_STOP", "Subject packet hash differs across contracts")
    if packet.sha256 != expected_packet_hash:
        raise RegistryError("SUBJECT_PACKET_HASH_MISMATCH_STOP", "Actual subject packet SHA-256 mismatch")

    normalized_records: dict[str, dict[str, Any]] = {}
    ordered_paths: list[str] = []
    for record in manifest.data["artifacts"]:
        relative_path = validate_relative_artifact_path(record["relative_path"])
        if relative_path in normalized_records:
            raise RegistryError("SUBJECT_ARTIFACT_PATH_UNSAFE_STOP", "Duplicate normalized artifact path")
        normalized_records[relative_path] = record
        ordered_paths.append(relative_path)
    reject_casefold_collisions(ordered_paths, classification="SUBJECT_ARTIFACT_PATH_UNSAFE_STOP")

    actual_files, actual_directories = _artifact_file_set(artifact_root)
    expected_files = set(normalized_records)
    missing = sorted(expected_files - set(actual_files))
    extra = sorted(set(actual_files) - expected_files)
    if missing:
        missing_path = artifact_root / Path(*PurePosixPath(missing[0]).parts)
        if missing_path.exists() and missing_path.is_dir():
            raise RegistryError("SUBJECT_ARTIFACT_RECORD_INVALID_STOP", "Manifest requires a file where a directory exists")
        raise RegistryError("SUBJECT_ARTIFACT_MISSING_STOP", "Manifested subject artifact is missing", details={"missing_count": len(missing)})
    if extra:
        raise RegistryError("SUBJECT_ARTIFACT_EXTRA_FILE_STOP", "Unmanifested subject artifact exists", details={"extra_count": len(extra)})
    if actual_directories != _expected_directories(ordered_paths):
        raise RegistryError("SUBJECT_ARTIFACT_SET_MISMATCH_STOP", "Artifact directory set differs from manifest prefixes")
    if len(actual_files) != int(manifest.data["artifact_count"]):
        raise RegistryError("SUBJECT_ARTIFACT_SET_MISMATCH_STOP", "Actual artifact set count differs from manifest")

    snapshots: list[VerifiedFileBytes] = []
    for relative_path in sorted(expected_files):
        record = normalized_records[relative_path]
        target = actual_files[relative_path]
        validate_safe_directory_chain(target.parent, containment_root=artifact_root, create=False, classification="SUBJECT_ARTIFACT_PATH_UNSAFE_STOP")
        snapshot = _snapshot(target, relative_path=relative_path, classification="SUBJECT_ARTIFACT_PATH_UNSAFE_STOP")
        if snapshot.byte_length != record["byte_length"]:
            raise RegistryError("SUBJECT_ARTIFACT_BYTE_LENGTH_MISMATCH_STOP", "Subject artifact byte length mismatch")
        if snapshot.sha256 != record["sha256"]:
            raise RegistryError("SUBJECT_ARTIFACT_HASH_MISMATCH_STOP", "Subject artifact SHA-256 mismatch")
        snapshots.append(snapshot)
    return SubjectInputVerification(packet=packet, artifacts=tuple(snapshots), exact_set_result="PASS")


def validate_live_preflight_immutable_inputs(
    *,
    payload: HumanReviewPayload,
    manifest: SubjectArtifactManifest,
    review_receipt: bytes,
    subject_packet_path: str | Path,
    subject_artifact_root: str | Path,
    expected_reviewer_input_hashes: Mapping[str, Any],
    approved_admin_root: str | Path,
    repository_root: str | Path,
    registry_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
) -> LivePreflightImmutableInputVerification:
    """Verify all reviewer and six subject inputs without writing any output."""

    classification = "LIVE_ENTRY_IMMUTABLE_INPUT_HASH_MISMATCH_STOP"
    required_hash_keys = {
        "human_review_payload_sha256",
        "review_receipt_sha256",
        "subject_artifact_manifest_sha256",
        "subject_artifact_sha256_by_path",
        "subject_packet_sha256",
    }
    if set(expected_reviewer_input_hashes) != required_hash_keys:
        raise RegistryError(classification, "Reviewer input hash binding is incomplete or contains unexpected fields")
    if not isinstance(review_receipt, bytes):
        raise RegistryError(classification, "Review receipt must be supplied as exact bytes")

    payload_sha256 = sha256_bytes(payload.exact_bytes)
    manifest_sha256 = sha256_bytes(manifest.exact_bytes)
    receipt_sha256 = sha256_bytes(review_receipt)
    exact_hashes = {
        "human_review_payload_sha256": payload_sha256,
        "review_receipt_sha256": receipt_sha256,
        "subject_artifact_manifest_sha256": manifest_sha256,
    }
    if payload_sha256 != payload.exact_sha256 or manifest_sha256 != manifest.exact_sha256:
        raise RegistryError(classification, "Parsed reviewer input does not match its exact byte hash")
    for field, observed in exact_hashes.items():
        if expected_reviewer_input_hashes.get(field) != observed:
            raise RegistryError(classification, f"Immutable reviewer input hash mismatch at {field}")

    try:
        subject_inputs = validate_subject_inputs(
            payload=payload,
            manifest=manifest,
            subject_packet_path=subject_packet_path,
            subject_artifact_root=subject_artifact_root,
            approved_admin_root=approved_admin_root,
            repository_root=repository_root,
            registry_root=registry_root,
            protected_roots=protected_roots,
        )
    except RegistryError as exc:
        raise RegistryError(
            classification,
            "Immutable subject input verification failed",
            details={"underlying_classification": exc.classification},
        ) from exc

    if len(subject_inputs.artifacts) != 6:
        raise RegistryError(classification, "Exactly six subject artifacts are required")
    if expected_reviewer_input_hashes.get("subject_packet_sha256") != subject_inputs.packet.sha256:
        raise RegistryError(classification, "Subject packet hash differs from the immutable reviewer binding")
    expected_artifacts = expected_reviewer_input_hashes.get("subject_artifact_sha256_by_path")
    observed_artifacts = {artifact.relative_path: artifact.sha256 for artifact in subject_inputs.artifacts}
    if not isinstance(expected_artifacts, Mapping) or dict(expected_artifacts) != observed_artifacts:
        raise RegistryError(classification, "One or more subject artifact hashes differ from the immutable reviewer binding")

    return LivePreflightImmutableInputVerification(
        human_review_payload_sha256=payload_sha256,
        subject_artifact_manifest_sha256=manifest_sha256,
        review_receipt_sha256=receipt_sha256,
        subject_inputs=subject_inputs,
    )


def revalidate_subject_inputs(
    baseline: SubjectInputVerification,
    **kwargs: Any,
) -> SubjectInputVerification:
    try:
        current = validate_subject_inputs(**kwargs)
    except RegistryError as exc:
        if exc.classification == "SUBJECT_INPUT_MUTATED_DURING_TRANSACTION_STOP":
            raise
        raise RegistryError(
            "SUBJECT_INPUT_MUTATED_DURING_TRANSACTION_STOP",
            "Subject packet or artifact changed during transaction",
            details={"underlying_classification": exc.classification},
        ) from exc
    if current.identity() != baseline.identity():
        raise RegistryError("SUBJECT_INPUT_MUTATED_DURING_TRANSACTION_STOP", "Subject input identity changed during transaction")
    return current
