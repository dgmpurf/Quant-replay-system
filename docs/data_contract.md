# Point-in-Time Data Contract v0.1

This project replays historical decisions using only records that were available at the replay decision time. For daily replay, the default decision time is `as_of_date 15:30:00` in local China exchange time.

## Timestamp Fields

- `event_time`: when the underlying market, company, or reference event happened.
- `publish_time`: when the record became public from the source.
- `ingest_time`: when this system ingested the record.
- `available_time`: the earliest time the replay engine is allowed to use the record.
- `revision_id`: the source version for revised data.
- `source`: source system or vendor name.
- `as_of_date`: historical decision date for replay.

## Core Eligibility Rule

A record is eligible only when:

```text
available_time <= decision_time
```

If `available_time` is after `decision_time`, the record must be excluded even when the row exists in a local CSV file.

`available_time` matters because local files are naturally hindsight-rich. Without this field, replay code can accidentally use rows that were discovered, corrected, or published after the historical decision.

## Market Price Schema

Required columns:

```text
symbol, trade_date, open, high, low, close, volume, amount, pre_close,
adj_factor, is_suspended, limit_up, limit_down, event_time, publish_time,
ingest_time, available_time, revision_id, source
```

For replay on `as_of_date`, market rows are eligible only if they pass the availability rule and `trade_date <= as_of_date`.

## Universe Snapshot Schema

Required columns:

```text
as_of_date, symbol, name, instrument_type, exchange, listed_date,
delisted_date, is_active, is_st, is_suspended, industry, min_lot,
t_plus_rule, available_time, revision_id, source
```

The replay dataset keeps the latest eligible snapshot per symbol at or before `as_of_date`, then excludes symbols that are inactive, not yet listed, already delisted, suspended, or ST when those filters are enabled.

## Corporate Action Schema

Required columns:

```text
symbol, action_type, ex_date, record_date, cash_dividend, split_ratio,
rights_issue, event_time, publish_time, ingest_time, available_time,
revision_id, source
```

MVP v0.1 includes only eligible corporate actions with `ex_date <= as_of_date`. Future scheduled actions require a separate event-policy model before they can be used safely.

## Avoiding Look-Ahead Bias

- Always load data through the contract loaders.
- Always filter by `available_time <= decision_time`.
- Treat local CSV presence as storage only, not eligibility.
- Use `assert_no_future_leak(df, decision_time)` before scoring or selection.
- Keep T+1 execution prices out of scoring inputs. They may be used only to simulate fills after candidate selection.

## Revisions

Revised rows must carry a distinct `revision_id` and their own `available_time`. During replay, only revisions available at `decision_time` are eligible. If multiple eligible revisions exist for the same logical record, v0.1 keeps the latest by `available_time` and `revision_id`.

## Examples

Valid for `decision_time = 2024-01-03 15:30:00`:

```text
symbol=510300.SH, trade_date=2024-01-03, available_time=2024-01-03 15:10:00
```

Invalid for that replay:

```text
symbol=510300.SH, trade_date=2024-01-03, available_time=2024-01-03 16:05:00
```

Even though the invalid row is for the same trading day, it was not available by the decision time.
