#!/usr/bin/env python
"""
Script to clean up test files to comply with pylint and mypy requirements.
"""
import os
import re
from pathlib import Path


def fix_file(file_path: str) -> None:
    """
    Fix a single test file.
    
    Args:
        file_path: Path to the file to fix
    """
    print(f"Fixing {file_path}...")
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Fix missing type annotations
    content = re.sub(
        r"def (test_[a-zA-Z0-9_]+)\(([^)]*)\):",
        r"def \1(\2) -> None:",
        content
    )
    
    # Fix trailing whitespace
    content = re.sub(r"[ \t]+$", "", content, flags=re.MULTILINE)
    
    # Fix import order
    lines = content.split("\n")
    
    # Parse imports
    standard_imports = []
    third_party_imports = []
    local_imports = []
    
    import_indices = []
    non_import_indices = []
    
    for i, line in enumerate(lines):
        # Skip empty lines or comments in the import section
        if not line.strip() or line.strip().startswith("#"):
            continue
        
        if line.startswith("import ") or line.startswith("from "):
            import_indices.append(i)
            
            if "unittest" in line or "typing" in line or "re" in line or "os" in line:
                standard_imports.append(line)
            elif "pytest" in line or "numpy" in line:
                third_party_imports.append(line)
            else:
                local_imports.append(line)
        else:
            non_import_indices.append(i)
    
    # If we found imports, reorder them
    if import_indices:
        first_import = min(import_indices)
        last_import = max(import_indices)
        
        # Get all non-import lines that appear before the imports
        prefix_lines = lines[:first_import]
        
        # Get all non-import lines that appear after the imports
        suffix_lines = lines[last_import + 1:]
        
        # Sort each group of imports
        standard_imports.sort()
        third_party_imports.sort()
        local_imports.sort()
        
        # Combine the sorted imports with proper spacing
        new_lines = prefix_lines.copy()
        
        if standard_imports:
            new_lines.extend(standard_imports)
            new_lines.append("")
        
        if third_party_imports:
            new_lines.extend(third_party_imports)
            new_lines.append("")
        
        if local_imports:
            new_lines.extend(local_imports)
            new_lines.append("")
        
        # Remove any extra blank lines at the end of the imports
        while new_lines and not new_lines[-1].strip():
            new_lines.pop()
        
        # Add the rest of the file
        new_lines.extend(suffix_lines)
        
        # Create new content
        content = "\n".join(new_lines)
    
    # Fix missing newline at the end of the file
    if not content.endswith("\n"):
        content += "\n"
    
    # Write the fixed content back to the file
    with open(file_path, "w") as f:
        f.write(content)


def fix_test_dir() -> None:
    """Fix all the test files in the tests directory."""
    tests_dir = Path("/Users/pau1tuck/dev/gaql_validator/tests")
    
    for test_file in tests_dir.glob("*.py"):
        fix_file(str(test_file))


if __name__ == "__main__":
    fix_test_dir()