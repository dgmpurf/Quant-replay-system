from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import make_synthetic_material, materialization_kwargs
from quant_replay_system.accepted_lineage_registry import transaction
from quant_replay_system.accepted_lineage_registry.models import RegistryError
from quant_replay_system.accepted_lineage_registry.transaction import materialize_synthetic


def _materialize(material, **overrides):
    kwargs = materialization_kwargs(material)
    kwargs.update(overrides)
    return materialize_synthetic(
        material["registry_root"],
        **kwargs,
        materialization_authorization_id="SYNTHETIC-SUBJECT-SECURITY-AUTH-001",
        operation_id="subject-security-test",
    )


def test_actual_subject_packet_and_artifact_bytes_are_verified_and_recorded(tmp_path: Path) -> None:
    material = make_synthetic_material(tmp_path)
    result = _materialize(material)
    import json

    runtime = json.loads(
        (
            material["registry_root"]
            / "entries"
            / result.subject_key
            / result.receipt_key
            / "entry_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert runtime["actual_subject_bytes_verified"] is True
    assert runtime["subject_packet_sha256"] == material["subject_packet_sha256"]
    assert runtime["subject_packet_byte_length"] == len(material["subject_packet_bytes"])
    assert runtime["subject_artifact_count"] == 2
    assert runtime["subject_input_rehash"] == {"initial": "PASS", "post_output": "PASS", "pre_rename": "PASS"}


def test_actual_subject_packet_path_is_required_even_for_fabricated_zero_hash(tmp_path: Path) -> None:
    material = make_synthetic_material(
        tmp_path,
        manifest_overrides={"subject_packet_sha256": "0" * 64},
        payload_overrides={"subject_packet_sha256": "0" * 64},
    )
    with pytest.raises(RegistryError) as caught:
        _materialize(material, subject_packet_path=None)
    assert caught.value.classification == "SUBJECT_PACKET_PATH_REQUIRED_STOP"
    assert not material["registry_root"].exists()


@pytest.mark.parametrize(
    "record",
    [
        {"relative_path": "missing-length.txt", "sha256": "0" * 64},
        {"relative_path": "bad-length.txt", "byte_length": -1, "sha256": "0" * 64},
        {"relative_path": "bad-hash.txt", "byte_length": 1, "sha256": "NOT_A_HASH"},
    ],
)
def test_malformed_artifact_records_stop(tmp_path: Path, record: dict[str, object]) -> None:
    material = make_synthetic_material(tmp_path, manifest_overrides={"artifact_count": 1, "artifacts": [record]})
    with pytest.raises(RegistryError) as caught:
        _materialize(material)
    assert caught.value.classification == "SUBJECT_ARTIFACT_RECORD_INVALID_STOP"


def test_missing_manifested_artifact_stops(tmp_path: Path) -> None:
    material = make_synthetic_material(tmp_path)
    (material["subject_artifact_root"] / "metadata" / "summary.txt").unlink()
    with pytest.raises(RegistryError) as caught:
        _materialize(material)
    assert caught.value.classification == "SUBJECT_ARTIFACT_MISSING_STOP"


def test_extra_unmanifested_artifact_stops(tmp_path: Path) -> None:
    material = make_synthetic_material(tmp_path)
    (material["subject_artifact_root"] / "extra.txt").write_text("synthetic extra", encoding="utf-8")
    with pytest.raises(RegistryError) as caught:
        _materialize(material)
    assert caught.value.classification == "SUBJECT_ARTIFACT_EXTRA_FILE_STOP"


@pytest.mark.parametrize(
    "paths",
    [
        ["../escape.txt"],
        ["duplicate.txt", "duplicate.txt"],
        ["Case.txt", "case.txt"],
        ["CON/file.txt"],
        ["trailing./file.txt"],
    ],
)
def test_artifact_traversal_duplicate_casefold_and_reserved_paths_stop(tmp_path: Path, paths: list[str]) -> None:
    records = [{"relative_path": path, "byte_length": 1, "sha256": "0" * 64} for path in paths]
    material = make_synthetic_material(tmp_path, manifest_overrides={"artifact_count": len(records), "artifacts": records})
    with pytest.raises(RegistryError) as caught:
        _materialize(material)
    assert caught.value.classification == "SUBJECT_ARTIFACT_PATH_UNSAFE_STOP"


def test_artifact_byte_length_mismatch_stops(tmp_path: Path) -> None:
    material = make_synthetic_material(tmp_path)
    material["manifest"]["artifacts"][0]["byte_length"] += 1
    from quant_replay_system.accepted_lineage_registry.canonical import canonical_json_bytes, sha256_bytes

    material["manifest_bytes"] = canonical_json_bytes(material["manifest"])
    material["payload"]["subject_artifact_manifest_sha256"] = sha256_bytes(material["manifest_bytes"])
    material["payload_bytes"] = canonical_json_bytes(material["payload"])
    with pytest.raises(RegistryError) as caught:
        _materialize(material)
    assert caught.value.classification == "SUBJECT_ARTIFACT_BYTE_LENGTH_MISMATCH_STOP"


def test_artifact_hash_mismatch_stops(tmp_path: Path) -> None:
    material = make_synthetic_material(tmp_path)
    material["manifest"]["artifacts"][0]["sha256"] = "0" * 64
    from quant_replay_system.accepted_lineage_registry.canonical import canonical_json_bytes, sha256_bytes

    material["manifest_bytes"] = canonical_json_bytes(material["manifest"])
    material["payload"]["subject_artifact_manifest_sha256"] = sha256_bytes(material["manifest_bytes"])
    material["payload_bytes"] = canonical_json_bytes(material["payload"])
    with pytest.raises(RegistryError) as caught:
        _materialize(material)
    assert caught.value.classification == "SUBJECT_ARTIFACT_HASH_MISMATCH_STOP"


def test_artifact_mutation_before_rename_stops_without_authoritative_entry(tmp_path: Path, monkeypatch) -> None:
    material = make_synthetic_material(tmp_path)
    original = transaction.revalidate_subject_inputs
    mutated = False

    def mutate_then_validate(baseline, **kwargs):
        nonlocal mutated
        if not mutated:
            mutated = True
            target = material["subject_artifact_root"] / "metadata" / "summary.txt"
            target.write_bytes(target.read_bytes() + b"mutation")
        return original(baseline, **kwargs)

    monkeypatch.setattr(transaction, "revalidate_subject_inputs", mutate_then_validate)
    with pytest.raises(RegistryError) as caught:
        _materialize(material)
    assert caught.value.classification == "SUBJECT_INPUT_MUTATED_DURING_TRANSACTION_STOP"
    assert not any(material["registry_root"].joinpath("entries").rglob("entry_manifest.json"))


def test_subject_packet_hardlink_is_rejected(tmp_path: Path) -> None:
    material = make_synthetic_material(tmp_path)
    os.link(material["subject_packet_path"], material["review_output_root"] / "packet-hardlink.zip")
    with pytest.raises(RegistryError) as caught:
        _materialize(material)
    assert caught.value.classification == "SUBJECT_PACKET_NOT_REGULAR_STOP"


def test_subject_packet_symlink_is_rejected(tmp_path: Path) -> None:
    material = make_synthetic_material(tmp_path)
    original = material["review_output_root"] / "packet-original.zip"
    material["subject_packet_path"].replace(original)
    os.symlink(original, material["subject_packet_path"])
    with pytest.raises(RegistryError) as caught:
        _materialize(material)
    assert caught.value.classification == "SUBJECT_PACKET_NOT_REGULAR_STOP"


def test_subject_artifact_hardlink_is_rejected(tmp_path: Path) -> None:
    material = make_synthetic_material(tmp_path)
    source = material["subject_artifact_root"] / "metadata" / "summary.txt"
    os.link(source, material["subject_artifact_root"] / "metadata" / "summary-hardlink.txt")
    with pytest.raises(RegistryError) as caught:
        _materialize(material)
    assert caught.value.classification == "SUBJECT_ARTIFACT_PATH_UNSAFE_STOP"


def test_subject_artifact_symlink_is_rejected(tmp_path: Path) -> None:
    material = make_synthetic_material(tmp_path)
    source = material["subject_artifact_root"] / "metadata" / "summary.txt"
    original = material["review_output_root"] / "summary-original.txt"
    source.replace(original)
    os.symlink(original, source)
    with pytest.raises(RegistryError) as caught:
        _materialize(material)
    assert caught.value.classification == "SUBJECT_ARTIFACT_PATH_UNSAFE_STOP"
