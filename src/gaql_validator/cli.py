"""
Command-line interface for GAQL validator.
"""
import argparse
import sys
from typing import cast

from gaql_validator.exceptions import GaqlError
from gaql_validator.fixer import GaqlFixer
from gaql_validator.utils import format_gaql
from gaql_validator.validator import GaqlValidator


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        args: Command-line arguments, defaults to sys.argv[1:].

    Returns:
        Parsed arguments.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Validate Google Ads Query Language (GAQL) queries"
    )

    input_group = parser.add_mutually_exclusive_group(required=True)
    _ = input_group.add_argument(
        "query",
        nargs="?",
        help="GAQL query string to validate",
        default=None
    )
    _ = input_group.add_argument(
        "-f", "--file",
        help="File containing GAQL query to validate",
        type=str
    )

    _ = parser.add_argument(
        "--strict",
        help="Enable strict validation mode (raises exceptions)",
        action="store_true"
    )

    _ = parser.add_argument(
        "--verbose",
        help="Enable verbose output",
        action="store_true"
    )
    
    _ = parser.add_argument(
        "--fix",
        help="Attempt to fix invalid queries automatically",
        action="store_true"
    )
    
    _ = parser.add_argument(
        "--format",
        help="Format the query for better readability",
        action="store_true"
    )
    
    _ = parser.add_argument(
        "-o", "--output",
        help="Output file to write the fixed/formatted query to",
        type=str
    )

    return parser.parse_args(args)


def main() -> None:
    """
    Main entry point for the CLI.
    """
    # Parse command-line arguments
    args: argparse.Namespace = parse_args()

    # Get the query from command-line or file
    query: str = ""
    if args.query:
        query = cast(str, args.query)
    elif args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                query = f.read().strip()
        except IOError as e:
            _ = sys.stderr.write(f"Error reading file: {str(e)}\n")
            sys.exit(1)

    # Format the query if requested
    if args.format:
        query = format_gaql(query)
        if not args.fix:  # If just formatting, show result
            _ = sys.stdout.write(f"{query}\n")
            if args.output:
                try:
                    with open(args.output, "w", encoding="utf-8") as f:
                        f.write(query)
                    _ = sys.stdout.write(f"Formatted query written to {args.output}\n")
                except IOError as e:
                    _ = sys.stderr.write(f"Error writing to file: {str(e)}\n")
                    sys.exit(1)
            return

    # Create validator and validate the query
    validator: GaqlValidator = GaqlValidator()

    try:
        result: dict[str, bool | list[str]] = validator.validate(query, strict=bool(args.strict))

        if result["valid"]:
            _ = sys.stdout.write("Valid GAQL query\n")
            if args.verbose:
                _ = sys.stdout.write("No validation errors found.\n")
                _ = sys.stdout.write(f"Query: {query}\n")
        else:
            if args.fix:
                # Try to fix the query
                fixer: GaqlFixer = GaqlFixer()
                fixed_query, changes = fixer.fix_query(query)
                
                # Check if the fix worked
                fix_result = validator.validate(fixed_query)
                if fix_result["valid"]:
                    _ = sys.stdout.write("Successfully fixed invalid query:\n")
                    _ = sys.stdout.write(f"{fixed_query}\n\n")
                    
                    if args.verbose:
                        _ = sys.stdout.write("Changes made:\n")
                        for change in changes:
                            _ = sys.stdout.write(f"- {change}\n")
                    
                    # Write to output file if requested
                    if args.output:
                        try:
                            with open(args.output, "w", encoding="utf-8") as f:
                                f.write(fixed_query)
                            _ = sys.stdout.write(f"Fixed query written to {args.output}\n")
                        except IOError as e:
                            _ = sys.stderr.write(f"Error writing to file: {str(e)}\n")
                            sys.exit(1)
                else:
                    _ = sys.stderr.write("Could not fully fix the query. Partial fixes applied:\n")
                    _ = sys.stderr.write(f"{fixed_query}\n\n")
                    _ = sys.stderr.write("Remaining issues:\n")
                    for error in cast(list[str], fix_result.get("errors", [])):
                        _ = sys.stderr.write(f"- {error}\n")
                    sys.exit(1)
            else:
                # Just report the errors without fixing
                _ = sys.stderr.write("Invalid GAQL query\n")
                errors = cast(list[str], result.get("errors", []))
                for error in errors:
                    _ = sys.stderr.write(f"- {error}\n")
                sys.exit(1)
    except GaqlError as e:
        _ = sys.stderr.write(f"Error: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()