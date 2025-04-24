"""
GAQL parsing implementation.
"""
import re
from typing import Any, Dict, List, Optional

from lark import Lark, ParseError, Transformer, UnexpectedToken, Tree

from gaql_validator.exceptions import GaqlSyntaxError
from gaql_validator.grammar import create_gaql_parser


class GaqlToDict(Transformer):
    """
    Transforms a Lark parse tree into a dictionary representation.
    """
    
    def query(self, items: List[Tree]) -> Dict[str, Any]:
        """Transforms a query Tree into a dictionary."""
        result = {}
        for item in items:
            if isinstance(item, Dict):
                result.update(item)
        return result
    
    def select_clause(self, items: List[Tree]) -> Dict[str, Any]:
        """Transforms a select_clause Tree into a dictionary."""
        return {"select_clause": {"fields": items[0]}}
    
    def from_clause(self, items: List[Tree]) -> Dict[str, Any]:
        """Transforms a from_clause Tree into a dictionary."""
        return {"from_clause": {"resource": str(items[0])}}
    
    def where_clause(self, items: List[Tree]) -> Dict[str, Any]:
        """Transforms a where_clause Tree into a dictionary."""
        conditions = []
        for item in items:
            if isinstance(item, Dict) and "condition" in item:
                conditions.append(item["condition"])
        return {"where_clause": {"conditions": conditions}}
    
    def order_by_clause(self, items: List[Tree]) -> Dict[str, Any]:
        """Transforms an order_by_clause Tree into a dictionary."""
        orderings = []
        for item in items:
            if isinstance(item, Dict) and "ordering" in item:
                orderings.append(item["ordering"])
        return {"order_by_clause": {"orderings": orderings}}
    
    def limit_clause(self, items: List[Tree]) -> Dict[str, Any]:
        """Transforms a limit_clause Tree into a dictionary."""
        return {"limit_clause": {"limit": int(items[0])}}
    
    def parameters_clause(self, items: List[Tree]) -> Dict[str, Any]:
        """Transforms a parameters_clause Tree into a dictionary."""
        parameters = {}
        for item in items:
            if isinstance(item, Dict) and "parameter" in item:
                name, value = item["parameter"]
                parameters[name] = value
        return {"parameters_clause": {"parameters": parameters}}
    
    def field_list(self, items: List[str]) -> List[str]:
        """Transforms a field_list Tree into a list of strings."""
        return items
    
    def field_name(self, items: List[str]) -> str:
        """Transforms a field_name Tree into a string."""
        return str(items[0])
    
    def resource_name(self, items: List[str]) -> str:
        """Transforms a resource_name Tree into a string."""
        return str(items[0])
    
    def condition(self, items: List[Any]) -> Dict[str, Any]:
        """Transforms a condition Tree into a dictionary."""
        field = str(items[0])
        op = items[1]
        value = items[2]
        
        return {"condition": {
            "field": field,
            "operator": op,
            "value": value
        }}
    
    def operator(self, items: List[str]) -> str:
        """Transforms an operator Tree into a string."""
        return " ".join(str(item) for item in items)
    
    def value(self, items: List[Any]) -> Any:
        """Transforms a value Tree into an appropriate Python type."""
        return items[0]
    
    def literal(self, items: List[str]) -> str:
        """Transforms a literal Tree into a string."""
        return str(items[0])
    
    def number(self, items: List[str]) -> float:
        """Transforms a number Tree into a float."""
        return float(items[0])
    
    def string(self, items: List[str]) -> str:
        """Transforms a string Tree into a string."""
        return str(items[0])
    
    def date_range_literal(self, items: List[str]) -> str:
        """Transforms a date_range_literal Tree into a string."""
        return str(items[0])
    
    def literal_list(self, items: List[str]) -> List[str]:
        """Transforms a literal_list Tree into a list of strings."""
        return items
    
    def number_list(self, items: List[float]) -> List[float]:
        """Transforms a number_list Tree into a list of floats."""
        return items
    
    def string_list(self, items: List[str]) -> List[str]:
        """Transforms a string_list Tree into a list of strings."""
        return items
    
    def ordering(self, items: List[Any]) -> Dict[str, Any]:
        """Transforms an ordering Tree into a dictionary."""
        field = str(items[0])
        direction = "ASC"  # Default direction
        if len(items) > 1:
            direction = items[1]
        
        return {"ordering": {
            "field": field,
            "direction": direction
        }}
    
    def direction(self, items: List[str]) -> str:
        """Transforms a direction Tree into a string."""
        return str(items[0])
    
    def parameter(self, items: List[str]) -> Dict[str, tuple]:
        """Transforms a parameter Tree into a dictionary."""
        name = str(items[0])
        value = str(items[1])
        return {"parameter": (name, value)}


class GaqlParser:
    """
    Parser for Google Ads Query Language (GAQL) queries.
    """

    def __init__(self) -> None:
        """Initialize the GAQL parser."""
        self.parser = create_gaql_parser()
        self.transformer = GaqlToDict()

    def parse(self, query: str) -> Dict[str, Any]:
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
        query = self._normalize_query(query)
        
        try:
            # Parse the query with Lark
            tree = self.parser.parse(query)
            
            # Transform the parse tree to a dictionary
            result = self.transformer.transform(tree)
            
            # Validate required components
            self._validate_parsed_query(result)
            
            return result
        except UnexpectedToken as e:
            position = e.pos_in_stream
            token = e.token
            expected = e.expected
            message = f"Syntax error at position {position}. Unexpected token: {token}. Expected: {expected}"
            
            if "FROM" not in query and "SELECT" in query:
                message = "FROM clause is required"
            
            raise GaqlSyntaxError(message, position)
        except ParseError as e:
            raise GaqlSyntaxError(str(e))
        except Exception as e:
            raise GaqlSyntaxError(f"Error parsing GAQL query: {str(e)}")

    def _normalize_query(self, query: str) -> str:
        """
        Normalize a GAQL query by removing extra whitespace and newlines.
        
        Args:
            query: The query to normalize.
            
        Returns:
            The normalized query.
        """
        # Remove comments and normalize whitespace
        query = re.sub(r'--[^\n]*', '', query)
        query = re.sub(r'\s+', ' ', query)
        return query.strip()
    
    def _validate_parsed_query(self, result: Dict[str, Any]) -> None:
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
