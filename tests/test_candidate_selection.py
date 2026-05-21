import pandas as pd
from pandas.testing import assert_frame_equal

from quant_replay_system.candidate_selection import select_candidates


def test_candidate_selector_excludes_blocked_rows_by_default() -> None:
    selected = select_candidates(
        pd.DataFrame(
            [
                _scored_row("AAA", 95, "BLOCKED"),
                _scored_row("BBB", 75, "PAPER_TRADE"),
            ]
        ),
        min_action="NO_TRADE",
    )

    assert list(selected["symbol"]) == ["BBB"]


def test_candidate_selector_sorts_by_final_score_descending() -> None:
    selected = select_candidates(
        pd.DataFrame(
            [
                _scored_row("AAA", 75, "PAPER_TRADE"),
                _scored_row("BBB", 88, "LIVE_CANDIDATE_SMALL"),
                _scored_row("CCC", 71, "PAPER_TRADE"),
            ]
        )
    )

    assert list(selected["symbol"]) == ["BBB", "AAA", "CCC"]


def test_top_n_works() -> None:
    selected = select_candidates(
        pd.DataFrame(
            [
                _scored_row("AAA", 75, "PAPER_TRADE"),
                _scored_row("BBB", 88, "LIVE_CANDIDATE_SMALL"),
                _scored_row("CCC", 82, "LIVE_CANDIDATE_SMALL"),
            ]
        ),
        top_n=2,
    )

    assert list(selected["symbol"]) == ["BBB", "CCC"]


def test_min_final_score_works() -> None:
    selected = select_candidates(
        pd.DataFrame(
            [
                _scored_row("AAA", 75, "PAPER_TRADE"),
                _scored_row("BBB", 88, "LIVE_CANDIDATE_SMALL"),
                _scored_row("CCC", 82, "LIVE_CANDIDATE_SMALL"),
            ]
        ),
        min_final_score=83,
    )

    assert list(selected["symbol"]) == ["BBB"]


def test_selector_preserves_explanation_columns() -> None:
    selected = select_candidates(pd.DataFrame([_scored_row("AAA", 75, "PAPER_TRADE")]))

    assert "score_breakdown" in selected.columns
    assert "score_reason" in selected.columns
    assert selected.loc[0, "score_breakdown"]["components"]["technical_score"] == 70


def test_selector_output_is_deterministic() -> None:
    scored = pd.DataFrame(
        [
            _scored_row("BBB", 80, "LIVE_CANDIDATE_SMALL"),
            _scored_row("AAA", 80, "LIVE_CANDIDATE_SMALL"),
            _scored_row("CCC", 72, "PAPER_TRADE"),
        ]
    )

    first = select_candidates(scored)
    second = select_candidates(scored)

    assert_frame_equal(first, second)
    assert list(first["symbol"]) == ["AAA", "BBB", "CCC"]


def test_selector_does_not_mutate_original_dataframe() -> None:
    scored = pd.DataFrame([_scored_row("AAA", 75, "PAPER_TRADE")])
    original = scored.copy(deep=True)

    _ = select_candidates(scored)

    assert_frame_equal(scored, original)


def _scored_row(symbol: str, final_score: float, action: str) -> dict:
    return {
        "decision_date": pd.Timestamp("2024-03-05"),
        "symbol": symbol,
        "final_score": final_score,
        "score_action": action,
        "score_breakdown": {
            "components": {
                "technical_score": 70,
                "expectation_score": 60,
                "liquidity_score": 80,
                "risk_penalty": 0,
            }
        },
        "score_reason": f"{symbol} reason",
    }
