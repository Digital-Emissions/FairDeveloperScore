# Coding Style Guide

## Overview
This document defines the coding standards and conventions for the devProductivity project. All contributors must follow these guidelines to maintain code consistency and readability.

## General Principles
- **Readability counts**: Code is read more often than it is written
- **Consistency**: Follow established patterns within the codebase
- **Simplicity**: Prefer simple, clear solutions over complex ones
- **Documentation**: Code should be self-documenting with clear naming

## File and Directory Naming

### Python Files
- Use **snake_case** for all Python files
- Use lowercase letters with underscores to separate words
- Be descriptive but concise

```
✅ Good:
user_authentication.py
database_connection.py
github_api_client.py
data_processor.py

❌ Bad:
UserAuthentication.py
databaseConnection.py
GitHubAPIClient.py
dataProcessor.py
```

### Directory Names
- Use **snake_case** for directory names
- Keep names short but descriptive

```
✅ Good:
user_management/
api_clients/
data_processing/
test_utilities/

❌ Bad:
UserManagement/
APIClients/
dataProcessing/
TestUtilities/
```

### Configuration Files
- Use **snake_case** for configuration files
- Include file extension

```
✅ Good:
database_config.yaml
app_settings.json
docker_compose.yml

❌ Bad:
DatabaseConfig.yaml
AppSettings.json
DockerCompose.yml
```

## Python Code Style

### Variable and Function Names
- Use **snake_case** for variables and functions
- Use descriptive names that explain purpose

```python
# ✅ Good
user_name = "john_doe"
total_count = 0

def calculate_average_score(scores):
    return sum(scores) / len(scores)

def fetch_user_data(user_id):
    pass

# ❌ Bad
userName = "john_doe"
totalCount = 0

def calculateAverageScore(scores):
    return sum(scores) / len(scores)

def fetchUserData(userId):
    pass
```

### Class Names
- Use **PascalCase** for class names
- Use descriptive nouns

```python
# ✅ Good
class UserManager:
    pass

class DatabaseConnection:
    pass

class GitHubAPIClient:
    pass

# ❌ Bad
class userManager:
    pass

class database_connection:
    pass

class githubAPIClient:
    pass
```

### Constants
- Use **UPPER_SNAKE_CASE** for constants
- Define at module level

```python
# ✅ Good
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30
API_BASE_URL = "https://api.github.com"

# ❌ Bad
maxRetryAttempts = 3
defaultTimeout = 30
apiBaseUrl = "https://api.github.com"
```

### Import Statements
- Group imports in this order:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports
- Use absolute imports when possible
- One import per line

```python
# ✅ Good
import os
import sys
from datetime import datetime

import requests
import pandas as pd
from django.conf import settings

from .models import User
from .utils import calculate_score

# ❌ Bad
import os, sys
from datetime import datetime
import requests, pandas as pd
from django.conf import settings
from .models import User
from .utils import calculate_score
```

## Code Formatting

### Line Length
- Maximum line length: **88 characters** (Black formatter standard)
- Break long lines using parentheses or backslashes

```python
# ✅ Good
result = some_function(
    parameter_one,
    parameter_two,
    parameter_three,
)

# ✅ Also good
result = (
    some_very_long_variable_name
    + another_very_long_variable_name
    + yet_another_long_name
)
```

### Indentation
- Use **4 spaces** for indentation
- No tabs allowed
- Consistent indentation throughout

### Blank Lines
- Two blank lines between top-level functions and classes
- One blank line between methods in a class
- Use blank lines sparingly within functions

```python
# ✅ Good
class UserManager:
    def __init__(self):
        self.users = []

    def add_user(self, user):
        self.users.append(user)


class DatabaseConnection:
    def __init__(self):
        self.connection = None
```

### Whitespace
- No trailing whitespace
- One space around operators
- No space before commas, colons, semicolons
- One space after commas, colons, semicolons

```python
# ✅ Good
x = 1
y = 2
result = x + y
my_list = [1, 2, 3, 4]
my_dict = {"key": "value"}

# ❌ Bad
x=1
y=2
result=x+y
my_list = [1,2,3,4]
my_dict = {"key":"value"}
```

## Comments and Documentation

### Comments
- Use `#` for single-line comments
- Comments should explain "why", not "what"
- Keep comments up-to-date with code changes

```python
# ✅ Good
# Calculate compound interest to account for inflation
final_amount = principal * (1 + rate) ** years

# ❌ Bad
# Multiply principal by rate plus one raised to years power
final_amount = principal * (1 + rate) ** years
```

### Docstrings
- Use triple quotes for docstrings
- Follow Google or NumPy docstring style
- Include parameters, return values, and exceptions

```python
# ✅ Good
def calculate_compound_interest(principal, rate, years):
    """
    Calculate compound interest for given principal, rate, and time period.
    
    Args:
        principal (float): Initial amount of money
        rate (float): Annual interest rate (as decimal)
        years (int): Number of years
    
    Returns:
        float: Final amount after compound interest
    
    Raises:
        ValueError: If any parameter is negative
    """
    if principal < 0 or rate < 0 or years < 0:
        raise ValueError("All parameters must be non-negative")
    
    return principal * (1 + rate) ** years
```

## Error Handling

### Exception Handling
- Use specific exception types
- Include meaningful error messages
- Don't use bare `except:` clauses

```python
# ✅ Good
try:
    result = api_call()
except requests.ConnectionError as e:
    logger.error(f"Failed to connect to API: {e}")
    raise
except requests.Timeout as e:
    logger.error(f"API request timed out: {e}")
    raise

# ❌ Bad
try:
    result = api_call()
except:
    print("Something went wrong")
```

### Logging
- Use Python's `logging` module
- Include appropriate log levels
- Use structured logging with context

```python
# ✅ Good
import logging

logger = logging.getLogger(__name__)

def process_user_data(user_id):
    logger.info(f"Processing data for user {user_id}")
    try:
        data = fetch_user_data(user_id)
        logger.debug(f"Fetched {len(data)} records for user {user_id}")
        return process_data(data)
    except Exception as e:
        logger.error(f"Failed to process user {user_id}: {e}")
        raise
```

## Django-Specific Guidelines

### Model Names
- Use singular nouns in PascalCase
- Be descriptive and clear

```python
# ✅ Good
class User(models.Model):
    pass

class ProjectCommit(models.Model):
    pass

# ❌ Bad
class Users(models.Model):
    pass

class project_commit(models.Model):
    pass
```

### View Names
- Use descriptive function names in snake_case
- Include HTTP method in name when appropriate

```python
# ✅ Good
def user_list_view(request):
    pass

def create_project_commit(request):
    pass

def update_user_profile(request):
    pass
```

### URL Patterns
- Use lowercase with hyphens for URL paths
- Be RESTful when possible

```python
# ✅ Good
urlpatterns = [
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('projects/<int:project_id>/commits/', views.project_commits, name='project_commits'),
]
```

## Database Guidelines

### Table Names
- Use snake_case for table names
- Use plural nouns

```sql
-- ✅ Good
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL
);

CREATE TABLE project_commits (
    id SERIAL PRIMARY KEY,
    commit_hash VARCHAR(40) NOT NULL
);
```

### Column Names
- Use snake_case for column names
- Be descriptive and consistent

```sql
-- ✅ Good
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email_address VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Git Commit Guidelines

### Commit Messages
- Use imperative mood in subject line
- Keep subject line under 50 characters
- Include body for complex changes

```
# ✅ Good
Add user authentication middleware

Implement JWT-based authentication system with refresh tokens.
Includes middleware for automatic token validation and user
context injection.

# ❌ Bad
added auth stuff
```

### Branch Names
- Use snake_case or kebab-case
- Include issue number when applicable

```
# ✅ Good
feature/user_authentication
bugfix/database_connection_timeout
hotfix/security_vulnerability_123

# ❌ Bad
Feature/UserAuthentication
BugFix/DatabaseConnectionTimeout
```

## Testing Guidelines

### Test File Names
- Use `test_` prefix for test files
- Mirror the structure of source files

```
# ✅ Good
src/
  user_manager.py
  database_connection.py
tests/
  test_user_manager.py
  test_database_connection.py
```

### Test Function Names
- Use descriptive names that explain what is being tested
- Use `test_` prefix

```python
# ✅ Good
def test_user_creation_with_valid_data():
    pass

def test_user_creation_fails_with_invalid_email():
    pass

def test_database_connection_timeout_handling():
    pass
```

## Tools and Automation

### Code Formatting
- Use **Black** for code formatting
- Use **isort** for import sorting
- Configuration in `pyproject.toml`

### Linting
- Use **flake8** for linting
- Use **mypy** for type checking
- Fix all linting errors before committing

### Pre-commit Hooks
- Install pre-commit hooks to enforce standards
- Include formatting, linting, and testing

## Project Structure

```
devProductivity/
├── src/
│   ├── user_management/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   └── utils.py
│   ├── api_clients/
│   │   ├── __init__.py
│   │   ├── github_client.py
│   │   └── base_client.py
│   └── data_processing/
│       ├── __init__.py
│       ├── commit_analyzer.py
│       └── metrics_calculator.py
├── tests/
│   ├── test_user_management/
│   └── test_api_clients/
├── docs/
├── requirements.txt
├── docker_compose.yml
└── README.md
```

## Enforcement

### Code Reviews
- All code must be reviewed before merging
- Reviewers should check for style compliance
- Use automated tools in CI/CD pipeline

### Continuous Integration
- Run linting and formatting checks on every commit
- Fail builds that don't meet standards
- Include test coverage requirements

---

**Remember**: These guidelines exist to make our code more readable, maintainable, and consistent. When in doubt, prioritize clarity and consistency over personal preference. 