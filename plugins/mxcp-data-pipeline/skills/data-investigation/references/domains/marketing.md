---
title: "Marketing Data Patterns"
description: "Pattern recognition reference for marketing data in Excel files"
---

## Domain Indicators

Match if 3+ indicators present (high confidence), 2 indicators (medium), 1 indicator (low).

**Positive indicators:** columns matching campaign + channel/source/medium + impressions/clicks/conversions + spend/budget/cost + lead/prospect

**Counter-indicators:** GL codes, journal entries, order/invoice, employee ID, warehouse

## Column Name Variants

| Concept | Common Names |
|---------|-------------|
| Campaign ID | campaign_id, CampaignID, campaign_name, campaign_code |
| Channel | channel, Channel, source, medium, utm_source, utm_medium, platform |
| Impressions | impressions, Impressions, views, reach |
| Clicks | clicks, Clicks, click_count, sessions |
| Conversions | conversions, Conversions, leads, signups, purchases |
| Spend | spend, Spend, cost, budget, ad_spend, media_cost |
| CTR | ctr, CTR, click_through_rate |
| CPC | cpc, CPC, cost_per_click |
| Date | date, Date, campaign_date, report_date, week, month |
| Lead Score | lead_score, score, quality_score, MQL_score |

## Expected Relationships

| From | To | Type | How to Verify |
|------|-----|------|---------------|
| CampaignMetrics.campaign_id | Campaigns.campaign_id | FK | Match rate > 99% |
| Leads.campaign_id | Campaigns.campaign_id | FK | Match rate > 90% |
| Leads.channel | Channels.channel_name | FK | Match rate > 85% |

## Calculated Fields

| Field | Formula | Verification |
|-------|---------|-------------|
| CTR | `clicks / impressions` | Compare with rtol=1e-2 |
| CPC | `spend / clicks` | Compare with rtol=1e-2 |
| Conversion Rate | `conversions / clicks` | Compare with rtol=1e-2 |
| ROAS | `revenue / spend` | Compare with rtol=1e-2 |

## Typical dbt Tests

```yaml
columns:
  - name: campaign_id
    data_tests:
      - not_null
  - name: impressions
    data_tests:
      - dbt_utils.expression_is_true:
          expression: ">= 0"
  - name: clicks
    data_tests:
      - dbt_utils.expression_is_true:
          expression: ">= 0"
      - dbt_utils.expression_is_true:
          expression: "<= impressions"
  - name: conversions
    data_tests:
      - dbt_utils.expression_is_true:
          expression: "<= clicks"
```

## Known Pitfalls

- Metrics may be aggregated at different time granularity per row (daily vs weekly vs monthly) — check date patterns
- Attribution models vary: last-click, first-click, linear — same conversion may appear in multiple campaigns
- Spend may include/exclude agency fees — check if totals match invoice amounts
- UTM parameters are often inconsistent (mixed case, typos) — normalize in staging
- Funnel stages (MQL/SQL/SAL) are company-specific — treat as enum, don't assume meanings
- Zero impressions with non-zero clicks indicates data quality issue
