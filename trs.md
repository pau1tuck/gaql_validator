# Task Requirements Sheet

## GAQL Query Validation Python Package

We aim to build a **Python package** that validates **Google Ads Query Language (GAQL)** queries, ensuring they meet the grammar rules and syntax constraints set by the official Google Ads API. The final library will allow anyone—especially your LLM-based QueryBuilder—to generate and then validate GAQL strings offline, just like the web-based Google validator.

---

## 1. Overall Strategy & Rationale

### 1.1 Purpose

- **Core Problem:** The Google Ads API provides only a web-based GAQL query validator. We need a **local/offline** and fully customisable tool.
- **Solution:** Develop a parser/validator in Python using **lark** (and possibly some regex for smaller validations). This library must parse a GAQL query into an internal structure (AST) and apply checks for:
    - Proper clause ordering (`SELECT`, `FROM`, `WHERE`, `ORDER BY`, `LIMIT`, `PARAMETERS`).
    - Allowed operators, valid resource names, field references, and so on.
- **Why TDD?** GAQL is extremely finicky, so test-driven development ensures we catch edge cases and maintain correctness.

### 1.2 Use Cases

- **AI Query Generation**: Validate queries output by an LLM (e.g., a “QueryBuilderNode”).
- **Manual & Scripted**: Dev teams can quickly test GAQL queries in CI pipelines or CLI.

### 1.3 Proposed Tools & Tech

- **Python**: Main language for easy integration with Django and your AI workflow.
- **lark**: Grammar-based parsing. Potentially augment with regex for literal or resource matching.
- **CLI & pip distribution**: Provide a command-line interface and package on PyPI.

---

## 2. Implementation Plan

### 2.1 Steps Overview

1. **Initial Project Setup**
    - Create a fresh **virtualenv** and set up a new git repo, e.g. `gaqlint`.
    - Add basic files: `pyproject.toml` or `setup.py`, `README.md`, `LICENSE`, `requirements.txt`.
2. **Grammar & Field Rules**
    - Define or import the GAQL grammar reference (based on your snippet in the doc).
    - Outline resource name patterns, allowed operators, etc.
    - Decide if we incorporate Google’s official field definitions or keep it minimal for now.
3. **Parser Construction**
    - Use **lark** to parse the GAQL skeleton: `SELECT -> FROM -> WHERE -> ORDER BY -> LIMIT -> PARAMETERS`.
    - Integrate regex for tricky tokens (e.g. string quoting, numeric detection, resource naming, operators).
4. **Validation Layer**
    - Perform deeper checks on AST (e.g., “Does ‘segments.date’ accept `DURING` only?”).
    - Possibly allow a pluggable ruleset for more advanced usage (later feature).
5. **CLI & Python Package**
    - Build a `validate_gaql.py` or similar CLI to accept a GAQL query from stdin or file.
    - Bundle everything into a distributable Python package (pip install).
6. **Future Enhancements**
    - More advanced suggestions (“Did you mean `campaign.id`?”).
    - Field-level type checks from official field definitions.
    - Web-based “playground” with syntax highlighting.

---

## 3. Test-Driven Development (TDD) Approach

We’ll create test files in a `tests/` folder (e.g. `test_gaqlint.py`). TDD flow:

1. Write a failing test covering a minimal or basic requirement (e.g. a valid SELECT/FROM).
2. Implement only enough code to pass that test.
3. Refine or add more tests for edge and error cases.
4. Iterate until all tests pass.

**We do not** short-circuit for test environments or cheat to pass tests. Each test must pass via genuine, production-like logic.

---

## 4. Implementation Rules

1. **One Test at a Time**
    - If a test fails, fix the code. Re-run until it passes. Then move on.
2. **No Env Checks**
    - Do *not* detect if we’re in a test environment to skip logic.
3. **No Cheating**
    - Must not hard-code test-specific responses.
4. **Test Corrections**
    - If a test is found invalid or contradictory, fix the test itself rather than hacking the code to pass.

A proper implementation should:

- Follow the **same** code paths in both tests and production usage.
- Use robust parsing/validation logic that naturally satisfies the specs.

---

## 5. Initial Test Cases

Below is the test list we’ll create. We’ll start with a few small ones, then expand:

1. **`test_valid_basic_query`**
    - Input: A minimal valid GAQL query: `SELECT campaign.id FROM campaign LIMIT 10`.
    - Expected: Pass with no errors.
2. **`test_missing_from_clause`**
    - Input: `SELECT campaign.id LIMIT 10` (no `FROM`).
    - Expected: Validation fails or raises a meaningful exception.
3. **`test_multiple_filters_where_clause`**
    - Input: `SELECT ad_group.id FROM ad_group WHERE ad_group.status = 'ENABLED' AND segments.date DURING LAST_7_DAYS`.
    - Expected: Parses successfully, no syntax errors.
4. **`test_invalid_operator`**
    - Input: `SELECT campaign.id FROM campaign WHERE campaign.status ^^ 'ENABLED'`.
    - Expected: Fails because `^^` is not a valid operator.
5. **`test_clause_order`**
    - Input: `FROM campaign SELECT campaign.id LIMIT 10`.
    - Expected: Fails because clauses are out of order.
6. **`test_parameters_clause`**
    - Input: `SELECT campaign.id FROM campaign PARAMETERS include_drafts=true`.
    - Expected: Succeeds if all rules are correct for `PARAMETERS`.
7. **`test_regexp_match`**
    - Input: `SELECT ad_group.name FROM ad_group WHERE ad_group.name REGEXP_MATCH '.*Sale.*'`.
    - Expected: Succeeds if lark grammar includes `REGEXP_MATCH`.
8. **`test_edge_case_string_quoting`**
    - Input: `SELECT campaign.name FROM campaign WHERE campaign.name = "'Quirky' Interiors"`.
    - Expected: Properly parses string with quotes inside quotes if allowed by grammar.

We will expand or refine these as needed. Each test will represent a single scenario to keep them atomic.

---

## 6. Immediate Next Steps

1. **Local Setup**
    - Create the virtualenv, initialise git, add `pyproject.toml` or `requirements.txt` for lark + dev tools.
2. **Write Basic Test Stubs**
    - Create `tests/test_gaqlint.py` with the tests above, *commented out or partially complete*, so the LLM knows what to aim for.
3. **Gradual Implementation**
    - Let the LLM implement the grammar, parser, and validator incrementally, passing each test in turn.
4. **Documentation**
    - Include a simple `README.md` explaining how to install and run tests, plus a short usage snippet.

---

## 7. Summary

This **GAQL Query Validation Python Package** will parse and validate GAQL queries offline, bridging a key gap for developers and AI-based query generators. We’ll rely on a **lark-based** grammar, additional regex checks, and **comprehensive TDD**. Ultimately, the package will be delivered as a pip-installable library with a CLI for quick validations, plus the potential for future expansions (e.g. advanced field type checks).

Once the above steps are set up, we’ll ask the LLM to build out the test suite, then the implementation, strictly following TDD and the rules above.


---

## 8. Complete File Structure for Professional Python Package

To ensure our package meets professional standards and is easily installable via pip, we'll include the following files and directories:

### 8.1 Core Package Files
- **pyproject.toml**: Modern Python packaging configuration (PEP 621 compliant)
- **README.md**: Project documentation, installation instructions, and usage examples
- **LICENSE**: MIT, Apache, or other appropriate license
- **CHANGELOG.md**: Version history and notable changes
- **CONTRIBUTING.md**: Guidelines for contributors

### 8.2 Package Structure
- **src/gaql_validator/**: Main package directory (using src layout)
  - **__init__.py**: Package initialization, version exports
  - **validator.py**: Core validation functionality
  - **parser.py**: GAQL parsing implementation
  - **grammar.py**: Lark grammar definitions
  - **exceptions.py**: Custom exception classes
  - **cli.py**: Command-line interface implementation
  - **utils.py**: Helper functions and utilities

### 8.3 Testing and Quality Assurance
- **tests/**: Test directory
  - **__init__.py**: Test package initialization
  - **test_validator.py**: Validator tests
  - **test_parser.py**: Parser tests
  - **test_grammar.py**: Grammar tests
  - **test_cli.py**: CLI tests
  - **conftest.py**: pytest fixtures and configuration
- **.github/workflows/**: CI/CD configuration
  - **tests.yml**: Automated testing workflow
  - **publish.yml**: PyPI publishing workflow
- **tox.ini**: Multi-environment testing configuration
- **.pre-commit-config.yaml**: Pre-commit hooks configuration

### 8.4 Development Tools
- **requirements-dev.txt**: Development dependencies
- **.gitignore**: Git ignore patterns
- **.flake8**: Flake8 linter configuration
- **mypy.ini**: Type checking configuration
- **.coveragerc**: Coverage configuration

### 8.5 Documentation
- **docs/**: Documentation directory
  - **conf.py**: Sphinx configuration
  - **index.rst**: Documentation index
  - **usage.rst**: Usage documentation
  - **api.rst**: API reference
- **.readthedocs.yml**: Read the Docs configuration

This structure follows modern Python packaging best practices, including the src-layout pattern, comprehensive testing setup, and proper documentation. It will ensure our package is maintainable, well-documented, and meets the standards expected of professional Python packages on PyPI.