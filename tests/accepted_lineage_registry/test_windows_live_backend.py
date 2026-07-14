from __future__ import annotations

import os
from pathlib import Path

import pytest

from quant_replay_system.accepted_lineage_registry import canonical as canonical_module
from quant_replay_system.accepted_lineage_registry.models import RegistryError
from quant_replay_system.accepted_lineage_registry.windows_live_backend import (
    DIRECTORY_DURABILITY_UNPROVEN_STOP,
    FILE_FLUSH_FAILED_STOP,
    HARDLINK_OR_IDENTITY_DRIFT_STOP,
    HANDLE_RELATIVE_RENAME_UNAVAILABLE_STOP,
    LOCK_OWNERSHIP_UNVERIFIED_STOP,
    REPARSE_OPEN_UNAVAILABLE_STOP,
    RENAME_RESULT_UNVERIFIED_STOP,
    WindowsCapabilityReport,
    WindowsHandleIdentity,
    WindowsLiveFilesystemBackend,
)


@pytest.fixture
def backend() -> WindowsLiveFilesystemBackend:
    assert os.name == "nt"
    return WindowsLiveFilesystemBackend()


class _RecordingDurabilityHandle:
    def __init__(self, kind: str) -> None:
        self.kind = kind

    def __enter__(self) -> "_RecordingDurabilityHandle":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None


class _RecordingDurabilityBackend:
    def __init__(
        self,
        *,
        file_failure: RegistryError | None = None,
        directory_failure: RegistryError | None = None,
    ) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.file_failure = file_failure
        self.directory_failure = directory_failure

    def open_file_no_reparse(
        self,
        path: str | Path,
        *,
        writable: bool = False,
        delete: bool = False,
    ) -> _RecordingDurabilityHandle:
        self.calls.append(("open_file", Path(path), writable, delete))
        return _RecordingDurabilityHandle("file")

    def open_directory_no_reparse(
        self,
        path: str | Path,
        *,
        writable: bool = False,
        delete: bool = False,
    ) -> _RecordingDurabilityHandle:
        self.calls.append(("open_directory", Path(path), writable, delete))
        return _RecordingDurabilityHandle("directory")

    def query_link_count(self, handle: _RecordingDurabilityHandle) -> int:
        self.calls.append(("query_link_count", handle.kind))
        return 1

    def flush_file_handle(self, handle: _RecordingDurabilityHandle) -> None:
        self.calls.append(("flush_file", handle.kind))
        if self.file_failure is not None:
            raise self.file_failure

    def flush_directory_handle(self, handle: _RecordingDurabilityHandle) -> bool:
        self.calls.append(("flush_directory", handle.kind))
        if self.directory_failure is not None:
            raise self.directory_failure
        return True


def test_capability_report_is_honest_and_does_not_grant_l2(
    backend: WindowsLiveFilesystemBackend,
) -> None:
    report = backend.capability_report()
    assert isinstance(report, WindowsCapabilityReport)
    assert report.backend_status == "IMPLEMENTED_FAIL_CLOSED_PENDING_SEPARATE_L2_HUMAN_ACCEPTANCE"
    assert report.windows_backend_available is True
    assert report.directory_durability_proven is False
    assert report.L2_platform_acceptance_granted is False
    assert report.risk_waiver_granted is False
    assert report.residual_risks


def test_open_directory_no_reparse_and_query_identity(
    backend: WindowsLiveFilesystemBackend,
    tmp_path: Path,
) -> None:
    directory = tmp_path / "identity-directory"
    directory.mkdir()
    with backend.open_directory_no_reparse(directory) as handle:
        identity = backend.query_handle_identity(handle)
        assert isinstance(identity, WindowsHandleIdentity)
        assert identity.is_directory is True
        assert identity.number_of_links == 1
        assert backend.query_link_count(handle) == 1


def test_file_flush_uses_retained_handle(
    backend: WindowsLiveFilesystemBackend,
    tmp_path: Path,
) -> None:
    target = tmp_path / "durable.txt"
    target.write_bytes(b"bounded-windows-flush\n")
    with backend.open_file_no_reparse(target, writable=True) as handle:
        backend.flush_file_handle(handle)
    assert target.read_bytes() == b"bounded-windows-flush\n"


def test_write_bytes_durable_delegates_once_to_explicit_backend(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = tmp_path / "mode-neutral-output.bin"
    exact_bytes = b"one deterministic durable write\n"
    writes: list[tuple[Path, bytes, bool]] = []
    original = canonical_module.write_bytes_fsync

    def record_write(path: str | Path, value: bytes, *, exclusive: bool = True) -> None:
        writes.append((Path(path), value, exclusive))
        original(path, value, exclusive=exclusive)

    monkeypatch.setattr(canonical_module, "write_bytes_fsync", record_write)
    recording_backend = _RecordingDurabilityBackend()
    canonical_module.write_bytes_durable(target, exact_bytes, backend=recording_backend)

    assert writes == [(target, exact_bytes, True)]
    assert target.read_bytes() == exact_bytes
    assert recording_backend.calls == [
        ("open_file", target, True, False),
        ("query_link_count", "file"),
        ("flush_file", "file"),
    ]


def test_write_bytes_durable_propagates_exact_file_flush_stop(tmp_path: Path) -> None:
    target = tmp_path / "flush-failure.bin"
    exact_bytes = b"written-before-required-flush\n"
    recording_backend = _RecordingDurabilityBackend(
        file_failure=RegistryError(FILE_FLUSH_FAILED_STOP, "injected deterministic flush failure")
    )

    with pytest.raises(RegistryError) as caught:
        canonical_module.write_bytes_durable(target, exact_bytes, backend=recording_backend)

    assert caught.value.classification == FILE_FLUSH_FAILED_STOP
    assert target.read_bytes() == exact_bytes
    assert recording_backend.calls[-1] == ("flush_file", "file")


def test_parent_directory_durability_uses_backend_and_fails_closed(tmp_path: Path) -> None:
    target = tmp_path / "entry.json"
    recording_backend = _RecordingDurabilityBackend()
    assert canonical_module.flush_parent_directory_durable(target, backend=recording_backend) is True
    assert recording_backend.calls == [
        ("open_directory", tmp_path, True, False),
        ("flush_directory", "directory"),
    ]

    unavailable_backend = _RecordingDurabilityBackend(
        directory_failure=RegistryError(
            DIRECTORY_DURABILITY_UNPROVEN_STOP,
            "injected deterministic directory durability failure",
        )
    )
    with pytest.raises(RegistryError) as caught:
        canonical_module.flush_parent_directory_durable(target, backend=unavailable_backend)
    assert caught.value.classification == DIRECTORY_DURABILITY_UNPROVEN_STOP


def test_backend_none_preserves_mode_neutral_candidate_write_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    mode_neutral_root = tmp_path / "accepted_lineage_registry_v0_1"
    mode_neutral_root.mkdir()
    target = mode_neutral_root / "candidate-compatible.bin"
    exact_bytes = b"backend-none-preserves-existing-behavior\n"
    directory_calls: list[Path] = []
    monkeypatch.setattr(
        canonical_module,
        "fsync_directory",
        lambda path: directory_calls.append(Path(path)) or False,
    )

    canonical_module.write_bytes_durable(target, exact_bytes, backend=None)
    assert canonical_module.flush_parent_directory_durable(target, backend=None) is False
    assert target.read_bytes() == exact_bytes
    assert directory_calls == [mode_neutral_root]


def test_directory_flush_is_observed_or_fails_with_exact_unproven_stop(
    backend: WindowsLiveFilesystemBackend,
    tmp_path: Path,
) -> None:
    with backend.open_directory_no_reparse(tmp_path, writable=True) as handle:
        try:
            observed = backend.flush_directory_handle(handle)
        except RegistryError as exc:
            assert exc.classification == DIRECTORY_DURABILITY_UNPROVEN_STOP
        else:
            assert observed is True
    assert backend.capability_report().directory_durability_proven is False


def test_handle_relative_directory_rename_proves_target_identity(
    backend: WindowsLiveFilesystemBackend,
    tmp_path: Path,
) -> None:
    source = tmp_path / "stage"
    source.mkdir()
    (source / "entry.json").write_text("{}\n", encoding="utf-8")
    with backend.open_directory_no_reparse(source) as handle:
        expected = backend.query_handle_identity(handle)
    observed = backend.rename_directory_by_handle(source, tmp_path, "entry")
    assert observed == expected
    assert not source.exists()
    assert (tmp_path / "entry" / "entry.json").read_text(encoding="utf-8") == "{}\n"


@pytest.mark.parametrize("target_name", ["", ".", "..", "nested/entry", "nested\\entry"])
def test_handle_relative_rename_rejects_unsafe_target_name(
    backend: WindowsLiveFilesystemBackend,
    tmp_path: Path,
    target_name: str,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    with pytest.raises(RegistryError) as caught:
        backend.rename_directory_by_handle(source, tmp_path, target_name)
    assert caught.value.classification == HANDLE_RELATIVE_RENAME_UNAVAILABLE_STOP
    assert source.exists()


def test_verified_handle_lock_disposition(
    backend: WindowsLiveFilesystemBackend,
    tmp_path: Path,
) -> None:
    lock = tmp_path / ".registry-write.lock"
    lock.write_text('{"nonce":"bounded"}\n', encoding="utf-8")
    with backend.open_file_no_reparse(lock) as handle:
        expected = backend.query_handle_identity(handle)
    backend.dispose_lock_by_verified_handle(lock, expected)
    assert not lock.exists()


def test_lock_disposition_rejects_identity_mismatch(
    backend: WindowsLiveFilesystemBackend,
    tmp_path: Path,
) -> None:
    lock = tmp_path / ".registry-write.lock"
    lock.write_text("first\n", encoding="utf-8")
    with backend.open_file_no_reparse(lock) as handle:
        expected = backend.query_handle_identity(handle)
    lock.unlink()
    lock.write_text("replacement\n", encoding="utf-8")
    with pytest.raises(RegistryError) as caught:
        backend.dispose_lock_by_verified_handle(lock, expected)
    assert caught.value.classification == LOCK_OWNERSHIP_UNVERIFIED_STOP
    assert lock.read_text(encoding="utf-8") == "replacement\n"


def test_hardlinked_file_is_rejected(
    backend: WindowsLiveFilesystemBackend,
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.lock"
    second = tmp_path / "second.lock"
    first.write_bytes(b"same-object\n")
    os.link(first, second)
    with backend.open_file_no_reparse(first) as handle:
        with pytest.raises(RegistryError) as caught:
            backend.query_link_count(handle)
    assert caught.value.classification == HARDLINK_OR_IDENTITY_DRIFT_STOP


def test_reparse_directory_is_rejected_without_skip(
    backend: WindowsLiveFilesystemBackend,
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    link = tmp_path / "link"
    target.mkdir()
    os.symlink(target, link, target_is_directory=True)
    with pytest.raises(RegistryError) as caught:
        backend.open_directory_no_reparse(link)
    assert caught.value.classification == REPARSE_OPEN_UNAVAILABLE_STOP


def test_committed_identity_mismatch_is_rejected(
    backend: WindowsLiveFilesystemBackend,
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    with backend.open_directory_no_reparse(first) as handle:
        expected = backend.query_handle_identity(handle)
    with pytest.raises(RegistryError) as caught:
        backend.verify_committed_directory_identity(second, expected)
    assert caught.value.classification == RENAME_RESULT_UNVERIFIED_STOP
