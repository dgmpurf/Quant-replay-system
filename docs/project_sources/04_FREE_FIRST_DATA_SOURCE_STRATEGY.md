# Free-First External Data Source Strategy

> Status: working memory document  
> Last generated: 2026-06-11  
> Permanence: temporary; update when a real paid vendor is purchased, a free source proves unusable, or the historical replay data strategy changes.

## Budget Constraint

Current budget constraint:

```text
Prefer free, open-source, local, public, or manually reviewed CSV sources.
Paid vendors are future backup candidates only.
Do not make current workflows depend on paid APIs.
```

Paid sources such as Wind, Choice, iFinD, RiceQuant premium, TickPlus, and similar vendors should be documented as future candidates, not implemented as required project dependencies unless explicitly requested.

## Data Source Strategy for Historical Replay

The project now treats historical replay training as a core capability. Therefore every external data source must support, or be wrapped to support:

```text
point-in-time availability
available_time
source provenance
source_hash or file hash
revision_id
permission_class
quality status
manual review status when needed
```

A dataset is not replay-ready just because it contains historical dates. It must answer:

```text
Could the system have known this information on decision date T?
```

## Data Source Priority

### First Priority: Free or Local

- LOCAL_CSV.
- Manually reviewed CSV files.
- AKShare.
- BaoStock.
- Tushare free or low-quota access, if usable.
- Public official announcement metadata.
- Exchange / official public pages with low-frequency, respectful fetches.
- Public macro/industry data that can be stored with release dates.

### Second Priority: Low-Cost or Optional

- Tushare paid/light plans if affordable.
- RiceQuant/RQData basic or trial tiers if useful.
- Low-cost data packs if exportable to CSV with clear historical availability and permission terms.

### Third Priority: Paid Vendor Backups

- Wind.
- Choice.
- iFinD.
- RiceQuant premium.
- TickPlus.
- Other institutional vendors.

These are not current dependencies.

## How External Data Should Enter the Project

All external data should follow the project pattern:

```text
source adapter
→ raw artifact
→ raw document store or raw dataset store
→ metadata with available_time / source_hash / permission_class
→ local cache
→ quality gate
→ source policy
→ PIT availability gate
→ reviewed export
→ factor or event context
→ replay/advisory artifacts
```

External data should not go directly into buy/sell logic.

## Historical Data Categories

### 1. Market Data

Initial role:

- price and volume history;
- universe eligibility support;
- market confirmation;
- forward-return labels;
- benchmark-relative labels.

Required metadata:

```text
trade_date
symbol
open/high/low/close/volume/amount
adjustment policy
source
available_time
revision_id
quality_status
```

### 2. Fundamental Data

Fundamental data should arrive before general news sentiment.

Suggested first schema areas:

- financial statements;
- financial indicators;
- disclosure calendar;
- earnings forecast / quick report;
- report_period;
- announcement_date;
- available_time;
- revision_id.

Suggested source order:

1. LOCAL_CSV fundamental ingestion.
2. AKShare optional fundamental adapter.
3. BaoStock optional fundamental adapter.
4. Tushare optional adapter if free/low-quota access is sufficient.
5. Paid sources later.

Why LOCAL_CSV first:

- lets the system define schema;
- lets PIT contracts be tested;
- avoids API credentials and quotas;
- supports manually reviewed historical samples;
- allows replay prototype before vendor dependency.

### 3. Announcement and Event Metadata

Announcements and event metadata are more structured than general news and should come before full news sentiment.

Suggested initial fields:

```text
symbol
event_date
publish_time
available_time
source
title
event_type
risk_flag
URL or file ID
source_hash
manual_review_required
parser_version
revision_id
```

First use:

```text
advisory context, risk notes, event_structured records, replay evidence bundles
```

Not first use:

```text
direct score boosting or automatic buy-review
```

### 4. Historical News and Public Event Context

News should be introduced later and conservatively.

First role:

- risk context;
- event notes;
- manual review context;
- structured event extraction;
- replay evidence context;
- source reliability experiments.

Avoid early:

- direct sentiment factor;
- automatic BUY/SELL action;
- LLM summaries as scoring inputs;
- high-frequency news trading;
- social-media-only trading signals.

News can enter replay only after:

```text
source permission is known;
publish_time and available_time are recorded;
raw text or stable raw reference is stored;
source_hash exists;
parser/extractor version is recorded;
manual review rules exist;
rumor / restricted / illegal sources are blocked or observe-only.
```

### 5. Macro / Policy / Industry / Commodity Data

Suggested first sources:

- official public statistics;
- exchange commodity/futures data where public and permitted;
- public policy announcements;
- manually reviewed industry CSVs;
- official or semi-official calendars.

Replay requirements:

```text
release_date
available_time
period_covered
revision_id
source_hash
lag_days
frequency
quality_status
```

A monthly macro value cannot be used before its release date.

## Raw Document Store Strategy

Future raw documents should be stored with enough metadata to make replay audit possible.

Suggested fields:

```text
document_id
source_id
source_name
source_type
permission_class
url_or_file_ref
title
body_or_text_ref
event_date
publish_time
available_time
fetch_time
source_hash
language
parser_version
revision_id
raw_artifact_path
manual_review_required
compliance_flag
```

The project should prefer storing references and hashes over copying large copyrighted texts into committed files. Generated raw data should not be committed to Git.

## Source Registry Fields

Future registry fields:

```text
source_id
source_name
official_url
source_type
supports_market_data
supports_fundamental
supports_announcement
supports_news
supports_sentiment
supports_macro
supports_industry
supports_historical_replay
free_or_paid
requires_token
requires_login
permission_class
commercial_use_risk
pricing_verified
official_docs_verified
project_role
recommended_stage
reliability_score
latency_profile
revision_risk
status
```

Suggested `status` values:

```text
VERIFIED
PARTIALLY_VERIFIED
UNVERIFIED
DO_NOT_USE_CORE
DO_NOT_USE_TRADING_SIGNAL
```

## Preliminary Source Classification

### Good Current Candidates

- LOCAL_CSV: primary fallback and prototype source.
- Manual reviewed CSV: critical for early replay samples.
- AKShare: free optional source; requires validation.
- BaoStock: free comparison/support source.
- Tushare free/low-quota: candidate for future optional adapter.
- Public CNInfo/official announcement metadata: candidate for announcement and event metadata.

### Future Paid Candidates

- Wind.
- Choice.
- iFinD.
- RiceQuant premium.

### Unverified or Caution

- 必盈 API.
- 太一金融 / wanxingai.com.
- TickPlus.

These should not enter core scoring until official docs, terms, quotas, historical replay suitability, and reliability are verified.

## Public Crawling Policy

The project may eventually use public crawling for official or publicly accessible data, but must avoid:

- bypassing login;
- bypassing paywalls;
- bypassing CAPTCHA;
- evading rate limits;
- high-frequency scraping;
- violating site terms;
- accessing non-public APIs;
- collecting private or restricted information.

Allowed design direction:

- low-frequency public metadata fetch;
- local cache;
- user-agent and rate limiting;
- retry/backoff;
- raw artifact storage;
- parser versioning;
- source URL and fetch time;
- quality gate.

## LLM Use for Data Extraction

LLM extraction can be considered later for offline structure extraction from public documents/news.

Allowed future role:

```text
raw public document
→ structured event draft
→ validation / parser checks
→ manual review when needed
→ event_structured artifact
```

Disallowed current role:

```text
LLM says bullish/bearish
→ buy/sell signal
```

LLM output must not be deterministic advisory logic unless explicitly redesigned and governed later. Any extraction must record model/prompt/parser version, raw references, and failure modes.

## Engineering Sequence

Recommended:

1. Fundamental Data Strategy and Schema.
2. Source Registry Schema.
3. Raw Document Store Schema.
4. Fundamental LOCAL_CSV Ingestion.
5. Fundamental Data Quality Gate.
6. Factor Definition Schema aligned with 8-layer taxonomy.
7. Factor Observation Prototype.
8. Announcement/Event Schema.
9. Announcement/Event LOCAL_CSV.
10. Public announcement metadata adapter.
11. Company Exposure Schema.
12. Historical Replay Decision Schema.
13. Forward Return Label Schema.
14. Stock Profile Schema.
15. News/Event Context only after official/fundamental/event foundations.
16. Alert/advisory display.
17. Paid API adapters only if budget allows.
