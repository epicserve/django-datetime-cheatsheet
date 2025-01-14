import json
import logging
import os
import random
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)


def get_random_string(length):
    return "".join(
        random.SystemRandom().choice(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        )
        for _ in range(length)
    )


def is_op_installed():
    try:
        subprocess.run(["op", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_op_item_by_tag(tag):
    command = ["op", "item", "list", "--tags", tag, "--format", "json"]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    items = json.loads(result.stdout)
    num_items = len(items)
    if num_items == 1:
        get_command = ["op", "item", "get", items[0]["id"], "--format", "json"]
        detail_result = subprocess.run(
            get_command, capture_output=True, text=True, check=True
        )

        result = json.loads(detail_result.stdout)
        rtv_val = {}
        for field in result["fields"]:
            key = field.get("label", field.get("id", "No id or label"))
            val = field.get("value", "")
            rtv_val[key] = val

        return rtv_val

    if num_items == 0:
        log.debug(f"No items found with tag {tag}")

    if num_items > 1:
        log.debug(
            f"WARNING: Multiple items found with tag {tag}: {', '.join([item['title'] for item in items])}"
        )

    return None


def get_input(question, /, *, default: str = "", required: bool = False):
    default_prompt_value = ""
    if default:
        default_prompt_value = f" [{default}]"
    resp = input(f"{question}{default_prompt_value}: ")
    if default and not resp:
        resp = default

    if not resp and required is True:
        resp = get_input(question, default=default, required=required)

    return resp


def get_superuser():
    if is_op_installed() is True:
        data = get_op_item_by_tag("superuser")
        email = data.get("email", "")
        username = data.get("username", "")
        password = data.get("password", "")
    else:
        print(
            "\n"
            "NOTE:\n"
            'If the 1Password CLI is installed and add an item with the tag "superuser" exists with\n'
            "your email address as your username and a password, then a Django superuser will\n"
            "be created for you without any prompts.\n"
        )
        email = get_input("Please enter your email address", required=True)
        username = get_input("Please enter your username", default=email, required=True)
        password = get_input("Please enter your password", required=True)

    return {
        "email": email,
        "username": username,
        "password": password,
    }


if __name__ == "__main__":
    env_file = Path(".env")
    if env_file.exists() is True:
        backup_env_file = Path(f".env.{datetime.now().strftime('%Y%m%d%H%M%S')}")
        # copy env_file contents to backup_env_file
        shutil.copy(env_file, backup_env_file)
        env_file.unlink()

    env_file_content = (
        "DEBUG=on\n"
        f"SECRET_KEY={get_random_string(50)}\n"
        "ALLOWED_HOSTS=127.0.0.1,0.0.0.0,localhost\n"
        "DATABASE_URL=sqlite:///db.sqlite3?transaction_mode=IMMEDIATE&init_command=PRAGMA+journal_mode+%3D+WAL%3BPRAGMA+synchronous+%3D+NORMAL%3BPRAGMA+mmap_size+%3D+134217728%3BPRAGMA+journal_size_limit+%3D+27103364%3BPRAGMA+cache_size+%3D+2000\n"
    )
    env_file.write_text(env_file_content)
    os.system("uv run manage.py migrate")

    data = get_superuser()
    os.system(
        f"DJANGO_SUPERUSER_EMAIL={data['username']} DJANGO_SUPERUSER_USERNAME={data['username']} DJANGO_SUPERUSER_PASSWORD={data['password']} uv run manage.py createsuperuser --noinput"
    )
