---
title: "Inventory Data Patterns"
description: "Pattern recognition reference for inventory/warehouse data in Excel files"
---

## Domain Indicators

Match if 3+ indicators present (high confidence), 2 indicators (medium), 1 indicator (low).

**Positive indicators:** columns matching SKU/item/product + warehouse/location/bin + quantity/stock/on_hand + movement/receipt/shipment + reorder/min_stock

**Counter-indicators:** GL codes, journal entries, campaign, employee/salary, order/invoice (unless paired with warehouse)

## Column Name Variants

| Concept | Common Names |
|---------|-------------|
| SKU | sku, SKU, item_id, ItemCode, part_number, product_id, material_number |
| Product Name | product_name, description, item_description, material_description |
| Warehouse | warehouse, Warehouse, warehouse_id, location, site, facility, plant |
| Bin/Slot | bin, Bin, slot, shelf, rack, storage_location |
| On Hand | on_hand, OnHand, qty_on_hand, stock_level, available_qty, balance |
| Movement Type | movement_type, type, transaction_type, mvt_type |
| Quantity | quantity, qty, Qty, units, amount |
| Date | date, Date, movement_date, transaction_date, receipt_date |
| Reorder Point | reorder_point, min_stock, safety_stock, min_qty |
| Unit Cost | unit_cost, cost, avg_cost, standard_cost |

## Expected Relationships

| From | To | Type | How to Verify |
|------|-----|------|---------------|
| Movements.sku | Products.sku | FK | Match rate > 99% |
| Movements.warehouse_id | Warehouses.warehouse_id | FK | Match rate > 99% |
| StockLevels.sku | Products.sku | FK | Match rate > 99% |
| StockLevels.warehouse_id | Warehouses.warehouse_id | FK | Match rate > 99% |

## Calculated Fields

| Field | Formula | Verification |
|-------|---------|-------------|
| closing_balance | `opening + receipts - issues` | Compare per SKU per warehouse |
| total_value | `on_hand * unit_cost` | Compare with rtol=1e-2 |
| days_of_supply | `on_hand / avg_daily_usage` | Compare with rtol=0.1 |

## Typical dbt Tests

```yaml
columns:
  - name: sku
    data_tests:
      - not_null
  - name: warehouse_id
    data_tests:
      - not_null
  - name: on_hand
    data_tests:
      - not_null
      - dbt_utils.expression_is_true:
          expression: ">= 0"
```

**Stock balance validation (custom):**
```sql
-- Opening + receipts - issues should equal closing balance
SELECT sku, warehouse_id,
    opening_balance + SUM(CASE WHEN movement_type = 'receipt' THEN quantity ELSE 0 END)
    - SUM(CASE WHEN movement_type = 'issue' THEN quantity ELSE 0 END) as calculated_balance,
    closing_balance
FROM {{ ref('stg_stock_movements') }}
GROUP BY sku, warehouse_id, opening_balance, closing_balance
HAVING ABS(calculated_balance - closing_balance) > 0.01
```

## Known Pitfalls

- Negative stock levels may be valid (backorders) or indicate data quality issues — ask
- Movement types vary by system (receipt/issue vs IN/OUT vs GR/GI) — treat as enum
- Multiple units of measure per SKU (ea, box, pallet) — check for UOM column
- Stock snapshots vs movement history: snapshots show point-in-time, movements show flow — don't mix
- Warehouse transfers appear as two rows (issue from A + receipt at B) — match by transfer ID
- Lot/batch tracking adds another dimension — check for lot_number column
