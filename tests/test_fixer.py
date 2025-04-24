"""
Tests for the GAQL fixer.
"""
import pytest
from unittest.mock import patch, MagicMock

from gaql_validator.fixer import GaqlFixer
from gaql_validator.exceptions import GaqlSyntaxError


def test_fixer_initialization():
    """Tests that the fixer can be initialized."""
    fixer = GaqlFixer()
    assert fixer is not None
    assert fixer.validator is not None
    assert fixer.parser is not None


def test_already_valid_query():
    """Tests that valid queries aren't modified."""
    fixer = GaqlFixer()
    query = "SELECT campaign.id FROM campaign LIMIT 10"
    
    # Mock validator to return valid result
    mock_result = {"valid": True, "errors": []}
    with patch.object(fixer.validator, 'validate', return_value=mock_result):
        fixed_query, changes = fixer.fix_query(query)
        
        assert fixed_query == query
        assert len(changes) == 1
        assert "already valid" in changes[0].lower()


def test_fix_invalid_resource():
    """Tests fixing an invalid resource name."""
    fixer = GaqlFixer()
    query = "SELECT campaign.id FROM campaing LIMIT 10"  # Typo in resource
    
    # Mock validator to return invalid result first, then valid
    mock_invalid = {"valid": False, "errors": ["Invalid resource: campaing"]}
    mock_valid = {"valid": True, "errors": []}
    
    # Mock parser to return a parse result with the invalid resource
    mock_parsed = {
        "select_clause": {"fields": ["campaign.id"]},
        "from_clause": {"resource": "campaing"},
        "limit_clause": {"limit": 10}
    }
    
    with patch.object(fixer.validator, 'validate', side_effect=[mock_invalid, mock_valid]):
        with patch.object(fixer.parser, 'parse', return_value=mock_parsed):
            fixed_query, changes = fixer.fix_query(query)
            
            assert "FROM campaign" in fixed_query
            assert any("Fixed invalid resource" in change for change in changes)


def test_fix_missing_from():
    """Tests fixing a query with missing FROM clause."""
    fixer = GaqlFixer()
    query = "SELECT campaign.id LIMIT 10"  # Missing FROM
    
    # Mock validator responses
    mock_invalid = {"valid": False, "errors": ["FROM clause is required"]}
    mock_valid = {"valid": True, "errors": []}
    
    # Mock parser to raise syntax error (can't parse without FROM)
    with patch.object(fixer.validator, 'validate', side_effect=[mock_invalid, mock_valid]):
        with patch.object(fixer.parser, 'parse', side_effect=GaqlSyntaxError("FROM clause is required")):
            fixed_query, changes = fixer.fix_query(query)
            
            assert "FROM campaign" in fixed_query
            assert any("FROM" in change for change in changes)


def test_fix_invalid_field_operator():
    """Tests fixing incompatible field-operator combinations."""
    fixer = GaqlFixer()
    query = "SELECT campaign.id FROM campaign WHERE segments.date = '2023-01-01'"  # Should use DURING
    
    # Mock validator responses
    mock_invalid = {"valid": False, "errors": ["Operator = cannot be used with field segments.date"]}
    mock_valid = {"valid": True, "errors": []}
    
    # Mock parser to return valid parse structure
    mock_parsed = {
        "select_clause": {"fields": ["campaign.id"]},
        "from_clause": {"resource": "campaign"},
        "where_clause": {
            "conditions": [{"field": "segments.date", "operator": "=", "value": "'2023-01-01'"}]
        }
    }
    
    with patch.object(fixer.validator, 'validate', side_effect=[mock_invalid, mock_valid]):
        with patch.object(fixer.parser, 'parse', return_value=mock_parsed):
            fixed_query, changes = fixer.fix_query(query)
            
            assert "segments.date DURING" in fixed_query
            assert any("Fixed incompatible operator" in change for change in changes)


def test_fix_missing_quotes():
    """Tests fixing missing quotes around string values."""
    fixer = GaqlFixer()
    query = "SELECT campaign.id FROM campaign WHERE campaign.name = test"  # Missing quotes
    
    # Mock validator responses
    mock_invalid = {"valid": False, "errors": ["Syntax error"]}
    mock_valid = {"valid": True, "errors": []}
    
    with patch.object(fixer.validator, 'validate', side_effect=[mock_invalid, mock_valid]):
        with patch.object(fixer.parser, 'parse', side_effect=GaqlSyntaxError("Syntax error")):
            fixed_query, changes = fixer.fix_query(query)
            
            assert "campaign.name = 'test'" in fixed_query
            assert any("quotes" in change.lower() for change in changes)


def test_string_similarity():
    """Tests the string similarity algorithm used for suggestions."""
    fixer = GaqlFixer()
    
    # Test with identical strings
    assert fixer._string_similarity("campaign", "campaign") == 1.0
    
    # Test with similar strings
    assert fixer._string_similarity("campaing", "campaign") > 0.8
    
    # Test with different strings
    assert fixer._string_similarity("ad_group", "customer") < 0.5
    
    # Test edge cases
    assert fixer._string_similarity("", "") == 1.0
    assert fixer._string_similarity("", "test") == 0.0
    assert fixer._string_similarity("test", "") == 0.0


def test_get_closest_match():
    """Tests finding the closest match for invalid values."""
    fixer = GaqlFixer()
    
    # Test exact match but different case
    valid_set = {"campaign", "ad_group", "customer"}
    assert fixer._get_closest_match("CAMPAIGN", valid_set) == ["campaign"]
    
    # Test similar match
    assert fixer._get_closest_match("campaing", valid_set) == ["campaign"]
    
    # Test no good match
    assert fixer._get_closest_match("xyz", valid_set) == []


def test_partially_fixable_query():
    """Tests handling a query that's only partially fixable."""
    fixer = GaqlFixer()
    query = "SELECT invalid.field FROM campaign"  # Invalid field can't be fixed automatically
    
    # Mock validator responses - still invalid after fixing
    mock_invalid1 = {"valid": False, "errors": ["Invalid field: invalid.field"]}
    mock_invalid2 = {"valid": False, "errors": ["Invalid field: invalid.field"]}
    
    # Mock parser to return valid structure but with invalid field
    mock_parsed = {
        "select_clause": {"fields": ["invalid.field"]},
        "from_clause": {"resource": "campaign"}
    }
    
    with patch.object(fixer.validator, 'validate', side_effect=[mock_invalid1, mock_invalid2]):
        with patch.object(fixer.parser, 'parse', return_value=mock_parsed):
            fixed_query, changes = fixer.fix_query(query)
            
            assert "Not all issues could be fixed" in changes
            assert any("Invalid field" in change for change in changes)


def test_fix_parameter_name():
    """Tests fixing invalid parameter names."""
    fixer = GaqlFixer()
    query = "SELECT campaign.id FROM campaign PARAMETERS include_draft=true"  # Should be include_drafts
    
    # Mock validator responses
    mock_invalid = {"valid": False, "errors": ["Invalid parameter name: include_draft"]}
    mock_valid = {"valid": True, "errors": []}
    
    # Mock parser to return structure with invalid parameter
    mock_parsed = {
        "select_clause": {"fields": ["campaign.id"]},
        "from_clause": {"resource": "campaign"},
        "parameters_clause": {"parameters": {"include_draft": "true"}}
    }
    
    with patch.object(fixer.validator, 'validate', side_effect=[mock_invalid, mock_valid]):
        with patch.object(fixer.parser, 'parse', return_value=mock_parsed):
            fixed_query, changes = fixer.fix_query(query)
            
            assert "include_drafts=true" in fixed_query
            assert any("parameter name" in change.lower() for change in changes)