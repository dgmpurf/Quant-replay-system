# Source Update Notes v1.35.0

## Summary

v1.35.0 adds `research-status` visibility for report-only Active Replay Input Emission artifacts.

The relevant command family is `active-replay-input-emission`, `active-replay-input-emission-index`, `active-replay-input-emission-health`, and `active-replay-input-emission-status`.

`docs/project_sources/` is intentionally absent from Git. ChatGPT Project Source is maintained separately by the user.

## Changed

- Added active replay input emission context to the unified local research dashboard.
- Added emission summary, metadata, and CLI `research-status` fields.
- Documented the report-only emission workflow and checkpoint.

## Manual Project Source Refresh

Refresh ChatGPT Project Source manually after tag v1.35.0 with this conceptual state:

- active replay input emission core is implemented;
- emission index/health/status artifact views are implemented;
- research-status and checkpoint docs are integrated;
- latest active emission run id is `96fae2783877` when present locally;
- `EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW` exists as report-only context;
- there is still no active replay input;
- `ACTIVE_REPLAY_INPUT_READY` is still not emitted;
- there is still no real replay;
- there are still no forward labels, training outputs, active stock profiles, or real buy-review eligibility;
- validator, smoke, promotion, acceptance, active-ready, final-review, and emission artifacts remain non-active;
- the next branch should be report-only active replay input emission acceptance or promotion planning, not real replay.

## Safety Notes

`EMISSION_READY_FOR_ACTIVE_REPLAY_INPUT_READY_REVIEW` remains emission context only. It is not active replay input and not `ACTIVE_REPLAY_INPUT_READY`.

This update does not emit ACTIVE_REPLAY_INPUT_READY. It does not create active replay input. It does not run replay. It does not compute forward labels. It does not train weights. It does not create active stock profiles. It does not create real buy-review eligibility. It does not authorize trading. It also does not run current-candidates, build snapshots, write data stores, mutate cache, call APIs, send messages, connect to brokers, place orders, apply `APPROVED_FOR_PAPER`, change signal semantics, or claim strategy performance is validated.

No `docs/project_sources/` folder was recreated, and no git tag is created by these notes.
