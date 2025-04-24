"""
Tests for the GAQL parser.
"""
import pytest

from gaql_validator.parser import GaqlParser
from gaql_validator.exceptions import GaqlSyntaxError


def test_parser_initialization():
    """Tests that the parser can be initialized."""
    parser = GaqlParser()
    assert parser is not None


def test_parse_valid_basic_query():
    """Tests parsing a minimal valid GAQL query."""
    parser = GaqlParser()
    query = "SELECT campaign.id FROM campaign LIMIT 10"
    
    result = parser.parse(query)
    assert result is not None
    assert "select_clause" in result
    assert "from_clause" in result
    assert "limit_clause" in result
    assert result["select_clause"]["fields"] == ["campaign.id"]
    assert result["from_clause"]["resource"] == "campaign"
    assert result["limit_clause"]["limit"] == 10


def test_parse_missing_from_clause():
    """Tests that a query without a FROM clause raises an exception."""
    parser = GaqlParser()
    query = "SELECT campaign.id LIMIT 10"
    
    with pytest.raises(GaqlSyntaxError) as excinfo:
        parser.parse(query)
    assert "FROM clause is required" in str(excinfo.value)


def test_parse_multiple_filters_where_clause():
    """Tests parsing a query with multiple WHERE conditions."""
    parser = GaqlParser()
    query = "SELECT ad_group.id FROM ad_group WHERE ad_group.status = 'ENABLED' AND segments.date DURING LAST_7_DAYS"
    
    result = parser.parse(query)
    assert result is not None
    assert "where_clause" in result
    assert len(result["where_clause"]["conditions"]) == 2
    
    # Check first condition
    assert result["where_clause"]["conditions"][0]["field"] == "ad_group.status"
    assert result["where_clause"]["conditions"][0]["operator"] == "="
    assert result["where_clause"]["conditions"][0]["value"] == "'ENABLED'"
    
    # Check second condition
    assert result["where_clause"]["conditions"][1]["field"] == "segments.date"
    assert result["where_clause"]["conditions"][1]["operator"] == "DURING"
    assert result["where_clause"]["conditions"][1]["value"] == "LAST_7_DAYS"


def test_parse_complex_query():
    """Tests parsing a complex query with all clause types."""
    parser = GaqlParser()
    query = """
    SELECT
      campaign.id,
      campaign.name,
      metrics.impressions
    FROM campaign
    WHERE
      campaign.status = 'ENABLED'
      AND metrics.impressions > 100
    ORDER BY metrics.impressions DESC
    LIMIT 50
    PARAMETERS include_drafts=true
    """
    
    result = parser.parse(query)
    assert result is not None
    assert "select_clause" in result
    assert "from_clause" in result
    assert "where_clause" in result
    assert "order_by_clause" in result
    assert "limit_clause" in result
    assert "parameters_clause" in result
    
    # Check SELECT fields
    assert len(result["select_clause"]["fields"]) == 3
    assert "campaign.id" in result["select_clause"]["fields"]
    assert "campaign.name" in result["select_clause"]["fields"]
    assert "metrics.impressions" in result["select_clause"]["fields"]
    
    # Check FROM
    assert result["from_clause"]["resource"] == "campaign"
    
    # Check WHERE
    assert len(result["where_clause"]["conditions"]) == 2
    
    # Check ORDER BY
    assert len(result["order_by_clause"]["orderings"]) == 1
    assert result["order_by_clause"]["orderings"][0]["field"] == "metrics.impressions"
    assert result["order_by_clause"]["orderings"][0]["direction"] == "DESC"
    
    # Check LIMIT
    assert result["limit_clause"]["limit"] == 50
    
    # Check PARAMETERS
    assert result["parameters_clause"]["parameters"]["include_drafts"] == "true"