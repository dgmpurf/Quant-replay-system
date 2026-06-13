# Source Update Notes v1.32.0

## Summary

v1.32.0 adds `research-status` visibility for report-only active replay input acceptance artifacts.

The relevant command family is `active-replay-input-acceptance`, `active-replay-input-acceptance-index`, `active-replay-input-acceptance-health`, and `active-replay-input-acceptance-status`.

`docs/project_sources/` is intentionally absent from Git. ChatGPT Project Source is maintained separately by the user.

## Changed

- Added active replay input acceptance context to the unified local research dashboard.
- Added acceptance-scoped summary, metadata, and CLI `research-status` fields.
- Documented the report-only acceptance workflow and checkpoint.

## Manual Project Source Refresh

After commit/tag review for `v1.32.0`, refresh ChatGPT Project Source manually with this conceptual state:

- active replay input acceptance core is implemented;
- acceptance index/health/status artifact views are implemented;
- research-status and checkpoint docs are integrated;
- `ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW` exists in test context;
- there is still no active replay input;
- `ACTIVE_REPLAY_INPUT_READY` is still not emitted;
- there is still no real replay;
- there are still no forward labels, training outputs, active stock profiles, or real buy-review eligibility;
- validator, smoke, promotion, and acceptance artifacts remain non-active;
- the next branch should be report-only active-ready governance/design, not real replay.

## Safety Notes

`ACCEPTANCE_READY_FOR_ACTIVE_READY_REVIEW` remains review context only. It is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`.

This update does not create active replay input, does not run replay, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, run current-candidates, build snapshots, write data stores, mutate cache, call APIs, send messages, connect to brokers, place orders, apply `APPROVED_FOR_PAPER`, change signal semantics, or claim strategy performance is validated.

No `docs/project_sources/` folder was recreated, and no git tag is created by these notes.
