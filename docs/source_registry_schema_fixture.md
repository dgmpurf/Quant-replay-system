# Source Registry Schema Fixture

`source-registry-schema-fixture` creates tiny synthetic source-registry schema rows
for report-only governance review. The current successful fixture status is:

`SOURCE_REGISTRY_SCHEMA_FIXTURE_CREATED`

This status means schema fixture artifacts exist for audit context only. It does not
create real source permissions, does not create production source registry state,
does not verify any API/vendor/source for production use, and does not fetch real data.

## Commands

- `source-registry-schema-fixture`
- `source-registry-schema-fixture-index`
- `source-registry-schema-fixture-health`
- `source-registry-schema-fixture-status`

## Research-Status Fields

`research-status` exposes the latest fixture run id, status, health, workflow stage,
artifact path, source count, validation issue count, report-only flags, report path,
next action, and safety flags. These fields are fixture context only.

Important distinctions:

- The Source Registry Schema Fixture does not create real source permissions.
- The Source Registry Schema Fixture does not create production source registry state.
- The Source Registry Schema Fixture does not fetch real data.
- The Source Registry Schema Fixture does not write data/raw.
- The Source Registry Schema Fixture does not write data/processed.
- The Source Registry Schema Fixture does not write data/cache.
- Source Registry Schema Fixture artifacts are not real buy-review eligibility.
- The Source Registry Schema Fixture does not set buy_review_allowed.
- Source Registry Schema Fixture artifacts are not strategy performance validation.
- The Source Registry Schema Fixture does not authorize current-candidates.
- The Source Registry Schema Fixture does not authorize snapshots.
- The Source Registry Schema Fixture does not authorize signal_semantics mutation.
- The Source Registry Schema Fixture does not authorize active stock_profile.
- The Source Registry Schema Fixture does not authorize promoted/production models.
- The Source Registry Schema Fixture does not authorize active thresholds.
- The Source Registry Schema Fixture does not authorize advisory predictions/probabilities.
- The Source Registry Schema Fixture does not authorize broker/order/message/API/trading.

## Fail-Closed Behavior

If fixture artifacts are absent, health is missing, or health is not PASS, the dashboard
must fail closed: do not fabricate source readiness, do not claim production source
permission, and do not treat fixture rows as verified replay-ready production sources.

## Future Work

Any future real source registry, raw document store, factor observation, event ingestion,
company exposure, replay evidence bundle, real buy-review, performance validation, or
trading workflow requires separate exact approval and separate validation.
