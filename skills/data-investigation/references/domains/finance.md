---
title: "Finance Data Patterns"
description: "Pattern recognition reference for finance/accounting data in Excel files"
---

## Domain Indicators

Match if 3+ indicators present (high confidence), 2 indicators (medium), 1 indicator (low).

**Positive indicators:** columns matching GL/account/ledger + debit/credit + period/fiscal + journal/entry + balance

**Counter-indicators:** order/invoice, product/SKU, campaign, employee name, warehouse

## Column Name Variants

| Concept | Common Names |
|---------|-------------|
| Account Code | account_code, AccountCode, GL_code, gl_number, account_id, chart_of_accounts |
| Account Name | account_name, AccountName, description, gl_description |
| Debit | debit, Debit, dr, DR, debit_amount |
| Credit | credit, Credit, cr, CR, credit_amount |
| Balance | balance, Balance, running_balance, ending_balance, net |
| Period | period, Period, fiscal_period, accounting_period, month, fiscal_month |
| Journal ID | journal_id, JournalID, entry_id, JE_number, voucher_no |
| Date | transaction_date, posting_date, effective_date, entry_date |
| Cost Center | cost_center, CostCenter, department, dept_code, profit_center |

## Expected Relationships

| From | To | Type | How to Verify |
|------|-----|------|---------------|
| Transactions.account_code | ChartOfAccounts.account_code | FK | Match rate > 99% |
| Transactions.cost_center | CostCenters.code | FK | Match rate > 95% |
| JournalEntries.journal_id | JournalHeaders.journal_id | FK | Match rate > 99% |

## Calculated Fields

| Field | Formula | Verification |
|-------|---------|-------------|
| net_amount | `debit - credit` | Compare with atol=0.01 |
| balance | Running sum of `debit - credit` per account | Verify end-of-period balances |

## Typical dbt Tests

```yaml
columns:
  - name: account_code
    data_tests:
      - not_null
      - relationships:
          to: ref('stg_chart_of_accounts')
          field: account_code
  - name: debit
    data_tests:
      - dbt_utils.expression_is_true:
          expression: ">= 0"
  - name: credit
    data_tests:
      - dbt_utils.expression_is_true:
          expression: ">= 0"
```

**Journal entry balance test (custom):**
```sql
-- Every journal entry must balance: SUM(debit) = SUM(credit)
SELECT journal_id, SUM(debit) as total_debit, SUM(credit) as total_credit
FROM {{ ref('stg_journal_entries') }}
GROUP BY journal_id
HAVING ABS(SUM(debit) - SUM(credit)) > 0.01
```

## Known Pitfalls

- Debit/credit may be in a single column with +/- signs instead of separate columns
- Account codes may have hierarchical structure (1000-1999 = Assets, 2000-2999 = Liabilities)
- Fiscal year may not align with calendar year (e.g., April-March)
- Period "13" or "0" often means adjustments or opening balances — don't filter
- Some systems export credit as negative debit — check if credit column is always zero
- Balance column may be period-end only (not every transaction) — verify before using as running total
