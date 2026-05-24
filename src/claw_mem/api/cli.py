"""CLI for claw-mem API server."""

import click


@click.command()
@click.option("--host", default="localhost", help="Host to bind")
@click.option("--port", default=8080, type=int, help="Port to bind")
def serve(host: str, port: int) -> None:
    """Start claw-mem API server."""
    from claw_mem.api.server import run_server

    run_server(host, port)


@click.group()
def api() -> None:
    """API commands."""
    pass


api.add_command(serve)
