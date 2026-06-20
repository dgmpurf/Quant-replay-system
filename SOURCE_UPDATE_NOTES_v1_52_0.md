# Source Update Notes v1.52.0

## Summary

v1.52.0 adds Active Model Phase 1 research-status visibility and checkpoint documentation.

The active-model workflow remains report-only. `ACTIVE_MODEL_RESEARCH_GOVERNED_ARTIFACTS_CREATED` means research-governed active-model reference artifacts were created for governance review. It is not active production serving, not promoted model, not production model, not active thresholds, not advisory predictions, not active probabilities, not stock_profile, not buy-review, not paper approval, not performance validation, not current-candidates, not snapshot, not signal_semantics, and not trading.

## Research Status Additions

`research-status` now surfaces:

- latest active-model run id;
- active-model status, health, and workflow stage;
- active-model artifact path;
- model-weight-versioning source lineage;
- model weight reference, model version, and parameter version ids;
- report-only active-model artifact flags;
- downstream safety flags;
- active-model report path and next action.

`PAPER_WORKFLOW_READY` remains the final workflow priority when later paper workflow artifacts exist.

## Source Packaging Note

docs/project_sources/ is intentionally absent from Git. ChatGPT Project Source is maintained separately and should not be duplicated in this repository.

## Safety Boundary

This checkpoint does not create or authorize:

- promoted model;
- production model;
- active thresholds;
- advisory predictions;
- active probabilities;
- stock_profile;
- buy-review;
- paper approval;
- performance validation;
- current-candidates;
- snapshot;
- signal_semantics;
- trading;
- broker API calls;
- orders;
- messages.

## Recommended Next Task

Active Model Acceptance / Governance Design Audit Report-Only v0.1.
