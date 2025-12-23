# Common Mistakes to Avoid

**Read this before creating any tools.** These mistakes cause validation errors.

## 1. Missing `tool:` Wrapper

```yaml
# WRONG
mxcp: 1
name: get_calendar
description: ...

# CORRECT
mxcp: 1
tool:
  name: get_calendar
  description: ...
```

## 2. Missing Parameter Description

```yaml
# WRONG - causes validation error
parameters:
  - name: user_id
    type: string

# CORRECT
parameters:
  - name: user_id
    type: string
    description: The unique user identifier
```

## 3. Invalid Type Names

Valid types: `string`, `number`, `integer`, `boolean`, `array`, `object`

```yaml
# WRONG
type: map      # Use 'object'
type: strng    # Typo
type: int      # Use 'integer'

# CORRECT
type: object
type: string
type: integer
```

## 4. Invalid Parameter Names

Parameter names must match `^[a-zA-Z_][a-zA-Z0-9_]*$`

```yaml
# WRONG
name: user-name    # Hyphens not allowed
name: 1st_param    # Can't start with number

# CORRECT
name: user_name
name: first_param
```

## 5. Invalid Format Values

Valid formats: `email`, `uri`, `date`, `time`, `date-time`, `duration`, `timestamp`

```yaml
# WRONG
format: datetime   # Missing hyphen

# CORRECT
format: date-time
```

## 6. Both `code` and `file` in Source

Source must have exactly one of `code` or `file`:

```yaml
# WRONG
source:
  code: "SELECT 1"
  file: "query.sql"  # Can't have both

# CORRECT
source:
  code: "SELECT 1"
# OR
source:
  file: ../sql/query.sql
```

## Quick Reference

| Mistake | Fix |
|---------|-----|
| Missing `tool:` wrapper | Add `tool:` before name/description |
| Missing parameter description | Add `description:` to every parameter |
| `type: int` | Use `type: integer` |
| `type: map` | Use `type: object` |
| `format: datetime` | Use `format: date-time` |
| `name: user-name` | Use `name: user_name` (no hyphens) |
| Both `code:` and `file:` | Use only one |
