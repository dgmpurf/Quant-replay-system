# Source Update Notes v1.43.0

`docs/project_sources/` is intentionally absent from Git. docs/project_sources/ is intentionally absent from Git. ChatGPT Project Source is maintained separately outside the repository.

After tag v1.43.0, refresh ChatGPT Project Source manually with this conceptual state. For exact source-pack wording, after tag v1.43.0 refresh the external Project Source, not a tracked `docs/project_sources/` folder:

- `replay-decision-freeze` core implemented;
- replay decision freeze artifact views implemented;
- `research-status` and checkpoint documentation integrated;
- `REPLAY_DECISION_FROZEN` can exist as report-only frozen decision-time review rows;
- frozen decision-time review rows are not forward labels and not future-return labels;
- forward labels are still absent;
- no forward_return_label artifacts exist from this workflow;
- no training;
- no weights;
- no training_result;
- no active stock_profile;
- no real buy-review eligibility;
- no paper approval;
- no strategy performance validation;
- no trading;
- no broker/order/message/API/cache side effects;
- no current-candidates generation;
- no snapshot build;
- `research-status` preserves `PAPER_WORKFLOW_READY` priority while showing replay decision freeze context.

Safety wording to preserve in Project Source: `REPLAY_DECISION_FROZEN` is a report-only frozen decision-time review row state. It does not compute forward labels, does not train weights, does not create training_result artifacts, does not create active stock_profile artifacts, does not create real buy-review eligibility, does not apply paper approval, does not validate strategy performance, and does not authorize trading.

Previous source context: Replay Decision Freeze Research-Status Integration and Checkpoint Report-Only v0.1.

Recommended next branch: Forward Return Label Planning Report-Only v0.1, unless code/docs clearly suggest a safer preceding audit; not immediate training, stock_profile, buy-review, paper approval, performance validation, or trading.

Do not recreate `docs/project_sources/` in Git and do not duplicate the full Project Source pack in the repository.
