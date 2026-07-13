"""Opaque identifiers, root authority, and descendant filesystem guards."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence

from .models import (
    GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE,
    LIVE_MODE_STOP,
    SYNTHETIC_MODE,
    RegistryError,
)


SUBJECT_KEY_RE = re.compile(r"^SUBJ_[0-9a-f]{32}$")
RECEIPT_KEY_RE = re.compile(r"^RCPT_[0-9a-f]{32}$")
WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
FILE_ATTRIBUTE_REPARSE_POINT = 0x400


@dataclass(frozen=True)
class PathSafetySnapshot:
    logical_root_name: str
    signatures: tuple[tuple[int, int, int, int], ...]
    platform_limitations: tuple[str, ...]


@dataclass(frozen=True)
class DirectoryChainSnapshot:
    containment_name: str
    signatures: tuple[tuple[str, int, int, int, int, int], ...]
    platform_limitations: tuple[str, ...]


def _absolute(path: str | Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _lexists(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


def _resolved(path: Path, *, classification: str) -> Path:
    try:
        return path.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise RegistryError(classification, "Path resolution failed safely") from exc


def _is_within(path: Path, parent: Path, *, strict: bool = False) -> bool:
    try:
        relative = path.relative_to(parent)
    except ValueError:
        return False
    return not strict or bool(relative.parts)


def _attributes(file_stat: os.stat_result) -> int:
    return int(getattr(file_stat, "st_file_attributes", 0) or 0)


def _file_identity(file_stat: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        int(file_stat.st_dev),
        int(file_stat.st_ino),
        int(file_stat.st_mode),
        int(getattr(file_stat, "st_nlink", 1)),
        _attributes(file_stat),
    )


def platform_path_limitations() -> tuple[str, ...]:
    limitations: list[str] = []
    if not hasattr(os, "O_NOFOLLOW"):
        limitations.append("PLATFORM_LIMITATION_O_NOFOLLOW_NOT_AVAILABLE")
    if os.name == "nt":
        limitations.append("PLATFORM_LIMITATION_DIRECTORY_HANDLE_RELATIVE_RENAME_NOT_AVAILABLE")
    else:
        limitations.append("PLATFORM_LIMITATION_WINDOWS_REPARSE_ATTRIBUTES_NOT_AVAILABLE")
    return tuple(sorted(set(limitations)))


def validate_logical_identifier(value: str, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", f"{label} is empty")
    if value != unicodedata.normalize("NFC", value):
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", f"{label} has Unicode-normalization drift")
    if value in {".", ".."} or "/" in value or "\\" in value:
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", f"{label} contains path syntax")
    if value[-1] in {".", " "}:
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", f"{label} has a trailing dot or space")
    if re.match(r"^[A-Za-z]:", value) or Path(value).is_absolute():
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", f"{label} resembles an absolute path")
    base = value.split(".", 1)[0].upper()
    if base in WINDOWS_RESERVED:
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", f"{label} is a reserved device name")
    if any(ord(character) < 32 for character in value):
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", f"{label} contains a control character")
    return value


def validate_relative_artifact_path(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise RegistryError("SUBJECT_ARTIFACT_PATH_UNSAFE_STOP", "Artifact relative_path is empty")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise RegistryError("SUBJECT_ARTIFACT_PATH_UNSAFE_STOP", "Artifact relative_path is not UTF-8 encodable") from exc
    if value != unicodedata.normalize("NFC", value):
        raise RegistryError("SUBJECT_ARTIFACT_PATH_UNSAFE_STOP", "Artifact relative_path is not NFC")
    if "\\" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise RegistryError("SUBJECT_ARTIFACT_PATH_UNSAFE_STOP", "Artifact relative_path is rooted or uses backslashes")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise RegistryError("SUBJECT_ARTIFACT_PATH_UNSAFE_STOP", "Artifact relative_path contains an unsafe segment")
    for part in path.parts:
        if part[-1] in {".", " "} or any(ord(character) < 32 for character in part):
            raise RegistryError("SUBJECT_ARTIFACT_PATH_UNSAFE_STOP", "Artifact path segment is unsafe")
        if part.split(".", 1)[0].upper() in WINDOWS_RESERVED:
            raise RegistryError("SUBJECT_ARTIFACT_PATH_UNSAFE_STOP", "Artifact path uses a reserved device name")
    return path.as_posix()


def _opaque_key(prefix: str, value: str, *, label: str) -> str:
    normalized = validate_logical_identifier(value, label=label)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"{prefix}{digest[:32]}"


def derive_subject_key(subject_phase_id: str) -> str:
    return _opaque_key("SUBJ_", subject_phase_id, label="subject_phase_id")


def derive_receipt_key(receipt_id: str) -> str:
    return _opaque_key("RCPT_", receipt_id, label="receipt_id")


def validate_subject_key(value: str) -> str:
    if not SUBJECT_KEY_RE.fullmatch(value):
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "subject_key is invalid")
    return value


def validate_receipt_key(value: str) -> str:
    if not RECEIPT_KEY_RE.fullmatch(value):
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "receipt_key is invalid")
    return value


def reject_casefold_collisions(values: Iterable[str], *, classification: str = "PATH_KEY_DERIVATION_OR_VALIDATION_STOP") -> None:
    seen: dict[str, str] = {}
    for value in values:
        folded = value.casefold()
        if folded in seen:
            raise RegistryError(classification, "Case-fold collision or duplicate path detected")
        seen[folded] = value


def _existing_chain(path: Path) -> list[Path]:
    absolute = _absolute(path)
    chain: list[Path] = []
    current = absolute
    while True:
        if _lexists(current):
            chain.append(current)
        if current.parent == current:
            break
        current = current.parent
    chain.reverse()
    return chain


def assert_no_filesystem_indirection(
    path: str | Path,
    *,
    classification: str = "PATH_KEY_DERIVATION_OR_VALIDATION_STOP",
) -> tuple[str, ...]:
    for component in _existing_chain(Path(path)):
        file_stat = os.lstat(component)
        if stat.S_ISLNK(file_stat.st_mode):
            raise RegistryError(classification, "Symbolic-link path component rejected")
        if _attributes(file_stat) & FILE_ATTRIBUTE_REPARSE_POINT:
            raise RegistryError(classification, "Reparse point or junction rejected")
    return platform_path_limitations()


def _assert_safe_directory(
    path: Path,
    *,
    classification: str,
    expected_device: int | None = None,
) -> os.stat_result:
    if not _lexists(path):
        raise RegistryError(classification, "Required directory is missing")
    file_stat = os.lstat(path)
    if stat.S_ISLNK(file_stat.st_mode) or _attributes(file_stat) & FILE_ATTRIBUTE_REPARSE_POINT:
        raise RegistryError(classification, "Indirect directory component rejected")
    if not stat.S_ISDIR(file_stat.st_mode):
        raise RegistryError(classification, "Required path component is not a directory")
    if expected_device is not None and int(file_stat.st_dev) != expected_device:
        raise RegistryError(classification, "Filesystem device drift rejected")
    return file_stat


def ensure_descendant(path: str | Path, parent: str | Path, *, strict: bool = False) -> Path:
    child = _absolute(path)
    root = _absolute(parent)
    if not _is_within(child, root, strict=strict):
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "Path escape rejected")
    return child


def validate_safe_directory_chain(
    path: str | Path,
    *,
    containment_root: str | Path,
    create: bool,
    classification: str = "PATH_KEY_DERIVATION_OR_VALIDATION_STOP",
) -> Path:
    target = _absolute(path)
    containment = _absolute(containment_root)
    if not _is_within(target, containment):
        raise RegistryError(classification, "Directory-chain containment failed")
    assert_no_filesystem_indirection(containment, classification=classification)
    containment_stat = _assert_safe_directory(containment, classification=classification)
    expected_device = int(containment_stat.st_dev)
    resolved_containment = _resolved(containment, classification=classification)
    current = containment
    relative = target.relative_to(containment)
    for part in relative.parts:
        validate_logical_identifier(part, label="directory_component")
        child = current / part
        if not _lexists(child):
            if not create:
                raise RegistryError(classification, "Required directory-chain component is missing")
            try:
                os.mkdir(child)
            except OSError as exc:
                raise RegistryError(classification, "Directory-chain component creation failed") from exc
        _assert_safe_directory(child, classification=classification, expected_device=expected_device)
        resolved_child = _resolved(child, classification=classification)
        if not _is_within(resolved_child, resolved_containment):
            raise RegistryError(classification, "Resolved directory escaped containment")
        current = child
    return target


def validate_nearest_existing_chain(
    path: str | Path,
    *,
    containment_root: str | Path,
    classification: str,
) -> Path:
    target = _absolute(path)
    containment = _absolute(containment_root)
    if not _is_within(target, containment):
        raise RegistryError(classification, "Path is outside the approved containment root")
    current = target
    while not _lexists(current):
        if current == containment:
            break
        current = current.parent
    validate_safe_directory_chain(current, containment_root=containment, create=False, classification=classification)
    resolved_containment = _resolved(containment, classification=classification)
    resolved_target = _resolved(target, classification=classification)
    if not _is_within(resolved_target, resolved_containment):
        raise RegistryError(classification, "Resolved future path escaped containment")
    return target


def _default_protected_roots(approved_admin_root: Path, repository_root: Path) -> tuple[Path, ...]:
    return (
        repository_root / "data" / "raw",
        repository_root / "data" / "processed",
        repository_root / "data" / "cache",
        repository_root / "outputs",
        approved_admin_root / "accepted_lineage_registry_v0_1",
    )


def _reject_protected_target(target: Path, protected_roots: Sequence[str | Path], *, classification: str) -> None:
    for protected in protected_roots:
        protected_path = _absolute(protected)
        if _is_within(target, protected_path) or target == protected_path:
            raise RegistryError(classification, "Protected or immutable input root target rejected")


def validate_registry_root_authority(
    registry_root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expected_registry_root: str | Path | None = None,
    registry_mode: str = SYNTHETIC_MODE,
    create: bool = False,
) -> Path:
    admin = _absolute(approved_admin_root)
    repository = _absolute(repository_root)
    root = _absolute(registry_root)
    assert_no_filesystem_indirection(admin, classification="REGISTRY_ROOT_OUTSIDE_APPROVED_ADMIN_ROOT_STOP")
    _assert_safe_directory(admin, classification="REGISTRY_ROOT_OUTSIDE_APPROVED_ADMIN_ROOT_STOP")
    assert_no_filesystem_indirection(repository, classification="REGISTRY_ROOT_NOT_REPO_EXTERNAL_STOP")
    _assert_safe_directory(repository, classification="REGISTRY_ROOT_NOT_REPO_EXTERNAL_STOP")
    if _is_within(root, repository) or root == repository:
        raise RegistryError("REGISTRY_ROOT_NOT_REPO_EXTERNAL_STOP", "Registry root is inside the repository")
    if not _is_within(root, admin, strict=True):
        raise RegistryError("REGISTRY_ROOT_OUTSIDE_APPROVED_ADMIN_ROOT_STOP", "Registry root is not below approved admin root")
    root_name = root.name.casefold()
    if registry_mode == SYNTHETIC_MODE:
        if root_name == "accepted_lineage_registry_v0_1" or "synthetic" not in root_name:
            raise RegistryError(LIVE_MODE_STOP, "Only an explicitly synthetic registry root is authorized")
    elif registry_mode == GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE:
        if expected_registry_root is None or root_name == "accepted_lineage_registry_v0_1" or "candidate" not in root_name:
            raise RegistryError(
                "REAL_CANDIDATE_MATERIALIZATION_ROOT_UNSAFE_STOP",
                "Governed candidate mode requires an exact, explicitly candidate root",
            )
    else:
        raise RegistryError(LIVE_MODE_STOP, "Requested registry mode is not authorized")
    if expected_registry_root is not None and os.path.normcase(os.fspath(root)) != os.path.normcase(os.fspath(_absolute(expected_registry_root))):
        raise RegistryError("REGISTRY_ROOT_OUTSIDE_APPROVED_ADMIN_ROOT_STOP", "Registry root differs from exact approved root")
    _reject_protected_target(
        root,
        (*_default_protected_roots(admin, repository), *protected_roots),
        classification="PROTECTED_OR_INPUT_ROOT_TARGET_STOP",
    )
    if create:
        validate_safe_directory_chain(root, containment_root=admin, create=True, classification="PATH_KEY_DERIVATION_OR_VALIDATION_STOP")
    else:
        validate_nearest_existing_chain(root, containment_root=admin, classification="PATH_KEY_DERIVATION_OR_VALIDATION_STOP")
    return root


def validate_review_output_root_authority(
    review_output_root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expected_review_output_root: str | Path | None = None,
    create: bool = False,
) -> Path:
    admin = _absolute(approved_admin_root)
    repository = _absolute(repository_root)
    output = _absolute(review_output_root)
    assert_no_filesystem_indirection(admin, classification="REVIEW_OUTPUT_ROOT_NOT_REPO_EXTERNAL_STOP")
    _assert_safe_directory(admin, classification="REVIEW_OUTPUT_ROOT_NOT_REPO_EXTERNAL_STOP")
    assert_no_filesystem_indirection(repository, classification="REVIEW_OUTPUT_ROOT_NOT_REPO_EXTERNAL_STOP")
    _assert_safe_directory(repository, classification="REVIEW_OUTPUT_ROOT_NOT_REPO_EXTERNAL_STOP")
    if not _is_within(output, admin, strict=True) or _is_within(output, repository) or output == repository:
        raise RegistryError("REVIEW_OUTPUT_ROOT_NOT_REPO_EXTERNAL_STOP", "Review output is not repo-external under approved admin root")
    if expected_review_output_root is not None and os.path.normcase(os.fspath(output)) != os.path.normcase(os.fspath(_absolute(expected_review_output_root))):
        raise RegistryError("REVIEW_OUTPUT_ROOT_NOT_REPO_EXTERNAL_STOP", "Review output differs from exact approved root")
    _reject_protected_target(
        output,
        (*_default_protected_roots(admin, repository), *protected_roots),
        classification="PROTECTED_OR_INPUT_ROOT_TARGET_STOP",
    )
    if create:
        validate_safe_directory_chain(output, containment_root=admin, create=True, classification="PATH_KEY_DERIVATION_OR_VALIDATION_STOP")
    else:
        validate_nearest_existing_chain(output, containment_root=admin, classification="PATH_KEY_DERIVATION_OR_VALIDATION_STOP")
    return output


def validate_review_zip_target(
    zip_path: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expected_zip_path: str | Path | None = None,
) -> Path:
    admin = _absolute(approved_admin_root)
    repository = _absolute(repository_root)
    target = _absolute(zip_path)
    if not _is_within(target, admin, strict=True) or _is_within(target, repository):
        raise RegistryError("REVIEW_OUTPUT_ROOT_NOT_REPO_EXTERNAL_STOP", "Review ZIP target is outside approved admin root")
    if expected_zip_path is not None and os.path.normcase(os.fspath(target)) != os.path.normcase(os.fspath(_absolute(expected_zip_path))):
        raise RegistryError("REVIEW_OUTPUT_ROOT_NOT_REPO_EXTERNAL_STOP", "Review ZIP differs from exact approved target")
    _reject_protected_target(target, protected_roots, classification="PROTECTED_OR_INPUT_ROOT_TARGET_STOP")
    validate_safe_directory_chain(target.parent, containment_root=admin, create=False, classification="PATH_KEY_DERIVATION_OR_VALIDATION_STOP")
    return target


def validate_external_input_path(
    path: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    registry_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expect_directory: bool,
    missing_classification: str,
) -> Path:
    admin = _absolute(approved_admin_root)
    repository = _absolute(repository_root)
    registry = _absolute(registry_root)
    target = _absolute(path)
    if not _is_within(target, admin, strict=True) or _is_within(target, repository) or _is_within(target, registry):
        raise RegistryError("PROTECTED_OR_INPUT_ROOT_TARGET_STOP", "Subject input path is outside its approved external surface")
    _reject_protected_target(target, protected_roots, classification="PROTECTED_OR_INPUT_ROOT_TARGET_STOP")
    if not _lexists(target):
        raise RegistryError(missing_classification, "Required subject input is missing")
    validate_safe_directory_chain(target if expect_directory else target.parent, containment_root=admin, create=False)
    file_stat = os.lstat(target)
    if stat.S_ISLNK(file_stat.st_mode) or _attributes(file_stat) & FILE_ATTRIBUTE_REPARSE_POINT:
        raise RegistryError("SUBJECT_PACKET_NOT_REGULAR_STOP" if not expect_directory else "SUBJECT_ARTIFACT_PATH_UNSAFE_STOP", "Indirect subject input rejected")
    if expect_directory and not stat.S_ISDIR(file_stat.st_mode):
        raise RegistryError("SUBJECT_ARTIFACT_PATH_UNSAFE_STOP", "Subject artifact root is not a directory")
    if not expect_directory and not stat.S_ISREG(file_stat.st_mode):
        raise RegistryError("SUBJECT_PACKET_NOT_REGULAR_STOP", "Subject packet is not a regular file")
    return target


def assert_synthetic_registry_root(path: str | Path) -> Path:
    root = _absolute(path)
    if not root.is_absolute():
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "Registry root must be absolute")
    if root.name.casefold() == "accepted_lineage_registry_v0_1" or "synthetic" not in root.name.casefold():
        raise RegistryError(LIVE_MODE_STOP, "Only an obviously synthetic registry root is authorized")
    assert_no_filesystem_indirection(root)
    return root


def assert_registry_root_mode(path: str | Path, *, registry_mode: str) -> Path:
    if registry_mode == SYNTHETIC_MODE:
        return assert_synthetic_registry_root(path)
    root = _absolute(path)
    if registry_mode != GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE:
        raise RegistryError(LIVE_MODE_STOP, "Requested registry mode is not authorized")
    if root.name.casefold() == "accepted_lineage_registry_v0_1" or "candidate" not in root.name.casefold():
        raise RegistryError(
            "REAL_CANDIDATE_MATERIALIZATION_ROOT_UNSAFE_STOP",
            "Governed candidate root name is not explicit",
        )
    assert_no_filesystem_indirection(root)
    return root


def assert_regular_single_link_file(
    path: str | Path,
    *,
    classification: str = "PATH_KEY_DERIVATION_OR_VALIDATION_STOP",
) -> None:
    target = Path(path)
    if not _lexists(target):
        raise RegistryError(classification, "Required regular file is missing")
    file_stat = os.lstat(target)
    if stat.S_ISLNK(file_stat.st_mode) or _attributes(file_stat) & FILE_ATTRIBUTE_REPARSE_POINT:
        raise RegistryError(classification, "Indirect authoritative file rejected")
    if not stat.S_ISREG(file_stat.st_mode):
        raise RegistryError(classification, "Authoritative file is not regular")
    link_count = getattr(file_stat, "st_nlink", None)
    if link_count is not None and link_count != 1:
        raise RegistryError(classification, "Hard-linked authoritative file rejected")


def nearest_existing(path: str | Path) -> Path:
    current = _absolute(path)
    while not _lexists(current):
        if current.parent == current:
            raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "No existing ancestor found")
        current = current.parent
    return current


def same_filesystem(left: str | Path, right: str | Path) -> bool:
    return os.stat(nearest_existing(left)).st_dev == os.stat(nearest_existing(right)).st_dev


def capture_path_snapshot(
    root: str | Path,
    *,
    registry_mode: str = SYNTHETIC_MODE,
) -> PathSafetySnapshot:
    safe_root = assert_registry_root_mode(root, registry_mode=registry_mode)
    signatures: list[tuple[int, int, int, int]] = []
    for component in _existing_chain(safe_root):
        file_stat = os.lstat(component)
        signatures.append((int(file_stat.st_dev), int(file_stat.st_ino), int(file_stat.st_mode), _attributes(file_stat)))
    return PathSafetySnapshot(
        logical_root_name=safe_root.name,
        signatures=tuple(signatures),
        platform_limitations=platform_path_limitations(),
    )


def revalidate_path_snapshot(
    root: str | Path,
    snapshot: PathSafetySnapshot,
    *,
    registry_mode: str = SYNTHETIC_MODE,
) -> None:
    current = (
        capture_path_snapshot(root)
        if registry_mode == SYNTHETIC_MODE
        else capture_path_snapshot(root, registry_mode=registry_mode)
    )
    if current.logical_root_name != snapshot.logical_root_name or current.signatures != snapshot.signatures:
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "TOCTOU root revalidation failed")


def capture_directory_chain_snapshot(
    paths: Sequence[str | Path],
    *,
    containment_root: str | Path,
    classification: str = "PATH_KEY_DERIVATION_OR_VALIDATION_STOP",
) -> DirectoryChainSnapshot:
    containment = _absolute(containment_root)
    signatures: list[tuple[str, int, int, int, int, int]] = []
    seen: set[str] = set()
    for value in paths:
        target = validate_safe_directory_chain(value, containment_root=containment, create=False, classification=classification)
        current = containment
        candidates = [containment]
        for part in target.relative_to(containment).parts:
            current = current / part
            candidates.append(current)
        for candidate in candidates:
            relative = candidate.relative_to(containment).as_posix() or "."
            if relative in seen:
                continue
            seen.add(relative)
            identity = _file_identity(os.lstat(candidate))
            signatures.append((relative, *identity))
    signatures.sort(key=lambda item: item[0])
    return DirectoryChainSnapshot(containment.name, tuple(signatures), platform_path_limitations())


def revalidate_directory_chain_snapshot(
    paths: Sequence[str | Path],
    snapshot: DirectoryChainSnapshot,
    *,
    containment_root: str | Path,
    classification: str = "PATH_KEY_DERIVATION_OR_VALIDATION_STOP",
) -> None:
    current = capture_directory_chain_snapshot(paths, containment_root=containment_root, classification=classification)
    if current.containment_name != snapshot.containment_name or current.signatures != snapshot.signatures:
        raise RegistryError(classification, "Descendant directory-chain TOCTOU revalidation failed")
