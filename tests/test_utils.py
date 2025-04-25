"""
Tests for utility functions.
"""
import pytest

from gaql_validator.exceptions import GaqlError
from gaql_validator.utils import (
    format_gaql,
    validate_resource,
    validate_field,
    escape_string,
    build_condition,
    build_gaql_query
)


def test_format_gaql() -> None:
    """Tests the GAQL query formatting function."""
    # Test basic query formatting
    query = "SELECT campaign.id FROM campaign LIMIT 10"
    formatted = format_gaql(query)
    assert "SELECT" in formatted
    assert "FROM" in formatted
    assert "LIMIT" in formatted

    # Test complex query formatting
    complex_query = "SELECT campaign.id, campaign.name, metrics.impressions FROM campaign WHERE campaign.status = 'ENABLED' AND metrics.impressions > 100 ORDER BY metrics.impressions DESC LIMIT 50"
    formatted = format_gaql(complex_query)
    assert "SELECT" in formatted
    assert "FROM" in formatted
    assert "WHERE" in formatted
    assert "ORDER BY" in formatted
    assert "LIMIT" in formatted


def test_validate_resource() -> None:
    """Tests resource validation."""
    # Test valid resource
    assert validate_resource("campaign") is True
    assert validate_resource("ad_group") is True

    # Test invalid resource
    assert validate_resource("invalid_resource") is False
    assert validate_resource("not_a_resource") is False


def test_validate_field() -> None:
    """Tests field validation."""
    # Test valid fields
    assert validate_field("campaign.id") is True
    assert validate_field("ad_group.name") is True
    assert validate_field("metrics.impressions") is True

    # Test invalid fields
    assert validate_field("invalid.field") is False
    assert validate_field("field_without_prefix") is False


def test_escape_string() -> None:
    """Tests string escaping."""
    # Test basic string
    assert escape_string("test") == "'test'"

    # Test string with quotes
    assert escape_string("test's") == "'test\\'s'"

    # Test string with special characters
    assert escape_string("test\"quote") == "'test\"quote'"


def test_build_condition() -> None:
    """Tests condition building."""
    # Test equals condition with string
    condition = build_condition("campaign.status", "=", "ENABLED")
    assert condition == "campaign.status = 'ENABLED'"

    # Test numeric condition
    condition = build_condition("metrics.impressions", ">", 100)
    assert condition == "metrics.impressions > 100"

    # Test list condition
    condition = build_condition("campaign.status", "IN", ["ENABLED", "PAUSED"])
    assert condition == "campaign.status IN ('ENABLED', 'PAUSED')"

    # Test date range literal
    condition = build_condition("segments.date", "DURING", "LAST_7_DAYS")
    assert condition == "segments.date DURING LAST_7_DAYS"


def test_build_gaql_query() -> None:
    """Tests complete query building."""
    # Test basic query
    query = build_gaql_query(
        select_fields=["campaign.id"],
        resource="campaign",
        limit=10
    )
    assert query == "SELECT campaign.id FROM campaign LIMIT 10"

    # Test query with WHERE conditions
    query = build_gaql_query(
        select_fields=["campaign.id", "campaign.name"],
        resource="campaign",
        where_conditions=["campaign.status = 'ENABLED'"],
        limit=10
    )
    assert query == "SELECT campaign.id, campaign.name FROM campaign WHERE campaign.status = 'ENABLED' LIMIT 10"

    # Test query with ORDER BY
    query = build_gaql_query(
        select_fields=["campaign.id", "metrics.impressions"],
        resource="campaign",
        order_by=[{"field": "metrics.impressions", "direction": "DESC"}],
        limit=10
    )
    assert query == "SELECT campaign.id, metrics.impressions FROM campaign ORDER BY metrics.impressions DESC LIMIT 10"

    # Test query with PARAMETERS
    query = build_gaql_query(
        select_fields=["campaign.id"],
        resource="campaign",
        parameters={"include_drafts": True}
    )
    assert query == "SELECT campaign.id FROM campaign PARAMETERS include_drafts=true"

    # Test complete query
    query = build_gaql_query(
        select_fields=["campaign.id", "campaign.name", "metrics.impressions"],
        resource="campaign",
        where_conditions=["campaign.status = 'ENABLED'", "metrics.impressions > 100"],
        order_by=[{"field": "metrics.impressions", "direction": "DESC"}],
        limit=50,
        parameters={"include_drafts": True}
    )
    assert "SELECT campaign.id, campaign.name, metrics.impressions" in query
    assert "FROM campaign" in query
    assert "WHERE campaign.status = 'ENABLED' AND metrics.impressions > 100" in query
    assert "ORDER BY metrics.impressions DESC" in query
    assert "LIMIT 50" in query
    assert "PARAMETERS include_drafts=true" in query


def test_build_gaql_query_validation() -> None:
    """Tests error handling in query building."""
    # Test missing select fields
    with pytest.raises(GaqlError) as excinfo:
        build_gaql_query(
            select_fields=[],
            resource="campaign"
        )
    assert "At least one field" in str(excinfo.value)

    # Test missing resource
    with pytest.raises(GaqlError) as excinfo:
        build_gaql_query(
            select_fields=["campaign.id"],
            resource=""
        )
    assert "Resource is required" in str(excinfo.value)
