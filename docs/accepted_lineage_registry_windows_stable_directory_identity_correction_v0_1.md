# Accepted Lineage Registry Windows Stable Directory Identity Correction v0.1

## Checkpoint scope

This checkpoint records the narrow Windows directory-identity correction authorized after the blocked L2 Windows platform acceptance review. It changes no registry authority, performs no real live-root initialization, accesses no retained candidate, and grants no L3, L4, L5, replay, research, buy-review, trading, broker, or order authority.

Prior evidence accepted for this correction:

- blocked L2 classification: `L2_WINDOWS_PLATFORM_ACCEPTANCE_BLOCKED`;
- blocked handoff SHA-256: `8039b0172fb0ffcecd4ff3c6b82153464b4569e367c8ae513004c36e282acee1`;
- blocked `L2_WORK_STATE.json` SHA-256: `95279b0996f3184e1afb93b9f2fe5fb811ff3dc4e8bf7fea1fab1237ed7f9bb5`;
- parent implementation commit: `6efa2ebafd8793c2e41eb919d6adeaf34db133be`.

## Stable directory identity contract

`WindowsHandleIdentity` continues to capture the complete queried metadata, including `file_size`. The correction adds an explicit `WindowsStableDirectoryIdentity` projection for continuity checks across directory content creation and directory rename.

The stable projection requires exact equality of:

- volume serial number;
- file index;
- directory object type;
- link count, with the invariant that it is exactly one;
- reparse-point status, with reparse points rejected.

Directory `file_size` is deliberately excluded because NTFS may change it when children are added. Other file-content integrity controls are unchanged: child-file handles are link-checked and durably flushed, and entry bytes remain governed by canonical hashes, manifests, seals, and post-write verification.

The correction is limited to committed directory continuity verification. File lock ownership checks and other identity comparisons retain their existing full-identity behavior.

## Committed handle-lifetime contract

Inspection of `canonical.write_bytes_durable` and `transaction.materialize_live_entry_transaction` confirms the committed authoritative-write sequence:

1. each staged child file is created and fsynced;
2. the child file is reopened without following reparse points;
3. its single-link invariant is checked and its handle is flushed;
4. the child-file context closes before `write_bytes_durable` returns;
5. all staged writes, parent-directory flushes, manifest/seal checks, and stage-directory flush complete before rename;
6. `rename_directory_by_handle` retains the source-directory handle and target-parent handle while issuing the handle-relative rename;
7. the source path must disappear, the target path must exist, and the reopened target must have the same stable directory identity;
8. entry bytes are subsequently checked through the existing manifest and seal verification path.

The earlier diagnostic that deliberately kept an additional child-file handle open across the parent-directory rename does not match this committed lifetime and is classified `OUT_OF_CONTRACT_HOST_DIAGNOSTIC_NOT_REQUIRED_BY_COMMITTED_TRANSACTION_PATH`. This classification is not a risk waiver.

## Regression coverage

The authorized tests cover:

- actual NTFS directory-size drift after nested content creation;
- stable volume and file-index continuity with an exact one-link invariant;
- fail-closed volume, file-index, link-count, type, and reparse substitutions;
- actual handle-relative rename after all child-file handles close;
- source disappearance and reopened target stable identity;
- byte preservation for all staged files;
- actual Windows-backend temporary empty-live-root initialization with zero authoritative entries;
- continued exclusion of retained candidates and prospective real live roots.

## Validation

The required test gates passed on the repository Windows virtual environment:

- affected files: `52 passed in 53.88s`, with zero failures, errors, or skips;
- bounded L2 platform set: `120 passed in 53.60s`, with zero failures, errors, or skips;
- full non-slow suite: `6705 passed, 109 deselected, 5 warnings in 1598.10s`, with zero failures or errors.

The five full-suite warnings are pre-existing pandas parsing/dtype warnings in unrelated data-ingestion, factor-dataset, forward-return-label, metric-evaluation, and metric-extension tests. No test uses a real network or API, and no real live-root action is performed. The fresh S5_006 correction and L2 rerun evidence bundle records these gates and the final `git diff --check` result.
