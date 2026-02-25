---
title: "Sales Data Patterns"
description: "Pattern recognition reference for sales data in Excel files"
---

## Domain Indicators

Match if 3+ indicators present (high confidence), 2 indicators (medium), 1 indicator (low).

**Positive indicators:** columns matching order/invoice/purchase + customer/buyer + product/item/SKU + quantity/qty + price/amount/total + discount

**Counter-indicators:** GL codes, journal entries, campaign IDs, employee IDs, warehouse locations

## Column Name Variants

| Concept | Common Names |
|---------|-------------|
| Order ID | order_id, OrderID, order_number, OrderNo, invoice_id, InvoiceNumber |
| Customer ID | customer_id, CustomerID, cust_id, CustNo, buyer_id, client_id |
| Product ID | product_id, ProductID, SKU, sku, item_id, ItemCode, part_number |
| Quantity | quantity, qty, Qty, units, Units, count |
| Unit Price | unit_price, price, Price, UnitCost, cost_per_unit, rate |
| Total | total, Total, amount, Amount, line_total, extended_price, revenue |
| Order Date | order_date, OrderDate, Date, date, purchase_date, invoice_date |
| Status | status, Status, order_status, state |
| Discount | discount, Discount, discount_pct, discount_amount |
| Region | region, Region, territory, area, zone |

## Expected Relationships

| From | To | Type | How to Verify |
|------|-----|------|---------------|
| Orders.customer_id | Customers.customer_id | FK | Match rate > 95% |
| LineItems.order_id | Orders.order_id | FK | Match rate > 99% |
| LineItems.product_id | Products.product_id | FK | Match rate > 95% |
| Orders.region_id | Regions.region_id | FK | Match rate > 90% |

## Calculated Fields

| Field | Formula | Verification |
|-------|---------|-------------|
| line_total | `quantity * unit_price` | Compare with rtol=1e-2 |
| discount_amount | `total * discount_pct` | Compare with rtol=1e-2 |
| net_amount | `total - discount_amount` | Compare with rtol=1e-2 |
| tax_amount | `net_amount * tax_rate` | Compare with rtol=1e-2 (varies by region) |

## Typical dbt Tests

```yaml
columns:
  - name: order_id
    data_tests:
      - not_null
      - unique
  - name: customer_id
    data_tests:
      - not_null
      - relationships:
          to: ref('stg_customers')
          field: customer_id
  - name: quantity
    data_tests:
      - not_null
      - dbt_utils.expression_is_true:
          expression: ">= 0"
  - name: order_date
    data_tests:
      - not_null
      - dbt_utils.expression_is_true:
          expression: ">= '2020-01-01'"
```

## Known Pitfalls

- Negative quantities often mean returns/refunds — don't filter them out without asking
- Tax calculations vary by region — never assume a single tax rate across all rows
- Excel dates stored as serial numbers (e.g., 44927) — must convert in staging
- "Total" column may include or exclude tax — check against `qty * price` to determine
- Currency columns may have mixed formats ($1,234.56 vs 1.234,56) — check locale
- Discount can be percentage (0.15) or amount (150.00) — check value ranges
