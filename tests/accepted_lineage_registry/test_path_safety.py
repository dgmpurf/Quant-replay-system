from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from quant_replay_system.accepted_lineage_registry.models import RegistryError
from quant_replay_system.accepted_lineage_registry.path_safety import (
    assert_no_filesystem_indirection,
    assert_regular_single_link_file,
    derive_receipt_key,
    derive_subject_key,
    ensure_descendant,
    reject_casefold_collisions,
    validate_logical_identifier,
)


def test_safe_key_derivation_matches_contract() -> None:
    assert derive_subject_key("SYNTHETIC-SUBJECT-001").startswith("SUBJ_")
    assert derive_receipt_key("SYNTHETIC-RECEIPT-001").startswith("RCPT_")
    assert len(derive_subject_key("SYNTHETIC-SUBJECT-001")) == 37
    assert len(derive_receipt_key("SYNTHETIC-RECEIPT-001")) == 37


@pytest.mark.parametrize(
    "value",
    ["", ".", "..", "a/b", "a\\b", "Z:\\synthetic-invalid", "CON", "NUL.txt", "trailing.", "trailing "],
)
def test_unsafe_logical_identifiers_are_rejected(value: str) -> None:
    with pytest.raises(RegistryError) as caught:
        validate_logical_identifier(value, label="test")
    assert caught.value.classification == "PATH_KEY_DERIVATION_OR_VALIDATION_STOP"


def test_unicode_normalization_drift_is_rejected() -> None:
    with pytest.raises(RegistryError, match="normalization drift"):
        derive_subject_key("Cafe\u0301")


def test_casefold_collision_is_rejected() -> None:
    with pytest.raises(RegistryError, match="Case-fold collision"):
        reject_casefold_collisions(["Synthetic-A", "synthetic-a"])


def test_path_escape_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(RegistryError, match="Path escape"):
        ensure_descendant(tmp_path.parent / "outside", tmp_path)


def test_symlink_path_component_is_rejected_without_platform_skip(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "root"
    root.mkdir()
    child = root / "child"
    child.mkdir()
    original_lstat = os.lstat

    def fake_lstat(path):
        result = original_lstat(path)
        if Path(path) == child:
            values = list(result)
            values[0] = stat.S_IFLNK | stat.S_IMODE(result.st_mode)
            return os.stat_result(values)
        return result

    monkeypatch.setattr(os, "lstat", fake_lstat)
    with pytest.raises(RegistryError):
        assert_no_filesystem_indirection(child)


def test_hardlink_guard_rejects_link_count_greater_than_one(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    linked = tmp_path / "linked.txt"
    source.write_text("synthetic", encoding="utf-8")
    os.link(source, linked)
    with pytest.raises(RegistryError, match="Hard-linked"):
        assert_regular_single_link_file(source)
