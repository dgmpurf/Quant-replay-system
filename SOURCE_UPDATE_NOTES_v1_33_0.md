# Source Update Notes v1.33.0

## Summary

v1.33.0 adds `research-status` visibility for report-only Active Replay Input Active-Ready artifacts.

The relevant command family is `active-replay-input-active-ready`, `active-replay-input-active-ready-index`, `active-replay-input-active-ready-health`, and `active-replay-input-active-ready-status`.

`docs/project_sources/` is intentionally absent from Git. ChatGPT Project Source is maintained separately by the user.

## Changed

- Added active replay input active-ready context to the unified local research dashboard.
- Added active-ready summary, metadata, and CLI `research-status` fields.
- Documented the report-only active-ready workflow and checkpoint.

## Manual Project Source Refresh

After commit/tag review for `v1.33.0`, refresh ChatGPT Project Source manually with this conceptual state:

- active replay input active-ready core is implemented;
- active-ready index/health/status artifact views are implemented;
- research-status and checkpoint docs are integrated;
- `ACTIVE_READY_READY_FOR_FINAL_REVIEW` exists in test context;
- there is still no active replay input;
- `ACTIVE_REPLAY_INPUT_READY` is still not emitted;
- there is still no real replay;
- there are still no forward labels, training outputs, active stock profiles, or real buy-review eligibility;
- validator, smoke, promotion, acceptance, and active-ready artifacts remain non-active;
- the next branch should be report-only active replay input active-ready final review / emission design, not real replay.

## Safety Notes

`ACTIVE_READY_READY_FOR_FINAL_REVIEW` remains final-review context only. It is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`.

This update does not create active replay input, does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, does not authorize trading, run current-candidates, build snapshots, write data stores, mutate cache, call APIs, send messages, connect to brokers, place orders, apply `APPROVED_FOR_PAPER`, change signal semantics, or claim strategy performance is validated.

No `docs/project_sources/` folder was recreated, and no git tag is created by these notes.
