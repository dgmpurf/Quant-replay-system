# Source Update Notes v1.42.0

`docs/project_sources/` is intentionally absent from Git. ChatGPT Project Source is maintained separately outside the repository.

After tag v1.42.0, refresh ChatGPT Project Source manually with this conceptual state. For exact source-pack wording, after tag v1.42.0 refresh the external Project Source, not a tracked `docs/project_sources/` folder:

- `actual-replay-execute` core implemented;
- actual replay execution artifact views implemented;
- `research-status` and checkpoint documentation integrated;
- `ACTUAL_REPLAY_EXECUTED` is report-only execution artifacts only;
- it is not replay_decision creation;
- it does not create replay decisions;
- it does not compute forward labels;
- it does not train weights;
- it does not create active stock_profile artifacts;
- it does not create real buy-review eligibility;
- it does not authorize trading;
- `research-status` preserves `PAPER_WORKFLOW_READY` priority while showing actual replay execution context;
- still no labels, training, stock_profile, buy-review, trading, broker/order/message/API/cache side effects, current-candidates generation, or snapshot build.

Safety wording to preserve in Project Source: `ACTUAL_REPLAY_EXECUTED` is a report-only execution artifact state. It is not replay_decision creation, no forward labels are computed, no training runs, no active stock_profile is created, no real buy-review eligibility is created, and no trading is authorized.

Previous source context: Actual Replay Execution Artifact Views Report-Only v0.1.

Recommended next branch: Replay Decision Freeze Planning Report-Only v0.1, not replay decision creation.

Do not recreate `docs/project_sources/` in Git and do not duplicate the full Project Source pack in the repository.
