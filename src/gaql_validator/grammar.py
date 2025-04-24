"""
Lark grammar definitions for GAQL.
"""
from lark import Lark

# GAQL grammar reference (kept for documentation purposes)
GAQL_GRAMMAR_REFERENCE = """
GAQL Grammar Reference:
Query            -> SelectClause FromClause WhereClause? OrderByClause?
                    LimitClause? ParametersClause?
SelectClause     -> SELECT FieldName (, FieldName)*
FromClause       -> FROM ResourceName
WhereClause      -> WHERE Condition (AND Condition)*
OrderByClause    -> ORDER BY Ordering (, Ordering)*
LimitClause      -> LIMIT PositiveInteger
ParametersClause -> PARAMETERS (include_drafts | omit_unselected_resource_names) = (true | false)
                    (, (include_drafts | omit_unselected_resource_names) = (true | false) )* # Example: PARAMETERS include_drafts = true
                    # IMPORTANT: PARAMETERS cannot be used for general value substitution in WHERE clause.
                    # Dynamic filter values must be validated and built into the query string before execution.

Condition        -> FieldName Operator Value
Operator         -> = | != | > | >= | < | <= | IN | NOT IN |
                    LIKE | NOT LIKE | CONTAINS ANY | CONTAINS ALL |
                    CONTAINS NONE | IS NULL | IS NOT NULL | DURING |
                    BETWEEN | REGEXP_MATCH | NOT REGEXP_MATCH
Value            -> Literal | LiteralList | Number | NumberList | String |
                    StringList | DateRangeLiteral # Note: DateRangeLiteral used with date fields/operators like 'segments.date'
Ordering         -> FieldName (ASC | DESC)?

FieldName        -> [a-z] ([a-zA-Z0-9._])*
ResourceName     -> [a-z] ([a-zA-Z_])*

StringList       -> ( String (, String)* )
LiteralList      -> ( Literal (, Literal)* )
NumberList       -> ( Number (, Number)* )

PositiveInteger  -> [1-9] ([0-9])*
Number           -> -? [0-9]+ (. [0-9] [0-9]*)?
String           -> (' Char* ') | (" Char* ")
Literal          -> [a-zA-Z0-9_]* # Covers enums like 'ENABLED', 'PAUSED', etc.

DateRangeLiteral -> LAST_14_DAYS | LAST_30_DAYS | LAST_7_DAYS |
                    LAST_BUSINESS_WEEK | LAST_MONTH | LAST_WEEK_MON_SUN |
                    LAST_WEEK_SUN_SAT | THIS_MONTH | THIS_WEEK_MON_TODAY |
                    THIS_WEEK_SUN_TODAY | TODAY | YESTERDAY
"""

# Actual Lark grammar definition
GAQL_GRAMMAR = r"""
    ?start: query

    query: select_clause from_clause [where_clause] [order_by_clause] [limit_clause] [parameters_clause]

    select_clause: "SELECT" field_list
    from_clause: "FROM" resource_name
    where_clause: "WHERE" condition ("AND" condition)*
    order_by_clause: "ORDER" "BY" ordering ("," ordering)*
    limit_clause: "LIMIT" POSITIVE_INT
    parameters_clause: "PARAMETERS" parameter ("," parameter)*

    field_list: field_name ("," field_name)*
    field_name: FIELD_NAME
    resource_name: RESOURCE_NAME

    condition: field_name operator value
    operator: EQUALS | NOT_EQUALS | GREATER_THAN | GREATER_THAN_EQUALS | LESS_THAN | LESS_THAN_EQUALS
            | IN_OP | NOT_IN_OP
            | LIKE_OP | NOT_LIKE_OP
            | CONTAINS_ANY | CONTAINS_ALL | CONTAINS_NONE
            | IS_NULL | IS_NOT_NULL
            | "DURING"
            | "BETWEEN"
            | REGEXP_OP | NOT_REGEXP_OP
    
    value: literal | literal_list | number | number_list | string | string_list | date_range_literal

    literal: LITERAL
    number: NUMBER
    string: SINGLE_QUOTED_STRING | DOUBLE_QUOTED_STRING
    date_range_literal: DATE_RANGE_LITERAL

    literal_list: "(" literal ("," literal)* ")"
    number_list: "(" number ("," number)* ")"
    string_list: "(" string ("," string)* ")"

    ordering: field_name [direction]
    direction: "ASC" | "DESC"

    parameter: PARAMETER_NAME "=" PARAMETER_VALUE

    // Terminals
    EQUALS: "="
    NOT_EQUALS: "!="
    GREATER_THAN: ">"
    GREATER_THAN_EQUALS: ">="
    LESS_THAN: "<"
    LESS_THAN_EQUALS: "<="
    IN_OP: "IN"
    NOT_IN_OP: "NOT" "IN"
    LIKE_OP: "LIKE"
    NOT_LIKE_OP: "NOT" "LIKE"
    CONTAINS_ANY: "CONTAINS" "ANY"
    CONTAINS_ALL: "CONTAINS" "ALL"
    CONTAINS_NONE: "CONTAINS" "NONE"
    IS_NULL: "IS" "NULL"
    IS_NOT_NULL: "IS" "NOT" "NULL"
    REGEXP_OP: "REGEXP_MATCH"
    NOT_REGEXP_OP: "NOT" "REGEXP_MATCH"
    
    FIELD_NAME: /[a-z][a-zA-Z0-9._]*/
    RESOURCE_NAME: /[a-z][a-zA-Z_]*/
    LITERAL: /[a-zA-Z0-9_]+/
    DATE_RANGE_LITERAL: "LAST_14_DAYS" | "LAST_30_DAYS" | "LAST_7_DAYS" 
                       | "LAST_BUSINESS_WEEK" | "LAST_MONTH" | "LAST_WEEK_MON_SUN" 
                       | "LAST_WEEK_SUN_SAT" | "THIS_MONTH" | "THIS_WEEK_MON_TODAY" 
                       | "THIS_WEEK_SUN_TODAY" | "TODAY" | "YESTERDAY"
    PARAMETER_NAME: "include_drafts" | "omit_unselected_resource_names"
    PARAMETER_VALUE: "true" | "false"

    POSITIVE_INT: /[1-9][0-9]*/
    NUMBER: /-?[0-9]+(\.[0-9]+)?/
    SINGLE_QUOTED_STRING: /'(?:[^'\\]|\\.)*'/
    DOUBLE_QUOTED_STRING: /"(?:[^"\\]|\\.)*"/

    // Import common terminals
    %import common.WS
    %import common.NEWLINE

    // Ignore whitespace and comments
    %ignore WS
    %ignore NEWLINE
    %ignore /--[^\n]*/
"""

def create_gaql_parser() -> Lark:
    """
    Creates a Lark parser for GAQL.

    Returns:
        A Lark parser instance configured for parsing GAQL queries.
    """
    return Lark(GAQL_GRAMMAR, parser='lalr', maybe_placeholders=False, debug=False)
