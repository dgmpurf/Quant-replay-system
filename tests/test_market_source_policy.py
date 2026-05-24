import json
from pathlib import Path

import pandas as pd

from quant_replay_system import cli
from quant_replay_system.config import load_settings
from quant_replay_system.market_source_policy import (
    MarketFieldReliability,
    annotate_market_frame_with_field_reliability,
    build_market_comparison_policy_hints,
    get_market_field_reliability,
    run_market_source_policy_report,
    select_preferred_source_for_fields,
    summarize_market_source_policy,
)


def test_market_source_policy_loads_default_config() -> None:
    settings = load_settings(Path("config/default.yaml"))
    frame = summarize_market_source_policy(config=settings)

    assert not frame.empty
    assert "AKSHARE_OPTIONAL" in set(frame["source"])
    assert "BAOSTOCK_OPTIONAL" in set(frame["source"])


def test_akshare_tencent_stock_core_fields_are_reliable() -> None:
    settings = load_settings(Path("config/default.yaml"))

    for field in ["close", "volume", "amount"]:
        assert (
            get_market_field_reliability(
                source="AKSHARE_OPTIONAL",
                upstream_source="TENCENT",
                security_type="STOCK",
                field=field,
                config=settings,
            )
            == MarketFieldReliability.RELIABLE
        )


def test_akshare_tencent_stock_pre_close_has_first_window_caveat() -> None:
    assert (
        get_market_field_reliability(
            source="AKSHARE_OPTIONAL",
            upstream_source="TENCENT",
            security_type="STOCK",
            field="pre_close",
        )
        == MarketFieldReliability.CAVEAT_FIRST_WINDOW_ROW
    )


def test_akshare_sina_etf_fields_are_provisional() -> None:
    assert (
        get_market_field_reliability(
            source="AKSHARE_OPTIONAL",
            upstream_source="SINA",
            security_type="ETF",
            field="amount",
        )
        == MarketFieldReliability.PROVISIONAL
    )


def test_baostock_stock_amount_is_reliable() -> None:
    assert (
        get_market_field_reliability(
            source="BAOSTOCK_OPTIONAL",
            upstream_source="BAOSTOCK",
            security_type="STOCK",
            field="amount",
        )
        == MarketFieldReliability.RELIABLE
    )


def test_baostock_etf_fields_are_unavailable() -> None:
    assert (
        get_market_field_reliability(
            source="BAOSTOCK_OPTIONAL",
            upstream_source="BAOSTOCK",
            security_type="ETF",
            field="close",
        )
        == MarketFieldReliability.UNAVAILABLE
    )


def test_unknown_source_returns_unknown() -> None:
    assert (
        get_market_field_reliability(
            source="UNKNOWN_SOURCE",
            upstream_source="UNKNOWN_UPSTREAM",
            security_type="STOCK",
            field="amount",
        )
        == MarketFieldReliability.UNKNOWN
    )


def test_source_preference_for_amount_sensitive_stock_allows_tencent_and_baostock() -> None:
    preferred = select_preferred_source_for_fields(
        source_a="AKSHARE_OPTIONAL",
        upstream_source_a="TENCENT",
        source_b="BAOSTOCK_OPTIONAL",
        upstream_source_b="BAOSTOCK",
        security_type="STOCK",
        fields=["amount"],
    )

    assert preferred == "AKSHARE_OPTIONAL,BAOSTOCK_OPTIONAL"


def test_source_preference_for_etf_amount_prefers_akshare_sina_provisional() -> None:
    preferred = select_preferred_source_for_fields(
        source_a="AKSHARE_OPTIONAL",
        upstream_source_a="SINA",
        source_b="BAOSTOCK_OPTIONAL",
        upstream_source_b="BAOSTOCK",
        security_type="ETF",
        fields=["amount"],
    )

    assert preferred == "AKSHARE_OPTIONAL"


def test_market_comparison_policy_hints_for_stock() -> None:
    frame = pd.DataFrame(
        [
            {
                "symbol": "000001",
                "upstream_source_a": "TENCENT",
                "upstream_source_b": "BAOSTOCK",
            }
        ]
    )

    hints = build_market_comparison_policy_hints(
        frame,
        symbol="000001",
        source_a="AKSHARE_OPTIONAL",
        source_b="BAOSTOCK_OPTIONAL",
    )

    assert hints["policy_security_type"] == "STOCK"
    assert hints["recommended_for_amount"] == "AKSHARE_OPTIONAL,BAOSTOCK_OPTIONAL"
    assert hints["pre_close_caveat"] == "CAVEAT_FIRST_WINDOW_ROW"
    assert json.loads(hints["source_a_field_reliability"])["amount"] == "RELIABLE"


def test_annotate_market_frame_with_field_reliability() -> None:
    frame = pd.DataFrame([{"symbol": "000001", "close": 10.0}])

    annotated = annotate_market_frame_with_field_reliability(
        frame,
        source="AKSHARE_OPTIONAL",
        upstream_source="TENCENT",
        security_type="STOCK",
        fields=["close", "pre_close"],
    )

    assert annotated.iloc[0]["close_reliability"] == "RELIABLE"
    assert annotated.iloc[0]["pre_close_reliability"] == "CAVEAT_FIRST_WINDOW_ROW"


def test_market_source_policy_report_artifacts(tmp_path: Path) -> None:
    settings = load_settings(Path("config/default.yaml")).model_copy(
        update={
            "market_source_policy": load_settings(Path("config/default.yaml")).market_source_policy.model_copy(
                update={"output_dir": tmp_path / "policy"}
            )
        }
    )

    result = run_market_source_policy_report(config=settings)
    metadata = json.loads(result.artifact_paths["metadata"].read_text(encoding="utf-8"))
    policy_csv = pd.read_csv(result.artifact_paths["market_source_policy_csv"])

    assert result.status == "PASS"
    assert result.row_count == len(policy_csv)
    assert result.artifact_paths["market_source_policy_report"].exists()
    assert metadata["no_live_trading"] is True
    assert metadata["no_broker_api"] is True


def test_cli_market_source_policy_works(tmp_path: Path, capsys) -> None:
    code = cli.main(["market-source-policy", "--output-dir", str(tmp_path / "policy")])
    output = capsys.readouterr()

    assert code == 0
    assert "Market source policy status: PASS" in output.out
    assert "Policy CSV path:" in output.out
    assert "No live trading or broker API was invoked." in output.out
