"""
Utility functions for working with GAQL queries.
"""
import re
from typing import Dict, List, Optional, Set, Union

from gaql_validator.exceptions import GaqlError
from gaql_validator.validator import VALID_RESOURCES, VALID_FIELD_PREFIXES


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
    query = re.sub(r'\s+', ' ', query.strip())
    
    # Replace keywords with newlines and indentation
    keywords = ["SELECT", "FROM", "WHERE", "ORDER BY", "LIMIT", "PARAMETERS"]
    formatted = query
    
    for i, keyword in enumerate(keywords):
        if i == 0:  # Don't add newline before the first keyword
            pattern = f"({keyword})"
        else:
            pattern = f"([\\s]+)({keyword})"
            replacement = f"\n{keyword}"
            formatted = re.sub(pattern, replacement, formatted)
    
    # Format field lists in SELECT clause
    if "SELECT" in formatted:
        select_pattern = r"(SELECT)([^F]+)(FROM)"
        select_match = re.search(select_pattern, formatted)
        
        if select_match:
            fields = select_match.group(2).strip()
            field_list = [f.strip() for f in fields.split(",")]
            indented_fields = ",\n" + " " * indent + " ".join(field_list)
            formatted = re.sub(select_pattern, f"\\1\\3", formatted)
    
    # Format conditions in WHERE clause
    if "WHERE" in formatted:
        where_pattern = r"(WHERE)([^O]+)(ORDER BY|LIMIT|PARAMETERS|$)"
        where_match = re.search(where_pattern, formatted)
        
        if where_match:
            conditions = where_match.group(2).strip()
            condition_list = conditions.split("AND")
            indented_conditions = "\n" + " " * indent + "AND ".join(condition_list)
            formatted = re.sub(where_pattern, f"\\1{indented_conditions}\\3", formatted)
    
    # Format ORDER BY clause
    if "ORDER BY" in formatted:
        order_pattern = r"(ORDER BY)([^L]+)(LIMIT|PARAMETERS|$)"
        order_match = re.search(order_pattern, formatted)
        
        if order_match:
            orderings = order_match.group(2).strip()
            ordering_list = [o.strip() for o in orderings.split(",")]
            indented_orderings = ",\n" + " " * indent + " ".join(ordering_list)
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
    
    prefix = field.split(".")[0]
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
    escaped = value.replace("'", "\\'")
    return f"'{escaped}'"


def build_condition(field: str, operator: str, value: Union[str, int, float, List[Union[str, int, float]]]) -> str:
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
        formatted_values = []
        for item in value:
            if isinstance(item, str):
                formatted_values.append(escape_string(item))
            else:
                formatted_values.append(str(item))
        
        value_str = f"({', '.join(formatted_values)})"
    elif isinstance(value, str):
        # Special handling for date range literals
        date_range_literals = [
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


def build_gaql_query(
    select_fields: List[str],
    resource: str,
    where_conditions: Optional[List[str]] = None,
    order_by: Optional[List[Dict[str, str]]] = None,
    limit: Optional[int] = None,
    parameters: Optional[Dict[str, bool]] = None
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
    query = f"SELECT {', '.join(select_fields)}"
    
    # Add FROM clause
    query += f" FROM {resource}"
    
    # Add WHERE clause if conditions are provided
    if where_conditions and len(where_conditions) > 0:
        query += f" WHERE {' AND '.join(where_conditions)}"
    
    # Add ORDER BY clause if ordering is provided
    if order_by and len(order_by) > 0:
        orderings = []
        for ordering in order_by:
            field = ordering["field"]
            direction = ordering.get("direction", "ASC")
            orderings.append(f"{field} {direction}")
        
        query += f" ORDER BY {', '.join(orderings)}"
    
    # Add LIMIT clause if provided
    if limit is not None:
        query += f" LIMIT {limit}"
    
    # Add PARAMETERS clause if provided
    if parameters and len(parameters) > 0:
        params = []
        for name, value in parameters.items():
            params.append(f"{name}={'true' if value else 'false'}")
        
        query += f" PARAMETERS {', '.join(params)}"
    
    return query