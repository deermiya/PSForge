# Contributing to PSForge

Thank you for your interest in contributing to PSForge! This document provides guidelines and instructions for contributing.

## 🌟 Ways to Contribute

- 🐛 **Report bugs** - Found a bug? Open an issue
- 💡 **Suggest features** - Have an idea? We'd love to hear it
- 📝 **Improve documentation** - Clarify or expand docs
- 🔧 **Fix bugs** - Submit a pull request
- ✨ **Add features** - Implement new tools or capabilities
- 🧪 **Write tests** - Improve test coverage
- 🌍 **Translate** - Help with internationalization

## 📋 Before You Start

1. **Check existing issues** - Someone might already be working on it
2. **Open an issue first** - For major changes, discuss the approach
3. **Follow the code style** - Use Ruff with line-length 120
4. **Write tests** - Maintain or improve test coverage
5. **Update documentation** - Keep docs in sync with code

## 🚀 Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/psforge.git
cd psforge
```

### 2. Install Dependencies

```bash
# Using Poetry (recommended)
poetry install

# Or using pip
pip install -e ".[dev]"
```

### 3. Install Pre-commit Hooks (Optional but Recommended)

```bash
poetry run pre-commit install
```

### 4. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

## 📝 Code Style Guidelines

### Python Code Style

PSForge uses [Ruff](https://docs.astral.sh/ruff/) for formatting and linting.

**Format your code:**
```bash
poetry run ruff format .
```

**Check for issues:**
```bash
poetry run ruff check .
```

**Auto-fix issues:**
```bash
poetry run ruff check --fix .
```

### Code Standards

- ✅ **Line length:** 120 characters
- ✅ **Type hints:** Required on all function parameters and returns
- ✅ **Docstrings:** Required on all public functions (Google style)
- ✅ **Naming:**
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
- ✅ **Imports:** Organized (stdlib → third-party → local)

### Docstring Example

```python
def create_text_layer(
    text: str,
    x: float = 100,
    y: float = 100,
    font_size: float = 24,
) -> dict[str, Any]:
    """Create a new text layer in the active document.

    Args:
        text: The text content to display.
        x: Horizontal position in pixels (default: 100).
        y: Vertical position in pixels (default: 100).
        font_size: Font size in points (default: 24).

    Returns:
        dict: Operation result containing:
            - success (bool): Whether the operation succeeded
            - layer_name (str): Name of the created layer
            - context (dict): Current Photoshop state

    Raises:
        ValueError: If text is empty or invalid.
        ConnectionError: If Photoshop is not running.
    """
    # Implementation...
```

## 🛠️ Adding New Tools

PSForge uses an auto-discovery system. To add a new tool:

### 1. Create a Tool File

Create `psforge/tools/my_new_tools.py`:

```python
"""My new Photoshop tools."""

from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.ps_adapter.context import get_context_info
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register all tools in this module.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered tool names.
    """
    registered_tools = []

    @debug_tool
    @log_tool_call
    def my_awesome_tool(param: str) -> dict[str, Any]:
        """Do something awesome in Photoshop.

        Args:
            param: Parameter description.

        Returns:
            dict: Operation result with context.
        """
        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
                "context": get_context_info(),
            }

        try:
            # Your implementation
            result = ps_app.execute_javascript(f"// Your JS code here")

            return {
                "success": True,
                "message": "Operation completed",
                "result": result,
                "context": get_context_info(),  # Always include context!
            }
        except Exception as e:
            logger.error(f"Failed to execute tool: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    registered_tools.append(register_tool(mcp, my_awesome_tool, "my_awesome_tool"))
    return registered_tools
```

### 2. Tool Requirements

Every tool MUST:
- ✅ Have `@debug_tool` and `@log_tool_call` decorators
- ✅ Return a `dict` with `success` field
- ✅ Include `context` from `get_context_info()` in return value
- ✅ Have complete docstring with Args and Returns sections
- ✅ Have type hints on all parameters and return value
- ✅ Validate parameters before executing
- ✅ Handle errors gracefully

### 3. Test Your Tool

Run the tool registration checker:
```bash
poetry run python check_tools.py
```

Your tool should appear in the list!

## 🧪 Testing

### Run All Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=psforge

# Run specific test file
poetry run pytest tests/unit/test_server.py
```

### Writing Tests

Create tests in `tests/unit/` or `tests/integration/`:

```python
"""Test my new tool."""

import pytest
from psforge.tools import my_new_tools


class TestMyAwesomeTool:
    """Test my_awesome_tool function."""

    def test_success_case(self):
        """Test successful execution."""
        # Arrange
        param = "test_value"

        # Act
        result = my_new_tools.my_awesome_tool(param)

        # Assert
        assert result["success"] is True
        assert "context" in result

    def test_no_document(self):
        """Test behavior with no document."""
        # This test requires mocking or integration testing
        pass
```

## 📚 Documentation

### Update Documentation When:

- ✅ Adding new tools → Update README.md tool list
- ✅ Changing behavior → Update CHANGELOG.md
- ✅ Adding features → Update QUICKSTART.md if relevant
- ✅ Fixing bugs → Add to CHANGELOG.md
- ✅ Changing API → Update relevant docs

### Documentation Files

- `README.md` / `README_ZH.md` - Main documentation
- `QUICKSTART.md` - Quick start guide
- `CHANGELOG.md` - Version history
- `CONTRIBUTING.md` - This file

## 🔄 Pull Request Process

### 1. Prepare Your Changes

```bash
# Make sure all tests pass
poetry run pytest

# Format code
poetry run ruff format .

# Check for issues
poetry run ruff check .

# Commit your changes
git add .
git commit -m "feat: Add awesome new feature"
```

### 2. Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

**Examples:**
```
feat: Add text alignment tool
fix: Handle timeout in connection retry
docs: Update README with new examples
test: Add integration tests for layer tools
```

### 3. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
```

### 4. PR Checklist

Before submitting, ensure:

- ✅ All tests pass
- ✅ Code is formatted with Ruff
- ✅ New features have tests
- ✅ Documentation is updated
- ✅ Commit messages follow convention
- ✅ PR description explains the change
- ✅ No merge conflicts

### 5. Code Review

- Address reviewer feedback
- Make requested changes
- Push updates to the same branch
- PR will update automatically

## 🐛 Reporting Bugs

### Before Reporting

1. **Search existing issues** - It might already be reported
2. **Test with latest version** - Bug might be fixed
3. **Reproduce consistently** - Ensure it's repeatable

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Open Photoshop
2. Execute tool '...'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Environment:**
- OS: Windows 11
- Python: 3.11.5
- Photoshop: 2024
- PSForge: 0.1.0

**Logs**
Attach relevant logs from `psforge_debug.log`

**Additional context**
Any other relevant information.
```

## 💡 Suggesting Features

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
How you think it should work.

**Describe alternatives you've considered**
Other approaches you've thought about.

**Additional context**
Mockups, examples, or references.
```

## 🎯 Development Tips

### Debugging

1. **Check logs:** `psforge_debug.log` has detailed execution logs
2. **Use test scripts:** `test_connection.py` and `check_tools.py`
3. **Enable verbose logging:** See `psforge/server.py`

### Testing with Photoshop

1. **Start Photoshop** before running tests
2. **Close test documents** after integration tests
3. **Save work** before running destructive tests

### Common Issues

- **Import errors:** Run `poetry install`
- **Connection failures:** Ensure PS is running
- **Type errors:** Add type hints and run `mypy`

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Your contributions make PSForge better for everyone. We appreciate your time and effort!

## 📞 Questions?

- 💬 **Discussion:** Open a GitHub Discussion
- 🐛 **Bugs:** Open a GitHub Issue
- 📧 **Private:** Contact maintainers (if applicable)

---

**Happy contributing! 🎨✨**
