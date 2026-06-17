# Release Checkpoint v1.44.0

## Scope

v1.44.0 integrates `forward-return-label-status` into unified `research-status` and documents the report-only forward-return label layer.

This checkpoint covers:

- dashboard visibility for the latest forward-return label run id, status, health status, workflow stage, report path, and replay-decision-freeze lineage;
- CSV and metadata export fields for label row counts, label names, symbol counts, replay decision counts, and safety flags;
- CLI printing of forward-return label context in `research-status`;
- documentation for the forward-return label workflow and its safety boundaries;
- a source update note file for the checkpoint.

## Safety Boundary

Forward-return labels are future outcome context. v1.44.0 remains report-only and does not turn labels into decision-time replay inputs.

This checkpoint is not training, not stock_profile creation, not buy-review eligibility, not paper approval, not performance validation, and not trading.

It also does not:

- run current-candidates,
- build snapshots,
- train weights,
- create active stock profiles,
- create real buy-review eligibility,
- call brokers,
- place orders,
- send messages,
- call LLM or external APIs,
- mutate cache,
- write `data/raw`,
- write `data/processed`,
- write `data/cache`,
- update Project Source,
- create `docs/project_sources/`.

## Expected Current Interpretation

`research-status` may show a forward-return label context row while preserving the final `PAPER_WORKFLOW_READY` priority when later paper workflow artifacts exist.

Forward label context should be read as downstream evaluation material only. It is not evidence that strategy performance is validated and is not permission to train, paper-approve, or trade.

## Recommended Next Task

Run a report-only forward-return label acceptance or governance design audit before any future workflow is allowed to consume labels for training or evaluation.
