@_default:
    just -l

@pre_commit:
    uv run ruff format
    uv run ruff check
    just test
    just update_readme

@run_initial_setup:
    uv run ./scripts/run_initial_setup.py

@start:
    uv run ./manage.py runserver

@test:
    uv run pytest .

@update_readme:
    uv run ./scripts/update_readme.py
