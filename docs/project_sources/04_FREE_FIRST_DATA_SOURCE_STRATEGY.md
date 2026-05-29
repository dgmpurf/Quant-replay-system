# Free-First External Data Source Strategy

> Status: working memory document  
> Last generated: 2026-05-28  
> Permanence: temporary; update when a real paid vendor is purchased or a free source proves unusable.

## Budget Constraint

Current budget constraint:

```text
Prefer free, open-source, local, public, or manually reviewed CSV sources.
Paid vendors are future backup candidates only.
Do not make current workflows depend on paid APIs.
```

Paid sources such as Wind, Choice, iFinD, RiceQuant premium, TickPlus, and similar vendors should be documented as future candidates, not implemented as required project dependencies unless explicitly requested.

## Data Source Priority

### First Priority: Free or Local

- LOCAL_CSV.
- AKShare.
- BaoStock.
- Tushare free or low-quota access, if usable.
- Public announcement metadata.
- Manual reviewed CSV files.
- Public official pages with low-frequency, respectful fetches.

### Second Priority: Low-Cost or Optional

- Tushare paid/light plans if affordable.
- RiceQuant/RQData basic or trial tiers if useful.
- Low-cost data packs if exportable to CSV.

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
→ metadata
→ local cache
→ quality gate
→ source policy
→ reviewed export
→ factor or event context
→ signal/advisory
```

External data should not go directly into buy/sell logic.

## Fundamental Data Strategy

Fundamental data should arrive before news sentiment.

Suggested first schema areas:

- financial statements,
- financial indicators,
- disclosure calendar,
- earnings forecast / quick report,
- report_period,
- announcement_date,
- available_time,
- revision_id.

### Suggested Fundamental Source Order

1. LOCAL_CSV fundamental ingestion.
2. AKShare optional fundamental adapter.
3. BaoStock optional fundamental adapter.
4. Tushare optional adapter if free/low-quota access is sufficient.
5. Paid sources later.

### Why LOCAL_CSV First?

It allows the system to define:

- schema,
- point-in-time contracts,
- quality checks,
- factor prototype,

without being blocked by API credentials, quotas, or vendor changes.

## Announcement and Event Strategy

Announcements and event metadata are more structured than general news and should come before full news sentiment.

Suggested initial fields:

- symbol,
- event_date,
- available_time,
- source,
- title,
- event_type,
- risk_flag,
- URL or file ID,
- source_hash,
- manual_review_required.

First use:

```text
advisory context and risk notes
```

Not first use:

```text
direct score boosting or automatic buy-review
```

## News Strategy

News should be introduced later and conservatively.

First role:

- risk context,
- event notes,
- manual review context.

Avoid early:

- direct sentiment factor,
- automatic BUY/SELL action,
- LLM summaries as scoring inputs,
- high-frequency news trading.

## Public Crawling Policy

The project may eventually use public crawling for official or publicly accessible data, but must avoid:

- bypassing login,
- bypassing paywalls,
- bypassing CAPTCHA,
- evading rate limits,
- high-frequency scraping,
- violating site terms,
- accessing non-public APIs.

Allowed design direction:

- low-frequency public metadata fetch,
- local cache,
- user-agent and rate limiting,
- retry/backoff,
- raw artifact storage,
- parser versioning,
- source URL and fetch time,
- quality gate.

## Candidate Data Source Registry

Future registry fields:

- source_name
- official_url
- source_type
- supports_market_data
- supports_fundamental
- supports_announcement
- supports_news
- supports_sentiment
- free_or_paid
- requires_token
- requires_login
- commercial_use_risk
- pricing_verified
- official_docs_verified
- project_role
- recommended_stage
- status:
  - VERIFIED
  - PARTIALLY_VERIFIED
  - UNVERIFIED
  - DO_NOT_USE_CORE

## Preliminary Source Classification

### Good Current Candidates

- LOCAL_CSV: primary fallback.
- AKShare: free optional source; requires validation.
- BaoStock: free comparison/support source.
- Tushare free/low-quota: candidate for future optional adapter.
- Public CNInfo/official announcement metadata: candidate for public announcement metadata.

### Future Paid Candidates

- Wind.
- Choice.
- iFinD.
- RiceQuant premium.

### Unverified or Caution

- 必盈 API.
- 太一金融 / wanxingai.com.
- TickPlus.

These should not enter core scoring until official docs, terms, quotas, and reliability are verified.

## Engineering Sequence

Recommended:

1. Fundamental Data Strategy and Schema.
2. Fundamental LOCAL_CSV Ingestion.
3. Fundamental Data Quality Gate.
4. Fundamental Factor Prototype.
5. Fundamental advisory context.
6. Announcement/Event Schema.
7. Announcement/Event LOCAL_CSV.
8. Public announcement metadata adapter.
9. News/Event Context.
10. Alert/advisory display.
11. Paid API adapters only if budget allows.
