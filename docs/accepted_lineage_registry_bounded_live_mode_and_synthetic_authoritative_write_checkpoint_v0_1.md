# Accepted Lineage Registry Bounded Live Mode and Synthetic Authoritative-Write Checkpoint v0.1

## Checkpoint identity

- Predecessor branch: `main`
- Predecessor commit: `55f1df796781baccfe0cccca09f88ed23fe1129c`
- Predecessor `origin/main`: `55f1df796781baccfe0cccca09f88ed23fe1129c`
- Checkpoint scope: governed accepted-lineage registry implementation with synthetic temporary-root verification only
- Tag created: no
- Project Source updated: no

## Cumulative implementation scope

P1 established the explicit live-registry policy and schema surface, review-contract validation, and candidate-mode regression boundaries. Candidate roots remain non-live and cannot be reclassified, copied, imported, renamed, or promoted into live state.

P2 added bounded Windows filesystem hardening and mode separation: reparse-safe handles, file and directory identity checks, hard-link checks, retained-handle flushes, handle-relative same-volume rename support, verified lock disposition, live/candidate path separation, and single-writer lock integration. These controls remain subject to separate L2 platform acceptance before any real workflow.

P3 added:

- initialized empty live-root support with exact policy, schema, instance, seal, and empty derived-index bindings;
- full authorization and immutable-input preflight for the reviewer payload, subject manifest, receipt, subject packet, and exact six artifacts;
- exact five-file non-authoritative staging;
- a verified source-disappearance and target-identity authoritative rename boundary;
- authorization consumption only after proven rename;
- immutable live-entry verification;
- exact identical replay, authorization replay-conflict, and receipt-collision decisions;
- crash classifications for pre-rename, ambiguous rename, post-rename verification, and derived-index transaction states;
- index-only recovery that never rematerializes the authoritative entry;
- pending human live-entry review with no downstream authority.

This L1 finalization hardens replay identity so it also binds:

- `accepted_candidate_entry_seal_sha256`;
- `accepted_pilot_review_zip_sha256`;
- a canonical SHA-256 binding over the immutable-input verification evidence for the subject packet and exact six artifacts;
- the live registry instance, policy version, and schema version already recorded in the entry manifest.

An identical replay requires every immutable identity field and the same consumed live materialization authorization. A different authorization with otherwise identical identity stops with `LIVE_ENTRY_AUTHORIZATION_REPLAY_CONFLICT_STOP`. Any immutable identity drift at the same receipt path, including either provenance hash, stops with `LIVE_ENTRY_RECEIPT_COLLISION_STOP`. Replay decisions do not rewrite entry bytes, index bytes, health state, or authorization state.

The existing-entry probe now occurs only inside the transaction after live-root authority, exact root binding, live configuration, registry instance, and opaque subject/receipt key derivation have validated. No target existence, type, stat, glob, or directory-list probe is performed against an unvalidated live target.

## Validation

Focused gates completed with zero failures, errors, or skips:

- Materialization, crash/recovery, and authorization lifecycle: `101 passed`.
- Empty live-root initialization: `24 passed`.
- Windows backend, root-mode separation, locking, ownership security, and index health: `51 passed`.
- Subject packet and artifact security: `19 passed`.

Final serial full non-slow gate, using the repository `.venv` interpreter:

```text
python -B -m pytest -m "not slow" -q
6696 passed, 109 deselected, 5 warnings in 1490.75s (0:24:50)
```

The warnings are existing pandas parsing/dtype warnings outside the accepted-lineage registry change surface. No test was skipped.

## Exact synthetic-only boundary

All live-entry write, replay, collision, crash, and recovery verification used synthetic inputs and per-test temporary roots. This checkpoint did not access or modify a real live root, a retained candidate registry, or real Stage1B-A inputs. It did not perform a real accepted-lineage materialization, live-entry human acceptance, broker operation, order submission, or network/API call.

The registry grants no business, research, evidence-acceptance, PIT, replay, buy-review, or trading authority. Every supported outcome preserves:

```text
business_authority = none
research_authority = none
evidence_acceptance_authority = none
PIT_authority = none
replay_authority = none
buy_review_authority = none
trading_authority = none
next_task_authorized_by_registry = false
```

## Remaining gates

Real L2 Windows platform acceptance, L3 live-root initialization, L4 real Stage1B-A fresh rematerialization, and L5 human live-entry acceptance remain separately gated. This checkpoint authorizes none of them.

Project Source remains intentionally deferred until an accepted L5 live entry exists and a separate exact Project Source authorization is granted. No tag is created by this checkpoint.
