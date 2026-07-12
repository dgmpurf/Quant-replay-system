from __future__ import annotations

import json

import pytest

from conftest import authority_kwargs, make_synthetic_material
from quant_replay_system.accepted_lineage_registry.canonical import canonical_json_bytes, sha256_bytes
from quant_replay_system.accepted_lineage_registry.models import HumanReviewPayload, RegistryError
from quant_replay_system.accepted_lineage_registry.verification import verify_entry


def test_system_json_is_deterministic_sorted_compact_utf8_with_lf() -> None:
    left = canonical_json_bytes({"z": "中国", "a": 1})
    right = canonical_json_bytes({"a": 1, "z": "中国"})
    assert left == right == '{"a":1,"z":"中国"}\n'.encode("utf-8")
    assert not left.startswith(b"\xef\xbb\xbf")


def test_human_payload_hash_uses_exact_bytes(tmp_path) -> None:
    material = make_synthetic_material(tmp_path)
    payload = HumanReviewPayload.from_bytes(material["payload_bytes"])
    alternate = json.dumps(material["payload"], indent=2, sort_keys=True).encode("utf-8")
    assert payload.exact_sha256 == sha256_bytes(material["payload_bytes"])
    assert payload.exact_sha256 != sha256_bytes(alternate)


def test_bom_is_rejected_without_rewriting(tmp_path) -> None:
    material = make_synthetic_material(tmp_path)
    with pytest.raises(RegistryError) as caught:
        HumanReviewPayload.from_bytes(b"\xef\xbb\xbf" + material["payload_bytes"])
    assert caught.value.classification == "HUMAN_REVIEW_PAYLOAD_MISMATCH_STOP"


def test_five_file_hash_graph_has_no_self_or_circular_hash(materialized_entry) -> None:
    root, material, result = materialized_entry
    entry = root / "entries" / result.subject_key / result.receipt_key
    manifest = json.loads((entry / "entry_manifest.json").read_text(encoding="utf-8"))
    seal = json.loads((entry / "entry_seal.json").read_text(encoding="utf-8"))
    assert "entry_manifest_sha256" not in manifest
    assert "entry_seal_sha256" not in manifest
    assert "entry_seal_sha256" not in seal
    assert seal["entry_manifest_sha256"]
    assert verify_entry(root, result.subject_key, result.receipt_key, **authority_kwargs(material))["status"] == "PASS"


def test_byte_mutation_is_detected(materialized_entry) -> None:
    root, material, result = materialized_entry
    path = root / "entries" / result.subject_key / result.receipt_key / "review_receipt.md"
    path.write_bytes(path.read_bytes() + b"mutation\n")
    with pytest.raises(RegistryError):
        verify_entry(root, result.subject_key, result.receipt_key, **authority_kwargs(material))
