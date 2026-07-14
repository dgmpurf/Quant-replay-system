from __future__ import annotations

import os
from pathlib import Path

import pytest

from quant_replay_system.accepted_lineage_registry.canonical import canonical_json_bytes
from quant_replay_system.accepted_lineage_registry.locking import LiveRegistryWriteLock, RegistryWriteLock
from quant_replay_system.accepted_lineage_registry.models import (
    GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE,
    GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE,
    GovernedLiveRegistryPolicy,
    RegistryError,
)
from quant_replay_system.accepted_lineage_registry.path_safety import (
    capture_live_root_parent_snapshot,
    revalidate_live_root_parent_snapshot,
    validate_candidate_live_root_separation,
    validate_live_registry_root_authority,
)
from quant_replay_system.accepted_lineage_registry.windows_live_backend import (
    LOCK_OWNERSHIP_UNVERIFIED_STOP,
    RENAME_RESULT_UNVERIFIED_STOP,
    WindowsLiveFilesystemBackend,
)


def _roots(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    admin = tmp_path / "admin"
    repository = tmp_path / "repository"
    candidate = admin / "retained-candidate"
    live = admin / "mode-neutral-target-name"
    admin.mkdir()
    repository.mkdir()
    candidate.mkdir()
    return admin, repository, candidate, live


def _write_policy(root: Path, mode: str) -> None:
    root.mkdir(exist_ok=True)
    (root / "registry_policy.json").write_bytes(canonical_json_bytes({"registry_mode": mode}))


class _RecordingLiveBackend(WindowsLiveFilesystemBackend):
    def __init__(self) -> None:
        super().__init__()
        self.events: list[str] = []

    def open_directory_no_reparse(
        self,
        path: str | Path,
        *,
        writable: bool = False,
        delete: bool = False,
    ):
        self.events.append("open_directory")
        return super().open_directory_no_reparse(path, writable=writable, delete=delete)

    def open_file_no_reparse(
        self,
        path: str | Path,
        *,
        writable: bool = False,
        delete: bool = False,
    ):
        self.events.append("open_file")
        return super().open_file_no_reparse(path, writable=writable, delete=delete)

    def verify_committed_directory_identity(self, path, expected):
        self.events.append("verify_live_root")
        return super().verify_committed_directory_identity(path, expected)

    def dispose_lock_by_verified_handle(self, lock_path, expected) -> None:
        self.events.append("dispose_verified_lock")
        return super().dispose_lock_by_verified_handle(lock_path, expected)


def _temporary_live_lock(
    tmp_path: Path,
    backend: WindowsLiveFilesystemBackend,
) -> LiveRegistryWriteLock:
    admin = tmp_path / "lock-admin"
    repository = tmp_path / "lock-repository"
    live = admin / "mode-neutral-lock-root"
    admin.mkdir()
    repository.mkdir()
    live.mkdir()
    return LiveRegistryWriteLock(
        registry_root=live,
        operator_alias="bounded-test-operator",
        operation_id="P2_DIRECT_LIVE_LOCK_TEST",
        approved_admin_root=admin,
        repository_root=repository,
        expected_registry_root=live,
        registry_mode=GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE,
        timeout_seconds=0.0,
        backend=backend,
    )


def test_live_root_authority_uses_explicit_mode_not_directory_name(tmp_path: Path) -> None:
    admin, repository, candidate, live = _roots(tmp_path)
    validated = validate_live_registry_root_authority(
        live,
        approved_admin_root=admin,
        repository_root=repository,
        expected_registry_root=live,
        candidate_root=candidate,
        expected_existing_state="ABSENT",
    )
    assert validated == live
    assert not live.exists()


def test_live_registry_write_lock_uses_explicit_backend_and_verified_disposition(tmp_path: Path) -> None:
    recording_backend = _RecordingLiveBackend()
    lock = _temporary_live_lock(tmp_path, recording_backend)

    assert lock.acquire() == "REGISTRY_WRITE_LOCK_ACQUIRED"
    assert lock.lock_path.is_file()
    lock.release()

    assert not lock.lock_path.exists()
    assert recording_backend.events.count("verify_live_root") == 2
    verify_indices = [
        index for index, event in enumerate(recording_backend.events) if event == "verify_live_root"
    ]
    dispose_index = recording_backend.events.index("dispose_verified_lock")
    assert dispose_index > verify_indices[-1]


def test_live_registry_write_lock_root_identity_change_fails_before_acquire(tmp_path: Path) -> None:
    lock = _temporary_live_lock(tmp_path, WindowsLiveFilesystemBackend())
    original_root = lock.registry_root.with_name("original-live-root")
    lock.registry_root.rename(original_root)
    lock.registry_root.mkdir()

    with pytest.raises(RegistryError) as caught:
        lock.acquire()

    assert caught.value.classification == RENAME_RESULT_UNVERIFIED_STOP
    assert not lock.lock_path.exists()


def test_live_registry_write_lock_requires_captured_lock_identity(tmp_path: Path) -> None:
    lock = _temporary_live_lock(tmp_path, WindowsLiveFilesystemBackend())
    lock.acquire()
    lock._live_lock_identity = None

    with pytest.raises(RegistryError) as caught:
        lock.release()

    assert caught.value.classification == LOCK_OWNERSHIP_UNVERIFIED_STOP
    assert lock.lock_path.is_file()


def test_live_registry_write_lock_preserves_replacement_owned_by_another_identity(tmp_path: Path) -> None:
    lock = _temporary_live_lock(tmp_path, WindowsLiveFilesystemBackend())
    lock.acquire()
    lock.lock_path.unlink()
    lock.lock_path.write_text("replacement-owned-by-another-identity\n", encoding="utf-8")

    with pytest.raises(RegistryError) as caught:
        lock.release()

    assert caught.value.classification == "REGISTRY_WRITE_LOCK_RELEASE_FAILED_HEALTH_WARNING"
    assert lock.lock_path.read_text(encoding="utf-8") == "replacement-owned-by-another-identity\n"


def test_base_registry_write_lock_remains_mode_neutral_and_backend_free(tmp_path: Path) -> None:
    admin = tmp_path / "base-admin"
    repository = tmp_path / "base-repository"
    synthetic = admin / "synthetic-registry"
    admin.mkdir()
    repository.mkdir()
    synthetic.mkdir()
    lock = RegistryWriteLock(
        registry_root=synthetic,
        operator_alias="bounded-test-operator",
        operation_id="P2_BASE_LOCK_REGRESSION",
        approved_admin_root=admin,
        repository_root=repository,
        timeout_seconds=0.0,
    )

    assert lock.acquire() == "REGISTRY_WRITE_LOCK_ACQUIRED"
    assert lock.lock_path.is_file()
    lock.release()
    assert not lock.lock_path.exists()


def test_live_root_exact_path_mismatch_stops(tmp_path: Path) -> None:
    admin, repository, candidate, live = _roots(tmp_path)
    with pytest.raises(RegistryError) as caught:
        validate_live_registry_root_authority(
            live,
            approved_admin_root=admin,
            repository_root=repository,
            expected_registry_root=admin / "different-live-root",
            candidate_root=candidate,
        )
    assert caught.value.classification == "LIVE_REGISTRY_EXACT_ROOT_MISMATCH_STOP"


@pytest.mark.parametrize("live_relation", ["same", "inside", "contains"])
def test_candidate_and_live_root_overlap_stops(tmp_path: Path, live_relation: str) -> None:
    admin, repository, candidate, live = _roots(tmp_path)
    if live_relation == "same":
        live = candidate
    elif live_relation == "inside":
        live = candidate / "live"
    else:
        live = admin / "parent"
        candidate.rename(live / "candidate") if False else None
        candidate = live / "candidate"
    with pytest.raises(RegistryError) as caught:
        validate_candidate_live_root_separation(
            candidate,
            live,
            approved_admin_root=admin,
            repository_root=repository,
        )
    assert caught.value.classification == "LIVE_REGISTRY_CANDIDATE_ROOT_OVERLAP_STOP"


def test_candidate_policy_cannot_be_reclassified_as_live(tmp_path: Path) -> None:
    admin, repository, candidate, live = _roots(tmp_path)
    _write_policy(live, GOVERNED_REAL_CANDIDATE_MATERIALIZATION_MODE)
    with pytest.raises(RegistryError) as caught:
        validate_live_registry_root_authority(
            live,
            approved_admin_root=admin,
            repository_root=repository,
            expected_registry_root=live,
            candidate_root=candidate,
        )
    assert caught.value.classification == "LIVE_REGISTRY_CANDIDATE_POLICY_RECLASSIFICATION_STOP"


def test_wrong_policy_root_cannot_be_reused(tmp_path: Path) -> None:
    admin, repository, candidate, live = _roots(tmp_path)
    _write_policy(live, "SYNTHETIC_FIXTURE_ONLY_NOT_A_PILOT")
    with pytest.raises(RegistryError) as caught:
        validate_live_registry_root_authority(
            live,
            approved_admin_root=admin,
            repository_root=repository,
            expected_registry_root=live,
            candidate_root=candidate,
        )
    assert caught.value.classification == "LIVE_REGISTRY_WRONG_POLICY_STOP"


def test_empty_existing_root_is_unexpected(tmp_path: Path) -> None:
    admin, repository, candidate, live = _roots(tmp_path)
    live.mkdir()
    with pytest.raises(RegistryError) as caught:
        validate_live_registry_root_authority(
            live,
            approved_admin_root=admin,
            repository_root=repository,
            expected_registry_root=live,
            candidate_root=candidate,
        )
    assert caught.value.classification == "LIVE_REGISTRY_UNEXPECTED_EXISTING_ROOT_STOP"


def test_explicit_live_policy_is_accepted_only_as_initialized_live(tmp_path: Path) -> None:
    admin, repository, candidate, live = _roots(tmp_path)
    _write_policy(live, GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE)
    validated = validate_live_registry_root_authority(
        live,
        approved_admin_root=admin,
        repository_root=repository,
        expected_registry_root=live,
        candidate_root=candidate,
        expected_existing_state="INITIALIZED_LIVE",
    )
    assert validated == live
    assert GovernedLiveRegistryPolicy().registry_mode == GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE


def test_live_parent_snapshot_detects_identity_change(tmp_path: Path) -> None:
    admin, repository, candidate, live = _roots(tmp_path)
    snapshot = capture_live_root_parent_snapshot(live, approved_admin_root=admin)
    original = tmp_path / "original-admin"
    admin.rename(original)
    admin.mkdir()
    with pytest.raises(RegistryError) as caught:
        revalidate_live_root_parent_snapshot(live, snapshot, approved_admin_root=admin)
    assert caught.value.classification == "LIVE_REGISTRY_ROOT_IDENTITY_CHANGED_STOP"


def test_live_root_reparse_component_stops_without_skip(tmp_path: Path) -> None:
    admin, repository, candidate, live = _roots(tmp_path)
    target = admin / "target"
    target.mkdir()
    os.symlink(target, live, target_is_directory=True)
    with pytest.raises(RegistryError) as caught:
        validate_live_registry_root_authority(
            live,
            approved_admin_root=admin,
            repository_root=repository,
            expected_registry_root=live,
            candidate_root=candidate,
        )
    assert caught.value.classification == "LIVE_REGISTRY_REPARSE_OR_INDIRECTION_STOP"
