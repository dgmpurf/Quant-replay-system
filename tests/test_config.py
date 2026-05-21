from pathlib import Path

import pytest

from quant_replay_system.config import load_settings


def test_load_default_settings() -> None:
    settings = load_settings(Path("config/default.yaml"))

    assert settings.project.name == "quant-replay-system"
    assert settings.execution.mode == "t_plus_1"
    assert settings.risk.allow_live_trading is False


def test_live_trading_is_rejected(tmp_path: Path) -> None:
    config_path = tmp_path / "unsafe.yaml"
    config_path.write_text(
        """
project:
  name: quant-replay-system
data: {}
output: {}
scoring: {}
execution: {}
risk:
  allow_live_trading: true
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="allow_live_trading"):
        load_settings(config_path)
