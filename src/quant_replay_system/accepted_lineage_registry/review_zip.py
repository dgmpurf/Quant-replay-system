"""Deterministic repo-external review ZIP generation and verification."""

from __future__ import annotations

import os
import re
import stat
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence

from .canonical import sha256_bytes, sha256_file
from .models import RegistryError
from .path_safety import (
    FILE_ATTRIBUTE_REPARSE_POINT,
    assert_regular_single_link_file,
    capture_directory_chain_snapshot,
    revalidate_directory_chain_snapshot,
    validate_review_output_root_authority,
    validate_review_zip_target,
    validate_safe_directory_chain,
)


FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


@dataclass(frozen=True)
class DeterministicZipResult:
    zip_name: str
    entry_count: int
    byte_length: int
    sha256: str
    compression_method: str
    lexical_order: bool
    round_trip_result: str
    zip_hash_registry_identity: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _safe_relative_name(value: str) -> str:
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if not normalized or normalized.startswith("/") or path.is_absolute():
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "ZIP entry path must be relative")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "ZIP traversal or dot segment rejected")
    if re.match(r"^[A-Za-z]:", normalized):
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "ZIP absolute drive path rejected")
    return path.as_posix()


def _file_identity(path: Path) -> tuple[int, int, int, int, int, int]:
    file_stat = os.lstat(path)
    return (
        int(file_stat.st_dev),
        int(file_stat.st_ino),
        int(file_stat.st_mode),
        int(getattr(file_stat, "st_nlink", 1)),
        int(file_stat.st_size),
        int(getattr(file_stat, "st_file_attributes", 0) or 0),
    )


def _revalidate_sources(sources: Sequence[tuple[str, Path, bytes, tuple[int, int, int, int, int, int]]]) -> None:
    for _, source, exact_bytes, identity in sources:
        assert_regular_single_link_file(source)
        if _file_identity(source) != identity or source.read_bytes() != exact_bytes:
            raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "Review source changed during packaging")


def _walk_review_files(root: Path) -> list[Path]:
    files: list[Path] = []
    stack = [root]
    while stack:
        directory = stack.pop()
        validate_safe_directory_chain(directory, containment_root=root, create=False)
        for child in sorted(directory.iterdir(), key=lambda item: item.name.casefold(), reverse=True):
            file_stat = os.lstat(child)
            attributes = int(getattr(file_stat, "st_file_attributes", 0) or 0)
            if stat.S_ISLNK(file_stat.st_mode) or attributes & FILE_ATTRIBUTE_REPARSE_POINT:
                raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "Indirect review-output descendant rejected")
            if stat.S_ISDIR(file_stat.st_mode):
                validate_safe_directory_chain(child, containment_root=root, create=False)
                stack.append(child)
            elif stat.S_ISREG(file_stat.st_mode):
                assert_regular_single_link_file(child)
                files.append(child)
            else:
                raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "Unsupported review-output descendant")
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def collect_relative_files(
    source_root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expected_review_output_root: str | Path | None = None,
) -> list[str]:
    root = validate_review_output_root_authority(
        source_root,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        protected_roots=protected_roots,
        expected_review_output_root=expected_review_output_root,
        create=False,
    )
    return [path.relative_to(root).as_posix() for path in _walk_review_files(root)]


def build_deterministic_review_zip(
    source_root: str | Path,
    zip_path: str | Path,
    relative_files: Iterable[str],
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expected_review_output_root: str | Path | None = None,
    expected_zip_path: str | Path | None = None,
) -> DeterministicZipResult:
    root = validate_review_output_root_authority(
        source_root,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        protected_roots=protected_roots,
        expected_review_output_root=expected_review_output_root,
        create=False,
    )
    target = validate_review_zip_target(
        zip_path,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        protected_roots=protected_roots,
        expected_zip_path=expected_zip_path,
    )
    names = [_safe_relative_name(value) for value in relative_files]
    if names != sorted(names):
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "ZIP entries must be supplied in lexical order")
    if len(names) != len(set(names)):
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "Duplicate ZIP entry rejected")
    sources: list[tuple[str, Path, bytes, tuple[int, int, int, int, int, int]]] = []
    directories: set[Path] = {root}
    for name in names:
        source = root / Path(*PurePosixPath(name).parts)
        try:
            source.relative_to(root)
        except ValueError as exc:
            raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "ZIP source escaped review root") from exc
        validate_safe_directory_chain(source.parent, containment_root=root, create=False)
        assert_regular_single_link_file(source)
        directories.add(source.parent)
        exact_bytes = source.read_bytes()
        identity = _file_identity(source)
        if len(exact_bytes) != identity[4]:
            raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "Review source changed while reading")
        sources.append((name, source, exact_bytes, identity))
    snapshot = capture_directory_chain_snapshot(tuple(directories), containment_root=root)
    if target.exists():
        raise RegistryError("PATH_KEY_DERIVATION_OR_VALIDATION_STOP", "Review ZIP already exists")
    temp = target.with_name(f".{target.name}.tmp")
    if temp.exists():
        assert_regular_single_link_file(temp)
        temp.unlink()
    revalidate_directory_chain_snapshot(tuple(directories), snapshot, containment_root=root)
    _revalidate_sources(sources)
    try:
        with zipfile.ZipFile(temp, mode="x", compression=zipfile.ZIP_STORED, strict_timestamps=True) as archive:
            for name, _, exact_bytes, _ in sources:
                info = zipfile.ZipInfo(filename=name, date_time=FIXED_ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_STORED
                info.create_system = 3
                info.external_attr = (0o100644 & 0xFFFF) << 16
                info.flag_bits = 0x800
                archive.writestr(info, exact_bytes)
        assert_regular_single_link_file(temp)
        with zipfile.ZipFile(temp, mode="r") as archive:
            actual_names = archive.namelist()
            if actual_names != names:
                raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "ZIP entry order or names changed")
            for name, _, exact_bytes, _ in sources:
                if archive.read(name) != exact_bytes:
                    raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "ZIP round-trip bytes differ")
                info = archive.getinfo(name)
                if info.date_time != FIXED_ZIP_TIMESTAMP or info.compress_type != zipfile.ZIP_STORED:
                    raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "ZIP metadata is not deterministic")
        revalidate_directory_chain_snapshot(tuple(directories), snapshot, containment_root=root)
        _revalidate_sources(sources)
        validate_review_zip_target(
            target,
            approved_admin_root=approved_admin_root,
            repository_root=repository_root,
            protected_roots=protected_roots,
            expected_zip_path=expected_zip_path,
        )
        os.replace(temp, target)
        assert_regular_single_link_file(target)
    except Exception:
        if temp.exists():
            assert_regular_single_link_file(temp)
            temp.unlink()
        raise
    return DeterministicZipResult(
        zip_name=target.name,
        entry_count=len(names),
        byte_length=target.stat().st_size,
        sha256=sha256_file(target),
        compression_method="ZIP_STORED",
        lexical_order=True,
        round_trip_result="PASS",
        zip_hash_registry_identity=False,
    )


def verify_review_zip_against_files(
    zip_path: str | Path,
    source_root: str | Path,
    relative_files: Iterable[str],
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expected_review_output_root: str | Path | None = None,
    expected_zip_path: str | Path | None = None,
) -> dict[str, object]:
    root = validate_review_output_root_authority(
        source_root,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        protected_roots=protected_roots,
        expected_review_output_root=expected_review_output_root,
        create=False,
    )
    target = validate_review_zip_target(
        zip_path,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        protected_roots=protected_roots,
        expected_zip_path=expected_zip_path,
    )
    assert_regular_single_link_file(target)
    names = sorted(_safe_relative_name(value) for value in relative_files)
    with zipfile.ZipFile(target, "r") as archive:
        if archive.namelist() != names:
            raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "ZIP file set or lexical order mismatch")
        hashes = {}
        for name in names:
            source = root / Path(*PurePosixPath(name).parts)
            validate_safe_directory_chain(source.parent, containment_root=root, create=False)
            assert_regular_single_link_file(source)
            exact_bytes = archive.read(name)
            if exact_bytes != source.read_bytes():
                raise RegistryError("REGISTRY_SCHEMA_OR_POLICY_MISMATCH_STOP", "ZIP source bytes mismatch")
            hashes[name] = sha256_bytes(exact_bytes)
    return {"status": "PASS", "entry_count": len(names), "entry_sha256": hashes}
