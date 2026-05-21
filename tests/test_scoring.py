import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from quant_replay_system.score_engine import map_score_to_action, score_factor_dataset


def test_final_score_formula_correctness() -> None:
    scored = score_factor_dataset(pd.DataFrame([_factor_row("AAA")]))
    row = scored.iloc[0]

    expected = (
        0.35 * 50.0
        + 0.25 * 80.0
        + 0.15 * 60.0
        + 0.10 * 74.0
        + 0.05 * 50.0
        - 0.25 * 0.0
    )
    assert row["technical_score"] == pytest.approx(80.0)
    assert row["expectation_score"] == pytest.approx(60.0)
    assert row["liquidity_score"] == pytest.approx(74.0)
    assert row["final_score"] == pytest.approx(expected)


def test_scores_are_clipped_to_zero_to_one_hundred() -> None:
    factor = pd.DataFrame(
        [
            _factor_row(
                "AAA",
                technical_score_v01=999.0,
                rel_return_5=10.0,
                rel_return_10=10.0,
                rel_return_20=10.0,
                rsi14=10.0,
                amount=10**20,
                volume_ratio_20=999.0,
                reality_score_v01=999.0,
                sentiment_score=999.0,
            )
        ]
    )

    scored = score_factor_dataset(factor)
    score_columns = [
        "technical_score",
        "liquidity_score",
        "expectation_score",
        "risk_penalty",
        "reality_score",
        "sentiment_score",
        "final_score",
    ]

    for column in score_columns:
        assert scored[column].between(0, 100).all()


def test_block_risk_overrides_high_final_score() -> None:
    scored = score_factor_dataset(
        pd.DataFrame(
            [
                _factor_row(
                    "AAA",
                    risk_precheck_status="BLOCK",
                    technical_score_v01=100,
                    rel_return_5=2,
                    rel_return_10=2,
                    rel_return_20=2,
                    reality_score_v01=100,
                    sentiment_score=100,
                )
            ]
        )
    )

    assert scored.loc[0, "score_action"] == "BLOCKED"
    assert scored.loc[0, "risk_penalty"] == 100


def test_action_mapping_thresholds() -> None:
    assert map_score_to_action(59.99) == "NO_TRADE"
    assert map_score_to_action(60.0) == "OBSERVE"
    assert map_score_to_action(70.0) == "PAPER_TRADE"
    assert map_score_to_action(80.0) == "LIVE_CANDIDATE_SMALL"
    assert map_score_to_action(90.0) == "STRONG_CANDIDATE_REVIEW_REQUIRED"


def test_missing_optional_score_fields_use_config_defaults() -> None:
    factor = pd.DataFrame([_factor_row("AAA")]).drop(
        columns=["technical_score_v01", "rel_return_5", "rel_return_10", "rel_return_20", "sentiment_score"]
    )

    scored = score_factor_dataset(factor)

    assert pd.notna(scored.loc[0, "technical_score"])
    assert scored.loc[0, "expectation_score"] == pytest.approx(50.0)
    assert scored.loc[0, "sentiment_score"] == pytest.approx(50.0)


def test_original_input_dataframe_is_not_mutated() -> None:
    factor = pd.DataFrame([_factor_row("AAA")])
    original = factor.copy(deep=True)

    _ = score_factor_dataset(factor)

    assert_frame_equal(factor, original)


def test_score_breakdown_and_reason_columns_exist() -> None:
    scored = score_factor_dataset(pd.DataFrame([_factor_row("AAA")]))

    assert "score_breakdown" in scored.columns
    assert "score_reason" in scored.columns
    assert isinstance(scored.loc[0, "score_breakdown"], dict)
    assert "technical_score" in scored.loc[0, "score_breakdown"]["components"]
    assert "final=" in scored.loc[0, "score_reason"]


def test_score_output_is_deterministic() -> None:
    factor = pd.DataFrame([_factor_row("BBB"), _factor_row("AAA")])

    first = score_factor_dataset(factor)
    second = score_factor_dataset(factor)

    assert_frame_equal(first, second)


def _factor_row(symbol: str, **overrides) -> dict:
    row = {
        "decision_date": pd.Timestamp("2024-03-05"),
        "decision_time": pd.Timestamp("2024-03-05 15:30:00"),
        "symbol": symbol,
        "name": f"{symbol} Name",
        "instrument_type": "ETF",
        "exchange": "SSE",
        "industry": "Test",
        "is_active": True,
        "is_st": False,
        "is_suspended": False,
        "min_lot": 100,
        "t_plus_rule": "t_plus_1",
        "close": 10.5,
        "open": 10.0,
        "high": 10.8,
        "low": 9.9,
        "volume": 1_000_000,
        "amount": 1_000_000_000,
        "pre_close": 10.1,
        "limit_up": 11.0,
        "limit_down": 9.0,
        "adj_factor": 1.0,
        "ma5": 10.4,
        "ma20": 10.0,
        "rsi14": 60.0,
        "volume_ratio_20": 1.2,
        "rel_return_5": 0.10,
        "rel_return_10": 0.10,
        "rel_return_20": 0.10,
        "technical_score_v01": 80.0,
        "reality_score_v01": 50.0,
        "sentiment_score": 50.0,
        "latest_market_available_time": pd.Timestamp("2024-03-05 15:10:00"),
        "universe_available_time": pd.Timestamp("2024-03-05 09:00:00"),
        "data_revision_id": "market:m1|universe:u1",
        "source": "unit-test",
        "universe_eligible": True,
        "market_data_available": True,
        "execution_data_available": True,
        "risk_precheck_status": "PASS",
        "risk_precheck_reason": "eligible",
    }
    row.update(overrides)
    return row
