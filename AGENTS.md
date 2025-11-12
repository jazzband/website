# AI Agent Guidelines for Jazzband.co

This document provides guidelines for AI agents working on the Jazzband.co codebase.

## Testing Patterns

### Test Framework

This project uses **pytest** with the following conventions:

- ✅ **Use pytest-mock's `mocker` fixture** - Available automatically via `pytest-mock` plugin
- ✅ **Function-based tests** - Not class-based test methods
- ❌ **Never import `unittest.mock` or `mock`** - Use `mocker` fixture instead
- ❌ **No `@patch` decorators** - Use `patch()` as context managers instead

### Test Structure

```python
def test_function_name(fixture1, fixture2, mocker):
    """Clear docstring describing what's being tested."""
    # Arrange - Set up test data and mocks
    mock_obj = mocker.MagicMock()
    mock_obj.method.return_value = expected_value

    # Act - Call the function under test
    with patch("module.path.to.object") as mock_something:
        result = function_under_test(args)

    # Assert - Verify the results
    assert result == expected_value
    mock_obj.method.assert_called_once()
```

### Available Fixtures

Common fixtures are defined in `tests/conftest.py`:

#### Application Fixtures
- `app` - Flask application instance
- `test_app_context` - Application context for isolated tests

#### Mock Fixtures
- `mocker` - pytest-mock's mocker fixture (use this instead of unittest.mock)
- `github_blueprint` - Returns `(blueprint, mock_admin_session)` tuple
- `mock_user` - Mock user object with id, login, email
- `mock_project` - Mock project instance
- `mock_github_api` - Mock GitHub API client
- `mock_response_factory` - Factory for creating mock HTTP responses
- `create_mock_response(status_code, data)` - Helper to create mock responses

#### Test Data Fixtures
- `github_org_name` - Test organization name ("test-org-name")
- `test_project_name` - Test project name ("test-project")

### Mocking Patterns

#### Mocking Database Queries

```python
def test_with_database_query(mocker):
    """Test function that queries the database."""
    mock_user = mocker.MagicMock()
    mock_user.login = "test-user"

    with patch("module.path.User") as mock_user_class:
        mock_user_class.query.get.return_value = mock_user

        # Your test code here
        result = function_that_queries_user(user_id=123)

        # Verify the query was called
        mock_user_class.query.get.assert_called_once_with(123)
```

#### Mocking GitHub API Calls

```python
def test_github_api_call(mocker, test_app_context):
    """Test function that calls GitHub API."""
    with patch("jazzband.projects.tasks.github") as mock_github:
        # Setup mock response
        mock_response = mocker.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_github.some_method.return_value = mock_response

        # Call function
        result = function_that_uses_github_api()

        # Verify
        mock_github.some_method.assert_called_once()
        assert result is not None
```

#### Mocking Multiple Related Objects

```python
def test_with_multiple_mocks(mocker):
    """Test with multiple related mock objects."""
    # Create related mocks
    mock_user = mocker.MagicMock()
    mock_user.login = "test-lead"

    mock_project = mocker.MagicMock()
    mock_project.team_slug = "test-project"
    mock_project.leads_team_slug = "test-project-leads"

    # Patch multiple classes
    with patch("module.User") as mock_user_class:
        with patch("module.Project") as mock_project_class:
            mock_user_class.query.get.return_value = mock_user
            mock_project_class.query.get.return_value = mock_project

            # Test code here
```

### Testing GitHub API Methods

When testing methods on `GitHubBlueprint`:

```python
def test_github_method(github_blueprint, github_org_name, mocker):
    """Test a GitHub API method."""
    blueprint, mock_admin_session = github_blueprint

    # Setup mock response
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": 12345, "name": "test"}
    mock_admin_session.get.return_value = mock_response

    # Call the method being tested
    result = GitHubBlueprint.method_name(blueprint, "argument")

    # Verify API was called correctly
    mock_admin_session.get.assert_called_once_with("expected/path")

    # Verify the result
    assert result.status_code == 200
    assert result.json()["id"] == 12345
```

### Testing Task Functions

Task functions often interact with database models and external APIs:

```python
def test_task_function(mocker, test_app_context):
    """Test a Spinach task function."""
    user_id = 123
    project_id = 456

    # Setup mocks for database objects
    mock_user = mocker.MagicMock()
    mock_user.login = "test-user"

    mock_project = mocker.MagicMock()
    mock_project.name = "test-project"

    # Patch database and GitHub
    with patch("jazzband.projects.tasks.User") as mock_user_class:
        with patch("jazzband.projects.tasks.Project") as mock_project_class:
            with patch("jazzband.projects.tasks.github") as mock_github:
                # Setup returns
                mock_user_class.query.get.return_value = mock_user
                mock_project_class.query.get.return_value = mock_project

                mock_response = mocker.MagicMock()
                mock_response.status_code = 200
                mock_github.some_api_call.return_value = mock_response

                # Call the task
                task_function(user_id, project_id)

                # Verify interactions
                mock_github.some_api_call.assert_called_once()
```

### Assertion Patterns

#### Verify Method Calls

```python
# Called once with specific arguments
mock_obj.method.assert_called_once_with("arg1", "arg2")

# Called once (any arguments)
mock_obj.method.assert_called_once()

# Called specific number of times
assert mock_obj.method.call_count == 3

# Never called
mock_obj.method.assert_not_called()

# Check multiple calls
calls = mock_obj.method.call_args_list
assert calls[0][0] == ("first", "call")
assert calls[1][0] == ("second", "call")
```

#### Verify Call Arguments (Non-strict)

When argument order might vary:

```python
# Instead of strict assertion
mock_session.put.assert_called_once_with(url, json=data, headers=hdrs)

# Use this pattern
call_args = mock_session.put.call_args
assert call_args[0][0] == expected_url
assert "json" in call_args[1]
assert call_args[1]["json"]["key"] == expected_value
```

### Test Organization

#### File Naming
- Test files: `tests/test_<feature>.py`
- Test functions: `test_<what_is_being_tested>`

#### Test Sections
Group related tests with comments:

```python
# Tests for GitHub API methods

def test_create_team():
    ...

def test_delete_team():
    ...


# Tests for task functions

def test_add_user_task():
    ...

def test_remove_user_task():
    ...
```

### Complete Example

Here's a complete test from `tests/test_leads_team_management.py`:

```python
def test_add_user_to_team_lead_member(mocker, test_app_context):
    """Test adding a lead member to both project team and leads team."""
    user_id = 123
    project_id = 456
    is_lead = True

    # Create mock user and project
    mock_user = mocker.MagicMock()
    mock_user.id = user_id
    mock_user.login = "test-lead"

    mock_project = mocker.MagicMock()
    mock_project.id = project_id
    mock_project.team_slug = "test-project"
    mock_project.leads_team_slug = "test-project-leads"

    # Mock User.query.get and Project.query.get
    with patch("jazzband.projects.tasks.User") as mock_user_class:
        with patch("jazzband.projects.tasks.Project") as mock_project_class:
            with patch("jazzband.projects.tasks.github") as mock_github:
                mock_user_class.query.get.return_value = mock_user
                mock_project_class.query.get.return_value = mock_project

                # Mock successful responses
                mock_response = mocker.MagicMock()
                mock_response.status_code = 200
                mock_github.join_team.return_value = mock_response

                # Call the task
                add_user_to_team(user_id, project_id, is_lead)

                # Verify join_team was called twice (main team and leads team)
                assert mock_github.join_team.call_count == 2
                calls = mock_github.join_team.call_args_list
                assert calls[0][0] == ("test-project", "test-lead")
                assert calls[1][0] == ("test-project-leads", "test-lead")
```

## Code Style

### General Conventions
- Use **Black** for code formatting (max line length: 88 characters)
- Use **Ruff** for linting
- Follow **PEP 8** style guidelines
- Use type hints where appropriate

### Imports
- Standard library imports first
- Third-party imports second
- Local imports last
- Separate groups with blank line
- Alphabetize within groups

```python
import logging
from datetime import datetime

from flask import current_app
from flask_mail import Message

from ..account import github
from ..email import mail
```

### Flask CLI Commands

Commands follow this pattern:

```python
@click.command("command_name")
@click.argument("required_arg")
@click.option("--optional", "-o", default="value", help="Description")
@click_log.simple_verbosity_option(logger)
@with_appcontext
def command_name(required_arg, optional):
    """Command description for help text."""
    try:
        logger.info(f"Starting command with {required_arg}")
        result = do_something(required_arg, optional)
        print(f"✅ Success: {result}")
    except Exception as exc:
        logger.error(f"Failed: {exc}")
        print(f"❌ Failed: {exc}")
        raise
```

## Database Patterns

### Event Listeners

Use SQLAlchemy event listeners for automatic actions:

```python
@postgres.event.listens_for(Model, "after_insert")
def handle_insert(mapper, connection, target):
    """Called after a new row is inserted."""
    tasks.schedule(background_task, target.id)

@postgres.event.listens_for(Model, "after_update")
def handle_update(mapper, connection, target):
    """Called after a row is updated."""
    history = postgres.inspect(target).attrs.field_name.history
    if history.has_changes():
        old_value = history.deleted[0] if history.deleted else None
        new_value = target.field_name
        # Handle the change

@postgres.event.listens_for(Model, "after_delete")
def handle_delete(mapper, connection, target):
    """Called after a row is deleted."""
    tasks.schedule(cleanup_task, target.id)
```

### Migrations

- Run `flask db migrate -m "Description"` to create migrations
- Review generated migration before committing
- Test both upgrade and downgrade paths
- Migration naming: Use revision ID format (e.g., `d69ef951e45_.py`)

## Task Patterns

### Spinach Tasks

Background tasks using Spinach:

```python
@tasks.task(name="task_name")
def task_name(arg1, arg2):
    """Task description."""
    # Get database objects
    obj = Model.query.get(arg1)
    if not obj:
        logger.error(f"Object {arg1} not found")
        return

    # Do work
    result = do_something(obj, arg2)

    # Log results
    if result:
        logger.info(f"Successfully processed {obj}")
    else:
        logger.error(f"Failed to process {obj}")
```

### Scheduling Tasks

```python
# From event listener
tasks.schedule(task_name, arg1, arg2)

# From view/command
from ..tasks import spinach
spinach.schedule(task_name, arg1, arg2)

# Periodic task
@tasks.task(name="periodic_task", periodicity=timedelta(minutes=30))
def periodic_task():
    """Runs every 30 minutes."""
    pass
```

## Documentation

### Docstrings

Use clear, concise docstrings:

```python
def function_name(arg1: str, arg2: int = 0) -> bool:
    """
    One-line summary of what the function does.

    Longer description if needed, explaining the purpose,
    behavior, and any important details.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2 (default: 0)

    Returns:
        Description of return value
    """
    pass
```

### Comments

- Use comments to explain **why**, not **what**
- Complex logic should have explanatory comments
- TODO comments should include context: `# TODO: Explain why this needs to be done`

## Git Commit Messages

Follow conventional commit format:

```
type(scope): short description

Longer description if needed explaining:
- What changed
- Why it changed
- Any breaking changes

Fixes #issue-number
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

Examples:
- `feat(leads): add automatic leads team management`
- `fix(tasks): handle missing leads team gracefully`
- `test(leads): add comprehensive leads team test suite`
- `docs(agents): add testing patterns documentation`

## Common Pitfalls

### ❌ Don't Do This

```python
# Using unittest.mock instead of mocker
from unittest.mock import Mock, patch

# Using @patch decorator
@patch("module.something")
def test_function(mock_something):
    pass

# Class-based tests
class TestSomething:
    def test_method(self):
        pass
```

### ✅ Do This Instead

```python
# Use mocker fixture
def test_function(mocker):
    mock_obj = mocker.MagicMock()

# Use patch as context manager
def test_function(mocker):
    with patch("module.something") as mock_something:
        pass

# Function-based tests
def test_something(mocker):
    pass
```

## Resources

- **pytest documentation**: https://docs.pytest.org/
- **pytest-mock documentation**: https://pytest-mock.readthedocs.io/
- **Flask testing**: https://flask.palletsprojects.com/en/latest/testing/
- **GitHub API docs**: https://docs.github.com/en/rest

## Questions?

When in doubt:
1. Look at similar tests in `tests/` directory
2. Check `tests/conftest.py` for available fixtures
3. Follow the patterns in this document
4. Keep tests simple and focused on one thing

