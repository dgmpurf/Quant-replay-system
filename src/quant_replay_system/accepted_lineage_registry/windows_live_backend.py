"""Fail-closed Windows handle operations for prospective live registry support."""

from __future__ import annotations

import ctypes
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from .models import RegistryError


REPARSE_OPEN_UNAVAILABLE_STOP = "LIVE_WINDOWS_REPARSE_SAFE_HANDLE_OPEN_UNAVAILABLE_STOP"
FILE_FLUSH_FAILED_STOP = "LIVE_WINDOWS_FILE_FLUSH_FAILED_STOP"
DIRECTORY_DURABILITY_UNPROVEN_STOP = "LIVE_WINDOWS_DIRECTORY_DURABILITY_UNPROVEN_STOP"
HANDLE_RELATIVE_RENAME_UNAVAILABLE_STOP = "LIVE_WINDOWS_HANDLE_RELATIVE_RENAME_UNAVAILABLE_STOP"
RENAME_RESULT_UNVERIFIED_STOP = "LIVE_WINDOWS_RENAME_RESULT_UNVERIFIED_STOP"
LOCK_OWNERSHIP_UNVERIFIED_STOP = "LIVE_WINDOWS_LOCK_OWNERSHIP_UNVERIFIED_STOP"
HARDLINK_OR_IDENTITY_DRIFT_STOP = "LIVE_WINDOWS_HARDLINK_OR_IDENTITY_DRIFT_STOP"
CRASH_RECOVERY_REVIEW_REQUIRED = "LIVE_WINDOWS_CRASH_RECOVERY_REVIEW_REQUIRED"


@dataclass(frozen=True)
class WindowsHandleIdentity:
    volume_serial_number: int
    file_index: int
    number_of_links: int
    file_attributes: int
    file_size: int
    is_directory: bool


@dataclass(frozen=True)
class WindowsCapabilityReport:
    backend_status: str
    windows_backend_available: bool
    reparse_safe_handle_open: bool
    volume_and_file_identity_queries: bool
    hardlink_count_query: bool
    file_handle_flush: bool
    directory_handle_flush_observed: bool
    directory_durability_proven: bool
    handle_relative_same_volume_rename: bool
    verified_handle_lock_disposition: bool
    L2_platform_acceptance_granted: bool
    risk_waiver_granted: bool
    residual_risks: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["residual_risks"] = list(self.residual_risks)
        return value


if os.name == "nt":
    from ctypes import wintypes

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
    _INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    class _BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

    class _FILE_STANDARD_INFO(ctypes.Structure):
        _fields_ = [
            ("AllocationSize", ctypes.c_longlong),
            ("EndOfFile", ctypes.c_longlong),
            ("NumberOfLinks", wintypes.DWORD),
            ("DeletePending", ctypes.c_ubyte),
            ("Directory", ctypes.c_ubyte),
        ]

    class _FILE_ATTRIBUTE_TAG_INFO(ctypes.Structure):
        _fields_ = [
            ("FileAttributes", wintypes.DWORD),
            ("ReparseTag", wintypes.DWORD),
        ]

    class _FILE_RENAME_INFO_HEADER(ctypes.Structure):
        _fields_ = [
            ("ReplaceIfExists", ctypes.c_ubyte),
            ("RootDirectory", wintypes.HANDLE),
            ("FileNameLength", wintypes.DWORD),
        ]

    class _FILE_DISPOSITION_INFO(ctypes.Structure):
        _fields_ = [("DeleteFile", ctypes.c_ubyte)]

    class _IO_STATUS_BLOCK(ctypes.Structure):
        _fields_ = [
            ("Status", ctypes.c_void_p),
            ("Information", ctypes.c_size_t),
        ]

    _kernel32.CreateFileW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    _kernel32.CreateFileW.restype = wintypes.HANDLE
    _kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _kernel32.CloseHandle.restype = wintypes.BOOL
    _kernel32.GetFileInformationByHandle.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_BY_HANDLE_FILE_INFORMATION),
    )
    _kernel32.GetFileInformationByHandle.restype = wintypes.BOOL
    _kernel32.GetFileInformationByHandleEx.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    _kernel32.GetFileInformationByHandleEx.restype = wintypes.BOOL
    _kernel32.FlushFileBuffers.argtypes = (wintypes.HANDLE,)
    _kernel32.FlushFileBuffers.restype = wintypes.BOOL
    _kernel32.SetFileInformationByHandle.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    _kernel32.SetFileInformationByHandle.restype = wintypes.BOOL
    _ntdll.NtSetInformationFile.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_IO_STATUS_BLOCK),
        wintypes.LPVOID,
        wintypes.ULONG,
        ctypes.c_int,
    )
    _ntdll.NtSetInformationFile.restype = ctypes.c_long
    _ntdll.RtlNtStatusToDosError.argtypes = (ctypes.c_long,)
    _ntdll.RtlNtStatusToDosError.restype = wintypes.ULONG
else:
    wintypes = None
    _kernel32 = None
    _ntdll = None
    _INVALID_HANDLE_VALUE = -1


_GENERIC_READ = 0x80000000
_GENERIC_WRITE = 0x40000000
_DELETE = 0x00010000
_FILE_READ_ATTRIBUTES = 0x0080
_FILE_SHARE_READ = 0x00000001
_FILE_SHARE_WRITE = 0x00000002
_FILE_SHARE_DELETE = 0x00000004
_OPEN_EXISTING = 3
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
_FILE_STANDARD_INFO_CLASS = 1
_FILE_RENAME_INFO_CLASS = 3
_FILE_RENAME_INFORMATION_CLASS = 10
_FILE_DISPOSITION_INFO_CLASS = 4
_FILE_ATTRIBUTE_TAG_INFO_CLASS = 9


def _raise_last_error(classification: str, message: str) -> None:
    raise RegistryError(
        classification,
        message,
        details={"winerror": int(ctypes.get_last_error())},
    )


def _raise_ntstatus(classification: str, message: str, status: int) -> None:
    winerror = int(_ntdll.RtlNtStatusToDosError(status)) if _ntdll is not None else 0
    raise RegistryError(
        classification,
        message,
        details={
            "ntstatus": f"0x{ctypes.c_ulong(status).value:08x}",
            "winerror": winerror,
        },
    )


class _WindowsHandle:
    def __init__(self, value: int) -> None:
        self.value = value
        self.closed = False

    def close(self) -> None:
        if not self.closed and _kernel32 is not None:
            if not _kernel32.CloseHandle(self.value):
                _raise_last_error(CRASH_RECOVERY_REVIEW_REQUIRED, "Windows handle close failed")
            self.closed = True

    def __enter__(self) -> "_WindowsHandle":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()


class WindowsLiveFilesystemBackend:
    """Use retained Windows handles and fail closed on unverified controls."""

    backend_status = "IMPLEMENTED_FAIL_CLOSED_PENDING_SEPARATE_L2_HUMAN_ACCEPTANCE"

    def __init__(self) -> None:
        if os.name != "nt" or _kernel32 is None:
            raise RegistryError(REPARSE_OPEN_UNAVAILABLE_STOP, "Windows handle backend is unavailable")

    def _open(
        self,
        path: str | Path,
        *,
        directory: bool,
        writable: bool = False,
        delete: bool = False,
    ) -> _WindowsHandle:
        access = _FILE_READ_ATTRIBUTES | _GENERIC_READ
        if writable:
            access |= _GENERIC_WRITE
        if delete:
            access |= _DELETE
        flags = _FILE_FLAG_OPEN_REPARSE_POINT
        if directory:
            flags |= _FILE_FLAG_BACKUP_SEMANTICS
        value = _kernel32.CreateFileW(
            os.fspath(Path(path)),
            access,
            _FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE,
            None,
            _OPEN_EXISTING,
            flags,
            None,
        )
        if value == _INVALID_HANDLE_VALUE:
            _raise_last_error(REPARSE_OPEN_UNAVAILABLE_STOP, "Reparse-safe Windows handle open failed")
        handle = _WindowsHandle(value)
        try:
            identity = self.query_handle_identity(handle)
            if identity.is_directory != directory:
                raise RegistryError(REPARSE_OPEN_UNAVAILABLE_STOP, "Windows handle type differs from expectation")
            if identity.file_attributes & _FILE_ATTRIBUTE_REPARSE_POINT:
                raise RegistryError(REPARSE_OPEN_UNAVAILABLE_STOP, "Reparse-point handle rejected")
        except Exception:
            handle.close()
            raise
        return handle

    def open_directory_no_reparse(
        self,
        path: str | Path,
        *,
        writable: bool = False,
        delete: bool = False,
    ) -> _WindowsHandle:
        return self._open(path, directory=True, writable=writable, delete=delete)

    def open_file_no_reparse(
        self,
        path: str | Path,
        *,
        writable: bool = False,
        delete: bool = False,
    ) -> _WindowsHandle:
        return self._open(path, directory=False, writable=writable, delete=delete)

    def query_handle_identity(self, handle: _WindowsHandle) -> WindowsHandleIdentity:
        basic = _BY_HANDLE_FILE_INFORMATION()
        if not _kernel32.GetFileInformationByHandle(handle.value, ctypes.byref(basic)):
            _raise_last_error(HARDLINK_OR_IDENTITY_DRIFT_STOP, "Windows file identity query failed")
        standard = _FILE_STANDARD_INFO()
        if not _kernel32.GetFileInformationByHandleEx(
            handle.value,
            _FILE_STANDARD_INFO_CLASS,
            ctypes.byref(standard),
            ctypes.sizeof(standard),
        ):
            _raise_last_error(HARDLINK_OR_IDENTITY_DRIFT_STOP, "Windows link-count query failed")
        tag = _FILE_ATTRIBUTE_TAG_INFO()
        if not _kernel32.GetFileInformationByHandleEx(
            handle.value,
            _FILE_ATTRIBUTE_TAG_INFO_CLASS,
            ctypes.byref(tag),
            ctypes.sizeof(tag),
        ):
            _raise_last_error(REPARSE_OPEN_UNAVAILABLE_STOP, "Windows reparse attribute query failed")
        if int(basic.nNumberOfLinks) != int(standard.NumberOfLinks):
            raise RegistryError(HARDLINK_OR_IDENTITY_DRIFT_STOP, "Windows link-count queries disagree")
        return WindowsHandleIdentity(
            volume_serial_number=int(basic.dwVolumeSerialNumber),
            file_index=(int(basic.nFileIndexHigh) << 32) | int(basic.nFileIndexLow),
            number_of_links=int(standard.NumberOfLinks),
            file_attributes=int(tag.FileAttributes),
            file_size=(int(basic.nFileSizeHigh) << 32) | int(basic.nFileSizeLow),
            is_directory=bool(standard.Directory),
        )

    def query_link_count(self, handle: _WindowsHandle) -> int:
        count = self.query_handle_identity(handle).number_of_links
        if count != 1:
            raise RegistryError(HARDLINK_OR_IDENTITY_DRIFT_STOP, "Windows object has multiple hard links")
        return count

    def flush_file_handle(self, handle: _WindowsHandle) -> None:
        if not _kernel32.FlushFileBuffers(handle.value):
            _raise_last_error(FILE_FLUSH_FAILED_STOP, "Windows file-handle flush failed")

    def flush_directory_handle(self, handle: _WindowsHandle) -> bool:
        if not _kernel32.FlushFileBuffers(handle.value):
            _raise_last_error(
                DIRECTORY_DURABILITY_UNPROVEN_STOP,
                "Windows directory-handle flush was not observed",
            )
        return True

    def verify_committed_directory_identity(
        self,
        path: str | Path,
        expected: WindowsHandleIdentity,
    ) -> WindowsHandleIdentity:
        with self.open_directory_no_reparse(path) as handle:
            observed = self.query_handle_identity(handle)
        if observed != expected or observed.number_of_links != 1:
            raise RegistryError(RENAME_RESULT_UNVERIFIED_STOP, "Committed directory identity differs")
        return observed

    def rename_directory_by_handle(
        self,
        source_path: str | Path,
        target_parent: str | Path,
        target_name: str,
    ) -> WindowsHandleIdentity:
        if not target_name or target_name in {".", ".."} or "/" in target_name or "\\" in target_name:
            raise RegistryError(HANDLE_RELATIVE_RENAME_UNAVAILABLE_STOP, "Target name is not one safe component")
        source = Path(source_path)
        target = Path(target_parent) / target_name
        with self.open_directory_no_reparse(source, delete=True) as source_handle:
            before = self.query_handle_identity(source_handle)
            self.query_link_count(source_handle)
            with self.open_directory_no_reparse(target_parent) as parent_handle:
                encoded_name = target_name.encode("utf-16-le")
                name_offset = _FILE_RENAME_INFO_HEADER.FileNameLength.offset + ctypes.sizeof(ctypes.c_ulong)
                size = max(ctypes.sizeof(_FILE_RENAME_INFO_HEADER), name_offset + len(encoded_name))
                buffer = ctypes.create_string_buffer(size)
                header = _FILE_RENAME_INFO_HEADER.from_buffer(buffer)
                header.ReplaceIfExists = 0
                header.RootDirectory = parent_handle.value
                header.FileNameLength = len(encoded_name)
                ctypes.memmove(ctypes.addressof(buffer) + name_offset, encoded_name, len(encoded_name))
                io_status = _IO_STATUS_BLOCK()
                status = _ntdll.NtSetInformationFile(
                    source_handle.value,
                    ctypes.byref(io_status),
                    ctypes.byref(buffer),
                    size,
                    _FILE_RENAME_INFORMATION_CLASS,
                )
                if status < 0:
                    _raise_ntstatus(
                        HANDLE_RELATIVE_RENAME_UNAVAILABLE_STOP,
                        "Handle-relative Windows directory rename failed",
                        status,
                    )
        if os.path.lexists(source) or not os.path.lexists(target):
            raise RegistryError(RENAME_RESULT_UNVERIFIED_STOP, "Rename source/target state is ambiguous")
        return self.verify_committed_directory_identity(target, before)

    def dispose_lock_by_verified_handle(
        self,
        lock_path: str | Path,
        expected: WindowsHandleIdentity,
    ) -> None:
        path = Path(lock_path)
        with self.open_file_no_reparse(path, delete=True) as handle:
            observed = self.query_handle_identity(handle)
            if observed != expected or observed.number_of_links != 1:
                raise RegistryError(LOCK_OWNERSHIP_UNVERIFIED_STOP, "Lock handle identity differs")
            disposition = _FILE_DISPOSITION_INFO(DeleteFile=1)
            if not _kernel32.SetFileInformationByHandle(
                handle.value,
                _FILE_DISPOSITION_INFO_CLASS,
                ctypes.byref(disposition),
                ctypes.sizeof(disposition),
            ):
                _raise_last_error(LOCK_OWNERSHIP_UNVERIFIED_STOP, "Verified lock disposition failed")
        if os.path.lexists(path):
            raise RegistryError(LOCK_OWNERSHIP_UNVERIFIED_STOP, "Verified lock remained after disposition")

    def capability_report(self) -> WindowsCapabilityReport:
        return WindowsCapabilityReport(
            backend_status=self.backend_status,
            windows_backend_available=True,
            reparse_safe_handle_open=True,
            volume_and_file_identity_queries=True,
            hardlink_count_query=True,
            file_handle_flush=True,
            directory_handle_flush_observed=False,
            directory_durability_proven=False,
            handle_relative_same_volume_rename=True,
            verified_handle_lock_disposition=True,
            L2_platform_acceptance_granted=False,
            risk_waiver_granted=False,
            residual_risks=(
                "WINDOWS_DIRECTORY_DURABILITY_REQUIRES_SEPARATE_L2_HUMAN_ACCEPTANCE",
                "WINDOWS_HANDLE_BACKEND_IMPLEMENTATION_IS_NOT_A_RISK_WAIVER",
            ),
        )
