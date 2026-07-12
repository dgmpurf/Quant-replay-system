"""Deterministic byte and JSON helpers for the synthetic registry."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize system-created JSON with a stable, non-recursive byte basis."""

    text = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return (text + "\n").encode("utf-8")


def decode_json_object(exact_bytes: bytes, *, label: str) -> dict[str, Any]:
    if exact_bytes.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"{label} must not contain a UTF-8 BOM")
    try:
        value = json.loads(exact_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def sha256_bytes(exact_bytes: bytes) -> str:
    return hashlib.sha256(exact_bytes).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_bytes_fsync(path: str | Path, exact_bytes: bytes, *, exclusive: bool = True) -> None:
    target = Path(path)
    mode = "xb" if exclusive else "wb"
    with target.open(mode) as handle:
        handle.write(exact_bytes)
        handle.flush()
        os.fsync(handle.fileno())


def write_canonical_json(path: str | Path, value: Any, *, exclusive: bool = True) -> bytes:
    exact_bytes = canonical_json_bytes(value)
    write_bytes_fsync(path, exact_bytes, exclusive=exclusive)
    return exact_bytes


def fsync_directory(path: str | Path) -> bool:
    """Fsync a directory where the platform exposes a compatible descriptor."""

    flags = getattr(os, "O_DIRECTORY", 0) | os.O_RDONLY
    try:
        descriptor = os.open(Path(path), flags)
    except (OSError, TypeError):
        return False
    try:
        os.fsync(descriptor)
    except OSError:
        return False
    finally:
        os.close(descriptor)
    return True
