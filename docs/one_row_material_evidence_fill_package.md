# One-Row Material Evidence Fill Package

`one-row-material-evidence-fill-package` builds a report-only diagnostics package for one PIT universe evidence row:

- `2024-04-02 / 000001 / stock_core` by default.
- It preserves leading-zero symbols and lineage to reviewer material guidance, material gate closure, partial completion impact, first-batch completion plan, validator, enrichment, reviewer no-hit acceptance, and downstream impact artifacts.
- It drafts context-safe fields only, such as identity context, exchange, listed-date context, industry context, min-lot/rule context, revision/source lineage, and a caveated SZSE 1815 quote-observation `as_of_date`.

The workflow does not approve rows and does not create clean `review_updates.csv`.

Safety defaults:

- `review_status=NEEDS_MORE_EVIDENCE`
- `include_flag=false`
- `valid_for_signal_date=false`
- `survivorship_bias_resolved=false`
- `approval_applied=false`

The package keeps active/not-delisted, no-ST, suspension/no-hit, PIT timing, and survivorship-bias resolution blockers visible. SZSE 1815 same-date quotation presence is treated as quotation/traded context only, not standalone not-delisted, no-ST, no-suspension, or survivorship evidence.

Example:

```bash
python -m quant_replay_system.cli one-row-material-evidence-fill-package
python -m quant_replay_system.cli one-row-material-evidence-fill-package-index
python -m quant_replay_system.cli one-row-material-evidence-fill-package-health
python -m quant_replay_system.cli one-row-material-evidence-fill-package-status
```

Outputs are written under:

`outputs/reports/one_row_material_evidence_fill_package/<package_id>/`

Artifact views:

- `one-row-material-evidence-fill-package-index` lists package id, target row identity, drafted-context count, material-blocker-closed count, checklist-pass candidate count, remaining-blocked count, safety flags, and artifact paths.
- `one-row-material-evidence-fill-package-health` verifies required artifacts, target row identity, leading-zero `000001`, non-approval flags, absence of clean review updates, and no PIT review/export/staging/current-candidates/data-write behavior.
- `one-row-material-evidence-fill-package-status` reports the latest package as `ONE_ROW_MATERIAL_EVIDENCE_FILL_PACKAGE_CONTEXT_DRAFTED` when context fields exist but material blockers remain.

`research-status` exposes the latest package as PIT evidence-preparation context only, including target signal date, symbol, universe, package row count, drafted-context count, material-blocker-closed count, checklist-pass candidate count, remaining-blocked count, clean-review-updates-created flag, approval-applied flag, report path, and next action. Later paper workflow priority is preserved.

This is research infrastructure only. It does not run PIT review, export-readiness, staging, universe export, current-candidates, snapshots, forward labels, live trading, broker APIs, orders, messages, external APIs, or cache mutation.
