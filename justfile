@pre_commit:
    uv run ruff format
    uv run ruff check

@run_initial_setup:
    uv run ./scripts/run_initial_setup.py

@start:
    uv run ./manage.py runserver


@test:
    uv run pytest .
