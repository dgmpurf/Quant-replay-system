# Current Candidate To Paper Review Handoff v0.1

Current Candidate To Paper Review Handoff creates a manual review update template from paper decisions.

It is local-only. It does not connect to brokers, place orders, automate execution, auto-approve trades, print secrets, or call market data APIs.

## Purpose

`current-to-paper` can create a daily paper decision log from a healthy `candidates.csv`. The next step is manual review.

This helper writes `review_updates_template.csv` so the user can edit review decisions before running:

```cmd
python -m quant_replay_system.cli paper-review-template-health --updates outputs\reports\current_to_paper_review_handoff\example\review_updates_template.csv --decisions outputs\reports\paper_trading\daily\example\decisions.csv
python -m quant_replay_system.cli paper-review-decisions --decisions outputs\reports\paper_trading\daily\example\decisions.csv --updates outputs\reports\current_to_paper_review_handoff\example\review_updates_template.csv
```

## Workflow Connection

```text
current-candidates
  -> current-to-paper
  -> current-to-paper-review
  -> manually edit review_updates_template.csv
  -> paper-review-template-health
  -> paper-review-decisions
  -> paper-daily --reviewed-decisions
  -> paper-reconcile-fills
```

The helper accepts:

- `decisions.csv` from `paper-daily`,
- a `current-to-paper` handoff artifact directory,
- a daily paper artifact directory containing `decisions.csv`.

## review_updates_template.csv Schema

The template includes paper-review columns plus context columns:

- `decision_id`
- `symbol`
- `name`
- `candidate_rank`
- `final_score`
- `action`
- `risk_precheck_status`
- `risk_precheck_reason`
- `suggested_manual_review_status`
- `manual_review_status`
- `manual_review_notes`
- `reviewer_id`
- `review_reason_code`

`paper-review-decisions` uses:

- `decision_id`
- `manual_review_status`
- `manual_review_notes`
- `reviewer_id`
- `review_reason_code`

The other fields are included for manual review context.

## Suggested Statuses Vs Actual Statuses

Suggestions are advisory only.

By default:

- `manual_review_status` remains `PENDING_REVIEW`.
- `suggested_manual_review_status` may contain `PENDING_REVIEW`, `WATCH_ONLY`, `REJECTED`, or `APPROVED_FOR_PAPER`.
- No row is auto-approved.

Even when score thresholds are configured for suggestions, they only affect `suggested_manual_review_status`.

The user must manually edit `manual_review_status` before applying updates if they want approvals, rejections, or watch-only decisions.

## CLI Usage

From a decisions CSV:

```cmd
python -m quant_replay_system.cli current-to-paper-review --decisions outputs\reports\paper_trading\daily\example\decisions.csv
```

From a current-to-paper handoff folder:

```cmd
python -m quant_replay_system.cli current-to-paper-review --handoff-dir outputs\reports\current_to_paper_handoff\example
```

With a default reviewer id:

```cmd
python -m quant_replay_system.cli current-to-paper-review --decisions outputs\reports\paper_trading\daily\example\decisions.csv --reviewer-id msj
```

The CLI prints template path, report path, and:

```text
No live trading or broker API was invoked.
```

## Artifact Outputs

Default output folder:

```text
outputs/reports/current_to_paper_review_handoff/<review_handoff_id>/
```

Files:

- `review_updates_template.csv`
- `review_handoff_report.md`
- `metadata.json`

`review_handoff_id` is deterministic from decision IDs, source path or source handoff id, and config version.

## Known MVP Limitations

- Uses local CSV/mock data only.
- Does not provide an interactive review UI.
- Does not auto-approve candidates.
- Does not validate future fills.
- Does not place or route orders.
- Does not connect to brokers.
- Suggested statuses are simple MVP hints, not trading instructions.
