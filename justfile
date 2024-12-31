@pre_commit:
    uv run ruff

@start:
    uv run ./manage.py runserver