from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import authority_kwargs
from quant_replay_system.accepted_lineage_registry.models import RegistryError
from quant_replay_system.accepted_lineage_registry.verification import preflight_next_task


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    return subprocess.run(
        [sys.executable, "-m", "quant_replay_system.accepted_lineage_registry", *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def test_package_local_cli_help_exists() -> None:
    result = _run("--help")
    assert result.returncode == 0
    for command in (
        "derive-keys",
        "validate-review",
        "materialize-synthetic",
        "verify-entry",
        "rebuild-index",
        "health",
        "preflight-next-task",
        "package-review",
    ):
        assert command in result.stdout


def test_derive_keys_cli_is_safe_and_has_no_paths() -> None:
    result = _run("derive-keys", "--subject-phase-id", "SYNTHETIC-SUBJECT-001", "--receipt-id", "SYNTHETIC-RECEIPT-001")
    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["subject_key"].startswith("SUBJ_")
    assert payload["receipt_key"].startswith("RCPT_")
    assert ":\\" not in result.stdout


def test_missing_current_exact_task_approval_stops(materialized_entry) -> None:
    root, material, result = materialized_entry
    with pytest.raises(RegistryError) as caught:
        preflight_next_task(
            root,
            result.subject_key,
            result.receipt_key,
            current_task_approval_id=None,
            **authority_kwargs(material),
        )
    assert caught.value.classification == "NEXT_TASK_EXACT_APPROVAL_MISSING_STOP"


def test_valid_predecessor_lookup_does_not_reuse_registry_authority(materialized_entry) -> None:
    root, material, result = materialized_entry
    preflight = preflight_next_task(
        root,
        result.subject_key,
        result.receipt_key,
        current_task_approval_id="CURRENT-SYNTHETIC-TASK-APPROVAL-001",
        **authority_kwargs(material),
    )
    assert preflight.classification == "PREDECESSOR_REVIEW_STATE_VALID_CURRENT_APPROVAL_PRESENT"
    assert preflight.next_task_authorized_by_registry is False


def test_cli_outputs_do_not_expose_private_root(materialized_entry) -> None:
    root, material, result = materialized_entry
    completed = _run(
        "verify-entry",
        "--root",
        str(root),
        "--approved-admin-root",
        str(material["approved_admin_root"]),
        "--repository-root",
        str(material["repository_root"]),
        "--expected-registry-root",
        str(root),
        "--subject-packet",
        str(material["subject_packet_path"]),
        "--subject-artifact-root",
        str(material["subject_artifact_root"]),
        "--subject-key",
        result.subject_key,
        "--receipt-key",
        result.receipt_key,
    )
    assert completed.returncode == 0
    assert str(root) not in completed.stdout
    assert "password" not in completed.stdout.lower()
    assert "token" not in completed.stdout.lower()


def test_synthetic_payload_contains_no_real_evidence_or_market_data(synthetic_material) -> None:
    text = synthetic_material["payload_bytes"].decode("utf-8") + synthetic_material["receipt_bytes"].decode("utf-8")
    assert "Stage1B-A" not in text
    assert "market_data" not in text
    assert "broker" not in text.lower()
    assert "trading" not in text.lower()
