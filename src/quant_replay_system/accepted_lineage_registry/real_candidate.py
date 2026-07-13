"""Governed, non-live, read-only validation for a real registry candidate."""

from __future__ import annotations

import os
import stat
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .canonical import canonical_json_bytes, decode_json_object, sha256_bytes
from .models import (
    REGISTRY_POLICY_VERSION,
    REGISTRY_SCHEMA_VERSION,
    RUNTIME_ONLY_FIELDS,
    SHA256_RE,
    HumanReviewPayload,
    RegistryError,
    ReviewReceiptReference,
    SubjectArtifactManifest,
)
from .path_safety import (
    assert_no_filesystem_indirection,
    derive_receipt_key,
    derive_subject_key,
    platform_path_limitations,
    validate_nearest_existing_chain,
    validate_safe_directory_chain,
)
from .subject_verification import revalidate_subject_inputs, validate_subject_inputs


GOVERNED_REAL_CANDIDATE_MODE = "GOVERNED_REAL_CANDIDATE_NON_LIVE_DRY_RUN"
SUCCESS_CLASSIFICATION = (
    "GOVERNED_REAL_CANDIDATE_DRY_RUN_VALIDATION_PASSED_"
    "MATERIALIZATION_NOT_AUTHORIZED"
)

PAYLOAD_HASH_STOP = "REAL_CANDIDATE_DRY_RUN_EXPECTED_PAYLOAD_HASH_MISMATCH_STOP"
MANIFEST_HASH_STOP = "REAL_CANDIDATE_DRY_RUN_EXPECTED_MANIFEST_HASH_MISMATCH_STOP"
REVIEW_RECEIPT_HASH_STOP = (
    "REAL_CANDIDATE_DRY_RUN_EXPECTED_REVIEW_RECEIPT_HASH_MISMATCH_STOP"
)
REVIEW_DECISION_STOP = "REAL_CANDIDATE_DRY_RUN_REVIEW_DECISION_ID_MISMATCH_STOP"
REVIEW_RECEIPT_STOP = "REAL_CANDIDATE_DRY_RUN_REVIEW_RECEIPT_MISMATCH_STOP"
PACKET_HASH_STOP = "REAL_CANDIDATE_DRY_RUN_PACKET_HASH_MISMATCH_STOP"
ARTIFACT_SET_STOP = "REAL_CANDIDATE_DRY_RUN_ARTIFACT_SET_MISMATCH_STOP"
CANDIDATE_EXISTS_STOP = "REAL_CANDIDATE_DRY_RUN_CANDIDATE_ROOT_EXISTS_STOP"
CANDIDATE_UNSAFE_STOP = "REAL_CANDIDATE_DRY_RUN_CANDIDATE_ROOT_UNSAFE_STOP"
LIVE_COLLISION_STOP = "REAL_CANDIDATE_DRY_RUN_LIVE_ROOT_COLLISION_STOP"
AUTHORITY_PRESENT_STOP = "REAL_CANDIDATE_DRY_RUN_MATERIALIZATION_AUTHORITY_PRESENT_STOP"
RUNTIME_FIELD_STOP = "REAL_CANDIDATE_DRY_RUN_RUNTIME_FIELD_PRESENT_STOP"
UNEXPECTED_WRITE_STOP = "REAL_CANDIDATE_DRY_RUN_UNEXPECTED_WRITE_STOP"


@dataclass(frozen=True)
class GovernedRealCandidateDryRunResult:
    classification: str
    status: str
    mode: str
    review_decision_valid: bool
    reviewer_input_hashes_valid: bool
    subject_packet_valid: bool
    subject_artifact_set_valid: bool
    review_receipt_valid: bool
    opaque_keys_derived: bool
    candidate_root_validated: bool
    candidate_root_created: bool
    acceptance_entry_created: bool
    runtime_manifest_created: bool
    entry_seal_created: bool
    derived_index_created: bool
    live_registry_created: bool
    materialization_authorization_present: bool
    materialization_ready: bool
    next_task_authorized_by_registry: bool
    would_stop_materialization_with: str
    materialization_prerequisites_missing: tuple[str, ...]
    subject_key: str
    receipt_key: str
    dry_run_input_identity: dict[str, Any]
    dry_run_input_identity_sha256: str
    platform_control_status: str
    platform_limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["materialization_prerequisites_missing"] = list(
            self.materialization_prerequisites_missing
        )
        value["platform_limitations"] = list(self.platform_limitations)
        return value


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


def _attributes(file_stat: os.stat_result) -> int:
    return int(getattr(file_stat, "st_file_attributes", 0) or 0)


def _path_chain_snapshot(target: Path, containment: Path) -> tuple[tuple[Any, ...], ...]:
    if not _within(target, containment):
        return ()
    paths = [containment]
    current = containment
    for part in target.relative_to(containment).parts:
        current = current / part
        paths.append(current)
    snapshot: list[tuple[Any, ...]] = []
    for path in paths:
        if os.path.lexists(path):
            file_stat = os.lstat(path)
            snapshot.append(
                (
                    path.relative_to(containment).as_posix() or ".",
                    True,
                    int(file_stat.st_dev),
                    int(file_stat.st_ino),
                    int(file_stat.st_mode),
                    int(getattr(file_stat, "st_nlink", 1)),
                    int(file_stat.st_size),
                    _attributes(file_stat),
                )
            )
        else:
            snapshot.append((path.relative_to(containment).as_posix(), False))
    return tuple(snapshot)


def _candidate_root(
    candidate_root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    expected_candidate_root: str | Path,
    subject_packet_path: str | Path,
    subject_artifact_root: str | Path,
) -> tuple[Path, Path, tuple[tuple[Any, ...], ...]]:
    candidate = _absolute(candidate_root)
    expected = _absolute(expected_candidate_root)
    admin = _absolute(approved_admin_root)
    repository = _absolute(repository_root)
    packet_parent = _absolute(subject_packet_path).parent
    artifact_root = _absolute(subject_artifact_root)
    live_root = admin / "accepted_lineage_registry_v0_1"

    if _same_path(candidate, live_root) or _within(candidate, live_root, strict=True):
        raise RegistryError(LIVE_COLLISION_STOP, "Candidate root collides with the future live registry root")
    if os.path.lexists(live_root):
        raise RegistryError(LIVE_COLLISION_STOP, "Future live registry root must remain absent")
    if not _same_path(candidate, expected):
        raise RegistryError(CANDIDATE_UNSAFE_STOP, "Candidate root differs from the exact approved root")
    if not _within(candidate, admin, strict=True):
        raise RegistryError(CANDIDATE_UNSAFE_STOP, "Candidate root is outside the approved administration root")
    if _same_path(candidate, repository) or _within(candidate, repository, strict=True):
        raise RegistryError(CANDIDATE_UNSAFE_STOP, "Candidate root is inside the repository")
    if (
        _same_path(candidate, packet_parent)
        or _within(candidate, packet_parent, strict=True)
        or _same_path(candidate, artifact_root)
        or _within(candidate, artifact_root, strict=True)
    ):
        raise RegistryError(CANDIDATE_UNSAFE_STOP, "Candidate root is inside immutable subject input")
    if os.path.lexists(candidate):
        raise RegistryError(CANDIDATE_EXISTS_STOP, "Candidate root must not exist during dry run")
    try:
        assert_no_filesystem_indirection(admin, classification=CANDIDATE_UNSAFE_STOP)
        validate_safe_directory_chain(
            admin,
            containment_root=admin,
            create=False,
            classification=CANDIDATE_UNSAFE_STOP,
        )
        assert_no_filesystem_indirection(repository, classification=CANDIDATE_UNSAFE_STOP)
        validate_safe_directory_chain(
            repository,
            containment_root=repository,
            create=False,
            classification=CANDIDATE_UNSAFE_STOP,
        )
        validate_nearest_existing_chain(
            candidate,
            containment_root=admin,
            classification=CANDIDATE_UNSAFE_STOP,
        )
    except RegistryError as exc:
        if exc.classification == CANDIDATE_UNSAFE_STOP:
            raise
        raise RegistryError(CANDIDATE_UNSAFE_STOP, "Candidate root path validation failed") from exc
    return candidate, live_root, _path_chain_snapshot(candidate, admin)


def _payload(
    exact_bytes: bytes,
    *,
    expected_sha256: str,
    expected_review_decision_id: str,
) -> HumanReviewPayload:
    if sha256_bytes(exact_bytes) != expected_sha256:
        raise RegistryError(PAYLOAD_HASH_STOP, "Reviewer payload differs from the exact approved hash")
    try:
        raw = decode_json_object(exact_bytes, label="human_review_payload")
    except ValueError as exc:
        raise RegistryError(REVIEW_DECISION_STOP, "Reviewer payload is not valid JSON") from exc
    runtime_fields = sorted(RUNTIME_ONLY_FIELDS.intersection(raw))
    if runtime_fields:
        raise RegistryError(
            RUNTIME_FIELD_STOP,
            "Reviewer payload contains runtime-only materialization fields",
            details={"runtime_fields": runtime_fields},
        )
    if raw.get("review_decision_id") != expected_review_decision_id:
        raise RegistryError(REVIEW_DECISION_STOP, "Reviewer decision ID differs from exact authority")
    if not isinstance(raw.get("reviewed_at"), str) or not raw["reviewed_at"].strip():
        raise RegistryError(REVIEW_DECISION_STOP, "Reviewer authority timestamp is missing")
    try:
        payload = HumanReviewPayload.from_bytes(exact_bytes)
    except RegistryError as exc:
        raise RegistryError(REVIEW_DECISION_STOP, "Reviewer payload contract validation failed") from exc
    authority = payload.data.get("authority_effects", {})
    materialization_authority = authority.get("materialization_authority")
    if materialization_authority not in {"NONE", "NONE_BY_THIS_REISSUE"}:
        raise RegistryError(
            AUTHORITY_PRESENT_STOP,
            "Reviewer decision does not provide materialization authority",
        )
    return payload


def _manifest(exact_bytes: bytes, *, expected_sha256: str) -> SubjectArtifactManifest:
    if sha256_bytes(exact_bytes) != expected_sha256:
        raise RegistryError(MANIFEST_HASH_STOP, "Subject manifest differs from the exact approved hash")
    try:
        return SubjectArtifactManifest.from_bytes(exact_bytes)
    except RegistryError as exc:
        raise RegistryError(ARTIFACT_SET_STOP, "Subject artifact manifest is invalid") from exc


def _receipt(
    exact_bytes: bytes,
    *,
    payload: HumanReviewPayload,
    expected_review_decision_id: str,
    expected_sha256: str,
) -> ReviewReceiptReference:
    if not isinstance(expected_sha256, str) or not SHA256_RE.fullmatch(expected_sha256):
        raise RegistryError(
            REVIEW_RECEIPT_HASH_STOP,
            "Expected review receipt SHA-256 must be 64 lowercase hexadecimal characters",
        )
    exact_sha256 = sha256_bytes(exact_bytes)
    if exact_sha256 != expected_sha256:
        raise RegistryError(
            REVIEW_RECEIPT_HASH_STOP,
            "Review receipt differs from the exact approved hash",
        )
    if not exact_bytes or b"\x00" in exact_bytes:
        raise RegistryError(REVIEW_RECEIPT_STOP, "Review receipt bytes are empty or invalid")
    try:
        text = exact_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RegistryError(REVIEW_RECEIPT_STOP, "Review receipt must be UTF-8") from exc

    required_fields = {
        "receipt_id": payload.receipt_id,
        "subject_phase_id": payload.subject_phase_id,
        "review_decision_id": expected_review_decision_id,
        "materialization_authorization_id": "null",
    }
    lines = text.splitlines()
    for field, expected_value in required_fields.items():
        expected_line = f"{field} = {expected_value}"
        field_lines = []
        for line in lines:
            if "=" not in line:
                continue
            left, _ = line.split("=", 1)
            if left.strip() == field:
                field_lines.append(line)
        # Exact fields allow no indentation and exactly one ASCII space around '='.
        if field_lines != [expected_line]:
            raise RegistryError(
                REVIEW_RECEIPT_STOP,
                f"Review receipt must contain exactly one exact {field} field line",
            )
    return ReviewReceiptReference(exact_bytes=exact_bytes, exact_sha256=exact_sha256)


def _cross_contracts(payload: HumanReviewPayload, manifest: SubjectArtifactManifest) -> None:
    if manifest.data["subject_phase_id"] != payload.subject_phase_id:
        raise RegistryError(ARTIFACT_SET_STOP, "Subject phase differs across reviewer contracts")
    if manifest.exact_sha256 != payload.data["subject_artifact_manifest_sha256"]:
        raise RegistryError(MANIFEST_HASH_STOP, "Reviewer payload references a different subject manifest")
    if manifest.data["subject_packet_identifier"] != payload.data["subject_packet_identifier"]:
        raise RegistryError(PACKET_HASH_STOP, "Subject packet identifier differs across reviewer contracts")
    if manifest.data["subject_packet_sha256"] != payload.data["subject_packet_sha256"]:
        raise RegistryError(PACKET_HASH_STOP, "Subject packet hash differs across reviewer contracts")


def _subject_inputs(
    *,
    payload: HumanReviewPayload,
    manifest: SubjectArtifactManifest,
    subject_packet_path: str | Path,
    subject_artifact_root: str | Path,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    candidate_root: str | Path,
):
    kwargs = {
        "payload": payload,
        "manifest": manifest,
        "subject_packet_path": subject_packet_path,
        "subject_artifact_root": subject_artifact_root,
        "approved_admin_root": approved_admin_root,
        "repository_root": repository_root,
        "registry_root": candidate_root,
    }
    try:
        verified = validate_subject_inputs(**kwargs)
    except RegistryError as exc:
        packet_classifications = {
            "SUBJECT_PACKET_PATH_REQUIRED_STOP",
            "SUBJECT_PACKET_NOT_REGULAR_STOP",
            "SUBJECT_PACKET_HASH_MISMATCH_STOP",
        }
        classification = PACKET_HASH_STOP if exc.classification in packet_classifications else ARTIFACT_SET_STOP
        raise RegistryError(classification, "Immutable subject input validation failed") from exc

    packet_path = _absolute(subject_packet_path)
    artifact_root = _absolute(subject_artifact_root)
    expected_records = {
        str(record["relative_path"]): record for record in manifest.data["artifacts"]
    }
    try:
        with zipfile.ZipFile(packet_path, "r") as archive:
            infos = archive.infolist()
            names = archive.namelist()
            if names != sorted(expected_records) or len(names) != len(set(names)):
                raise RegistryError(ARTIFACT_SET_STOP, "Subject packet member set differs from manifest")
            for info in infos:
                member = PurePosixPath(info.filename)
                mode = (info.external_attr >> 16) & 0xFFFF
                if (
                    member.is_absolute()
                    or any(part in {"", ".", ".."} for part in member.parts)
                    or ":" in member.parts[0]
                    or info.is_dir()
                    or stat.S_ISLNK(mode)
                ):
                    raise RegistryError(ARTIFACT_SET_STOP, "Subject packet contains an unsafe member")
                exact_bytes = archive.read(info.filename)
                record = expected_records[info.filename]
                if (
                    len(exact_bytes) != record["byte_length"]
                    or sha256_bytes(exact_bytes) != record["sha256"]
                    or exact_bytes != (artifact_root / Path(*member.parts)).read_bytes()
                ):
                    raise RegistryError(ARTIFACT_SET_STOP, "Subject packet member bytes differ from extracted artifact")
    except RegistryError:
        raise
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        raise RegistryError(PACKET_HASH_STOP, "Subject packet is not a valid immutable ZIP") from exc
    return verified, kwargs


def dry_run_real_candidate(
    candidate_root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    expected_candidate_root: str | Path,
    human_review_payload_bytes: bytes,
    subject_artifact_manifest_bytes: bytes,
    subject_packet_path: str | Path,
    subject_artifact_root: str | Path,
    review_receipt_bytes: bytes,
    expected_review_decision_id: str,
    expected_payload_sha256: str,
    expected_subject_manifest_sha256: str,
    expected_review_receipt_sha256: str,
    materialization_authorization_id: str | None = None,
) -> GovernedRealCandidateDryRunResult:
    """Validate a real candidate without creating any registry state."""

    if materialization_authorization_id is not None:
        raise RegistryError(
            AUTHORITY_PRESENT_STOP,
            "A materialization authorization ID is forbidden in dry-run mode",
        )

    payload = _payload(
        human_review_payload_bytes,
        expected_sha256=expected_payload_sha256,
        expected_review_decision_id=expected_review_decision_id,
    )
    manifest = _manifest(
        subject_artifact_manifest_bytes,
        expected_sha256=expected_subject_manifest_sha256,
    )
    _cross_contracts(payload, manifest)
    receipt = _receipt(
        review_receipt_bytes,
        payload=payload,
        expected_review_decision_id=expected_review_decision_id,
        expected_sha256=expected_review_receipt_sha256,
    )
    verified_subject, subject_kwargs = _subject_inputs(
        payload=payload,
        manifest=manifest,
        subject_packet_path=subject_packet_path,
        subject_artifact_root=subject_artifact_root,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        candidate_root=candidate_root,
    )
    subject_key = derive_subject_key(payload.subject_phase_id)
    receipt_key = derive_receipt_key(payload.receipt_id)
    candidate, live_root, candidate_snapshot = _candidate_root(
        candidate_root,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        expected_candidate_root=expected_candidate_root,
        subject_packet_path=subject_packet_path,
        subject_artifact_root=subject_artifact_root,
    )

    revalidate_subject_inputs(verified_subject, **subject_kwargs)
    admin = _absolute(approved_admin_root)
    if (
        os.path.lexists(candidate)
        or os.path.lexists(live_root)
        or _path_chain_snapshot(candidate, admin) != candidate_snapshot
    ):
        raise RegistryError(UNEXPECTED_WRITE_STOP, "Dry-run validation changed filesystem state")

    artifacts = [
        {"relative_path": artifact.relative_path, "sha256": artifact.sha256}
        for artifact in verified_subject.artifacts
    ]
    identity = {
        "review_decision_id": payload.data["review_decision_id"],
        "receipt_id": payload.receipt_id,
        "subject_phase_id": payload.subject_phase_id,
        "human_review_payload_sha256": payload.exact_sha256,
        "subject_artifact_manifest_sha256": manifest.exact_sha256,
        "review_receipt_sha256": receipt.exact_sha256,
        "subject_packet_sha256": verified_subject.packet.sha256,
        "subject_artifact_sha256": artifacts,
        "subject_key": subject_key,
        "receipt_key": receipt_key,
        "registry_schema_version": REGISTRY_SCHEMA_VERSION,
        "registry_policy_version": REGISTRY_POLICY_VERSION,
    }
    limitations = platform_path_limitations()
    return GovernedRealCandidateDryRunResult(
        classification=SUCCESS_CLASSIFICATION,
        status="PASS",
        mode=GOVERNED_REAL_CANDIDATE_MODE,
        review_decision_valid=True,
        reviewer_input_hashes_valid=True,
        subject_packet_valid=True,
        subject_artifact_set_valid=True,
        review_receipt_valid=True,
        opaque_keys_derived=True,
        candidate_root_validated=True,
        candidate_root_created=False,
        acceptance_entry_created=False,
        runtime_manifest_created=False,
        entry_seal_created=False,
        derived_index_created=False,
        live_registry_created=False,
        materialization_authorization_present=False,
        materialization_ready=False,
        next_task_authorized_by_registry=False,
        would_stop_materialization_with="MATERIALIZATION_EXACT_APPROVAL_MISSING_STOP",
        materialization_prerequisites_missing=(
            "EXACT_MATERIALIZATION_AUTHORIZATION_ID",
            "SEPARATE_NON_LIVE_CANDIDATE_MATERIALIZATION_APPROVAL",
        ),
        subject_key=subject_key,
        receipt_key=receipt_key,
        dry_run_input_identity=identity,
        dry_run_input_identity_sha256=sha256_bytes(canonical_json_bytes(identity)),
        platform_control_status=(
            "PASS_WITH_EXPLICIT_PLATFORM_LIMITATIONS" if limitations else "PASS"
        ),
        platform_limitations=limitations,
    )
