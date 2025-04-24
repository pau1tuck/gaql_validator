"""
Core validation functionality for GAQL queries.
"""
import re
from typing import Dict, List, Optional, Set, Union

from gaql_validator.exceptions import GaqlFieldError, GaqlResourceError, GaqlSyntaxError, GaqlValidationError
from gaql_validator.parser import GaqlParser


# Valid Google Ads resources
VALID_RESOURCES = {
    "account_budget", "ad_group", "ad_group_ad", "ad_group_criterion", "campaign",
    "campaign_budget", "campaign_criterion", "customer", "keyword_view",
    "ad_group_audience_view", "campaign_audience_view", "feed", "feed_item",
    "geo_target_constant", "user_list", "asset", "location_view", "search_term_view"
}

# Valid field prefixes
VALID_FIELD_PREFIXES = {
    "ad_group", "campaign", "customer", "metrics", "segments",
    "ad_group_criterion", "campaign_criterion", "keyword_view", "asset"
}

# Fields that are date-related and can use DURING operator
DATE_FIELDS = {
    "segments.date", "segments.month", "segments.quarter", "segments.week", "segments.year"
}

# Fields that only accept specific operators
FIELD_OPERATOR_RESTRICTIONS = {
    "segments.date": {"DURING", "BETWEEN", "="},
    "metrics.impressions": {"=", "!=", ">", ">=", "<", "<="},
    "metrics.clicks": {"=", "!=", ">", ">=", "<", "<="},
    "metrics.cost_micros": {"=", "!=", ">", ">=", "<", "<="},
    "campaign.status": {"=", "!=", "IN", "NOT IN"}
}

# Valid parameter names
VALID_PARAMETERS = {"include_drafts", "omit_unselected_resource_names"}


class GaqlValidator:
    """
    Validator for Google Ads Query Language (GAQL) queries.
    """

    def __init__(self) -> None:
        """Initialize the GAQL validator."""
        self.parser = GaqlParser()

    def validate(self, query: str, strict: bool = False) -> Dict[str, Union[bool, List[str]]]:
        """
        Validate a GAQL query.

        Args:
            query: The GAQL query string to validate.
            strict: If True, raises exceptions for validation errors instead of returning them in the result.

        Returns:
            A dictionary containing validation results:
            {
                "valid": bool,
                "errors": List[str]  # Empty list if valid is True
            }
            
        Raises:
            GaqlSyntaxError: If the query has syntax errors and strict is True.
            GaqlValidationError: If the query has validation errors and strict is True.
            GaqlResourceError: If the query uses an invalid resource and strict is True.
            GaqlFieldError: If the query uses an invalid field and strict is True.
        """
        errors = []
        
        try:
            # Parse the query
            parsed = self.parser.parse(query)
            
            # Validate the parsed query structure
            structure_errors = self._validate_structure(parsed)
            errors.extend(structure_errors)
            
            # Validate the resource names
            resource_errors = self._validate_resources(parsed)
            errors.extend(resource_errors)
            
            # Validate the field names
            field_errors = self._validate_fields(parsed)
            errors.extend(field_errors)
            
            # Validate field-operator compatibility
            operator_errors = self._validate_field_operators(parsed)
            errors.extend(operator_errors)
            
            # Validate parameters if present
            if "parameters_clause" in parsed:
                parameter_errors = self._validate_parameters(parsed["parameters_clause"]["parameters"])
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
        valid = len(errors) == 0
        
        return {
            "valid": valid,
            "errors": errors
        }
    
    def _validate_structure(self, parsed: Dict) -> List[str]:
        """
        Validate the structure of the parsed query.
        
        Args:
            parsed: The parsed query dictionary.
            
        Returns:
            A list of error messages, empty if no errors.
        """
        errors = []
        
        # Validate required clauses
        if "select_clause" not in parsed:
            errors.append("SELECT clause is required")
        
        if "from_clause" not in parsed:
            errors.append("FROM clause is required")
        
        # Validate the order of clauses
        expected_order = ["select_clause", "from_clause", "where_clause", 
                         "order_by_clause", "limit_clause", "parameters_clause"]
        
        # Extract actual order from the parsed query
        actual_clauses = [key for key in parsed.keys()]
        
        # Check if the actual order matches the expected order
        for i, clause in enumerate(actual_clauses):
            if clause not in expected_order:
                errors.append(f"Unknown clause type: {clause}")
                continue
                
            expected_index = expected_order.index(clause)
            
            if i > 0 and expected_index < expected_order.index(actual_clauses[i-1]):
                prev_clause = actual_clauses[i-1].replace("_clause", "").upper()
                current_clause = clause.replace("_clause", "").upper()
                errors.append(f"Invalid clause order: {current_clause} cannot come after {prev_clause}")
        
        return errors
    
    def _validate_resources(self, parsed: Dict) -> List[str]:
        """
        Validate the resources used in the query.
        
        Args:
            parsed: The parsed query dictionary.
            
        Returns:
            A list of error messages, empty if no errors.
        """
        errors = []
        
        if "from_clause" in parsed:
            resource = parsed["from_clause"]["resource"]
            
            if resource not in VALID_RESOURCES:
                errors.append(f"Invalid resource: {resource}")
        
        return errors
    
    def _validate_fields(self, parsed: Dict) -> List[str]:
        """
        Validate the fields used in the query.
        
        Args:
            parsed: The parsed query dictionary.
            
        Returns:
            A list of error messages, empty if no errors.
        """
        errors = []
        
        # Extract all fields from the query
        fields = []
        
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
                
            prefix = field.split(".")[0]
            
            if prefix not in VALID_FIELD_PREFIXES:
                errors.append(f"Invalid field prefix: {prefix} in field {field}")
        
        return errors
    
    def _validate_field_operators(self, parsed: Dict) -> List[str]:
        """
        Validate the compatibility between fields and operators in WHERE conditions.
        
        Args:
            parsed: The parsed query dictionary.
            
        Returns:
            A list of error messages, empty if no errors.
        """
        errors = []
        
        if "where_clause" not in parsed:
            return errors
        
        for condition in parsed["where_clause"]["conditions"]:
            field = condition["field"]
            operator = condition["operator"]
            
            # Check if the field is date-related and the operator is DURING
            if operator == "DURING" and field not in DATE_FIELDS:
                errors.append(f"Operator DURING can only be used with date fields, not with {field}")
            
            # Check if there are specific restrictions for this field
            if field in FIELD_OPERATOR_RESTRICTIONS:
                allowed_operators = FIELD_OPERATOR_RESTRICTIONS[field]
                
                if operator not in allowed_operators:
                    allowed_list = ", ".join(allowed_operators)
                    errors.append(f"Operator {operator} cannot be used with field {field}. Allowed operators: {allowed_list}")
        
        return errors
    
    def _validate_parameters(self, parameters: Dict[str, str]) -> List[str]:
        """
        Validate the parameters used in the query.
        
        Args:
            parameters: The parameters dictionary.
            
        Returns:
            A list of error messages, empty if no errors.
        """
        errors = []
        
        for name, value in parameters.items():
            if name not in VALID_PARAMETERS:
                errors.append(f"Invalid parameter name: {name}")
            
            if value not in ("true", "false"):
                errors.append(f"Invalid parameter value: {value}. Expected 'true' or 'false'")
        
        return errors
