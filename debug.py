#!/usr/bin/env python
"""Debug script for testing GaqlFixer."""
from unittest.mock import patch, MagicMock
from gaql_validator.fixer import GaqlFixer

# Create fixer instance
fixer = GaqlFixer()
query = "SELECT campaign.id FROM campaign WHERE segments.date = '2023-01-01'"

# Mock the parse result
mock_parsed = {
    "select_clause": {"fields": ["campaign.id"]},
    "from_clause": {"resource": "campaign"},
    "where_clause": {
        "conditions": [{"field": "segments.date", "operator": "=", "value": "'2023-01-01'"}]
    }
}

# Run the _fix_from_parsed method directly
fixed_query, changes = fixer._fix_from_parsed(query, mock_parsed)

print("Fixed query:", fixed_query)
print("Changes:", changes)