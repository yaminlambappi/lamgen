# Naming Conventions

This document outlines the naming conventions used in the project.

## Project Structure

- **`apps/`**: Contains all Django applications. Each application is a self-contained module with a specific functionality.
- **`config/`**: Contains project-level configuration files, such as settings, URLs, and WSGI/ASGI configurations.
- **`static/`**: Contains static files (CSS, JavaScript, images).
- **`templates/`**: Contains base templates and templates for project-level pages.
- **`scripts/`**: Contains utility scripts for various tasks.
- **`tests/`**: Contains project-level tests.

## Django Apps

Each Django app in the `apps/` directory follows this structure:

- **`admin/`**: Django admin configurations.
- **`api/`**: API-related files (e.g., serializers, views).
- **`models/`**: Database models.
- **`selectors/`**: Business logic for retrieving data.
- **`services/`**: Business logic for modifying data.
- **`tasks/`**: Celery tasks.
- **`templates/`**: App-specific templates.
- **`tests/`**: App-specific tests.
- **`utils/`**: Utility functions.

## File Naming

- **Python files**: Use snake_case (e.g., `views.py`, `models.py`).
- **Test files**: Prefixed with `test_` (e.g., `test_views.py`).
- **Template files**: Use kebab-case or snake_case (e.g., `my-template.html`, `base.html`).
