# Universe Profile Split Worklist Plan v0.1

`universe-profile-split-worklist-plan` is a report-only workflow that applies a local universe profile registry to existing PIT evidence worklists and universe-profile policy audits.

It is designed for the current legacy `etf_core` artifacts, where the label contains both STOCK and ETF rows. The command produces future split guidance only. It does not regenerate active worklists, approve or reject rows, export universe files, write `data/raw` or `data/processed`, run current-candidates, build snapshots, compute labels, mutate cache files, call APIs, send messages, connect to brokers, or place orders.

## Profile Registry

The default registry lives at:

```text
config/universe_profiles.yaml
```

The initial profiles are:

- `stock_core`: allows `STOCK` rows only.
- `etf_core`: allows `ETF` rows only.
- `mixed_demo_core`: allows `STOCK` and `ETF` rows for demo or mixed workflow validation only.

Registry fields are:

- `profile_name`
- `allowed_instrument_types`
- `profile_type`
- `mixed_allowed`
- `demo_only`
- `description`

The registry is a future-planning control, not a retroactive approval rule. Existing legacy `etf_core` artifacts remain unchanged and should be treated as `legacy_mixed_demo_universe` context until a reviewer explicitly creates new worklists under clarified profiles.

## CLI Usage

```cmd
python -m quant_replay_system.cli universe-profile-split-worklist-plan --worklist outputs\reports\point_in_time_universe_evidence_review_worklist\1c7972988f59\pit_universe_evidence_review_worklist.csv --policy-audit outputs\reports\universe_profile_policy_audit\844794b3aae1\universe_profile_policy_audit.csv --profiles config\universe_profiles.yaml
```

Inputs:

- `--worklist`: PIT universe evidence review worklist CSV. This is the preferred row-grain input because it preserves `signal_date + symbol + universe_name`.
- `--policy-audit`: universe profile policy audit CSV. When both inputs are supplied, the planner enriches worklist rows with audit classifications.
- `--profiles`: local YAML registry of universe profiles.
- `--output-dir`: report destination. Defaults to `outputs/reports/universe_profile_split_worklist_plan`.

## Artifacts

The command writes:

```text
outputs/reports/universe_profile_split_worklist_plan/<plan_id>/
  universe_profile_registry_snapshot.yaml
  universe_profile_split_worklist_plan.csv
  universe_profile_split_summary.csv
  universe_profile_split_guidance_stock_core.csv
  universe_profile_split_guidance_etf_core.csv
  universe_profile_split_guidance_mixed_demo_core.csv
  universe_profile_split_worklist_plan_report.md
  metadata.json
```

## Artifact Views

Use these commands to make split-worklist plan artifacts discoverable and dashboard-ready:

```cmd
python -m quant_replay_system.cli universe-profile-split-worklist-plan-index
python -m quant_replay_system.cli universe-profile-split-worklist-plan-health
python -m quant_replay_system.cli universe-profile-split-worklist-plan-status
```

`universe-profile-split-worklist-plan-index` scans `outputs/reports/universe_profile_split_worklist_plan/` and records plan ids, row counts, STOCK/ETF counts, legacy mixed-demo counts, recommended future universe counts, profile-conflict counts, safety flags, and artifact paths.

`universe-profile-split-worklist-plan-health` checks that metadata, plan CSVs, summary CSVs, registry snapshots, guidance CSVs, and reports are readable and keep the planning-only safety contract. Profile conflicts are reported as warning context, because the current legacy `etf_core` rows are expected to remain visible without being approved, rejected, or mutated.

`universe-profile-split-worklist-plan-status` summarizes the latest plan. A current mixed legacy artifact should surface as `UNIVERSE_PROFILE_SPLIT_WORKLIST_PLAN_HAS_PROFILE_CONFLICTS`, with next action focused on reviewing split guidance before generating any replacement worklists.

## Research Status

`research-status` includes the latest split-worklist plan as universe-profile planning context. The summary CSV, metadata, markdown report, and CLI output expose:

- latest split-worklist plan id
- split-worklist plan status/stage/health
- row, STOCK, ETF, and legacy mixed-demo counts
- recommended `stock_core`, `etf_core`, and `mixed_demo_core` counts
- profile-conflict count
- report path
- next action

Split-worklist plan warnings do not override later paper workflow priority. If a later paper workflow is already ready, the final `workflow_stage` remains on that later workflow while split-plan fields stay visible as context.

## Plan Fields

The row-level plan includes:

- source ids from the worklist and policy audit
- `signal_date`
- current universe label
- symbol and instrument type
- resolved instrument type
- current profile classification
- recommended future universe
- profile rule applied
- profile conflict flag and reason
- legacy classification
- safety flags showing no mutation, approval, rejection, export, candidate generation, snapshot build, label computation, cache mutation, trading, broker access, orders, or messages

## Current Legacy Result

For the active 72-row PIT worklist, the expected planning interpretation is:

- 56 STOCK rows should move to future `stock_core` guidance.
- 16 ETF rows should move to future `etf_core` guidance.
- The current `etf_core` label remains legacy mixed/demo context.
- STOCK rows under future ETF-only `etf_core` rules are profile conflicts and should not be treated as ETF approvals.
- The active worklist should be left unchanged.

## Safety Boundaries

This workflow does not:

- approve rows
- reject rows
- mutate active worklists
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

- The plan does not create new stock or ETF worklists.
- The plan does not validate PIT evidence sufficiency.
- The plan does not make any row eligible for current-candidates.
- The plan does not resolve survivorship-bias warnings.
- The plan does not enforce profile rules inside candidate generation yet.

## Recommended Next Step

Use `reviewed-replacement-worklist-plan` to create report-only future replacement templates under `stock_core`, `etf_core`, or `mixed_demo_core`. See [reviewed_replacement_worklist_plan.md](reviewed_replacement_worklist_plan.md). Do not mutate the active 72-row worklist or treat replacement templates as approvals.
