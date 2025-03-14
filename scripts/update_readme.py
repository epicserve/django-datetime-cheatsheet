#!/usr/bin/env python
"""
Script to generate README.md content from test files.

This script extracts documentation and examples from the test files and updates
the README.md file with the extracted content.

Usage:
    python scripts/update_readme.py
    python scripts/update_readme.py --github-url https://github.com/username/repo/blob/main

The --github-url parameter enables links to the original test files in the README.
"""

import re
import ast
from pathlib import Path
import subprocess
import tempfile
import os
import argparse

# Define the root directory of the project
ROOT_DIR = Path(__file__).parent.parent
TESTS_DIR = ROOT_DIR / "tests"
README_PATH = ROOT_DIR / "README.md"

# Configuration options
# Default GitHub repository URL (without trailing slash)
# Set to None to disable GitHub links by default
DEFAULT_GITHUB_REPO_URL = None


# Parse command-line arguments
def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate README.md content from test files."
    )
    parser.add_argument(
        "--github-url",
        default=DEFAULT_GITHUB_REPO_URL,
        help="GitHub repository URL for linking to test files (e.g., https://github.com/username/repo/blob/main)",
    )
    return parser.parse_args()


# Define the sections to extract from the test files
def get_sections():
    """Get sections from test files in the tests directory."""
    sections = {}
    for test_file in sorted(TESTS_DIR.glob("test_*.py")):
        module = ast.parse(test_file.read_text())

        docstring = ast.get_docstring(module)
        if docstring:
            # Split docstring into title and description
            parts = docstring.split("\n\n", 1)
            title = parts[0].strip()
            description = parts[1].strip() if len(parts) > 1 else ""

            # Create section key from filename without test_ prefix and .py extension
            key = test_file.stem.replace("test_", "")

            sections[key] = {
                "file": test_file.name,
                "title": title,
                "description": description,
            }
    return sections


def extract_docstring(node: ast.AST) -> str | None:
    """Extract the docstring from an AST node."""
    if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
        docstring = ast.get_docstring(node)
        if docstring:
            return docstring
    return None


def extract_test_method_info(node: ast.FunctionDef, file_content: str) -> dict:
    """Extract information from a test method."""
    docstring = extract_docstring(node)

    # Get the source code of the entire method
    start_lineno = node.lineno
    end_lineno = 0

    # Find the end line number by looking at the last node in the function body
    for item in node.body:
        if hasattr(item, "end_lineno") and item.end_lineno > end_lineno:
            end_lineno = item.end_lineno

    # If we couldn't determine the end line, use a reasonable default
    if end_lineno == 0:
        end_lineno = start_lineno + len(node.body) + 5  # Add some buffer

    # Extract the method source code from the file content
    file_lines = file_content.splitlines()
    method_source = "\n".join(file_lines[start_lineno - 1 : end_lineno])

    return {
        "name": node.name,
        "docstring": docstring,
        "source_code": method_source,
        "start_line": start_lineno,
        "end_line": end_lineno,
    }


def extract_test_class_info(node: ast.ClassDef, file_content: str) -> dict:
    """Extract information from a test class."""
    docstring = extract_docstring(node)
    methods = []

    for item in node.body:
        if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
            methods.append(extract_test_method_info(item, file_content))

    return {
        "name": node.name,
        "docstring": docstring,
        "methods": methods,
    }


def parse_test_file(file_path: Path) -> list[dict]:
    """Parse a test file and extract test classes and methods."""
    with open(file_path, "r") as f:
        content = f.read()

    tree = ast.parse(content)
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            classes.append(extract_test_class_info(node, content))

    return classes


def extract_comments_from_file(file_path: Path) -> dict[int, str]:
    """Extract comments from a file, indexed by line number."""
    with open(file_path, "r") as f:
        lines = f.readlines()

    comments = {}
    current_comment = []
    current_comment_start = None

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith("#"):
            if current_comment_start is None:
                current_comment_start = i + 1
            current_comment.append(line[1:].strip())
        elif current_comment:
            # End of a comment block
            comments[current_comment_start] = "\n# ".join(current_comment)
            current_comment = []
            current_comment_start = None

    # Handle case where file ends with a comment
    if current_comment:
        comments[current_comment_start] = "\n# ".join(current_comment)

    return comments


def clean_test_method_code(method_source: str) -> str:
    """Clean up a test method for better readability in the README."""
    # Remove the method definition line (def test_...)
    lines = method_source.splitlines()
    if lines and lines[0].strip().startswith("def test_"):
        lines = lines[1:]

    # Remove docstring if present
    if len(lines) >= 2 and (
        lines[0].strip().startswith('"""') or lines[0].strip().startswith("'''")
    ):
        # Find the end of the docstring
        docstring_delimiter = '"""' if lines[0].strip().startswith('"""') else "'''"
        docstring_end_idx = None

        # Handle single-line docstrings
        if docstring_delimiter in lines[0][lines[0].find(docstring_delimiter) + 3 :]:
            docstring_end_idx = 0
        else:
            # Multi-line docstring
            for i, line in enumerate(lines[1:], 1):
                if docstring_delimiter in line:
                    docstring_end_idx = i
                    break

        if docstring_end_idx is not None:
            lines = lines[docstring_end_idx + 1 :]

    # Fix indentation (remove the method indentation)
    if lines:
        # Find the minimum indentation level
        min_indent = float("inf")
        for line in lines:
            if line.strip():  # Skip empty lines
                indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent)

        # Remove the common indentation
        if min_indent < float("inf"):
            lines = [line[min_indent:] if line.strip() else line for line in lines]

    # Clean up self.render_str_template calls
    code = "\n".join(lines)
    code = re.sub(
        r"self\.render_str_template\((.*?), (.*?)\)",
        r"render_template(\1, \2)",
        code,
    )

    # Format the code using ruff
    try:
        # Create a temporary file with the code
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        # Run ruff format on the temporary file
        subprocess.run(
            [
                "bash",
                "-c",
                f"cd {ROOT_DIR} && source .venv/bin/activate && ruff format {temp_file_path} --line-length 88",
            ],
            check=True,
            capture_output=True,
        )

        # Read the formatted code
        with open(temp_file_path, "r") as temp_file:
            formatted_code = temp_file.read()

        # Clean up the temporary file
        os.unlink(temp_file_path)

        return formatted_code.strip()
    except Exception as e:
        print(f"Error formatting code with ruff: {e}")
        # If there's an error, return the original code
        return code.strip()


def generate_markdown_for_section(
    section_key: str, section_info: dict, github_repo_url=None
) -> str:
    """Generate markdown content for a section."""
    file_path = TESTS_DIR / section_info["file"]
    classes = parse_test_file(file_path)

    markdown = f"## {section_info['title']}\n\n"
    markdown += f"{section_info['description']}\n\n"

    for cls in classes:
        for method in cls["methods"]:
            if method["docstring"]:
                markdown += f"### {method['name'].replace('test_', '').replace('_', ' ').title()}\n\n"
                markdown += f"{method['docstring']}\n\n"

                # Add the entire method as a code example
                cleaned_code = clean_test_method_code(method["source_code"])
                if cleaned_code:
                    # Add a right-aligned link to the full test file if GitHub URL is configured
                    if github_repo_url:
                        test_file_name = section_info["file"]
                        start_line = method["start_line"]
                        end_line = method["end_line"]

                        # Create a GitHub-style link to the specific lines in the file
                        file_link = f"{github_repo_url}/tests/{test_file_name}#L{start_line}-L{end_line}"

                        # Add a right-aligned link with an icon and better styling
                        markdown += (
                            '<div align="right" style="margin-bottom: -10px;">'
                            f'<a href="{file_link}" title="View full example in source code" '
                            'style="font-size: 0.8em; color: #5a5a5a; text-decoration: none;">'
                            "📝 View full example</a></div>\n\n"
                        )

                    markdown += "```python\n"
                    markdown += cleaned_code
                    markdown += "\n```\n\n"

    return markdown


def generate_readme_content(github_repo_url=None):
    """Generate the content for the README.md file."""
    content = ""

    # Add each section
    sections = get_sections()
    for section_key, section_info in sections.items():
        content += generate_markdown_for_section(
            section_key, section_info, github_repo_url
        )

    return content


def update_readme(github_repo_url=None):
    """Update the README.md file with the generated content."""
    # Define the tags that will mark the start and end of the generated content
    start_tag = "<!-- section-examples-start -->"
    end_tag = "<!-- section-examples-end -->"

    # Generate the content to insert between the tags
    generated_content = generate_readme_content(github_repo_url)

    # Read the current README.md file
    current_content = README_PATH.read_text()

    # Find the start and end tags in the current content
    start_index = current_content.find(start_tag)
    end_index = current_content.find(end_tag)

    if start_index == -1 or end_index == -1:
        print(
            f"Error: Tags not found in {README_PATH}. Make sure the README.md contains the tags `{start_tag}` and `{end_tag}`."
        )
        exit(1)
    else:
        # Replace the content between the tags
        new_content = (
            current_content[: start_index + len(start_tag)]
            + "\n"
            + generated_content
            + "\n"
            + current_content[end_index:]
        )

    # Write the updated content back to the file
    README_PATH.write_text(new_content)

    print("Updated README.md with examples from tests.")


if __name__ == "__main__":
    args = parse_args()
    update_readme(args.github_url)
