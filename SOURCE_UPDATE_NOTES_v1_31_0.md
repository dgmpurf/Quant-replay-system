# Source Update Notes v1.31.0

## Summary

v1.31.0 adds `research-status` visibility for report-only active replay input promotion artifacts.

`docs/project_sources/` is intentionally absent from Git. ChatGPT Project Source is maintained separately by the user.

## Changed

- Added active replay input promotion context to the unified local research dashboard.
- Added promotion-scoped summary, metadata, and CLI `research-status` fields.
- Documented the report-only promotion workflow and checkpoint.

## Manual Project Source Refresh

After commit/tag review for `v1.31.0`, refresh ChatGPT Project Source manually with this conceptual state:

- active replay input promotion core is implemented;
- promotion index/health/status artifact views are implemented;
- research-status and checkpoint docs are integrated;
- `PROMOTION_READY_FOR_HUMAN_REVIEW` exists as review context;
- there is still no active replay input;
- `ACTIVE_REPLAY_INPUT_READY` is still not emitted;
- there is still no real replay;
- there are still no forward labels, training outputs, active stock profiles, or real buy-review eligibility;
- the next branch should be report-only `ACTIVE_REPLAY_INPUT_READY` promotion design or active-ready test-context design, not real replay.

## Safety Notes

`PROMOTION_READY_FOR_HUMAN_REVIEW` remains review context only. It is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`.

This update does not run replay, compute forward labels, train weights, create active stock profiles, create real buy-review eligibility, run current-candidates, build snapshots, write data stores, mutate cache, call APIs, send messages, connect to brokers, place orders, apply `APPROVED_FOR_PAPER`, change signal semantics, or claim strategy performance is validated.

No `docs/project_sources/` folder was recreated, and no git tag is created by these notes.
