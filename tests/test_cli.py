"""
Tests for the GAQL validator CLI.
"""
from unittest.mock import patch, MagicMock

import pytest

from gaql_validator.cli import main, parse_args


@patch('gaql_validator.cli.parse_args')
@patch('sys.stdout', new_callable=MagicMock)
@patch('sys.stderr', new_callable=MagicMock)
def test_cli_valid_query(mock_stderr, mock_stdout, mock_parse_args) -> None:
    """Tests CLI with a valid query."""
    # Mock the args returned by parse_args
    args = MagicMock()
    args.query = "SELECT campaign.id FROM campaign LIMIT 10"
    args.file = None
    args.strict = False
    args.verbose = False
    mock_parse_args.return_value = args

    # Run CLI
    main()

    # Check output
    mock_stdout.write.assert_any_call('Valid GAQL query\n')
    assert not mock_stderr.write.called


@patch('gaql_validator.cli.parse_args')
@patch('sys.stdout', new_callable=MagicMock)
@patch('sys.stderr', new_callable=MagicMock)
def test_cli_invalid_query(mock_stderr, _, mock_parse_args) -> None:  # Using _ for unused argument
    """Tests CLI with an invalid query."""
    # Mock the args returned by parse_args
    args = MagicMock()
    args.query = "SELECT campaign.id LIMIT 10"
    args.file = None
    args.strict = False
    args.verbose = False
    args.fix = False  # No auto-fixing
    args.format = False  # No formatting
    args.output = None  # No output file
    mock_parse_args.return_value = args

    # Run CLI
    with pytest.raises(SystemExit) as excinfo:
        main()

    # Check exit code is 1 (error)
    assert excinfo.value.code == 1

    # Check that stderr.write was called with some error message
    # This is more flexible than checking for a specific message
    assert mock_stderr.write.called


@patch('argparse.ArgumentParser.parse_args')
def test_parse_args(mock_parse_args) -> None:
    """Tests the argument parsing function."""
    # Create a mock return value for parse_args
    args = MagicMock()
    args.query = "SELECT campaign.id FROM campaign LIMIT 10"
    args.file = None
    args.strict = False
    args.verbose = False
    mock_parse_args.return_value = args

    # Call parse_args
    result = parse_args([args.query])

    # Check result
    assert result == args


@patch('gaql_validator.cli.parse_args')
@patch('sys.stdout', new_callable=MagicMock)
@patch('sys.stderr', new_callable=MagicMock)
def test_cli_file_input(mock_stderr, mock_stdout, mock_parse_args) -> None:
    """Tests CLI with file input."""
    # Mock the args returned by parse_args
    args = MagicMock()
    args.query = None
    args.file = "query.gaql"
    args.strict = False
    args.verbose = False
    mock_parse_args.return_value = args

    # Create a temporary file with a valid query
    with patch('builtins.open', MagicMock()) as mock_open:
        mock_file = MagicMock()
        mock_file.read.return_value = 'SELECT campaign.id FROM campaign LIMIT 10'
        mock_open.return_value.__enter__.return_value = mock_file

        # Run CLI
        main()

        # Check output
        mock_stdout.write.assert_any_call('Valid GAQL query\n')
        assert not mock_stderr.write.called
