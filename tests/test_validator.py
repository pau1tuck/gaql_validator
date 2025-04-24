"""
Tests for the GAQL validator.
"""
import pytest

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
    
    result = validator.validate(query)
    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_validate_invalid_operator():
    """Tests validating a query with an invalid operator."""
    validator = GaqlValidator()
    query = "SELECT campaign.id FROM campaign WHERE campaign.status ^^ 'ENABLED'"
    
    result = validator.validate(query)
    assert result["valid"] is False
    assert any("invalid operator" in error.lower() for error in result["errors"])


def test_validate_clause_order():
    """Tests validating a query with incorrect clause order."""
    validator = GaqlValidator()
    query = "FROM campaign SELECT campaign.id LIMIT 10"
    
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
    
    result = validator.validate(query)
    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_validate_invalid_resource():
    """Tests validating a query with an invalid resource."""
    validator = GaqlValidator()
    query = "SELECT campaign.id FROM invalid_resource LIMIT 10"
    
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
    
    with pytest.raises(GaqlFieldError) as excinfo:
        validator.validate(query, strict=True)
    assert "invalid field" in str(excinfo.value).lower()
    
    result = validator.validate(query, strict=False)
    assert result["valid"] is False
    assert any("invalid field" in error.lower() for error in result["errors"])


def test_validate_field_operator_mismatch():
    """Tests validating a query where field and operator don't match."""
    validator = GaqlValidator()
    query = "SELECT campaign.id FROM campaign WHERE campaign.id DURING LAST_7_DAYS"
    
    result = validator.validate(query)
    assert result["valid"] is False
    assert any("cannot be used with" in error.lower() for error in result["errors"])