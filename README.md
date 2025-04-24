# GAQL Validator

A Python package for validating Google Ads Query Language (GAQL) queries offline. This package provides a local/offline tool for validating GAQL queries, ensuring they meet the grammar rules and syntax constraints set by the official Google Ads API.

## Features

- **Syntax Validation**: Ensures queries follow the proper GAQL syntax
- **Clause Ordering**: Verifies that clauses appear in the correct order (SELECT, FROM, WHERE, ORDER BY, LIMIT, PARAMETERS)
- **Resource Validation**: Checks that the queried resource exists
- **Field Validation**: Validates field names and their compatibility with operators
- **Operator Validation**: Ensures operators are valid and compatible with the fields
- **Format Utilities**: Provides utilities for formatting and building GAQL queries
- **CLI Interface**: Includes a command-line tool for quick validations

## Installation

```bash
pip install gaql-validator
```

## Usage

### Basic Validation

```python
from gaql_validator.validator import GaqlValidator

validator = GaqlValidator()

# Validate a GAQL query
query = "SELECT campaign.id FROM campaign LIMIT 10"
result = validator.validate(query)

if result["valid"]:
    print("Query is valid!")
else:
    print("Query is invalid. Errors:")
    for error in result["errors"]:
        print(f"- {error}")
```

### Strict Validation Mode

```python
from gaql_validator.validator import GaqlValidator
from gaql_validator.exceptions import GaqlSyntaxError, GaqlResourceError, GaqlFieldError

validator = GaqlValidator()

try:
    # Use strict mode to raise exceptions
    result = validator.validate("SELECT campaign.id FROM invalid_resource", strict=True)
    print("Query is valid!")
except GaqlSyntaxError as e:
    print(f"Syntax error: {e}")
except GaqlResourceError as e:
    print(f"Resource error: {e}")
except GaqlFieldError as e:
    print(f"Field error: {e}")
```

### Query Building

```python
from gaql_validator.utils import build_gaql_query, build_condition

# Build a simple condition
condition = build_condition("campaign.status", "=", "ENABLED")
print(condition)  # Output: campaign.status = 'ENABLED'

# Build a complete query
query = build_gaql_query(
    select_fields=["campaign.id", "campaign.name", "metrics.impressions"],
    resource="campaign",
    where_conditions=[
        "campaign.status = 'ENABLED'",
        "metrics.impressions > 100"
    ],
    order_by=[{"field": "metrics.impressions", "direction": "DESC"}],
    limit=50,
    parameters={"include_drafts": True}
)
print(query)
```

### Query Formatting

```python
from gaql_validator.utils import format_gaql

# Format a GAQL query for better readability
query = "SELECT campaign.id, campaign.name FROM campaign WHERE campaign.status = 'ENABLED' LIMIT 50"
formatted_query = format_gaql(query, indent=2)
print(formatted_query)
```

### Command-Line Interface

```bash
# Validate a query directly
gaql-validate "SELECT campaign.id FROM campaign LIMIT 10"

# Validate a query from a file
gaql-validate -f query.gaql

# Use strict mode
gaql-validate --strict "SELECT campaign.id FROM campaign LIMIT 10"

# Enable verbose output
gaql-validate --verbose "SELECT campaign.id FROM campaign LIMIT 10"
```

## GAQL Grammar

GAQL queries follow this structure:

```
Query            -> SelectClause FromClause WhereClause? OrderByClause?
                    LimitClause? ParametersClause?
SelectClause     -> SELECT FieldName (, FieldName)*
FromClause       -> FROM ResourceName
WhereClause      -> WHERE Condition (AND Condition)*
OrderByClause    -> ORDER BY Ordering (, Ordering)*
LimitClause      -> LIMIT PositiveInteger
ParametersClause -> PARAMETERS (include_drafts | omit_unselected_resource_names) = (true | false)
                    (, (include_drafts | omit_unselected_resource_names) = (true | false) )*
```

For a complete reference, see the [Google Ads API documentation](https://developers.google.com/google-ads/api/docs/query/grammar).

## Example GAQL Queries

### Basic Query

```sql
SELECT
  campaign.id,
  campaign.name,
  metrics.impressions
FROM campaign
WHERE campaign.status = 'ENABLED'
LIMIT 100
```

### Query with Multiple Conditions

```sql
SELECT
  ad_group.id,
  ad_group.name,
  campaign.name,
  metrics.impressions
FROM ad_group
WHERE
  ad_group.status = 'ENABLED'
  AND segments.date DURING LAST_7_DAYS
  AND campaign.name LIKE '%2023%'
ORDER BY metrics.impressions DESC
LIMIT 50
```

### Query with Parameters

```sql
SELECT
  campaign.id,
  campaign.name
FROM campaign
WHERE campaign.status = 'ENABLED'
PARAMETERS include_drafts=true
```

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.