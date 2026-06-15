# Source Update Notes v1.40.0

`docs/project_sources/` is intentionally absent from Git. docs/project_sources/ is intentionally absent from Git. ChatGPT Project Source is maintained separately outside the repository.

After tag v1.40.0, refresh ChatGPT Project Source manually with this conceptual state:

- active replay input creation core implemented;
- active replay input creation artifact views implemented;
- `research-status` and checkpoint documentation integrated;
- report-only active replay input artifact can exist when the explicit allow flag is used;
- this active input does not run replay;
- this active input does not create replay decisions;
- this active input does not compute forward labels;
- this active input does not train weights;
- this active input does not create active stock profiles;
- this active input does not create real buy-review eligibility;
- this active input does not authorize trading;
- still no labels, training, stock_profile, buy-review, trading, broker/order/message/API/cache side effects, current-candidates generation, or snapshot build.

Safety wording to preserve in Project Source: `ACTIVE_REPLAY_INPUT_CREATED` is a report-only diagnostics artifact for a future separate replay execution workflow. It does not run replay, does not create replay decisions, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not authorize trading.

Recommended next branch: Real Replay Execution Planning / Design Report-Only v0.1, not replay execution implementation.

Do not recreate `docs/project_sources/` in Git and do not duplicate the full Project Source pack in the repository.
