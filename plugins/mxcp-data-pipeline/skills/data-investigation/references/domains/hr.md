---
title: "HR Data Patterns"
description: "Pattern recognition reference for HR/people data in Excel files"
---

## Domain Indicators

Match if 3+ indicators present (high confidence), 2 indicators (medium), 1 indicator (low).

**Positive indicators:** columns matching employee/emp + department/dept + hire_date/start_date + salary/compensation + title/position/role

**Counter-indicators:** order/invoice, GL codes, campaign, product/SKU, warehouse

## Column Name Variants

| Concept | Common Names |
|---------|-------------|
| Employee ID | employee_id, EmployeeID, emp_id, EmpNo, staff_id, badge_number |
| Name | name, Name, full_name, first_name + last_name, employee_name |
| Department | department, Department, dept, dept_code, division, team |
| Title | title, Title, job_title, position, role, designation |
| Hire Date | hire_date, HireDate, start_date, date_of_joining, DOJ |
| End Date | end_date, termination_date, last_day, separation_date |
| Salary | salary, Salary, compensation, base_pay, annual_salary, CTC |
| Manager | manager, Manager, manager_id, reports_to, supervisor |
| Status | status, Status, employment_status, active, is_active |
| Location | location, Location, office, site, work_location |

## Expected Relationships

| From | To | Type | How to Verify |
|------|-----|------|---------------|
| Employees.department_id | Departments.department_id | FK | Match rate > 99% |
| Employees.manager_id | Employees.employee_id | Self-FK | Match rate > 90% (CEO has no manager) |
| Attendance.employee_id | Employees.employee_id | FK | Match rate > 99% |
| Compensation.employee_id | Employees.employee_id | FK | Match rate > 99% |

## Calculated Fields

| Field | Formula | Verification |
|-------|---------|-------------|
| tenure_years | `(today - hire_date) / 365.25` | Compare with rtol=0.05 |
| annual_salary | `monthly_salary * 12` | Compare with rtol=1e-2 |
| headcount | `COUNT(*) WHERE status = 'active'` per department | Verify against department totals |

## Typical dbt Tests

```yaml
columns:
  - name: employee_id
    data_tests:
      - not_null
      - unique
  - name: hire_date
    data_tests:
      - not_null
      - dbt_utils.expression_is_true:
          expression: "<= CURRENT_DATE"
  - name: salary
    data_tests:
      - dbt_utils.expression_is_true:
          expression: "> 0"
  - name: department
    data_tests:
      - not_null
```

## Known Pitfalls

- Terminated employees may still appear in exports — check status/end_date columns
- Manager self-references create hierarchy — ensure no circular references
- Salary may be monthly, annual, or hourly — check value ranges to determine
- Date formats vary wildly across regions (DD/MM vs MM/DD) — validate with known employees
- PII sensitivity: name, email, SSN columns should be flagged for masking
- Multiple rows per employee may indicate effective-dated records (salary history)
