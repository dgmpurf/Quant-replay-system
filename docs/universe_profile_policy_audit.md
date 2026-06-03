# Universe Profile Policy Audit v0.1

`universe-profile-policy-audit` is a report-only governance workflow for checking whether local universe artifacts have clear profile semantics.

It is designed for the current PIT universe workflow where legacy artifacts may carry a misleading `universe_name` such as `etf_core` while containing both STOCK and ETF rows.

## What It Answers

- Which `universe_name` values are present?
- Which instrument types appear under each universe label?
- Is a universe mixed STOCK/ETF despite being named `etf_core`?
- Should future rows be split into `stock_core`, `etf_core`, or `mixed_demo_core`?
- Are current artifacts legacy mixed/demo context rather than ETF-only context?

## Command

```powershell
python -m quant_replay_system.cli universe-profile-policy-audit --worklist outputs\reports\point_in_time_universe_evidence_review_worklist\1c7972988f59\pit_universe_evidence_review_worklist.csv --review outputs\reports\point_in_time_universe_overlay_review\7bc8ba08bf5a\reviewed_pit_universe_overlay.csv
```

At least one local source is required:

- `--worklist`: PIT universe evidence review worklist CSV.
- `--review`: reviewed PIT universe overlay CSV.

When both sources describe the same rows, the audit de-duplicates by `signal_date + symbol + universe_name` to avoid double-counting.

## Artifacts

The command writes:

```text
outputs/reports/universe_profile_policy_audit/<audit_id>/
  universe_profile_policy_audit.csv
  universe_profile_policy_summary.csv
  universe_profile_policy_split_guidance.csv
  universe_profile_policy_audit_report.md
  metadata.json
```

## Artifact Views

Use the artifact views to make policy-audit runs discoverable and dashboard-ready:

```powershell
python -m quant_replay_system.cli universe-profile-policy-audit-index
python -m quant_replay_system.cli universe-profile-policy-audit-health
python -m quant_replay_system.cli universe-profile-policy-audit-status
```

`universe-profile-policy-audit-index` scans `outputs/reports/universe_profile_policy_audit/` and reports row counts, instrument mix counts, split-guidance counts, safety flags, and artifact paths.

`universe-profile-policy-audit-health` checks that audit CSVs, summaries, split-guidance CSVs, reports, and metadata are readable and preserve the report-only safety contract. It fails if an artifact claims approval, rejection, universe export, `data/raw` or `data/processed` writes, current-candidates generation, snapshot build, forward labels, cache mutation, network/API calls, broker access, order placement, or message delivery.

`universe-profile-policy-audit-status` summarizes the latest audit. Mixed legacy `etf_core` artifacts surface as `UNIVERSE_PROFILE_POLICY_AMBIGUOUS_MIXED_UNIVERSE`, which is a reviewable policy context warning, not a row approval or rejection.

## Research Status

`research-status` includes universe profile policy audit context when artifacts exist:

- latest audit id
- status and workflow stage
- health status
- stock/ETF/mixed row counts
- ambiguous policy count
- recommended `stock_core`, `etf_core`, and `mixed_demo_core` counts
- report path
- next manual action

This context is earlier than generated current-candidates, advisory layers, market-update handoff, and paper workflow. Later paper workflow priority is preserved, so a mixed-universe policy warning remains visible without replacing `PAPER_WORKFLOW_READY`.

## Classifications

The current v0.1 policy recognizes:

- `legacy_mixed_demo_universe`: a legacy universe label, such as `etf_core`, that contains both STOCK and ETF rows.
- `mixed_demo_universe`: an explicitly mixed demo profile.
- `stock_only_universe`: a universe containing only STOCK rows.
- `etf_only_universe`: a universe containing only ETF rows.
- `unknown_universe_profile`: rows without enough instrument-type information.

For legacy mixed `etf_core` artifacts, the audit reports:

- `legacy_universe_classification=legacy_mixed_demo_universe`
- `policy_issue=POLICY_AMBIGUOUS_DEMO_MIXED_UNIVERSE`

This is context only. It does not reject rows automatically.

## Future Split Guidance

Row-level guidance is:

- STOCK rows should move to `stock_core`.
- ETF rows should move to `etf_core`.
- Intentional mixed/demo workflows should use `mixed_demo_core`.

Future non-demo validation should block:

- STOCK rows from ETF-only universes.
- ETF rows from stock-only universes.
- Mixed demo rows from being treated as non-demo PIT approvals without a separate mixed-universe policy.

## Safety Boundaries

This workflow does not:

- approve rows
- reject rows
- modify active worklists
- regenerate PIT overlay plans
- export universe files
- write `data/raw`
- write `data/processed`
- run current-candidates
- build snapshot manifests
- compute forward labels
- mutate market cache
- call network, external APIs, or LLM APIs
- place orders, contact brokers, or send messages

## Known Limitations

- It does not validate PIT evidence sufficiency.
- It does not prove that a row belongs to a universe.
- It does not modify active artifact lineage.
- It does not add a config-backed profile registry yet.
- It does not integrate profile policy into approval/export health checks yet.
- It does not regenerate worklists under the recommended split profiles.

## Recommended Next Step

Create a future profile-registry or split-worklist plan so new worklists can use `stock_core`, `etf_core`, or `mixed_demo_core` deliberately. Do not approve or reject existing ambiguous rows automatically.

Use `universe-profile-split-worklist-plan` for the first report-only version of that step. It consumes this audit and/or the source worklist, applies `config/universe_profiles.yaml`, and writes future split guidance under `outputs/reports` without mutating active worklists. See [universe_profile_split_worklist_plan.md](universe_profile_split_worklist_plan.md).
