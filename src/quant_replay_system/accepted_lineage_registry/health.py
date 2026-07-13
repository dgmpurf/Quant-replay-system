"""Read-only synthetic registry health reporting."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

from .index import verify_index
from .locking import inspect_lock
from .models import (
    GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE,
    SYNTHETIC_MODE,
    RegistryError,
    RegistryHealthResult,
)
from .path_safety import platform_path_limitations, validate_registry_root_authority, validate_safe_directory_chain
from .verification import load_registry_configuration, verify_entry


def registry_health(
    root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expected_registry_root: str | Path | None = None,
    registry_mode: str = SYNTHETIC_MODE,
) -> RegistryHealthResult:
    authority = {
        "approved_admin_root": approved_admin_root,
        "repository_root": repository_root,
        "protected_roots": protected_roots,
        "expected_registry_root": expected_registry_root,
        "registry_mode": registry_mode,
    }
    registry_root = validate_registry_root_authority(root, create=False, **authority)
    policy, schema = load_registry_configuration(registry_root, **authority)
    warnings: list[str] = []
    privacy_warnings: list[str] = []
    limitations = list(platform_path_limitations())
    if os.name == "nt":
        limitations.append("PLATFORM_LIMITATION_DIRECTORY_FSYNC_NOT_AVAILABLE")
    entry_pairs: list[tuple[str, str]] = []
    entries_root = validate_safe_directory_chain(registry_root / "entries", containment_root=registry_root, create=False)
    for subject_dir in sorted(entries_root.iterdir(), key=lambda item: item.name):
        if not subject_dir.is_dir():
            warnings.append("UNEXPECTED_ENTRY_CHILD")
            continue
        try:
            validate_safe_directory_chain(subject_dir, containment_root=registry_root, create=False)
        except RegistryError as exc:
            warnings.append(exc.classification)
            continue
        for receipt_dir in sorted(subject_dir.iterdir(), key=lambda item: item.name):
            if receipt_dir.is_dir():
                entry_pairs.append((subject_dir.name, receipt_dir.name))
            else:
                warnings.append("UNEXPECTED_SUBJECT_CHILD")
    entry_status = "PASS"
    for subject_key, receipt_key in entry_pairs:
        try:
            verify_entry(registry_root, subject_key, receipt_key, **authority)
        except RegistryError as exc:
            entry_status = "FAIL"
            warnings.append(exc.classification)
    try:
        index_result = verify_index(registry_root, **authority)
        index_status = str(index_result["status"])
    except RegistryError as exc:
        index_status = "PATH_SAFETY_STOP" if exc.classification == "DERIVED_INDEX_PATH_SAFETY_STOP" else "FAIL"
        warnings.append(exc.classification)
    stale = index_status in {"STALE", "STALE_OR_REBUILD_REQUIRED"}
    orphan_count = 0
    try:
        staging = validate_safe_directory_chain(registry_root / ".staging", containment_root=registry_root, create=False)
        orphan_count = sum(1 for item in staging.iterdir() if item.is_dir())
    except RegistryError as exc:
        warnings.append(exc.classification)
    if orphan_count:
        warnings.append("ORPHAN_TEMPORARY_DIRECTORIES_PRESENT")
    if policy.get("registry_mode") not in {
        SYNTHETIC_MODE,
        GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE,
    }:
        privacy_warnings.append("NON_SYNTHETIC_MODE")
    return RegistryHealthResult(
        registry_mode=str(policy["registry_mode"]),
        registry_schema_version=str(schema["registry_schema_version"]),
        registry_policy_version=str(policy["registry_policy_version"]),
        root_safety="PASS",
        lock_status=inspect_lock(registry_root, **authority),
        authoritative_entry_count=len(entry_pairs),
        entry_verification_status=entry_status,
        derived_index_status=index_status,
        stale_index_status=stale,
        orphan_temporary_directories=orphan_count,
        path_safety_warnings=tuple(sorted(set(warnings))),
        platform_limitations=tuple(sorted(set(limitations))),
        privacy_warnings=tuple(sorted(set(privacy_warnings))),
    )
