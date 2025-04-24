"""
GAQL parsing implementation.
"""
import re
from typing import Any, TypeVar, cast

from lark import ParseError, Token, Transformer, Tree, UnexpectedToken

from gaql_validator.exceptions import GaqlSyntaxError
from gaql_validator.grammar import create_gaql_parser

# Type variable for tree nodes
T = TypeVar('T')
R = TypeVar('R')

# pylint: disable=too-many-public-methods
class GaqlToDict(Transformer[Tree, dict[str, Any]]):
    """
    Transforms a Lark parse tree into a dictionary representation.
    """

    def query(self, items: list[Tree[T]]) -> dict[str, Any]:
        """Transforms a query Tree into a dictionary."""
        result: dict[str, Any] = {}
        for item in items:
            if isinstance(item, dict):
                result.update(item)
        return result

    def select_clause(self, items: list[Tree[T]]) -> dict[str, Any]:
        """Transforms a select_clause Tree into a dictionary."""
        return {"select_clause": {"fields": items[0]}}

    def from_clause(self, items: list[Tree[T]]) -> dict[str, Any]:
        """Transforms a from_clause Tree into a dictionary."""
        return {"from_clause": {"resource": str(items[0])}}

    def where_clause(self, items: list[Tree[T]]) -> dict[str, Any]:
        """Transforms a where_clause Tree into a dictionary."""
        conditions: list[dict[str, Any]] = []
        for item in items:
            if isinstance(item, dict) and "condition" in item:
                conditions.append(item["condition"])
        return {"where_clause": {"conditions": conditions}}

    def order_by_clause(self, items: list[Tree[T]]) -> dict[str, Any]:
        """Transforms an order_by_clause Tree into a dictionary."""
        orderings: list[dict[str, Any]] = []
        for item in items:
            if isinstance(item, dict) and "ordering" in item:
                orderings.append(item["ordering"])
        return {"order_by_clause": {"orderings": orderings}}

    def limit_clause(self, items: list[Tree[T]]) -> dict[str, Any]:
        """Transforms a limit_clause Tree into a dictionary."""
        return {"limit_clause": {"limit": int(str(items[0]))}}

    def parameters_clause(self, items: list[Tree[T]]) -> dict[str, Any]:
        """Transforms a parameters_clause Tree into a dictionary."""
        parameters: dict[str, str] = {}
        for item in items:
            if isinstance(item, dict) and "parameter" in item:
                param_tuple = item["parameter"]
                if isinstance(param_tuple, tuple) and len(param_tuple) == 2:
                    name, value = param_tuple
                    parameters[str(name)] = str(value)
        return {"parameters_clause": {"parameters": parameters}}

    def field_list(self, items: list[str]) -> list[str]:
        """Transforms a field_list Tree into a list of strings."""
        return items

    def field_name(self, items: list[str]) -> str:
        """Transforms a field_name Tree into a string."""
        return str(items[0])

    def resource_name(self, items: list[str]) -> str:
        """Transforms a resource_name Tree into a string."""
        return str(items[0])

    def condition(self, items: list[Any]) -> dict[str, Any]:
        """Transforms a condition Tree into a dictionary."""
        field: str = str(items[0])
        op: str = str(items[1])
        value: Any = items[2]

        return {"condition": {
            "field": field,
            "operator": op,
            "value": value
        }}

    def operator(self, items: list[Token]) -> str:
        """Transforms an operator Tree into a string."""
        # Map the token names to their actual string representation
        op_map: dict[str, str] = {
            "EQUALS": "=",
            "NOT_EQUALS": "!=",
            "GREATER_THAN": ">",
            "GREATER_THAN_EQUALS": ">=",
            "LESS_THAN": "<",
            "LESS_THAN_EQUALS": "<=",
            "IN_OP": "IN",
            "NOT_IN_OP": "NOT IN",
            "LIKE_OP": "LIKE",
            "NOT_LIKE_OP": "NOT LIKE",
            "CONTAINS_ANY": "CONTAINS ANY",
            "CONTAINS_ALL": "CONTAINS ALL",
            "CONTAINS_NONE": "CONTAINS NONE",
            "IS_NULL": "IS NULL",
            "IS_NOT_NULL": "IS NOT NULL",
            "REGEXP_OP": "REGEXP_MATCH",
            "NOT_REGEXP_OP": "NOT REGEXP_MATCH",
            "DURING": "DURING",
            "BETWEEN": "BETWEEN"
        }

        if not items:
            return ""

        token_type: str = items[0].type
        if token_type in op_map:
            return op_map[token_type]
        return str(items[0])

    def value(self, items: list[Any]) -> Any:
        """Transforms a value Tree into an appropriate Python type."""
        return items[0]

    def literal(self, items: list[str]) -> str:
        """Transforms a literal Tree into a string."""
        return str(items[0])

    def number(self, items: list[str]) -> float:
        """Transforms a number Tree into a float."""
        return float(items[0])

    def string(self, items: list[str]) -> str:
        """Transforms a string Tree into a string."""
        return str(items[0])

    def date_range_literal(self, items: list[str]) -> str:
        """Transforms a date_range_literal Tree into a string."""
        return str(items[0])

    def literal_list(self, items: list[str]) -> list[str]:
        """Transforms a literal_list Tree into a list of strings."""
        return items

    def number_list(self, items: list[float]) -> list[float]:
        """Transforms a number_list Tree into a list of floats."""
        return items

    def string_list(self, items: list[str]) -> list[str]:
        """Transforms a string_list Tree into a list of strings."""
        return items

    def ordering(self, items: list[Any]) -> dict[str, Any]:
        """Transforms an ordering Tree into a dictionary."""
        field: str = str(items[0])
        direction: str = "ASC"  # Default direction
        if len(items) > 1:
            direction = str(items[1])

        return {"ordering": {
            "field": field,
            "direction": direction
        }}

    def direction(self, items: list[str]) -> str:
        """Transforms a direction Tree into a string."""
        return str(items[0])

    def parameter(self, items: list[str]) -> dict[str, tuple[str, str]]:
        """Transforms a parameter Tree into a dictionary."""
        name: str = str(items[0])
        value: str = str(items[1])
        return {"parameter": (name, value)}


# pylint: disable=too-few-public-methods
class GaqlParser:
    """
    Parser for Google Ads Query Language (GAQL) queries.
    """

    def __init__(self) -> None:
        """Initialize the GAQL parser."""
        self.parser: Any = create_gaql_parser()
        self.transformer: GaqlToDict = GaqlToDict()

    def parse(self, query: str) -> dict[str, Any]:
        """
        Parse a GAQL query into an AST.

        Args:
            query: The GAQL query string to parse.

        Returns:
            An AST representation of the query.

        Raises:
            GaqlSyntaxError: If the query has syntax errors.
        """
        # Clean up and normalize the query
        query_normalized: str = self._normalize_query(query)

        try:
            # Parse the query with Lark
            tree: Tree[Any] = self.parser.parse(query_normalized)

            # Transform the parse tree to a dictionary
            result: dict[str, Any] = cast(dict[str, Any], self.transformer.transform(tree))

            # Validate required components
            self._validate_parsed_query(result)

            return result
        except UnexpectedToken as e:
            position: int = cast(int, e.pos_in_stream)
            token: Token = e.token
            expected: list[str] = cast(list[str], e.expected or [])
            message: str = (
                f"Syntax error at position {position}. "
                f"Unexpected token: {token}. Expected: {expected}"
            )

            if "FROM" not in query_normalized and "SELECT" in query_normalized:
                message = "FROM clause is required"

            raise GaqlSyntaxError(message, position) from e
        except ParseError as e:
            raise GaqlSyntaxError(str(e)) from e
        except Exception as e:
            raise GaqlSyntaxError(f"Error parsing GAQL query: {str(e)}") from e

    def _normalize_query(self, query: str) -> str:
        """
        Normalize a GAQL query by removing extra whitespace and newlines.

        Args:
            query: The query to normalize.

        Returns:
            The normalized query.
        """
        # Remove comments and normalize whitespace
        query_without_comments: str = re.sub(r'--[^\n]*', '', query)
        query_normalized: str = re.sub(r'\s+', ' ', query_without_comments)
        return query_normalized.strip()

    def _validate_parsed_query(self, result: dict[str, Any]) -> None:
        """
        Validate that the parsed query has all required components.

        Args:
            result: The parsed query result.

        Raises:
            GaqlSyntaxError: If the query is missing required components.
        """
        if "select_clause" not in result:
            raise GaqlSyntaxError("SELECT clause is required")

        if "from_clause" not in result:
            raise GaqlSyntaxError("FROM clause is required")
