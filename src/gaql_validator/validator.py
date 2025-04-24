"""
Core validation functionality for GAQL queries.
"""
from typing import Any

from gaql_validator.exceptions import GaqlFieldError, GaqlResourceError, GaqlSyntaxError, GaqlValidationError
from gaql_validator.parser import GaqlParser


# Valid Google Ads resources
VALID_RESOURCES: set[str] = {
    "account_budget", "ad_group", "ad_group_ad", "ad_group_criterion", "campaign",
    "campaign_budget", "campaign_criterion", "customer", "keyword_view",
    "ad_group_audience_view", "campaign_audience_view", "feed", "feed_item",
    "geo_target_constant", "user_list", "asset", "location_view", "search_term_view"
}

# Valid field prefixes
VALID_FIELD_PREFIXES: set[str] = {
    "ad_group", "campaign", "customer", "metrics", "segments",
    "ad_group_criterion", "campaign_criterion", "keyword_view", "asset"
}

# Fields that are date-related and can use DURING operator
DATE_FIELDS: set[str] = {
    "segments.date", "segments.month", "segments.quarter", "segments.week", "segments.year"
}

# Fields that only accept specific operators
FIELD_OPERATOR_RESTRICTIONS: dict[str, set[str]] = {
    "segments.date": {"DURING", "BETWEEN", "="},
    "metrics.impressions": {"=", "!=", ">", ">=", "<", "<="},
    "metrics.clicks": {"=", "!=", ">", ">=", "<", "<="},
    "metrics.cost_micros": {"=", "!=", ">", ">=", "<", "<="},
    "campaign.status": {"=", "!=", "IN", "NOT IN"}
}

# Valid parameter names
VALID_PARAMETERS: set[str] = {"include_drafts", "omit_unselected_resource_names"}


class GaqlValidator:
    """
    Validator for Google Ads Query Language (GAQL) queries.
    """

    def __init__(self) -> None:
        """Initialize the GAQL validator."""
        self.parser: GaqlParser = GaqlParser()

    def validate(self, query: str, strict: bool = False) -> dict[str, bool | list[str]]:
        """
        Validate a GAQL query.

        Args:
            query: The GAQL query string to validate.
            strict: If True, raises exceptions for validation errors instead of returning them in the result.

        Returns:
            A dictionary containing validation results:
            {
                "valid": bool,
                "errors": list[str]  # Empty list if valid is True
            }
            
        Raises:
            GaqlSyntaxError: If the query has syntax errors and strict is True.
            GaqlValidationError: If the query has validation errors and strict is True.
            GaqlResourceError: If the query uses an invalid resource and strict is True.
            GaqlFieldError: If the query uses an invalid field and strict is True.
        """
        errors: list[str] = []
        
        try:
            # Parse the query
            parsed: dict[str, Any] = self.parser.parse(query)
            
            # Validate the parsed query structure
            structure_errors: list[str] = self._validate_structure(parsed)
            errors.extend(structure_errors)
            
            # Validate the resource names
            resource_errors: list[str] = self._validate_resources(parsed)
            errors.extend(resource_errors)
            
            # Validate the field names
            field_errors: list[str] = self._validate_fields(parsed)
            errors.extend(field_errors)
            
            # Validate field-operator compatibility
            operator_errors: list[str] = self._validate_field_operators(parsed)
            errors.extend(operator_errors)
            
            # Validate parameters if present
            if "parameters_clause" in parsed:
                parameter_errors: list[str] = self._validate_parameters(
                    parsed["parameters_clause"]["parameters"]
                )
                errors.extend(parameter_errors)
            
        except GaqlSyntaxError as e:
            if strict:
                raise
            errors.append(str(e))
        except Exception as e:
            if strict:
                if "invalid resource" in str(e).lower():
                    raise GaqlResourceError(str(e))
                elif "invalid field" in str(e).lower():
                    raise GaqlFieldError(str(e))
                else:
                    raise GaqlValidationError(str(e))
            errors.append(str(e))
        
        # Check if there are any errors
        valid: bool = len(errors) == 0
        
        # Handle strict mode for validation errors
        if not valid and strict:
            for error in errors:
                if "invalid resource" in error.lower():
                    raise GaqlResourceError(error)
                elif "invalid field" in error.lower():
                    raise GaqlFieldError(error)
                elif "clause order" in error.lower() or "operator" in error.lower():
                    raise GaqlSyntaxError(error)
            
            # If we get here, it's a general validation error
            raise GaqlValidationError(errors[0] if errors else "Unknown validation error")
        
        return {
            "valid": valid,
            "errors": errors
        }
    
    def _validate_structure(self, parsed: dict[str, Any]) -> list[str]:
        """
        Validate the structure of the parsed query.
        
        Args:
            parsed: The parsed query dictionary.
            
        Returns:
            A list of error messages, empty if no errors.
        """
        errors: list[str] = []
        
        # Validate required clauses
        if "select_clause" not in parsed:
            errors.append("SELECT clause is required")
        
        if "from_clause" not in parsed:
            errors.append("FROM clause is required")
        
        # Validate the order of clauses
        expected_order: list[str] = [
            "select_clause", "from_clause", "where_clause", 
            "order_by_clause", "limit_clause", "parameters_clause"
        ]
        
        # Extract actual order from the parsed query
        actual_clauses: list[str] = [key for key in parsed.keys()]
        
        # Check if the actual order matches the expected order
        for i, clause in enumerate(actual_clauses):
            if clause not in expected_order:
                errors.append(f"Unknown clause type: {clause}")
                continue
                
            expected_index: int = expected_order.index(clause)
            
            if i > 0 and expected_index < expected_order.index(actual_clauses[i-1]):
                prev_clause: str = actual_clauses[i-1].replace("_clause", "").upper()
                current_clause: str = clause.replace("_clause", "").upper()
                errors.append(f"Invalid clause order: {current_clause} cannot come after {prev_clause}")
        
        return errors
    
    def _validate_resources(self, parsed: dict[str, Any]) -> list[str]:
        """
        Validate the resources used in the query.
        
        Args:
            parsed: The parsed query dictionary.
            
        Returns:
            A list of error messages, empty if no errors.
        """
        errors: list[str] = []
        
        if "from_clause" in parsed:
            resource: str = parsed["from_clause"]["resource"]
            
            if resource not in VALID_RESOURCES:
                errors.append(f"Invalid resource: {resource}")
        
        return errors
    
    def _validate_fields(self, parsed: dict[str, Any]) -> list[str]:
        """
        Validate the fields used in the query.
        
        Args:
            parsed: The parsed query dictionary.
            
        Returns:
            A list of error messages, empty if no errors.
        """
        errors: list[str] = []
        
        # Extract all fields from the query
        fields: list[str] = []
        
        if "select_clause" in parsed:
            fields.extend(parsed["select_clause"]["fields"])
        
        if "where_clause" in parsed:
            for condition in parsed["where_clause"]["conditions"]:
                fields.append(condition["field"])
        
        if "order_by_clause" in parsed:
            for ordering in parsed["order_by_clause"]["orderings"]:
                fields.append(ordering["field"])
        
        # Validate each field
        for field in fields:
            if "." not in field:
                errors.append(f"Invalid field format: {field}. Expected format: 'prefix.field_name'")
                continue
                
            prefix: str = field.split(".")[0]
            
            if prefix not in VALID_FIELD_PREFIXES:
                errors.append(f"Invalid field prefix: {prefix} in field {field}")
        
        return errors
    
    def _validate_field_operators(self, parsed: dict[str, Any]) -> list[str]:
        """
        Validate the compatibility between fields and operators in WHERE conditions.
        
        Args:
            parsed: The parsed query dictionary.
            
        Returns:
            A list of error messages, empty if no errors.
        """
        errors: list[str] = []
        
        if "where_clause" not in parsed:
            return errors
        
        for condition in parsed["where_clause"]["conditions"]:
            field: str = condition["field"]
            operator: str = condition["operator"].strip()
            
            # Validate custom operators like "^^" that might be malformed
            valid_operators: tuple[str, ...] = (
                "=", "!=", ">", ">=", "<", "<=", "IN", "NOT IN", "LIKE", "NOT LIKE",
                "CONTAINS ANY", "CONTAINS ALL", "CONTAINS NONE", "IS NULL", "IS NOT NULL",
                "DURING", "BETWEEN", "REGEXP_MATCH", "NOT REGEXP_MATCH"
            )
            
            if operator not in valid_operators:
                errors.append(f"Invalid operator: '{operator}'")
            
            # Check if the field is date-related and the operator is DURING
            if operator == "DURING" and field not in DATE_FIELDS:
                errors.append(f"Operator DURING can only be used with date fields, not with {field}")
            
            # Check if there are specific restrictions for this field
            if field in FIELD_OPERATOR_RESTRICTIONS:
                allowed_operators: set[str] = FIELD_OPERATOR_RESTRICTIONS[field]
                
                if operator not in allowed_operators:
                    allowed_list: str = ", ".join(allowed_operators)
                    errors.append(
                        f"Operator {operator} cannot be used with field {field}. Allowed operators: {allowed_list}"
                    )
        
        return errors
    
    def _validate_parameters(self, parameters: dict[str, str]) -> list[str]:
        """
        Validate the parameters used in the query.
        
        Args:
            parameters: The parameters dictionary.
            
        Returns:
            A list of error messages, empty if no errors.
        """
        errors: list[str] = []
        
        for name, value in parameters.items():
            if name not in VALID_PARAMETERS:
                errors.append(f"Invalid parameter name: {name}")
            
            if value not in ("true", "false"):
                errors.append(f"Invalid parameter value: {value}. Expected 'true' or 'false'")
        
        return errors
