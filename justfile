@pre_commit:
    uv run ruff format
    uv run ruff check

@start:
    uv run ./manage.py runserver

@run_initial_setup:
    uv run ./scripts/run_initial_setup.py
