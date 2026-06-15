# Source Update Notes v1.39.0

`docs/project_sources/` is intentionally absent from Git. docs/project_sources/ is intentionally absent from Git. ChatGPT Project Source is maintained separately outside the repository.

After tag v1.39.0, refresh ChatGPT Project Source manually with this conceptual state:

- actual `ACTIVE_REPLAY_INPUT_READY` marker-only core implemented;
- actual marker-only emission artifact views implemented;
- `research-status` and checkpoint documentation integrated;
- marker-only `ACTIVE_REPLAY_INPUT_READY` can exist in report-only manual diagnostics when the explicit allow flag is used;
- this marker does not create active replay input;
- this marker does not run replay;
- this marker does not create replay decisions;
- this marker does not compute forward labels;
- this marker does not train weights;
- this marker does not create active stock profiles;
- this marker does not create real buy-review eligibility;
- this marker does not authorize trading;
- still no labels, training, stock_profile, buy-review, trading, broker/order/message/API/cache side effects, current-candidates generation, or snapshot build.

Safety wording to preserve in Project Source: marker-only `ACTIVE_REPLAY_INPUT_READY` is a diagnostics marker only. It does not create active replay input, does not run replay, does not create replay decisions, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not authorize trading.

Recommended next branch: active replay input creation planning/design, not real replay.

Do not recreate `docs/project_sources/` in Git and do not duplicate the full Project Source pack in the repository.
