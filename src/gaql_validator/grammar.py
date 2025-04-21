"""
Lark grammar definitions for GAQL.
"""

# GAQL grammar definition
GAQL_GRAMMAR = r"""
    // This is a placeholder for the actual GAQL grammar
    // It will be implemented using Lark grammar syntax
    
    start: select_clause from_clause [where_clause] [order_by_clause] [limit_clause] [parameters_clause]
    
    select_clause: "SELECT" field_list
    from_clause: "FROM" resource
    where_clause: "WHERE" condition
    order_by_clause: "ORDER" "BY" order_list
    limit_clause: "LIMIT" INTEGER
    parameters_clause: "PARAMETERS" parameter_list
    
    field_list: field ("," field)*
    field: CNAME ("." CNAME)*
    
    resource: CNAME
    
    condition: _condition
    _condition: simple_condition
             | _condition "AND" _condition -> and_condition
             | _condition "OR" _condition -> or_condition
             | "(" _condition ")" -> grouped_condition
    
    simple_condition: field operator value
    
    operator: "="
            | "!="
            | ">"
            | ">="
            | "<"
            | "<="
            | "IN"
            | "NOT" "IN"
            | "CONTAINS"
            | "CONTAINS" "ANY"
            | "CONTAINS" "ALL"
            | "DURING"
            | "REGEXP_MATCH"
    
    value: STRING
         | INTEGER
         | FLOAT
         | "TRUE" -> true
         | "FALSE" -> false
         | date_constant
    
    date_constant: "TODAY"
                 | "YESTERDAY"
                 | "LAST_7_DAYS"
                 | "LAST_14_DAYS"
                 | "LAST_30_DAYS"
                 | "LAST_90_DAYS"
                 | "THIS_MONTH"
                 | "LAST_MONTH"
                 | "THIS_QUARTER"
                 | "LAST_QUARTER"
                 | "THIS_YEAR"
                 | "LAST_YEAR"
    
    order_list: order_item ("," order_item)*
    order_item: field ["ASC" | "DESC"]
    
    parameter_list: parameter ("," parameter)*
    parameter: CNAME "=" value
    
    // Terminals
    STRING: /'[^']*'/ | /"[^"]*"/
    INTEGER: /[0-9]+/
    FLOAT: /[0-9]+\.[0-9]+/
    CNAME: /[a-zA-Z_][a-zA-Z0-9_]*/
    
    // Ignore whitespace
    %import common.WS
    %ignore WS
"""
