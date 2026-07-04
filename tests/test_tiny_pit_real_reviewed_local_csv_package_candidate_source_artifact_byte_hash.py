from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pytest

from quant_replay_system import (
    tiny_pit_real_reviewed_local_csv_package_candidate_source_artifact_byte_hash as core,
)


FULL_HASH = hashlib.sha256(b"synthetic source artifact bytes\n").hexdigest()
MISMATCH_HASH = hashlib.sha256(b"different declared source hash\n").hexdigest()


def test_no_input_safe_artifact_set(tmp_path: Path) -> None:
    result = core.run_source_artifact_byte_hash(output_root=tmp_path / "out", run_id="no_input")

    assert result["runtime_status"] == core.STATUS_NO_INPUT
    assert result["health_status"] == "PASS"
    assert result["source_artifact_byte_read_level"] == core.SOURCE_ARTIFACT_BYTE_READ_NONE
    assert result["source_hash_recompute_level"] == core.SOURCE_HASH_RECOMPUTE_NONE
    assert result["source_content_read_level"] == core.SOURCE_CONTENT_READ_NONE
    assert result["csv_read_level"] == core.CSV_READ_NONE
    assert result["source_artifact_opened_for_hash"] is False
    assert result["source_artifact_bytes_streamed_for_hash"] is False
    assert result["source_hash_recomputed"] is False
    assert result["source_hash_validated"] is False
    _assert_downstream_false(result)
    _assert_artifacts_exist(result)


def test_no_input_does_not_open_supplied_paths(tmp_path: Path) -> None:
    source_artifact = tmp_path / "missing.bin"
    metadata = tmp_path / "missing_metadata.json"

    result = core.run_source_artifact_byte_hash(
        output_root=tmp_path / "out",
        run_id="no_input_with_paths",
        source_artifact_path=source_artifact,
        source_lineage_metadata_path=metadata,
    )

    assert result["runtime_status"] == core.STATUS_NO_INPUT
    assert result["source_artifact_opened_for_hash"] is False
    assert result["source_artifact_bytes_streamed_for_hash"] is False


def test_missing_allow_flag_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, _ = _write_fixture(tmp_path)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        allow=False,
        run_id="missing_allow",
    )

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_MISSING_ALLOW_FLAG
    assert result["health_status"] == "FAIL"
    assert result["source_artifact_opened_for_hash"] is False


def test_malformed_manifest_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, _ = _write_fixture(tmp_path)
    _write_text(manifest_path, "{not-json")

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        run_id="malformed_manifest",
    )

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_MANIFEST_SCHEMA
    assert result["source_artifact_opened_for_hash"] is False


def test_missing_required_manifest_field_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, _ = _write_fixture(tmp_path)
    manifest = _read_json(manifest_path)
    manifest.pop("source_artifact_id")
    _write_json(manifest_path, manifest)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        run_id="missing_manifest_field",
    )

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_MANIFEST_SCHEMA


def test_unsupported_algorithm_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, _ = _write_fixture(tmp_path)
    manifest = _read_json(manifest_path)
    manifest["source_hash_algorithm"] = "MD5"
    _write_json(manifest_path, manifest)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        hash_algorithm="MD5",
        run_id="bad_algorithm",
    )

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_UNSUPPORTED_ALGORITHM


def test_size_limit_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, _ = _write_fixture(tmp_path)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        max_source_artifact_size_bytes=1,
        run_id="size_limit",
    )

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_FILE_SIZE_LIMIT
    assert result["source_artifact_opened_for_hash"] is False


@pytest.mark.parametrize(
    ("path_text", "run_id"),
    [
        ("https://example.invalid/source.bin", "url"),
        ("..\\escape.bin", "traversal"),
        ("secret\\source.bin", "secret"),
        (".env-source.bin", "env"),
    ],
)
def test_path_guard_blocks_unsafe_path_text(tmp_path: Path, path_text: str, run_id: str) -> None:
    manifest_path, metadata_path, source_artifact, _ = _write_fixture(tmp_path)
    manifest = _read_json(manifest_path)
    manifest["source_artifact_path_ref"] = path_text
    _write_json(manifest_path, manifest)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        run_id=run_id,
    )

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_PATH_GUARD


def test_path_guard_blocks_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    source_root = tmp_path / "source"
    outside.mkdir()
    source_root.mkdir()
    real_file = outside / "real.bin"
    _write_bytes(real_file, b"outside")
    link = source_root / "link.bin"
    try:
        link.symlink_to(real_file)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    manifest_path, metadata_path, _source_artifact, _ = _write_fixture(tmp_path, artifact_path=link)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=link,
        allowed_source_roots=[source_root],
        run_id="symlink_escape",
    )

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_PATH_GUARD


@pytest.mark.parametrize("protected", ["docs/project_sources", "data/raw", "data/processed", "data/cache"])
def test_path_guard_blocks_protected_paths(tmp_path: Path, protected: str) -> None:
    protected_root = tmp_path / protected
    protected_root.mkdir(parents=True)
    artifact = protected_root / "source.bin"
    _write_bytes(artifact, b"blocked")
    manifest_path, metadata_path, _source_artifact, _ = _write_fixture(tmp_path, artifact_path=artifact)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=artifact,
        allowed_source_roots=[tmp_path],
        run_id=protected.replace("/", "_"),
    )

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_PATH_GUARD


def test_path_guard_blocks_directories_and_package_roots(tmp_path: Path) -> None:
    directory = tmp_path / "source_dir"
    directory.mkdir()
    manifest_path, metadata_path, _source_artifact, _ = _write_fixture(tmp_path, artifact_path=directory)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=directory,
        run_id="directory",
    )

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_PATH_GUARD


@pytest.mark.parametrize("suffix", [".csv", ".CSV", ".CsV"])
def test_csv_source_artifact_blocked_in_v0_1(tmp_path: Path, suffix: str) -> None:
    csv_artifact = tmp_path / "source" / f"source{suffix}"
    csv_artifact.parent.mkdir()
    _write_bytes(csv_artifact, b"not,parsed\n")
    manifest_path, metadata_path, _source_artifact, _ = _write_fixture(tmp_path, artifact_path=csv_artifact)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=csv_artifact,
        allowed_source_roots=[csv_artifact.parent],
        run_id=f"csv_block_{suffix.strip('.')}",
    )

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_FORBIDDEN_EXTENSION
    assert result["target_csv_opened"] is False


def test_opaque_byte_stream_does_not_decode_or_parse_source_artifact(tmp_path: Path) -> None:
    source_artifact = tmp_path / "source" / "opaque-source.bin"
    payload = b"\xff\xfe\x00{\"looks\":\"json\"}\nnot,csv,content\n"
    _write_bytes(source_artifact, payload)
    expected_hash = hashlib.sha256(payload).hexdigest()
    manifest_path, metadata_path, _source_artifact, _ = _write_fixture(
        tmp_path,
        artifact_path=source_artifact,
        declared_hash=expected_hash,
    )

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        run_id="opaque_not_decoded",
    )

    assert result["runtime_status"] == core.STATUS_MATCHED
    assert result["computed_source_hash_preview"] == expected_hash[: core.HASH_PREVIEW_LENGTH]
    assert result["source_content_read"] is False
    assert result["source_content_semantically_read"] is False
    assert result["csv_header_read"] is False
    assert result["csv_values_read"] is False


def test_safe_non_csv_byte_artifact_computes_sha256(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, expected_hash = _write_fixture(tmp_path)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        run_id="matched",
    )

    assert result["runtime_status"] == core.STATUS_MATCHED
    assert result["health_status"] == "PASS"
    assert result["source_artifact_byte_read_level"] == core.SOURCE_ARTIFACT_BYTE_READ_STREAMING_HASH_ONLY
    assert result["source_hash_recompute_level"] == core.SOURCE_HASH_RECOMPUTE_SHA256_ONLY
    assert result["source_content_read_level"] == core.SOURCE_CONTENT_READ_NONE
    assert result["csv_read_level"] == core.CSV_READ_NONE
    assert result["source_artifact_opened_for_hash"] is True
    assert result["source_artifact_bytes_streamed_for_hash"] is True
    assert result["source_hash_recomputed"] is True
    assert result["computed_source_hash_preview"] == expected_hash[: core.HASH_PREVIEW_LENGTH]
    assert result["source_artifact_byte_identity_matched"] is True
    assert result["source_hash_validated"] is False


def test_safe_hash_mode_keeps_content_csv_and_downstream_boundaries_false(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, _ = _write_fixture(tmp_path)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        run_id="boundaries",
    )

    for field in [
        "source_content_read",
        "source_content_semantically_read",
        "target_csv_opened",
        "csv_header_read",
        "csv_values_read",
        "csv_full_content_read",
        "local_file_hash_recomputed",
        "expected_hash_reverified",
        "available_time_compared_to_decision_time",
        "source_hash_validated",
        "revision_id_validated",
        "available_time_validated",
        "pit_admissibility_validated",
        "source_reliability_scored",
        "reviewer_authority_validated",
    ]:
        assert result[field] is False
    _assert_downstream_false(result)


def test_mismatch_warns_and_is_actionable(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, _ = _write_fixture(tmp_path, declared_hash=MISMATCH_HASH)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        run_id="mismatch",
    )

    assert result["runtime_status"] == core.STATUS_MISMATCHED
    assert result["health_status"] == "WARN"
    assert result["source_artifact_byte_identity_matched"] is False
    assert result["source_artifact_byte_identity_mismatch"] is True
    assert result["source_artifact_byte_identity_actionable_mismatch"] is True
    assert result["source_hash_validated"] is False


def test_missing_declared_source_hash_warns_if_compare_policy_permits(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, _ = _write_fixture(tmp_path, declared_hash="")

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        compare_to_declared_source_hash=False,
        run_id="missing_hash_warn",
    )

    assert result["runtime_status"] == core.STATUS_WARN_SOURCE_HASH_METADATA_MISSING
    assert result["health_status"] == "WARN"
    assert result["declared_source_hash_present"] is False


def test_full_hash_only_in_metadata_when_policy_allows(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, expected_hash = _write_fixture(tmp_path)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        run_id="full_hash_policy",
    )

    metadata = _read_json(result["artifact_paths"]["metadata"])
    assert metadata["computed_source_hash_full"] == expected_hash
    assert metadata["computed_source_hash_full_recorded_in_metadata"] is True
    public_text = _public_artifact_text(result)
    assert expected_hash not in public_text
    assert result["declared_source_hash_preview"] in public_text


def test_full_hash_recording_policy_can_suppress_metadata_full_hash(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, expected_hash = _write_fixture(tmp_path)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        full_hash_recording_policy="NO_FULL_HASH_METADATA",
        run_id="suppress_full_hash",
    )

    metadata = _read_json(result["artifact_paths"]["metadata"])
    assert metadata["computed_source_hash_full"] == ""
    assert metadata["computed_source_hash_full_recorded_in_metadata"] is False
    assert expected_hash not in json.dumps(metadata)
    assert expected_hash not in _public_artifact_text(result)


def test_public_artifacts_do_not_expose_full_hash_private_path_or_secret_sentinel(tmp_path: Path) -> None:
    secret_root = tmp_path / "allowed_root_with_private_name"
    secret_root.mkdir()
    source_artifact = secret_root / "synthetic-source.bin"
    _write_bytes(source_artifact, b"private-secret-sentinel bytes")
    expected_hash = hashlib.sha256(b"private-secret-sentinel bytes").hexdigest()
    manifest_path, metadata_path, _artifact, _ = _write_fixture(
        tmp_path,
        artifact_path=source_artifact,
        declared_hash=expected_hash,
    )

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        allowed_source_roots=[secret_root],
        run_id="no_leak",
    )

    public_text = _public_artifact_text(result)
    assert expected_hash not in public_text
    assert str(source_artifact) not in public_text
    assert "private-secret-sentinel" not in public_text


def test_source_artifact_path_ref_and_explicit_path_mismatch_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, _ = _write_fixture(tmp_path)
    alternate = source_artifact.parent / "alternate-source.bin"
    _write_bytes(alternate, b"alternate bytes")

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=alternate,
        allowed_source_roots=[source_artifact.parent],
        run_id="path_mismatch",
    )

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_PATH_GUARD
    assert result["source_artifact_opened_for_hash"] is False


def test_blocked_error_messages_do_not_echo_full_private_paths(tmp_path: Path) -> None:
    manifest_path, metadata_path, _source_artifact, _ = _write_fixture(tmp_path)
    private_artifact = tmp_path / "outside_private_root" / "nested" / "private-source.bin"
    _write_bytes(private_artifact, b"private bytes")
    manifest = _read_json(manifest_path)
    manifest["source_artifact_path_ref"] = str(private_artifact)
    _write_json(manifest_path, manifest)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=private_artifact,
        allowed_source_roots=[tmp_path / "source"],
        run_id="no_private_path_echo",
    )

    public_text = _public_artifact_text(result)
    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_PATH_GUARD
    assert str(private_artifact) not in public_text
    assert "outside_private_root" not in public_text


def test_unsafe_validation_claim_in_manifest_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, _ = _write_fixture(tmp_path)
    manifest = _read_json(manifest_path)
    manifest["requested_source_hash_validation_level"] = "SOURCE_HASH_VALIDATED"
    _write_json(manifest_path, manifest)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        run_id="unsafe_claim",
    )

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_UNSAFE_VALIDATION_CLAIM
    assert result["source_hash_validated"] is False


def test_forbidden_downstream_flag_blocks(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, _ = _write_fixture(tmp_path)
    manifest = _read_json(manifest_path)
    manifest["forbidden_downstream_flags"]["active_replay_input"] = True
    _write_json(manifest_path, manifest)

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        run_id="forbidden_downstream",
    )

    assert result["runtime_status"] == core.STATUS_BLOCKED_BY_FORBIDDEN_DOWNSTREAM
    assert result["active_replay_input"] is False


def test_unsafe_positive_wording_absent_from_live_outputs(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, _ = _write_fixture(tmp_path)
    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        run_id="wording",
    )

    live_text = "\n".join(
        [
            str(result["runtime_status"]),
            str(result["workflow_stage"]),
            str(result["recommended_next_task"]),
            _public_artifact_text(result),
        ]
    )
    for phrase in core.FORBIDDEN_LIVE_POSITIVE_STATUSES:
        assert phrase not in live_text


def test_public_api_signature_has_no_forbidden_args() -> None:
    forbidden = {
        "target_csv_path",
        "package_root",
        "package_discovery",
        "url_fetch",
        "source_content_parse",
        "semantic_content_read",
        "csv_parser",
        "expected_hash_reverify",
        "local_package_file_hash_recompute",
        "available_time_pit_gate",
        "pit_admissibility_validation",
        "reviewer_authority_validation",
        "source_reliability_scoring",
        "real_package_candidate_creation",
        "active_input",
        "replay",
        "trading",
    }
    assert forbidden.isdisjoint(inspect.signature(core.run_source_artifact_byte_hash).parameters)


def test_docs_project_sources_not_created(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, _ = _write_fixture(tmp_path)
    _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        run_id="no_project_sources",
    )

    assert not Path("docs/project_sources").exists()


def test_artifact_writes_stay_under_tmp_output_root(tmp_path: Path) -> None:
    manifest_path, metadata_path, source_artifact, _ = _write_fixture(tmp_path)
    output_root = tmp_path / "out"

    result = _run_hash(
        tmp_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
        source_artifact=source_artifact,
        output_root=output_root,
        run_id="output_root",
    )

    for path in result["artifact_paths"].values():
        assert Path(path).resolve().is_relative_to(output_root.resolve())


def _write_fixture(
    tmp_path: Path,
    *,
    artifact_path: Path | None = None,
    declared_hash: str | None = FULL_HASH,
) -> tuple[Path, Path, Path, str]:
    source_root = tmp_path / "source"
    manifest_root = tmp_path / "manifest"
    source_root.mkdir(exist_ok=True)
    manifest_root.mkdir(exist_ok=True)
    source_artifact = artifact_path or source_root / "synthetic-source.bin"
    if not source_artifact.exists() and source_artifact.suffix != "":
        source_artifact.parent.mkdir(parents=True, exist_ok=True)
        _write_bytes(source_artifact, b"synthetic source artifact bytes\n")
    full_hash = hashlib.sha256(b"synthetic source artifact bytes\n").hexdigest()
    metadata_path = manifest_root / "source_lineage_metadata.json"
    manifest_path = manifest_root / "source_artifact_hash_manifest.json"
    _write_json(metadata_path, _source_metadata(declared_hash if declared_hash is not None else full_hash))
    _write_json(
        manifest_path,
        _manifest(
            source_artifact,
            metadata_path,
            declared_hash if declared_hash is not None else full_hash,
        ),
    )
    return manifest_path, metadata_path, source_artifact, declared_hash if declared_hash else full_hash


def _manifest(source_artifact: Path, metadata_path: Path, declared_hash: str) -> dict:
    return {
        "source_artifact_hash_request_id": "source_artifact_hash_request_001",
        "source_id": "SYNTH_SOURCE",
        "source_artifact_id": "synthetic_source_artifact",
        "source_artifact_declared_name": "Synthetic source artifact",
        "source_artifact_path_ref": str(source_artifact),
        "report_only": True,
        "diagnostic_only": True,
        "requested_source_artifact_byte_read_level": core.SOURCE_ARTIFACT_BYTE_READ_STREAMING_HASH_ONLY,
        "requested_source_hash_recompute_level": core.SOURCE_HASH_RECOMPUTE_SHA256_ONLY,
        "requested_source_content_read_level": core.SOURCE_CONTENT_READ_NONE,
        "requested_csv_read_level": core.CSV_READ_NONE,
        "requested_local_file_hash_level": core.LOCAL_FILE_HASH_NONE,
        "requested_expected_hash_verification_level": core.EXPECTED_HASH_VERIFICATION_NONE,
        "requested_source_hash_validation_level": core.SOURCE_HASH_VALIDATION_NONE,
        "requested_revision_id_validation_level": core.REVISION_ID_VALIDATION_NONE,
        "requested_available_time_validation_level": core.AVAILABLE_TIME_VALIDATION_NONE,
        "requested_pit_admissibility_level": core.PIT_ADMISSIBILITY_NONE,
        "requested_source_reliability_level": core.SOURCE_RELIABILITY_NONE,
        "requested_reviewer_authority_level": core.REVIEWER_AUTHORITY_NONE,
        "requested_package_creation_level": core.PACKAGE_CREATION_NONE,
        "requested_active_input_level": core.ACTIVE_INPUT_NONE,
        "requested_replay_readiness_level": core.REPLAY_READINESS_NONE,
        "source_hash_algorithm": "SHA-256",
        "declared_source_hash": declared_hash,
        "source_lineage_metadata_ref": str(metadata_path),
        "revision_id_metadata_ref": "metadata-only-revision-ref",
        "available_time_metadata_ref": "metadata-only-available-time-ref",
        "compare_to_declared_source_hash": True,
        "full_hash_recording_policy": core.FULL_HASH_RECORDING_LOCAL_METADATA_ONLY,
        "disclosure_policy": core.DISCLOSURE_PREVIEW_ONLY_PUBLIC_SURFACES,
        "forbidden_downstream_flags": {field: False for field in core.REQUIRED_FALSE_FLAGS},
        "limitations": ["Synthetic byte artifact for report-only source artifact hash tests."],
    }


def _source_metadata(declared_hash: str) -> dict:
    return {
        "source_id": "SYNTH_SOURCE",
        "source_hash_algorithm": "SHA-256",
        "source_hash_value": declared_hash,
        "revision_id": "rev-001",
        "available_time": "2024-01-01T00:00:00Z",
        "report_only": True,
        "diagnostic_only": True,
        "source_hash_validated": False,
        "pit_admissibility_validated": False,
        "reviewer_authority_validated": False,
        "forbidden_downstream_flags": {field: False for field in core.REQUIRED_FALSE_FLAGS},
    }


def _run_hash(
    tmp_path: Path,
    *,
    manifest_path: Path,
    metadata_path: Path,
    source_artifact: Path,
    output_root: Path | None = None,
    allowed_source_roots: list[Path] | None = None,
    allow: bool = True,
    hash_algorithm: str = "SHA-256",
    compare_to_declared_source_hash: bool = True,
    max_source_artifact_size_bytes: int = core.DEFAULT_MAX_SOURCE_ARTIFACT_SIZE_BYTES,
    full_hash_recording_policy: str = core.FULL_HASH_RECORDING_LOCAL_METADATA_ONLY,
    run_id: str,
) -> dict:
    return core.run_source_artifact_byte_hash(
        output_root=output_root or tmp_path / "out",
        run_id=run_id,
        source_artifact_hash_manifest_path=manifest_path,
        source_lineage_metadata_path=metadata_path,
        source_artifact_path=source_artifact,
        allowed_manifest_roots=[manifest_path.parent],
        allowed_source_artifact_roots=allowed_source_roots or [source_artifact.parent],
        allow_source_artifact_byte_hash=allow,
        max_source_artifact_size_bytes=max_source_artifact_size_bytes,
        hash_algorithm=hash_algorithm,
        source_artifact_byte_read_level=core.SOURCE_ARTIFACT_BYTE_READ_STREAMING_HASH_ONLY,
        source_hash_recompute_level=core.SOURCE_HASH_RECOMPUTE_SHA256_ONLY,
        compare_to_declared_source_hash=compare_to_declared_source_hash,
        full_hash_recording_policy=full_hash_recording_policy,
    )


def _assert_downstream_false(result: dict) -> None:
    for field in core.REQUIRED_FALSE_FLAGS:
        assert result[field] is False


def _assert_artifacts_exist(result: dict) -> None:
    for path in result["artifact_paths"].values():
        assert Path(path).exists()


def _public_artifact_text(result: dict) -> str:
    paths = result["artifact_paths"]
    chunks = []
    for key in ["report", "summary", "issues", "limitations", "forbidden_downstream_flags"]:
        with Path(paths[key]).open("r", encoding="utf-8") as handle:
            chunks.append(handle.read())
    return "\n".join(chunks)


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(text)


def _write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(payload)
