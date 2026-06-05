# PIT Evidence Policy Profile Comparison v0.1

`pit-evidence-policy-profile-comparison` compares the strict PIT evidence checklist result with explicit opt-in policy profiles such as `EOD_POST_CLOSE_LOW_BUDGET_PIT` and `EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT`.

This workflow is report-only. It does not apply approvals, set `APPROVED_FOR_PIT_UNIVERSE`, run `pit-universe-overlay-review`, run export readiness, run export staging, export universe files, write `data/raw`, write `data/processed`, run current-candidates, build snapshots, compute forward labels, mutate cache, call APIs, send messages, connect to brokers, or place orders.

## Purpose

The strict checklist validator remains the reference default. The comparison workflow asks a narrower question:

- Which strict blockers would remain under the normal `STRICT_PIT` checklist?
- Which timing blockers would be relaxed only under an explicit EOD/post-close research policy?
- Which official no-hit context would be visible only under an explicit reviewed no-hit policy?
- Which non-relaxed PIT evidence blockers still prevent checklist pass?
- Would any row become only an approval-candidate preview under the opt-in profile?

The answer is context only. A preview is not an approval and does not create review updates.

## Policy Profiles

`STRICT_PIT` remains the default reference profile.

`EOD_POST_CLOSE_LOW_BUDGET_PIT` is opt-in and applies only to historical EOD/post-close research review. It may relax:

- post-close `available_time` when `available_time <= decision_time`;
- same-day local market cache as supporting evidence for active/traded/suspension context;
- `as_of_date=signal_date` only when tied to accepted same-day evidence snapshot context.

It does not relax:

- official identity and listed-date evidence;
- not-delisted evidence;
- stock ST/no-ST evidence;
- survivorship-bias resolution;
- reviewer, reviewed-at, and review-reason requirements;
- evidence source and evidence reference requirements;
- future-dated universe hint rejection.

`EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT` is also opt-in and report-only. It may treat official no-hit searches as supporting context only when all of the following are explicit:

- same-date official quotation presence exists for the row;
- official source coverage and query windows are documented;
- reviewer, reviewed-at, review reason, evidence source, and evidence reference/path are present;
- the row still carries an explicit survivorship-bias rationale requirement.

This profile may expose `no_hit_context_supported=true` for not-delisted, no-suspension, and stock no-ST context, but it still does not set `APPROVED_FOR_PIT_UNIVERSE`, create approval updates, run PIT review, export universe files, or resolve survivorship automatically.

## CLI Usage

```powershell
python -m quant_replay_system.cli pit-evidence-policy-profile-comparison --validator outputs/reports/pit_evidence_checklist_validator/62e9eb747197 --completed-updates outputs/reports/manual_diagnostics/codex_official_evidence_acquisition_v0_1/combined_updated_draft_completed_updates.csv --policy-audit outputs/reports/manual_diagnostics/eod_post_close_low_budget_pit_policy_profile_audit_v0_1 --profile EOD_POST_CLOSE_LOW_BUDGET_PIT --decision-policy EOD_POST_CLOSE --output-dir outputs/reports/pit_evidence_policy_profile_comparison
```

Reviewed no-hit support is opt-in:

```powershell
python -m quant_replay_system.cli pit-evidence-policy-profile-comparison --validator outputs/reports/pit_evidence_checklist_validator/62e9eb747197 --completed-updates outputs/reports/pit_official_status_evidence_packet/8efabe2ffe62/updated_draft_completed_updates.csv --policy-audit outputs/reports/manual_diagnostics/official_no_hit_evidence_policy_audit_v0_1 --profile EOD_POST_CLOSE_REVIEWED_NO_HIT_SUPPORT_PIT --decision-policy EOD_POST_CLOSE --output-dir outputs/reports/pit_evidence_policy_profile_comparison
```

Use `--decision-time` to set an explicit post-close decision time. Without it, the command uses the conservative default encoded in the workflow.

## Artifacts

Artifacts are written under:

```text
outputs/reports/pit_evidence_policy_profile_comparison/<comparison_id>/
```

Files:

- `pit_evidence_policy_profile_comparison.csv`
- `pit_evidence_policy_profile_summary.csv`
- `relaxed_blocker_matrix.csv`
- `remaining_blocker_matrix.csv`
- `eod_post_close_policy_profile_snapshot.csv`
- `report.md`
- `metadata.json`

The metadata records `profile_is_opt_in=true`, `strict_default_unchanged=true`, `approval_applied=false`, `pit_review_run=false`, `export_readiness_run=false`, `export_staging_run=false`, `universe_exported=false`, `active_worklist_mutated=false`, and local-only safety flags.

## Artifact Views

Use:

```powershell
python -m quant_replay_system.cli pit-evidence-policy-profile-comparison-index
python -m quant_replay_system.cli pit-evidence-policy-profile-comparison-health
python -m quant_replay_system.cli pit-evidence-policy-profile-comparison-status
```

The index discovers comparison artifacts. The health check verifies required files, required columns, strict-reference/default safety, opt-in profile metadata, and that no approvals or downstream workflows were created. The status command summarizes the latest comparison with stages:

- `NO_PIT_EVIDENCE_POLICY_PROFILE_COMPARISONS`
- `PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_READY`
- `PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_ALL_BLOCKED`
- `PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_HAS_CANDIDATE_PREVIEWS`
- `PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_FAILED`

## Research Status

`research-status` includes the latest policy-profile comparison as evidence-policy context. The unified summary exposes comparison id, status/stage, health status, profile name, row count, strict pass count, EOD low-budget pass count, reviewed no-hit support pass count, no-hit context supported count, reviewer acceptance required count, relaxed blocker count, remaining blocked count, report path, and next action.

When the comparison is `PIT_EVIDENCE_POLICY_PROFILE_COMPARISON_ALL_BLOCKED`, the dashboard treats the warning as expected reviewable PIT evidence policy work. If later paper workflow artifacts exist, final `workflow_stage` remains on the later paper workflow path and comparison fields remain visible as audit context.

## Known Limitations

- The workflow does not verify external evidence documents.
- The low-budget profile is a comparison profile only; it is not the strict validator default.
- The reviewed no-hit profile is opt-in only and no-hit context is supporting evidence, not approval evidence.
- Same-day local cache can support active/traded/suspension context only when timing is explicitly compatible with the decision policy.
- Not-delisted, ST/no-ST, survivorship, reviewer, and evidence-reference blockers remain strict unless a reviewer explicitly accepts documented no-hit context. Survivorship still requires separate rationale.
- A comparison pass would still be only a manual preview, not approval, export readiness, staging, or strategy validation.
