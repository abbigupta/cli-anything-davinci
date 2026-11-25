import json
from typing import Any

import click


def show(data: Any, machine: bool, *, failed: bool = False) -> None:
    if machine:
        click.echo(
            json.dumps(
                {"ok": not failed, "error" if failed else "data": data},
                ensure_ascii=False,
                allow_nan=False,
            )
        )
    elif failed:
        click.echo(f"Error [{data['code']}] {data['message']}", err=True)
        if data.get("details"):
            click.echo(
                json.dumps(data["details"], indent=2, ensure_ascii=False), err=True
            )
    elif isinstance(data, dict):
        for key, value in data.items():
            text = (
                json.dumps(value, indent=2, ensure_ascii=False)
                if isinstance(value, (dict, list))
                else str(value)
            )
            click.echo(f"{key}: {text}")
    else:
        for row in data:
            click.echo(
                json.dumps(row, ensure_ascii=False) if isinstance(row, dict) else row
            )
        if not data:
            click.echo("(empty)")
