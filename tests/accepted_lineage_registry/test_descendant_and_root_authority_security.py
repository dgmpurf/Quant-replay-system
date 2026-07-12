from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import authority_kwargs, materialization_kwargs
from quant_replay_system.accepted_lineage_registry.models import RegistryError
from quant_replay_system.accepted_lineage_registry.path_safety import derive_subject_key
from quant_replay_system.accepted_lineage_registry.review_zip import collect_relative_files
from quant_replay_system.accepted_lineage_registry.transaction import initialize_synthetic_registry, materialize_synthetic


def _replace_empty_directory_with_symlink(path: Path, outside: Path) -> None:
    outside.mkdir(parents=True)
    path.rmdir()
    os.symlink(outside, path, target_is_directory=True)


def _materialize(material, *, root: Path | None = None, **overrides):
    kwargs = materialization_kwargs(material)
    kwargs.update(overrides)
    return materialize_synthetic(
        root or material["registry_root"],
        **kwargs,
        materialization_authorization_id="SYNTHETIC-PATH-SECURITY-AUTH-001",
        operation_id="path-security-test",
    )


@pytest.mark.parametrize("directory_name", ["entries", ".staging", "derived"])
def test_core_descendant_symlink_escape_stops_before_external_write(
    tmp_path: Path,
    synthetic_material,
    directory_name: str,
) -> None:
    root = initialize_synthetic_registry(synthetic_material["registry_root"], **authority_kwargs(synthetic_material))
    outside = tmp_path / f"outside-{directory_name.replace('.', 'dot')}"
    _replace_empty_directory_with_symlink(root / directory_name, outside)
    with pytest.raises(RegistryError) as caught:
        _materialize(synthetic_material)
    expected = "DERIVED_INDEX_PATH_SAFETY_STOP" if directory_name == "derived" else "PATH_KEY_DERIVATION_OR_VALIDATION_STOP"
    assert caught.value.classification == expected
    assert list(outside.iterdir()) == []


def test_target_subject_directory_symlink_stops_before_external_write(tmp_path: Path, synthetic_material) -> None:
    root = initialize_synthetic_registry(synthetic_material["registry_root"], **authority_kwargs(synthetic_material))
    subject_key = derive_subject_key(synthetic_material["payload"]["subject_phase_id"])
    outside = tmp_path / "outside-subject"
    outside.mkdir()
    os.symlink(outside, root / "entries" / subject_key, target_is_directory=True)
    with pytest.raises(RegistryError) as caught:
        _materialize(synthetic_material)
    assert caught.value.classification == "PATH_KEY_DERIVATION_OR_VALIDATION_STOP"
    assert list(outside.iterdir()) == []


def test_target_receipt_path_symlink_stops_before_external_write(tmp_path: Path, synthetic_material) -> None:
    root = initialize_synthetic_registry(synthetic_material["registry_root"], **authority_kwargs(synthetic_material))
    subject_key = derive_subject_key(synthetic_material["payload"]["subject_phase_id"])
    from quant_replay_system.accepted_lineage_registry.path_safety import derive_receipt_key

    receipt_key = derive_receipt_key(synthetic_material["payload"]["receipt_id"])
    subject = root / "entries" / subject_key
    subject.mkdir()
    outside = tmp_path / "outside-receipt"
    outside.mkdir()
    os.symlink(outside, subject / receipt_key, target_is_directory=True)
    with pytest.raises(RegistryError) as caught:
        _materialize(synthetic_material)
    assert caught.value.classification == "PATH_KEY_DERIVATION_OR_VALIDATION_STOP"
    assert list(outside.iterdir()) == []


def test_repository_internal_synthetic_root_is_rejected_before_creation(synthetic_material) -> None:
    unsafe = synthetic_material["repository_root"] / "synthetic_registry"
    with pytest.raises(RegistryError) as caught:
        _materialize(synthetic_material, root=unsafe, expected_registry_root=unsafe)
    assert caught.value.classification == "REGISTRY_ROOT_NOT_REPO_EXTERNAL_STOP"
    assert not unsafe.exists()


def test_protected_synthetic_root_is_rejected_before_creation(synthetic_material) -> None:
    protected = synthetic_material["approved_admin_root"] / "immutable_execution_packet"
    protected.mkdir()
    unsafe = protected / "synthetic_registry"
    with pytest.raises(RegistryError) as caught:
        _materialize(
            synthetic_material,
            root=unsafe,
            expected_registry_root=unsafe,
            protected_roots=(protected,),
        )
    assert caught.value.classification == "PROTECTED_OR_INPUT_ROOT_TARGET_STOP"
    assert not unsafe.exists()


def test_sibling_outside_approved_admin_root_is_rejected(synthetic_material) -> None:
    unsafe = synthetic_material["approved_admin_root"].parent / "outside-admin" / "synthetic_registry"
    with pytest.raises(RegistryError) as caught:
        _materialize(synthetic_material, root=unsafe, expected_registry_root=unsafe)
    assert caught.value.classification == "REGISTRY_ROOT_OUTSIDE_APPROVED_ADMIN_ROOT_STOP"
    assert not unsafe.exists()


def test_exact_registry_root_mismatch_is_rejected(synthetic_material) -> None:
    alternate = synthetic_material["approved_admin_root"] / "alternate_synthetic_registry"
    with pytest.raises(RegistryError) as caught:
        _materialize(synthetic_material, root=alternate)
    assert caught.value.classification == "REGISTRY_ROOT_OUTSIDE_APPROVED_ADMIN_ROOT_STOP"
    assert not alternate.exists()


def test_review_output_descendant_symlink_is_rejected(tmp_path: Path) -> None:
    admin = tmp_path / "admin"
    repository = tmp_path / "repository"
    review = admin / "synthetic_review"
    outside = tmp_path / "outside-review"
    repository.mkdir()
    review.mkdir(parents=True)
    outside.mkdir()
    (outside / "do-not-read.txt").write_text("outside", encoding="utf-8")
    os.symlink(outside, review / "indirect", target_is_directory=True)
    with pytest.raises(RegistryError) as caught:
        collect_relative_files(
            review,
            approved_admin_root=admin,
            repository_root=repository,
            expected_review_output_root=review,
        )
    assert caught.value.classification == "PATH_KEY_DERIVATION_OR_VALIDATION_STOP"
    assert sorted(path.name for path in outside.iterdir()) == ["do-not-read.txt"]


def test_repository_internal_review_output_is_rejected(tmp_path: Path) -> None:
    admin = tmp_path / "admin"
    repository = tmp_path / "repository"
    unsafe = repository / "synthetic_review"
    admin.mkdir()
    unsafe.mkdir(parents=True)
    with pytest.raises(RegistryError) as caught:
        collect_relative_files(
            unsafe,
            approved_admin_root=admin,
            repository_root=repository,
            expected_review_output_root=unsafe,
        )
    assert caught.value.classification == "REVIEW_OUTPUT_ROOT_NOT_REPO_EXTERNAL_STOP"
