"""
Command-line interface for GAQL validator.
"""
import argparse
import sys
from typing import List, Optional

from gaql_validator.exceptions import GaqlError
from gaql_validator.validator import GaqlValidator


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Args:
        args: Command-line arguments, defaults to sys.argv[1:].
        
    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Validate Google Ads Query Language (GAQL) queries"
    )
    
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "query", 
        nargs="?", 
        help="GAQL query string to validate", 
        default=None
    )
    input_group.add_argument(
        "-f", "--file", 
        help="File containing GAQL query to validate", 
        type=str
    )
    
    parser.add_argument(
        "--strict", 
        help="Enable strict validation mode (raises exceptions)", 
        action="store_true"
    )
    
    parser.add_argument(
        "--verbose", 
        help="Enable verbose output", 
        action="store_true"
    )
    
    return parser.parse_args(args)


def main() -> None:
    """
    Main entry point for the CLI.
    """
    # Parse command-line arguments
    args = parse_args()
    
    # Get the query from command-line or file
    query = None
    if args.query:
        query = args.query
    elif args.file:
        try:
            with open(args.file, "r") as f:
                query = f.read().strip()
        except Exception as e:
            sys.stderr.write(f"Error reading file: {str(e)}\n")
            sys.exit(1)
    
    # Create validator and validate the query
    validator = GaqlValidator()
    
    try:
        result = validator.validate(query, strict=args.strict)
        
        if result["valid"]:
            sys.stdout.write("Valid GAQL query\n")
            if args.verbose:
                sys.stdout.write("No validation errors found.\n")
        else:
            sys.stderr.write("Invalid GAQL query\n")
            for error in result["errors"]:
                sys.stderr.write(f"- {error}\n")
            sys.exit(1)
    except GaqlError as e:
        sys.stderr.write(f"Error: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()