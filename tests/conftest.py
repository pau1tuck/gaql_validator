"""
Pytest fixtures for testing the GAQL validator.
"""
import pytest

from gaql_validator.grammar import create_gaql_parser
from gaql_validator.parser import GaqlParser
from gaql_validator.validator import GaqlValidator


@pytest.fixture
def gaql_parser():  # -> Lark:  # Would add this if we could import Lark properly
    """Returns a GAQL parser instance."""
    return create_gaql_parser()


@pytest.fixture
def gaql_parser_instance() -> GaqlParser:
    """Returns a GaqlParser instance."""
    return GaqlParser()


@pytest.fixture
def gaql_validator_instance() -> GaqlValidator:
    """Returns a GaqlValidator instance."""
    return GaqlValidator()


@pytest.fixture
def valid_basic_query() -> str:
    """Returns a valid basic GAQL query."""
    return "SELECT campaign.id FROM campaign LIMIT 10"


@pytest.fixture
def valid_complex_query() -> str:
    """Returns a valid complex GAQL query with all clause types."""
    return """
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


@pytest.fixture
def invalid_queries() -> dict[str, dict[str, str]]:
    """Returns a dictionary of invalid GAQL queries with their error types."""
    return {
        "missing_from": {
            "query": "SELECT campaign.id LIMIT 10",
            "error_type": "FROM clause is required"
        },
        "invalid_operator": {
            "query": "SELECT campaign.id FROM campaign WHERE campaign.status ^^ 'ENABLED'",
            "error_type": "invalid operator"
        },
        "clause_order": {
            "query": "FROM campaign SELECT campaign.id LIMIT 10",
            "error_type": "clause order"
        },
        "invalid_resource": {
            "query": "SELECT campaign.id FROM invalid_resource LIMIT 10",
            "error_type": "invalid resource"
        },
        "invalid_field": {
            "query": "SELECT campaign.invalid_field FROM campaign LIMIT 10",
            "error_type": "invalid field"
        },
        "field_operator_mismatch": {
            "query": "SELECT campaign.id FROM campaign WHERE campaign.id DURING LAST_7_DAYS",
            "error_type": "cannot be used with"
        }
    }
