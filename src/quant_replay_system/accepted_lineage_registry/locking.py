"""Single-writer lock with ownership-verified safe release."""

from __future__ import annotations

import json
import os
import secrets
import stat
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence

from .canonical import canonical_json_bytes, sha256_bytes
from .models import (
    GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE,
    SYNTHETIC_MODE,
    RegistryError,
)
from .path_safety import (
    FILE_ATTRIBUTE_REPARSE_POINT,
    assert_regular_single_link_file,
    validate_registry_root_authority,
    validate_safe_directory_chain,
)
from .windows_live_backend import WindowsHandleIdentity, WindowsLiveFilesystemBackend


LOCK_FILENAME = ".registry-write.lock"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _attributes(file_stat: os.stat_result) -> int:
    return int(getattr(file_stat, "st_file_attributes", 0) or 0)


def _identity(file_stat: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        int(file_stat.st_dev),
        int(file_stat.st_ino),
        int(file_stat.st_mode),
        int(getattr(file_stat, "st_nlink", 1)),
        _attributes(file_stat),
    )


@dataclass
class RegistryWriteLock:
    registry_root: Path
    operator_alias: str
    operation_id: str
    approved_admin_root: Path
    repository_root: Path
    protected_roots: Sequence[Path] = ()
    expected_registry_root: Path | None = None
    registry_mode: str = SYNTHETIC_MODE
    timeout_seconds: float = 5.0
    stale_after_seconds: float = 300.0
    clock: Callable[[], datetime] = _utc_now

    def __post_init__(self) -> None:
        self.registry_root = validate_registry_root_authority(
            self.registry_root,
            approved_admin_root=self.approved_admin_root,
            repository_root=self.repository_root,
            protected_roots=self.protected_roots,
            expected_registry_root=self.expected_registry_root,
            registry_mode=self.registry_mode,
            create=False,
        )
        validate_safe_directory_chain(self.registry_root, containment_root=self.approved_admin_root, create=False)
        self._owned = False
        self._lock_path = self.registry_root / LOCK_FILENAME
        self._operation_nonce: str | None = None
        self._captured_identity: tuple[int, int, int, int, int] | None = None
        self._metadata_sha256: str | None = None

    @property
    def lock_path(self) -> Path:
        return self._lock_path

    @property
    def operation_nonce(self) -> str | None:
        return self._operation_nonce

    def acquire(self) -> str:
        validate_safe_directory_chain(self.registry_root, containment_root=self.approved_admin_root, create=False)
        deadline = time.monotonic() + max(0.0, self.timeout_seconds)
        nonce = secrets.token_hex(32)
        metadata = {
            "created_at": _timestamp(self.clock()),
            "lock_schema_version": "accepted-lineage-registry-write-lock-v0.1",
            "operation_identifier": self.operation_id,
            "operation_nonce": nonce,
            "process_identifier": os.getpid(),
            "synthetic_operator_alias": self.operator_alias,
        }
        exact_bytes = canonical_json_bytes(metadata)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        flags |= int(getattr(os, "O_NOFOLLOW", 0))
        while True:
            try:
                descriptor = os.open(self._lock_path, flags, 0o600)
                try:
                    os.write(descriptor, exact_bytes)
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
                assert_regular_single_link_file(self._lock_path)
                file_stat = os.lstat(self._lock_path)
                self._operation_nonce = nonce
                self._captured_identity = _identity(file_stat)
                self._metadata_sha256 = sha256_bytes(exact_bytes)
                self._owned = True
                return "REGISTRY_WRITE_LOCK_ACQUIRED"
            except FileExistsError:
                if time.monotonic() >= deadline:
                    self._raise_timeout_or_stale()
                time.sleep(min(0.02, max(0.0, deadline - time.monotonic())))

    def _raise_timeout_or_stale(self) -> None:
        try:
            assert_regular_single_link_file(self._lock_path)
            data = json.loads(self._lock_path.read_text(encoding="utf-8"))
            created_at = datetime.fromisoformat(str(data["created_at"]).replace("Z", "+00:00"))
            age = (self.clock() - created_at).total_seconds()
        except Exception:
            age = self.stale_after_seconds + 1
        if age > self.stale_after_seconds:
            raise RegistryError(
                "REGISTRY_STALE_LOCK_DETECTED_HUMAN_REVIEW_REQUIRED",
                "A stale or unreadable registry lock requires human review",
            )
        raise RegistryError("REGISTRY_WRITE_LOCK_TIMEOUT_STOP", "Exclusive registry write lock timed out")

    def _validate_release_ownership(self) -> None:
        if self._captured_identity is None or self._metadata_sha256 is None or self._operation_nonce is None:
            raise RegistryError(
                "REGISTRY_WRITE_LOCK_RELEASE_FAILED_HEALTH_WARNING",
                "Lock ownership state is incomplete; lock preserved for review",
            )
        try:
            assert_regular_single_link_file(
                self._lock_path,
                classification="REGISTRY_WRITE_LOCK_RELEASE_FAILED_HEALTH_WARNING",
            )
            before = os.lstat(self._lock_path)
            if stat.S_ISLNK(before.st_mode) or _attributes(before) & FILE_ATTRIBUTE_REPARSE_POINT:
                raise OSError("indirect lock")
            if _identity(before) != self._captured_identity:
                raise OSError("lock identity changed")
            flags = os.O_RDONLY | int(getattr(os, "O_NOFOLLOW", 0))
            descriptor = os.open(self._lock_path, flags)
            try:
                opened = os.fstat(descriptor)
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(descriptor, 65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
            finally:
                os.close(descriptor)
            exact_bytes = b"".join(chunks)
            after = os.lstat(self._lock_path)
            if _identity(opened) != self._captured_identity or _identity(after) != self._captured_identity:
                raise OSError("lock identity changed during release")
            if sha256_bytes(exact_bytes) != self._metadata_sha256:
                raise OSError("lock metadata changed")
            metadata = json.loads(exact_bytes.decode("utf-8"))
            if metadata.get("operation_nonce") != self._operation_nonce:
                raise OSError("lock nonce changed")
            if metadata.get("operation_identifier") != self.operation_id:
                raise OSError("lock operation changed")
        except (OSError, ValueError, KeyError, json.JSONDecodeError, RegistryError) as exc:
            if isinstance(exc, RegistryError) and exc.classification == "REGISTRY_WRITE_LOCK_RELEASE_FAILED_HEALTH_WARNING":
                raise
            raise RegistryError(
                "REGISTRY_WRITE_LOCK_RELEASE_FAILED_HEALTH_WARNING",
                "Registry lock ownership changed; lock was not unlinked",
                details={"lock_preserved": True},
            ) from exc

    def release(self) -> None:
        if not self._owned:
            return
        try:
            validate_safe_directory_chain(self.registry_root, containment_root=self.approved_admin_root, create=False)
            self._validate_release_ownership()
            os.unlink(self._lock_path)
        except RegistryError:
            raise
        except OSError as exc:
            raise RegistryError(
                "REGISTRY_WRITE_LOCK_RELEASE_FAILED_HEALTH_WARNING",
                "Registry write lock release failed; lock state requires review",
                details={"lock_preserved": self._lock_path.exists()},
            ) from exc
        finally:
            self._owned = False

    def __enter__(self) -> "RegistryWriteLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.release()


@dataclass
class LiveRegistryWriteLock(RegistryWriteLock):
    backend: WindowsLiveFilesystemBackend | None = None

    def __post_init__(self) -> None:
        if self.registry_mode != GOVERNED_LIVE_ACCEPTED_LINEAGE_MATERIALIZATION_MODE:
            raise RegistryError(
                "LIVE_REGISTRY_WRONG_POLICY_STOP",
                "Live lock requires explicit live registry mode",
            )
        super().__post_init__()
        self.backend = self.backend or WindowsLiveFilesystemBackend()
        with self.backend.open_directory_no_reparse(self.registry_root) as handle:
            self._live_root_identity = self.backend.query_handle_identity(handle)
        self._live_lock_identity: WindowsHandleIdentity | None = None

    def _verify_live_root_identity(self) -> None:
        assert self.backend is not None
        observed = self.backend.verify_committed_directory_identity(
            self.registry_root,
            self._live_root_identity,
        )
        if observed.number_of_links != 1:
            raise RegistryError(
                "LIVE_REGISTRY_ROOT_IDENTITY_CHANGED_STOP",
                "Live registry root identity or link count changed",
            )

    def acquire(self) -> str:
        self._verify_live_root_identity()
        result = super().acquire()
        assert self.backend is not None
        with self.backend.open_file_no_reparse(self.lock_path) as handle:
            self._live_lock_identity = self.backend.query_handle_identity(handle)
            self.backend.query_link_count(handle)
        return result

    def release(self) -> None:
        if not self._owned:
            return
        try:
            self._verify_live_root_identity()
            self._validate_release_ownership()
            if self._live_lock_identity is None:
                raise RegistryError(
                    "LIVE_WINDOWS_LOCK_OWNERSHIP_UNVERIFIED_STOP",
                    "Live lock handle identity was not captured",
                )
            assert self.backend is not None
            self.backend.dispose_lock_by_verified_handle(
                self.lock_path,
                self._live_lock_identity,
            )
        finally:
            self._owned = False


def inspect_lock(
    registry_root: str | Path,
    *,
    approved_admin_root: str | Path,
    repository_root: str | Path,
    protected_roots: Sequence[str | Path] = (),
    expected_registry_root: str | Path | None = None,
    registry_mode: str = SYNTHETIC_MODE,
    stale_after_seconds: float = 300.0,
) -> str:
    root = validate_registry_root_authority(
        registry_root,
        approved_admin_root=approved_admin_root,
        repository_root=repository_root,
        protected_roots=protected_roots,
        expected_registry_root=expected_registry_root,
        registry_mode=registry_mode,
        create=False,
    )
    lock_path = root / LOCK_FILENAME
    if not lock_path.exists():
        return "UNLOCKED"
    try:
        assert_regular_single_link_file(lock_path)
        data = json.loads(lock_path.read_text(encoding="utf-8"))
        created_at = datetime.fromisoformat(str(data["created_at"]).replace("Z", "+00:00"))
        age = (_utc_now() - created_at).total_seconds()
    except Exception:
        return "STALE_OR_UNREADABLE_HUMAN_REVIEW_REQUIRED"
    if age > stale_after_seconds:
        return "STALE_HUMAN_REVIEW_REQUIRED"
    return "LOCKED"
