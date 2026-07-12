from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pytest

from quant_replay_system.accepted_lineage_registry.models import RegistryError
from quant_replay_system.accepted_lineage_registry import review_zip
from quant_replay_system.accepted_lineage_registry.review_zip import (
    FIXED_ZIP_TIMESTAMP,
    build_deterministic_review_zip,
    collect_relative_files,
    verify_review_zip_against_files,
)


def _source(tmp_path: Path) -> tuple[Path, Path, Path]:
    admin = tmp_path / "admin"
    repository = tmp_path / "repository"
    root = admin / "synthetic_review_source"
    repository.mkdir()
    (root / "nested").mkdir(parents=True)
    (root / "b.txt").write_bytes(b"b\n")
    (root / "nested" / "a.json").write_bytes(b'{"a":1}\n')
    return root, admin, repository


def _authority(root: Path, admin: Path, repository: Path) -> dict[str, Path]:
    return {
        "approved_admin_root": admin,
        "repository_root": repository,
        "expected_review_output_root": root,
    }


def test_repeated_review_zips_have_deterministic_bytes(tmp_path: Path) -> None:
    source, admin, repository = _source(tmp_path)
    authority = _authority(source, admin, repository)
    names = collect_relative_files(source, **authority)
    first = admin / "first.zip"
    second = admin / "second.zip"
    left = build_deterministic_review_zip(source, first, names, expected_zip_path=first, **authority)
    right = build_deterministic_review_zip(source, second, names, expected_zip_path=second, **authority)
    assert first.read_bytes() == second.read_bytes()
    assert left.sha256 == right.sha256
    assert left.zip_hash_registry_identity is False


def test_zip_entries_are_lexical_fixed_stored_and_root_relative(tmp_path: Path) -> None:
    source, admin, repository = _source(tmp_path)
    authority = _authority(source, admin, repository)
    names = collect_relative_files(source, **authority)
    target = admin / "review.zip"
    build_deterministic_review_zip(source, target, names, expected_zip_path=target, **authority)
    with zipfile.ZipFile(target) as archive:
        assert archive.namelist() == sorted(names)
        assert all(info.date_time == FIXED_ZIP_TIMESTAMP for info in archive.infolist())
        assert all(info.compress_type == zipfile.ZIP_STORED for info in archive.infolist())
        assert all(not info.filename.startswith(source.name + "/") for info in archive.infolist())


@pytest.mark.parametrize("names", [["../escape"], ["/absolute"], ["C:/private"], ["a", "a"]])
def test_zip_rejects_traversal_absolute_and_duplicates(tmp_path: Path, names: list[str]) -> None:
    source, admin, repository = _source(tmp_path)
    with pytest.raises(RegistryError):
        build_deterministic_review_zip(
            source,
            admin / "unsafe.zip",
            names,
            expected_zip_path=admin / "unsafe.zip",
            **_authority(source, admin, repository),
        )


def test_zip_rejects_unallowlisted_missing_file(tmp_path: Path) -> None:
    source, admin, repository = _source(tmp_path)
    with pytest.raises(RegistryError, match="missing"):
        build_deterministic_review_zip(
            source,
            admin / "missing.zip",
            ["missing.txt"],
            expected_zip_path=admin / "missing.zip",
            **_authority(source, admin, repository),
        )


def test_zip_rejects_hardlinked_source(tmp_path: Path) -> None:
    source, admin, repository = _source(tmp_path)
    os.link(source / "b.txt", source / "linked.txt")
    authority = _authority(source, admin, repository)
    with pytest.raises(RegistryError, match="Hard-linked"):
        collect_relative_files(source, **authority)


def test_zip_round_trip_hash_validation(tmp_path: Path) -> None:
    source, admin, repository = _source(tmp_path)
    authority = _authority(source, admin, repository)
    names = collect_relative_files(source, **authority)
    target = admin / "review.zip"
    build_deterministic_review_zip(source, target, names, expected_zip_path=target, **authority)
    result = verify_review_zip_against_files(
        target,
        source,
        names,
        expected_zip_path=target,
        **authority,
    )
    assert result["status"] == "PASS"
    assert result["entry_count"] == 2


def test_review_source_mutation_during_packaging_stops_before_zip_activation(tmp_path: Path, monkeypatch) -> None:
    source, admin, repository = _source(tmp_path)
    authority = _authority(source, admin, repository)
    names = collect_relative_files(source, **authority)
    target = admin / "review.zip"
    original = review_zip._revalidate_sources
    mutated = False

    def mutate_then_validate(sources):
        nonlocal mutated
        if not mutated:
            mutated = True
            (source / "b.txt").write_bytes(b"changed\n")
        return original(sources)

    monkeypatch.setattr(review_zip, "_revalidate_sources", mutate_then_validate)
    with pytest.raises(RegistryError, match="changed"):
        build_deterministic_review_zip(source, target, names, expected_zip_path=target, **authority)
    assert not target.exists()
