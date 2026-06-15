# Source Update Notes v1.41.0

`docs/project_sources/` is intentionally absent from Git. docs/project_sources/ is intentionally absent from Git. ChatGPT Project Source is maintained separately outside the repository.

After tag v1.41.0, refresh ChatGPT Project Source manually with this conceptual state:

- real replay execution precheck core implemented;
- real replay execution artifact views implemented;
- `research-status` and checkpoint documentation integrated;
- `READY_FOR_REAL_REPLAY_EXECUTION_REVIEW` is pre-execution review only;
- it does not run replay;
- it does not create replay decisions;
- it does not compute forward labels;
- it does not train weights;
- it does not create active stock profiles;
- it does not create real buy-review eligibility;
- it does not authorize trading;
- `research-status` preserves `PAPER_WORKFLOW_READY` priority while showing real replay execution precheck context;
- still no labels, training, stock_profile, buy-review, trading, broker/order/message/API/cache side effects, current-candidates generation, or snapshot build.

Safety wording to preserve in Project Source: `READY_FOR_REAL_REPLAY_EXECUTION_REVIEW` is a report-only pre-execution review state for a future separate replay execution workflow. It does not run replay, does not create replay decisions, does not compute forward labels, does not train weights, does not create active stock profiles, does not create real buy-review eligibility, and does not authorize trading.

Previous source context: Real Replay Execution Artifact Views Report-Only v0.1.

Recommended next branch: Real Replay Execution Dry-Run Governance / Design Report-Only v0.1, not actual replay execution.

Do not recreate `docs/project_sources/` in Git and do not duplicate the full Project Source pack in the repository.
