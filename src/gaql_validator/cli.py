"""
Command-line interface for GAQL validator.
"""
import argparse
import sys
from typing import cast

from gaql_validator.exceptions import GaqlError
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

    # Create validator and validate the query
    validator: GaqlValidator = GaqlValidator()

    try:
        result: dict[str, bool | list[str]] = validator.validate(query, strict=bool(args.strict))

        if result["valid"]:
            _ = sys.stdout.write("Valid GAQL query\n")
            if args.verbose:
                _ = sys.stdout.write("No validation errors found.\n")
        else:
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
