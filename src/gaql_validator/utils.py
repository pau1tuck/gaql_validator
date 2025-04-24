"""
Utility functions for working with GAQL queries.
"""
import re

from gaql_validator.exceptions import GaqlError
from gaql_validator.validator import VALID_RESOURCES, VALID_FIELD_PREFIXES  # type: ignore


# pylint: disable=too-many-locals
def format_gaql(query: str, indent: int = 2) -> str:
    """
    Format a GAQL query for better readability.

    Args:
        query: The GAQL query to format.
        indent: Number of spaces to use for indentation.

    Returns:
        A formatted GAQL query string.
    """
    # Normalize whitespace first
    normalized_query: str = re.sub(r'\s+', ' ', query.strip())

    # Replace keywords with newlines and indentation
    keywords: list[str] = ["SELECT", "FROM", "WHERE", "ORDER BY", "LIMIT", "PARAMETERS"]
    formatted: str = normalized_query

    for i, keyword in enumerate(keywords):
        if i == 0:  # Don't add newline before the first keyword
            pattern: str = f"({keyword})"
        else:
            pattern = f"([\\s]+)({keyword})"
            replacement: str = f"\n{keyword}"
            formatted = re.sub(pattern, replacement, formatted)

    # Format field lists in SELECT clause
    if "SELECT" in formatted:
        select_pattern: str = r"(SELECT)([^F]+)(FROM)"
        select_match = re.search(select_pattern, formatted)

        if select_match:
            fields = select_match.group(2).strip()
            formatted = re.sub(select_pattern, f"SELECT {fields} FROM", formatted)

    # Format conditions in WHERE clause
    if "WHERE" in formatted:
        where_pattern: str = r"(WHERE)([^O]+?)(ORDER BY|LIMIT|PARAMETERS|$)"
        where_match = re.search(where_pattern, formatted)

        if where_match:
            conditions: str = where_match.group(2).strip()
            condition_list: list[str] = [c.strip() for c in conditions.split("AND")]
            indented_conditions: str = "\n" + " " * indent + (" AND ".join(condition_list))
            formatted = re.sub(where_pattern, f"\\1{indented_conditions}\\3", formatted)

    # Format ORDER BY clause
    if "ORDER BY" in formatted:
        # Fix the pattern to handle complex ORDER BY cases
        order_pattern: str = r"(ORDER BY)([^L]+?)(LIMIT|PARAMETERS|$)"
        order_match = re.search(order_pattern, formatted)

        if order_match:
            # Clean up the orderings by fixing any issues with spacing
            orderings: str = order_match.group(2).strip()
            orderings = re.sub(r'ASCENDING', 'ASC', orderings, flags=re.IGNORECASE)
            orderings = re.sub(r'DESCENDING', 'DESC', orderings, flags=re.IGNORECASE)
            
            # Split the orderings and clean up each one
            ordering_list: list[str] = [o.strip() for o in orderings.split(",")]
            order_parts = []
            for ordering in ordering_list:
                if ordering.strip():
                    if " ASC" not in ordering.upper() and " DESC" not in ordering.upper():
                        ordering = ordering.strip() + " ASC"  # Default direction
                    order_parts.append(ordering)
                    
            # If we have parts, join them and add to the formatted query
            if order_parts:
                indented_orderings: str = " " + ", ".join(order_parts)
                formatted = re.sub(order_pattern, f"\\1{indented_orderings}\\3", formatted)

    return formatted


def validate_resource(resource: str) -> bool:
    """
    Validate that a resource name is valid for GAQL.

    Args:
        resource: The resource name to validate.

    Returns:
        True if the resource is valid, False otherwise.
    """
    return resource in VALID_RESOURCES


def validate_field(field: str) -> bool:
    """
    Validate that a field name has a valid prefix.

    Args:
        field: The field name to validate.

    Returns:
        True if the field has a valid prefix, False otherwise.
    """
    if "." not in field:
        return False

    prefix: str = field.split(".")[0]
    return prefix in VALID_FIELD_PREFIXES


def escape_string(value: str) -> str:
    """
    Escape a string value for use in a GAQL query.

    Args:
        value: The string value to escape.

    Returns:
        An escaped string ready for use in a GAQL query.
    """
    # Use single quotes and escape any existing single quotes
    escaped: str = value.replace("'", "\\'")
    return f"'{escaped}'"


def build_condition(field: str, operator: str,
                  value: str | int | float | list[str | int | float]) -> str:
    """
    Build a condition string for use in a WHERE clause.

    Args:
        field: The field name.
        operator: The operator to use.
        value: The value or list of values.

    Returns:
        A formatted condition string.
    """
    # Handle different value types
    if isinstance(value, list):
        # Format list values
        formatted_values: list[str] = []
        for item in value:
            if isinstance(item, str):
                formatted_values.append(escape_string(item))
            else:
                formatted_values.append(str(item))

        value_str: str = f"({', '.join(formatted_values)})"
    elif isinstance(value, str):
        # Special handling for date range literals
        date_range_literals: list[str] = [
            "LAST_14_DAYS", "LAST_30_DAYS", "LAST_7_DAYS",
            "LAST_BUSINESS_WEEK", "LAST_MONTH", "LAST_WEEK_MON_SUN",
            "LAST_WEEK_SUN_SAT", "THIS_MONTH", "THIS_WEEK_MON_TODAY",
            "THIS_WEEK_SUN_TODAY", "TODAY", "YESTERDAY"
        ]

        if value.upper() in date_range_literals:
            value_str = value.upper()
        else:
            value_str = escape_string(value)
    else:
        value_str = str(value)

    return f"{field} {operator} {value_str}"


# pylint: disable=too-many-arguments,too-many-positional-arguments
def build_gaql_query(
    select_fields: list[str],
    resource: str,
    where_conditions: list[str] | None = None,
    order_by: list[dict[str, str]] | None = None,
    limit: int | None = None,
    parameters: dict[str, bool] | None = None
) -> str:
    """
    Build a GAQL query from components.

    Args:
        select_fields: List of fields to select.
        resource: Resource to query.
        where_conditions: List of WHERE conditions.
        order_by: List of dictionaries with 'field' and 'direction' keys.
        limit: Maximum number of results to return.
        parameters: Dictionary of parameter name and boolean value pairs.

    Returns:
        A formatted GAQL query.
    """
    # Validate inputs
    if not select_fields:
        raise GaqlError("At least one field must be selected")

    if not resource:
        raise GaqlError("Resource is required")

    # Build SELECT clause
    query: str = f"SELECT {', '.join(select_fields)}"

    # Add FROM clause
    query += f" FROM {resource}"

    # Add WHERE clause if conditions are provided
    if where_conditions and len(where_conditions) > 0:
        query += f" WHERE {' AND '.join(where_conditions)}"

    # Add ORDER BY clause if ordering is provided
    if order_by and len(order_by) > 0:
        orderings: list[str] = []
        for ordering in order_by:
            field: str = ordering["field"]
            direction: str = ordering.get("direction", "ASC")
            orderings.append(f"{field} {direction}")

        query += f" ORDER BY {', '.join(orderings)}"

    # Add LIMIT clause if provided
    if limit is not None:
        query += f" LIMIT {limit}"

    # Add PARAMETERS clause if provided
    if parameters and len(parameters) > 0:
        params: list[str] = []
        for name, value in parameters.items():
            params.append(f"{name}={'true' if value else 'false'}")

        query += f" PARAMETERS {', '.join(params)}"

    return query
