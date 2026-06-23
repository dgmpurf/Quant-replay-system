"""Small pandas markdown fallback for environments without tabulate."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pandas as pd


_PATCH_MARKER = "_quant_replay_system_markdown_fallback_installed"


def install_pandas_markdown_fallback() -> None:
    """Install a minimal DataFrame.to_markdown fallback when tabulate is absent."""

    if getattr(pd.DataFrame, _PATCH_MARKER, False):
        return
    if importlib.util.find_spec("tabulate") is not None:
        return

    def _to_markdown(
        self: pd.DataFrame,
        buf: Any = None,
        *,
        mode: str = "wt",
        index: bool = True,
        storage_options: Any = None,
        **_: Any,
    ) -> str | None:
        _ = storage_options
        markdown = _render_markdown_table(self, index=index)
        if buf is None:
            return markdown
        if hasattr(buf, "write"):
            buf.write(markdown)
            return None
        Path(buf).write_text(markdown, encoding="utf-8")
        _ = mode
        return None

    pd.DataFrame.to_markdown = _to_markdown  # type: ignore[method-assign]
    setattr(pd.DataFrame, _PATCH_MARKER, True)


def _render_markdown_table(frame: pd.DataFrame, *, index: bool) -> str:
    table_frame = frame.reset_index() if index else frame.copy()
    columns = [str(column) for column in table_frame.columns]
    header = "| " + " | ".join(_markdown_cell(column) for column in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for row in table_frame.itertuples(index=False, name=None):
        rows.append("| " + " | ".join(_markdown_cell(value) for value in row) + " |")
    return "\n".join([header, separator, *rows])


def _markdown_cell(value: Any) -> str:
    if _is_missing(value):
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ")
    return text.replace("|", "\\|")


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        missing = pd.isna(value)
    except (TypeError, ValueError):
        return False
    if isinstance(missing, bool):
        return missing
    return False
