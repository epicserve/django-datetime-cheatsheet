#!/usr/bin/env python
"""
Script to generate README.md content from test files.

This script extracts documentation and examples from the test files and updates
the README.md file with the extracted content.
"""

import re
import ast
from pathlib import Path
import subprocess
import tempfile
import os

# Define the root directory of the project
ROOT_DIR = Path(__file__).parent.parent
TESTS_DIR = ROOT_DIR / "tests"
README_PATH = ROOT_DIR / "README.md"

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
                "description": description
            }
    return sections

def extract_docstring(node: ast.AST) -> str | None:
    """Extract the docstring from an AST node."""
    if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
        docstring = ast.get_docstring(node)
        if docstring:
            return docstring
    return None


def extract_test_method_info(node: ast.FunctionDef) -> dict:
    """Extract information from a test method."""
    docstring = extract_docstring(node)

    # Extract code examples from the function body
    code_examples = []
    for item in node.body:
        if (
            isinstance(item, ast.Expr)
            and isinstance(item.value, ast.Constant)
            and isinstance(item.value.value, str)
        ):
            # Skip docstrings
            continue

        # Extract various code elements as examples
        if isinstance(item, ast.Assert):
            code_examples.append({"code": ast.unparse(item), "lineno": item.lineno})
        elif isinstance(item, ast.Assign) and hasattr(item, "lineno"):
            code_examples.append({"code": ast.unparse(item), "lineno": item.lineno})
        elif isinstance(item, ast.Expr) and hasattr(item, "lineno"):
            code_examples.append({"code": ast.unparse(item), "lineno": item.lineno})
        elif isinstance(item, ast.With) and hasattr(item, "lineno"):
            # Include context managers (with statements)
            code_examples.append({"code": ast.unparse(item), "lineno": item.lineno})
        elif isinstance(item, ast.FunctionDef) and hasattr(item, "lineno"):
            # Include function definitions
            code_examples.append({"code": ast.unparse(item), "lineno": item.lineno})
        elif isinstance(item, ast.ClassDef) and hasattr(item, "lineno"):
            # Include class definitions
            code_examples.append({"code": ast.unparse(item), "lineno": item.lineno})
        elif isinstance(item, ast.If) and hasattr(item, "lineno"):
            # Include if statements
            code_examples.append({"code": ast.unparse(item), "lineno": item.lineno})
        elif isinstance(item, ast.For) and hasattr(item, "lineno"):
            # Include for loops
            code_examples.append({"code": ast.unparse(item), "lineno": item.lineno})
        elif isinstance(item, ast.Try) and hasattr(item, "lineno"):
            # Include try/except blocks
            code_examples.append({"code": ast.unparse(item), "lineno": item.lineno})

    return {
        "name": node.name,
        "docstring": docstring,
        "code_examples": code_examples,
    }


def extract_test_class_info(node: ast.ClassDef) -> dict:
    """Extract information from a test class."""
    docstring = extract_docstring(node)
    methods = []

    for item in node.body:
        if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
            methods.append(extract_test_method_info(item))

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
            classes.append(extract_test_class_info(node))

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


def clean_code_example(example: str) -> str:
    """Clean up a code example for better readability."""
    # Keep assert statements without adding comments
    # We don't need to modify assert statements

    # Add an empty line after class definitions
    # This improves readability in the README
    if example.strip().startswith("class "):
        # Add an empty line after the class definition
        example += "\n"

    # Fix indentation
    lines = example.split('\n')
    if len(lines) > 1:
        # Find the minimum indentation level (excluding empty lines)
        min_indent = float('inf')
        for line in lines:
            if line.strip():  # Skip empty lines
                indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent)
        
        # If there's excessive indentation, remove it
        if min_indent > 4:
            lines = [line[min_indent:] if line.strip() else line for line in lines]
            example = '\n'.join(lines)

    # Clean up self.render_str_template calls
    example = re.sub(
        r"self\.render_str_template\((.*?), (.*?)\)",
        r"render_template(\1, \2)",
        example,
    )

    # Clean up long string literals
    example = re.sub(
        r'""".*?"""',
        lambda m: m.group(0).replace("\n", "\\n"),
        example,
        flags=re.DOTALL,
    )
    example = re.sub(
        r"'''.*?'''",
        lambda m: m.group(0).replace("\n", "\\n"),
        example,
        flags=re.DOTALL,
    )

    # Clean up long template strings
    if "render_template(" in example and "\\n" in example:
        # Simplify template strings in render_template calls
        example = re.sub(
            r'render_template\("(.*?)\\n.*?", (.*?)\)',
            r'render_template("{{ ... }}", \2)',
            example,
        )

    # Format the code using ruff
    try:
        # Create a temporary file with the code
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as temp_file:
            temp_file.write(example)
            temp_file_path = temp_file.name

        # Run ruff format on the temporary file
        subprocess.run(
            [
                "bash", "-c", 
                f"cd {ROOT_DIR} && source .venv/bin/activate && ruff format {temp_file_path} --line-length 88"
            ],
            check=True,
            capture_output=True,
        )

        # Read the formatted code
        with open(temp_file_path, 'r') as temp_file:
            formatted_example = temp_file.read()

        # Clean up the temporary file
        os.unlink(temp_file_path)

        # Remove empty lines between consecutive assert statements
        # Process the formatted code line by line to handle consecutive assert statements
        lines = formatted_example.split('\n')
        processed_lines = []
        i = 0
        while i < len(lines):
            processed_lines.append(lines[i])
            
            # If this is an assert statement, check if the next non-empty line is also an assert
            if lines[i].strip().startswith('assert'):
                j = i + 1
                # Skip empty lines
                while j < len(lines) and not lines[j].strip():
                    j += 1
                
                # If the next non-empty line is an assert, skip the empty lines
                if j < len(lines) and lines[j].strip().startswith('assert'):
                    i = j - 1  # Will be incremented to j in the next iteration
                
            i += 1
        
        formatted_example = '\n'.join(processed_lines)

        # Return the formatted code
        return formatted_example
    except Exception as e:
        print(f"Error formatting code with ruff: {e}")
        # If there's an error, return the original example
        return example


def generate_markdown_for_section(section_key: str, section_info: dict) -> str:
    """Generate markdown content for a section."""
    file_path = TESTS_DIR / section_info["file"]
    classes = parse_test_file(file_path)
    comments = extract_comments_from_file(file_path)

    markdown = f"## {section_info['title']}\n\n"
    markdown += f"{section_info['description']}\n\n"

    for cls in classes:
        for method in cls["methods"]:
            if method["docstring"]:
                markdown += f"### {method['name'].replace('test_', '').replace('_', ' ').title()}\n\n"
                markdown += f"{method['docstring']}\n\n"

                # Add code examples
                if method["code_examples"]:
                    code_block = "```python\n"
                    
                    # Keep track of comments already added in this code block
                    added_comments = set()
                    previous_was_code = False
                    
                    for i, example in enumerate(method["code_examples"]):
                        line_number = example["lineno"]
                        
                        # Check for comments in a range of lines before the code
                        # Look for comments up to 3 lines before the code
                        for j in range(line_number, max(0, line_number - 4), -1):
                            if j in comments and j not in added_comments:
                                # Add an empty line before comment if previous line was code
                                if previous_was_code:
                                    code_block += "\n"
                                code_block += f"# {comments[j]}\n"
                                added_comments.add(j)
                                previous_was_code = False
                                break
                        
                        # Clean up the example
                        clean_example = clean_code_example(example["code"])
                        
                        # Add the code example
                        code_block += f"{clean_example}"
                        
                        # Add a newline after the example, but only if it's not the last example
                        if i < len(method["code_examples"]) - 1:
                            code_block += "\n"
                        
                        previous_was_code = True
                    
                    # Add the closing code block marker without an extra newline
                    code_block += "\n```\n\n"
                    
                    markdown += code_block

    # Post-process the markdown to remove empty lines between consecutive assert statements
    # Apply the regex substitution multiple times to catch all cases
    prev_markdown = ""
    while prev_markdown != markdown:
        prev_markdown = markdown
        markdown = re.sub(r'```python\n(.*?)(assert .*?)\n\n(assert .*?)```', r'```python\n\1\2\n\3```', markdown, flags=re.DOTALL)
        markdown = re.sub(r'(assert .*?)\n\n(assert .*?)(\n\n|```)', r'\1\n\2\3', markdown, flags=re.DOTALL)

    # Post-process the markdown to remove the extra line at the end of each code block
    markdown = re.sub(r'\n\n```', r'\n```', markdown)

    return markdown


def generate_readme_content() -> str:
    """Generate the content for the README.md file."""
    content = ""

    # Add each section
    sections = get_sections()
    for section_key, section_info in sections.items():
        content += generate_markdown_for_section(section_key, section_info)

    return content


def update_readme():
    """Update the README.md file with the generated content."""
    # Define the tags that will mark the start and end of the generated content
    start_tag = "<!-- section-examples-start -->"
    end_tag = "<!-- section-examples-end -->"

    # Generate the content to insert between the tags
    generated_content = generate_readme_content()

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
    update_readme()
