"""Deterministic derived index with explicit crash-state recovery."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Sequence

from .canonical import canonical_json_bytes, fsync_directory, sha256_bytes, sha256_file, write_bytes_fsync
from .locking import RegistryWriteLock
from .models import SYNTHETIC_MODE, DerivedIndexRecord, RegistryError
from .path_safety import (
    assert_regular_single_link_file,
    validate_receipt_key,
    validate_registry_root_authority,
    validate_safe_directory_chain,
    validate_subject_key,
)
from .verification import load_registry_configuration, verify_entry


INDEX_FILENAME = "registry_index.jsonl"
INDEX_MANIFEST_FILENAME = "registry_index_manifest.json"
STALE_MARKER_FILENAME = "registry_index_stale.json"
TRANSACTION_MARKER_FILENAME = "registry_index_transaction.json"
INDEX_TRANSACTION_TEMP = ".registry_index.jsonl.transaction"
MANIFEST_TRANSACTION_TEMP = ".registry_index_manifest.json.transaction"
INDEX_ROW_FIELDS = frozenset(
    {
        "subject_key",
        "receipt_key",
        "subject_phase_id",
        "receipt_id",
        "review_status",
        "accepted_classification",
        "registry_schema_version",
        "registry_policy_version",
        "entry_seal_sha256",
    }
)


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


def _entry_key_pairs(root: Path, *, authority: dict[str, Any]) -> list[tuple[str, str]]:
    entries_root = validate_safe_directory_chain(
        root / "entries",
        containment_root=root,
        create=False,
        classification="DERIVED_INDEX_PATH_SAFETY_STOP",
    )
    pairs: list[tuple[str, str]] = []
    for subject_dir in sorted(entries_root.iterdir(), key=lambda item: item.name):
        if not subject_dir.is_dir():
            raise RegistryError("DERIVED_INDEX_PATH_SAFETY_STOP", "Unexpected non-directory under entries")
        validate_subject_key(subject_dir.name)
        validate_safe_directory_chain(subject_dir, containment_root=root, create=False, classification="DERIVED_INDEX_PATH_SAFETY_STOP")
        for receipt_dir in sorted(subject_dir.iterdir(), key=lambda item: item.name):
            if not receipt_dir.is_dir():
                raise RegistryError("DERIVED_INDEX_PATH_SAFETY_STOP", "Unexpected non-directory under subject entry")
            validate_receipt_key(receipt_dir.name)
            validate_safe_directory_chain(receipt_dir, containment_root=root, create=False, classification="DERIVED_INDEX_PATH_SAFETY_STOP")
            pairs.append((subject_dir.name, receipt_dir.name))
    return pairs


def _safe_unlink(path: Path, *, parent: Path, classification: str) -> None:
    if not path.exists():
        return
    validate_safe_directory_chain(parent, containment_root=parent, create=False, classification=classification)
    assert_regular_single_link_file(path, classification=classification)
    path.unlink()


def _active_pair_is_valid(index_path: Path, manifest_path: Path, *, expected_count: int, expected_hash: str) -> None:
    assert_regular_single_link_file(index_path, classification="DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED")
    assert_regular_single_link_file(manifest_path, classification="DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256_file(index_path) != expected_hash or manifest.get("registry_index_sha256") != expected_hash:
        raise RegistryError("DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED", "Activated derived index hash mismatch")
    if manifest.get("entry_count") != expected_count:
        raise RegistryError("DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED", "Activated derived index count mismatch")


def regenerate_index(
    root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expected_registry_root: str | Path | None = None,
    registry_mode: str = SYNTHETIC_MODE,
    failure_injection: str | None = None,
    lock_held: bool = False,
    lock_timeout_seconds: float = 5.0,
) -> dict[str, Any]:
    authority = _authority_kwargs(
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        protected_roots=protected_roots,
        expected_registry_root=expected_registry_root,
        registry_mode=registry_mode,
    )
    registry_root = validate_registry_root_authority(root, create=False, **authority)
    if not lock_held:
        with RegistryWriteLock(
            registry_root=registry_root,
            operator_alias="synthetic-index-rebuilder",
            operation_id="synthetic-derived-index-rebuild",
            approved_admin_root=Path(approved_admin_root),
            repository_root=Path(repository_root),
            protected_roots=tuple(Path(item) for item in protected_roots),
            expected_registry_root=Path(expected_registry_root) if expected_registry_root is not None else None,
            registry_mode=registry_mode,
            timeout_seconds=lock_timeout_seconds,
        ):
            return regenerate_index(
                registry_root,
                failure_injection=failure_injection,
                lock_held=True,
                lock_timeout_seconds=lock_timeout_seconds,
                **authority,
            )
    policy, schema = load_registry_configuration(registry_root, **authority)
    derived = validate_safe_directory_chain(
        registry_root / "derived",
        containment_root=registry_root,
        create=False,
        classification="DERIVED_INDEX_PATH_SAFETY_STOP",
    )
    transaction_marker = derived / TRANSACTION_MARKER_FILENAME
    index_tmp = derived / INDEX_TRANSACTION_TEMP
    manifest_tmp = derived / MANIFEST_TRANSACTION_TEMP
    recovering = transaction_marker.exists()
    if recovering:
        assert_regular_single_link_file(transaction_marker, classification="DERIVED_INDEX_PATH_SAFETY_STOP")
        for temporary in (index_tmp, manifest_tmp):
            _safe_unlink(temporary, parent=derived, classification="DERIVED_INDEX_PATH_SAFETY_STOP")
    if failure_injection == "before_derived_transaction_marker":
        raise RegistryError(
            "DERIVED_INDEX_REGENERATION_FAILED_ENTRY_REMAINS_VALID_INDEX_STALE",
            "Injected failure before derived transaction marker",
        )
    if not recovering:
        write_bytes_fsync(
            transaction_marker,
            canonical_json_bytes(
                {
                    "design": "EXPLICIT_TRANSACTION_MARKER_TWO_FILE_REPLACEMENT",
                    "status": "DERIVED_INDEX_TRANSACTION_IN_PROGRESS",
                }
            ),
        )

    try:
        if recovering and failure_injection == "during_rebuild":
            raise RegistryError("DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED", "Injected recovery failure")
        records: list[DerivedIndexRecord] = []
        for subject_key, receipt_key in _entry_key_pairs(registry_root, authority=authority):
            verified = verify_entry(registry_root, subject_key, receipt_key, **authority)
            records.append(
                DerivedIndexRecord(
                    subject_key=subject_key,
                    receipt_key=receipt_key,
                    subject_phase_id=verified["subject_phase_id"],
                    receipt_id=verified["receipt_id"],
                    review_status=verified["review_status"],
                    accepted_classification=verified["accepted_classification"],
                    registry_schema_version=verified["registry_schema_version"],
                    registry_policy_version=verified["registry_policy_version"],
                    entry_seal_sha256=verified["entry_seal_sha256"],
                )
            )
        records.sort(key=lambda row: (row.subject_key, row.receipt_key))
        index_bytes = b"".join(canonical_json_bytes(record.to_dict()) for record in records)
        index_hash = sha256_bytes(index_bytes)
        manifest_bytes = canonical_json_bytes(
            {
                "entry_count": len(records),
                "index_filename": INDEX_FILENAME,
                "registry_index_sha256": index_hash,
                "registry_policy_version": policy["registry_policy_version"],
                "registry_schema_version": schema["registry_schema_version"],
                "status": "DERIVED_NON_AUTHORITATIVE_INDEX_VALID",
            }
        )
        write_bytes_fsync(index_tmp, index_bytes)
        if failure_injection == "after_index_file_write":
            raise RegistryError("DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED", "Injected failure after index write")
        write_bytes_fsync(manifest_tmp, manifest_bytes)
        if failure_injection in {"after_manifest_file_write", "index_regeneration"}:
            raise RegistryError("DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED", "Injected failure after manifest write")
        if failure_injection == "before_derived_activation":
            raise RegistryError("DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED", "Injected failure before derived activation")
        validate_safe_directory_chain(derived, containment_root=registry_root, create=False, classification="DERIVED_INDEX_PATH_SAFETY_STOP")
        os.replace(index_tmp, derived / INDEX_FILENAME)
        if failure_injection == "after_first_authoritative_derived_replacement":
            raise RegistryError("DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED", "Injected split derived replacement")
        os.replace(manifest_tmp, derived / INDEX_MANIFEST_FILENAME)
        _active_pair_is_valid(
            derived / INDEX_FILENAME,
            derived / INDEX_MANIFEST_FILENAME,
            expected_count=len(records),
            expected_hash=index_hash,
        )
        if failure_injection == "before_stale_marker_cleanup":
            raise RegistryError("DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED", "Injected failure before marker cleanup")
        _safe_unlink(derived / STALE_MARKER_FILENAME, parent=derived, classification="DERIVED_INDEX_PATH_SAFETY_STOP")
        _safe_unlink(transaction_marker, parent=derived, classification="DERIVED_INDEX_PATH_SAFETY_STOP")
        fsync_directory(derived)
        return {
            "status": "PASS",
            "classification": "DERIVED_INDEX_RECOVERY_COMPLETED" if recovering else "DERIVED_INDEX_VALID",
            "entry_count": len(records),
            "registry_index_sha256": index_hash,
        }
    except RegistryError:
        raise
    except Exception as exc:
        raise RegistryError(
            "DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED",
            "Derived index transaction interrupted; authoritative entries remain valid",
        ) from exc


def mark_index_stale(
    root: str | Path,
    classification: str,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expected_registry_root: str | Path | None = None,
    registry_mode: str = SYNTHETIC_MODE,
) -> None:
    authority = _authority_kwargs(
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        protected_roots=protected_roots,
        expected_registry_root=expected_registry_root,
        registry_mode=registry_mode,
    )
    registry_root = validate_registry_root_authority(root, create=False, **authority)
    derived = validate_safe_directory_chain(
        registry_root / "derived",
        containment_root=registry_root,
        create=False,
        classification="DERIVED_INDEX_PATH_SAFETY_STOP",
    )
    marker = canonical_json_bytes(
        {
            "classification": classification,
            "status": "DERIVED_INDEX_STALE_ENTRY_REMAINS_AUTHORITATIVE",
        }
    )
    path = derived / STALE_MARKER_FILENAME
    temporary = derived / f".{STALE_MARKER_FILENAME}.tmp"
    _safe_unlink(temporary, parent=derived, classification="DERIVED_INDEX_PATH_SAFETY_STOP")
    write_bytes_fsync(temporary, marker)
    os.replace(temporary, path)
    fsync_directory(derived)


def verify_index(
    root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expected_registry_root: str | Path | None = None,
    registry_mode: str = SYNTHETIC_MODE,
) -> dict[str, Any]:
    authority = _authority_kwargs(
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        protected_roots=protected_roots,
        expected_registry_root=expected_registry_root,
        registry_mode=registry_mode,
    )
    registry_root = validate_registry_root_authority(root, create=False, **authority)
    policy, schema = load_registry_configuration(registry_root, **authority)
    derived = validate_safe_directory_chain(
        registry_root / "derived",
        containment_root=registry_root,
        create=False,
        classification="DERIVED_INDEX_PATH_SAFETY_STOP",
    )
    transaction_marker = derived / TRANSACTION_MARKER_FILENAME
    if transaction_marker.exists():
        assert_regular_single_link_file(transaction_marker, classification="DERIVED_INDEX_PATH_SAFETY_STOP")
        return {
            "status": "STALE_OR_REBUILD_REQUIRED",
            "classification": "DERIVED_INDEX_TRANSACTION_INCOMPLETE_REBUILD_REQUIRED",
        }
    if (derived / STALE_MARKER_FILENAME).exists():
        assert_regular_single_link_file(derived / STALE_MARKER_FILENAME, classification="DERIVED_INDEX_PATH_SAFETY_STOP")
        return {"status": "STALE", "classification": "DERIVED_INDEX_STALE_ENTRY_REMAINS_AUTHORITATIVE"}
    index_path = derived / INDEX_FILENAME
    manifest_path = derived / INDEX_MANIFEST_FILENAME
    if not index_path.is_file() or not manifest_path.is_file():
        return {"status": "MISSING", "classification": "DERIVED_INDEX_MISSING"}
    assert_regular_single_link_file(index_path, classification="DERIVED_INDEX_PATH_SAFETY_STOP")
    assert_regular_single_link_file(manifest_path, classification="DERIVED_INDEX_PATH_SAFETY_STOP")
    lines = index_path.read_bytes().splitlines()
    try:
        records = [json.loads(line.decode("utf-8")) for line in lines if line]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "Derived index JSON is malformed") from exc
    if not isinstance(manifest, dict):
        raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "Derived index manifest must be an object")
    for row in records:
        if not isinstance(row, dict) or set(row) != INDEX_ROW_FIELDS:
            raise RegistryError(
                "DERIVED_INDEX_SEMANTIC_RECORD_MISMATCH_STOP",
                "Derived index row does not match the exact semantic schema",
            )
        if any(not isinstance(row[field], str) for field in INDEX_ROW_FIELDS):
            raise RegistryError(
                "DERIVED_INDEX_SEMANTIC_RECORD_MISMATCH_STOP",
                "Derived index semantic values must be strings",
            )
    keys = [(row["subject_key"], row["receipt_key"]) for row in records]
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "Derived index order or uniqueness failed")
    if manifest.get("registry_index_sha256") != sha256_file(index_path):
        raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "Derived index manifest hash mismatch")
    if manifest.get("entry_count") != len(records):
        raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "Derived index count mismatch")
    if (
        manifest.get("registry_schema_version") != schema["registry_schema_version"]
        or manifest.get("registry_policy_version") != policy["registry_policy_version"]
    ):
        raise RegistryError(
            "DERIVED_INDEX_SEMANTIC_RECORD_MISMATCH_STOP",
            "Derived index manifest versions do not match registry configuration",
        )
    for row in records:
        try:
            verified = verify_entry(registry_root, row["subject_key"], row["receipt_key"], **authority)
        except RegistryError as exc:
            raise RegistryError(
                "DERIVED_INDEX_SEMANTIC_RECORD_MISMATCH_STOP",
                "Derived index row does not resolve to a valid authoritative entry",
            ) from exc
        expected_row = DerivedIndexRecord(
            subject_key=verified["subject_key"],
            receipt_key=verified["receipt_key"],
            subject_phase_id=verified["subject_phase_id"],
            receipt_id=verified["receipt_id"],
            review_status=verified["review_status"],
            accepted_classification=verified["accepted_classification"],
            registry_schema_version=verified["registry_schema_version"],
            registry_policy_version=verified["registry_policy_version"],
            entry_seal_sha256=verified["entry_seal_sha256"],
        ).to_dict()
        if row != expected_row:
            raise RegistryError(
                "DERIVED_INDEX_SEMANTIC_RECORD_MISMATCH_STOP",
                "Derived index semantic row differs from its authoritative entry",
            )
    if keys != _entry_key_pairs(registry_root, authority=authority):
        return {"status": "STALE", "classification": "DERIVED_INDEX_ENTRY_SET_STALE"}
    return {"status": "PASS", "entry_count": len(records), "registry_index_sha256": manifest["registry_index_sha256"]}
