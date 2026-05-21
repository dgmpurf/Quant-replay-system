"""Command line helpers for local-only paper trading workflows."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd

from quant_replay_system.config import load_settings
from quant_replay_system.daily_paper_runner import run_daily_paper_trading
from quant_replay_system.paper_reconciliation import reconcile_paper_fills
from quant_replay_system.paper_review import apply_paper_review_updates


FILL_COLUMNS = [
    "fill_id",
    "decision_id",
    "symbol",
    "side",
    "fill_date",
    "fill_price",
    "quantity",
    "gross_notional",
    "fees",
    "slippage",
    "net_cash_flow",
    "fill_source",
    "manual_notes",
]

REQUIRED_FILL_COLUMNS = ["decision_id", "symbol", "side", "fill_date", "fill_price", "quantity"]
VALID_FILL_SIDES = {"BUY", "SELL"}


@dataclass(frozen=True)
class FillValidationResult:
    valid: bool
    row_count: int
    errors: list[str]
    warnings: list[str]


def main(argv: Sequence[str] | None = None) -> int:
    """Run the quant replay CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argparse parser."""

    parser = argparse.ArgumentParser(prog="python -m quant_replay_system.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    daily = subparsers.add_parser("paper-daily", help="Write a local daily paper trading report")
    daily.add_argument("--date", required=True, help="Paper trading date, e.g. 2024-05-20")
    daily.add_argument("--candidates", required=True, help="Candidates CSV path")
    daily.add_argument("--fills", help="Optional manual paper fills CSV path")
    daily.add_argument("--mark-prices", help="Optional mark-to-market price CSV path")
    daily.add_argument("--output-dir", help="Optional output directory")
    daily.add_argument("--journal-id", help="Optional explicit journal id")
    daily.add_argument("--config", help="Optional config YAML path")
    daily.set_defaults(handler=_handle_paper_daily)

    validate = subparsers.add_parser("paper-validate-fills", help="Validate a manual fills CSV")
    validate.add_argument("--fills", required=True, help="Manual fills CSV path")
    validate.set_defaults(handler=_handle_validate_fills)

    template = subparsers.add_parser("paper-template-fills", help="Write an empty fills CSV template")
    template.add_argument("--output", required=True, help="Output CSV path")
    template.add_argument("--overwrite", action="store_true", help="Overwrite an existing template")
    template.set_defaults(handler=_handle_template_fills)

    reconcile = subparsers.add_parser("paper-reconcile-fills", help="Reconcile manual fills against decisions")
    reconcile.add_argument("--decisions", required=True, help="Paper decisions CSV path")
    reconcile.add_argument("--fills", required=True, help="Manual fills CSV path")
    reconcile.add_argument("--output-dir", help="Optional reconciliation output directory")
    reconcile.add_argument("--config", help="Optional config YAML path")
    reconcile.add_argument("--allow-fail", action="store_true", help="Exit zero even when reconciliation status is FAIL")
    reconcile.set_defaults(handler=_handle_reconcile_fills)

    review = subparsers.add_parser("paper-review-decisions", help="Apply manual review updates to paper decisions")
    review.add_argument("--decisions", required=True, help="Paper decisions CSV path")
    review.add_argument("--updates", required=True, help="Review updates CSV path")
    review.add_argument("--output-dir", help="Optional review artifact output directory")
    review.add_argument("--reviewer-id", help="Default reviewer id for updates without reviewer_id")
    review.add_argument("--allow-pending", action="store_true", help="Allow reviewed decisions to remain PENDING_REVIEW")
    review.add_argument("--config", help="Optional config YAML path")
    review.set_defaults(handler=_handle_review_decisions)
    return parser


def validate_fills_csv(path: str | Path) -> FillValidationResult:
    """Validate a manual paper fills CSV."""

    csv_path = Path(path)
    if not csv_path.exists():
        return FillValidationResult(False, 0, [f"Fills file not found: {csv_path}"], [])
    try:
        frame = pd.read_csv(csv_path)
    except Exception as exc:
        return FillValidationResult(False, 0, [f"Could not read fills CSV: {exc}"], [])
    return validate_fills_frame(frame)


def validate_fills_frame(frame: pd.DataFrame) -> FillValidationResult:
    """Validate the expected manual paper fills schema and values."""

    errors: list[str] = []
    warnings: list[str] = []
    missing = [column for column in REQUIRED_FILL_COLUMNS if column not in frame.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return FillValidationResult(False, len(frame), errors, warnings)

    extra_missing = [column for column in FILL_COLUMNS if column not in frame.columns]
    if extra_missing:
        warnings.append(f"Optional columns missing: {', '.join(extra_missing)}")

    sides = frame["side"].astype(str).str.upper().str.strip()
    invalid_sides = frame.loc[~sides.isin(VALID_FILL_SIDES)]
    if not invalid_sides.empty:
        errors.append(f"Invalid side values at rows: {_row_numbers(invalid_sides.index)}")

    quantity = pd.to_numeric(frame["quantity"], errors="coerce")
    invalid_quantity = frame.loc[quantity.isna() | (quantity <= 0)]
    if not invalid_quantity.empty:
        errors.append(f"Non-positive quantity at rows: {_row_numbers(invalid_quantity.index)}")

    fill_price = pd.to_numeric(frame["fill_price"], errors="coerce")
    invalid_price = frame.loc[fill_price.isna() | (fill_price <= 0)]
    if not invalid_price.empty:
        errors.append(f"Non-positive fill_price at rows: {_row_numbers(invalid_price.index)}")

    parsed_dates = pd.to_datetime(frame["fill_date"], errors="coerce")
    invalid_dates = frame.loc[parsed_dates.isna()]
    if not invalid_dates.empty:
        errors.append(f"Unparseable fill_date at rows: {_row_numbers(invalid_dates.index)}")

    return FillValidationResult(not errors, len(frame), errors, warnings)


def write_fills_template(path: str | Path, *, overwrite: bool = False) -> Path:
    """Write an empty manual paper fills CSV template."""

    output = Path(path)
    if output.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file without --overwrite: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=FILL_COLUMNS).to_csv(output, index=False)
    return output


def _handle_paper_daily(args: argparse.Namespace) -> int:
    result = run_daily_paper_trading(
        args.date,
        candidates_path=args.candidates,
        fills_path=args.fills,
        mark_prices=args.mark_prices,
        output_dir=args.output_dir,
        journal_id=args.journal_id,
        config=args.config,
    )
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Report path: {result.artifact_paths['paper_report']}")
    print(f"decision_count: {result.decision_count}")
    print(f"fill_count: {result.fill_count}")
    print(f"open_position_count: {result.open_position_count}")
    print(f"closed_trade_count: {result.closed_trade_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_validate_fills(args: argparse.Namespace) -> int:
    result = validate_fills_csv(args.fills)
    print(f"fills_path: {args.fills}")
    print(f"row_count: {result.row_count}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    if result.valid:
        print("Validation passed.")
        print("No live trading or broker API was invoked.")
        return 0
    print("Validation failed.", file=sys.stderr)
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


def _handle_template_fills(args: argparse.Namespace) -> int:
    output = write_fills_template(args.output, overwrite=bool(args.overwrite))
    print(f"Wrote fills template: {output}")
    print("No live trading or broker API was invoked.")
    return 0


def _handle_reconcile_fills(args: argparse.Namespace) -> int:
    decisions_path = Path(args.decisions)
    fills_path = Path(args.fills)
    if not decisions_path.exists():
        raise FileNotFoundError(f"Decisions CSV not found: {decisions_path}")
    if not fills_path.exists():
        raise FileNotFoundError(f"Fills CSV not found: {fills_path}")
    settings = load_settings(args.config) if args.config else None
    if args.output_dir:
        project_settings = settings or load_settings(Path("config/default.yaml"))
        settings = project_settings.model_copy(
            update={
                "paper_reconciliation": project_settings.paper_reconciliation.model_copy(
                    update={"output_dir": Path(args.output_dir)}
                )
            }
        )
    result = reconcile_paper_fills(pd.read_csv(decisions_path), pd.read_csv(fills_path), settings=settings)
    print(f"Reconciliation status: {result.status}")
    print(f"issue_count: {result.issue_count}")
    print(f"error_count: {result.error_count}")
    print(f"warning_count: {result.warning_count}")
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Report path: {result.artifact_paths['reconciliation_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    if result.status == "FAIL" and not args.allow_fail:
        return 1
    return 0


def _handle_review_decisions(args: argparse.Namespace) -> int:
    decisions_path = Path(args.decisions)
    updates_path = Path(args.updates)
    if not decisions_path.exists():
        raise FileNotFoundError(f"Decisions CSV not found: {decisions_path}")
    if not updates_path.exists():
        raise FileNotFoundError(f"Review updates CSV not found: {updates_path}")
    settings = load_settings(args.config) if args.config else load_settings(Path("config/default.yaml"))
    review_updates = {}
    if args.output_dir:
        review_updates["output_dir"] = Path(args.output_dir)
    if args.allow_pending:
        review_updates["allow_pending_reviews"] = True
    if review_updates:
        settings = settings.model_copy(
            update={
                "paper_review": settings.paper_review.model_copy(update=review_updates)
            }
        )
    result = apply_paper_review_updates(
        pd.read_csv(decisions_path),
        pd.read_csv(updates_path),
        reviewer_id=args.reviewer_id,
        settings=settings,
    )
    summary = result.review_summary.iloc[0].to_dict() if not result.review_summary.empty else {}
    print(f"review_id: {result.review_id}")
    print(f"total_decisions: {summary.get('total_decisions', 0)}")
    print(f"approved_count: {summary.get('approved_count', 0)}")
    print(f"rejected_count: {summary.get('rejected_count', 0)}")
    print(f"watch_only_count: {summary.get('watch_only_count', 0)}")
    print(f"pending_count: {summary.get('pending_count', 0)}")
    print(f"Artifact folder: {result.artifact_paths['artifact_dir']}")
    print(f"Report path: {result.artifact_paths['paper_review_report']}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print("No live trading or broker API was invoked.")
    return 0


def _row_numbers(index: pd.Index) -> str:
    return ", ".join(str(int(value) + 2) for value in index)


if __name__ == "__main__":
    raise SystemExit(main())
