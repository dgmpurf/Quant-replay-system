# Source Update Notes v1.38.0

`docs/project_sources/` is intentionally absent from Git. ChatGPT Project Source is maintained separately outside the repository.

after tag v1.38.0, refresh ChatGPT Project Source with this conceptual state:

- `active-replay-input-ready-emission` core implemented;
- active-ready emission-decision artifact views implemented;
- `research-status` and checkpoint documentation integrated;
- `READY_FOR_ACTIVE_REPLAY_INPUT_READY_EMISSION_DECISION` exists in test/report-only context;
- still no `ACTIVE_REPLAY_INPUT_READY`;
- still no active replay input;
- still no real replay;
- still no replay decisions;
- still no forward labels, training, active stock profiles, or real buy-review eligibility;
- still no performance validation or trading authorization.

Safety wording to preserve in Project Source: the emission-decision workflow does not emit ACTIVE_REPLAY_INPUT_READY, does not create active replay input, does not run replay, does not create replay decisions, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not authorize trading.

Recommended next branch: an explicitly scoped actual `ACTIVE_REPLAY_INPUT_READY` emission planning or implementation decision, not active replay input creation and not real replay.

Do not recreate `docs/project_sources/` in Git and do not duplicate the full Project Source pack in the repository.
