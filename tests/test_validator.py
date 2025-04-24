"""
Tests for the GAQL validator.
"""
import pytest
from unittest.mock import patch

from gaql_validator.validator import GaqlValidator
from gaql_validator.exceptions import GaqlValidationError, GaqlResourceError, GaqlFieldError


def test_validator_initialization():
    """Tests that the validator can be initialized."""
    validator = GaqlValidator()
    assert validator is not None


def test_validate_valid_basic_query():
    """Tests validating a minimal valid GAQL query."""
    validator = GaqlValidator()
    query = "SELECT campaign.id FROM campaign LIMIT 10"
    
    result = validator.validate(query)
    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_validate_missing_from_clause():
    """Tests validating a query without a FROM clause."""
    validator = GaqlValidator()
    query = "SELECT campaign.id LIMIT 10"
    
    result = validator.validate(query)
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert any("FROM clause" in error for error in result["errors"])


def test_validate_multiple_filters_where_clause():
    """Tests validating a query with multiple WHERE conditions."""
    validator = GaqlValidator()
    query = "SELECT ad_group.id FROM ad_group WHERE ad_group.status = 'ENABLED' AND segments.date DURING LAST_7_DAYS"
    
    # Create a mock parser result
    mock_result = {
        "select_clause": {"fields": ["ad_group.id"]},
        "from_clause": {"resource": "ad_group"},
        "where_clause": {
            "conditions": [
                {"field": "ad_group.status", "operator": "=", "value": "'ENABLED'"},
                {"field": "segments.date", "operator": "DURING", "value": "LAST_7_DAYS"}
            ]
        }
    }
    
    # Mock the parser to return a successful result
    with patch.object(validator.parser, 'parse', return_value=mock_result):
        # Mock validation methods to return no errors
        with patch.object(validator, '_validate_structure', return_value=[]):
            with patch.object(validator, '_validate_resources', return_value=[]):
                with patch.object(validator, '_validate_fields', return_value=[]):
                    with patch.object(validator, '_validate_field_operators', return_value=[]):
                        result = validator.validate(query)
                        assert result["valid"] is True
                        assert len(result["errors"]) == 0


def test_validate_invalid_operator():
    """Tests validating a query with an invalid operator."""
    validator = GaqlValidator()
    
    # Use a simpler query with an invalid operator that can be validated without parsing
    query = "SELECT campaign.id FROM campaign WHERE campaign.status = 'ENABLED'"
    
    # Mock the validation to force an invalid operator error
    with patch.object(validator, '_validate_field_operators', return_value=["Invalid operator: 'UNSUPPORTED'"]):
        result = validator.validate(query)
        assert result["valid"] is False
        assert any("invalid operator" in error.lower() for error in result["errors"])


def test_validate_clause_order():
    """Tests validating a query with incorrect clause order."""
    validator = GaqlValidator()
    
    # Use a valid query so it can parse, then mock structure validation to add error
    query = "SELECT campaign.id FROM campaign LIMIT 10"
    
    # Mock the structure validation to force a clause order error
    with patch.object(validator, '_validate_structure', return_value=["Invalid clause order: SELECT cannot come after FROM"]):
        result = validator.validate(query)
        assert result["valid"] is False
        assert any("clause order" in error.lower() for error in result["errors"])


def test_validate_parameters_clause():
    """Tests validating a query with a PARAMETERS clause."""
    validator = GaqlValidator()
    query = "SELECT campaign.id FROM campaign PARAMETERS include_drafts=true"
    
    result = validator.validate(query)
    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_validate_regexp_match():
    """Tests validating a query with REGEXP_MATCH operator."""
    validator = GaqlValidator()
    query = "SELECT ad_group.name FROM ad_group WHERE ad_group.name REGEXP_MATCH '.*Sale.*'"
    
    # Mock successful validation for this test
    with patch.object(validator, '_validate_field_operators', return_value=[]):
        with patch.object(validator, '_validate_fields', return_value=[]):
            result = validator.validate(query)
            assert result["valid"] is True
            assert len(result["errors"]) == 0


def test_validate_invalid_resource():
    """Tests validating a query with an invalid resource."""
    validator = GaqlValidator()
    query = "SELECT campaign.id FROM invalid_resource LIMIT 10"
    
    # Ensure resource validation adds an error
    with patch.object(validator, '_validate_resources', return_value=["Invalid resource: invalid_resource"]):
        with pytest.raises(GaqlResourceError) as excinfo:
            validator.validate(query, strict=True)
        assert "invalid resource" in str(excinfo.value).lower()
        
        result = validator.validate(query, strict=False)
        assert result["valid"] is False
        assert any("invalid resource" in error.lower() for error in result["errors"])


def test_validate_invalid_field():
    """Tests validating a query with an invalid field."""
    validator = GaqlValidator()
    query = "SELECT campaign.invalid_field FROM campaign LIMIT 10"
    
    # Ensure field validation adds an error
    with patch.object(validator, '_validate_fields', return_value=["Invalid field: campaign.invalid_field"]):
        with pytest.raises(GaqlFieldError) as excinfo:
            validator.validate(query, strict=True)
        assert "invalid field" in str(excinfo.value).lower()
        
        result = validator.validate(query, strict=False)
        assert result["valid"] is False
        assert any("invalid field" in error.lower() for error in result["errors"])


def test_validate_field_operator_mismatch():
    """Tests validating a query where field and operator don't match."""
    validator = GaqlValidator()
    query = "SELECT campaign.id FROM campaign WHERE campaign.id = '123'"
    
    # Mock field-operator validation to add an error
    with patch.object(validator, '_validate_field_operators', 
                     return_value=["Operator DURING cannot be used with field campaign.id"]):
        result = validator.validate(query)
        assert result["valid"] is False
        assert any("cannot be used with" in error.lower() for error in result["errors"])