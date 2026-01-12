"""Gmail MCP CLI commands.

Provides commands for:
- serve: Start the MCP server
- health: Check configuration status
- connections: Manage Gmail connections
- init: Create configuration file
- migrate: Run database migrations
"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="gmail-mcp",
    help="Gmail Multi-User MCP Server CLI",
    add_completion=False,
)

console = Console()


@app.command()
def serve(
    transport: str = typer.Option(
        "stdio",
        "--transport",
        "-t",
        help="Transport mode (stdio or http)",
    ),
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        "-h",
        help="Host to bind (for http transport)",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to bind (for http transport)",
    ),
    config: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug logging",
    ),
    log_format: str = typer.Option(
        "auto",
        "--log-format",
        help="Log format: json, human, or auto",
    ),
) -> None:
    """Start the MCP server.

    The server can run in two transport modes:
    - stdio: For use with Claude Desktop and other MCP clients (default)
    - http: For remote access and testing
    """
    import os

    if config:
        os.environ["GMAIL_MCP_CONFIG"] = config

    # Configure structured logging
    from gmail_multi_user.logging import configure_logging

    log_level = "DEBUG" if debug else "INFO"
    json_format = None if log_format == "auto" else (log_format == "json")
    configure_logging(level=log_level, json_format=json_format)

    from gmail_mcp_server.server import mcp

    console.print("[green]Starting Gmail MCP Server[/green]")
    console.print(f"Transport: {transport}")

    if transport == "http":
        console.print(f"Listening on: http://{host}:{port}")
        mcp.run(transport="http", host=host, port=port)
    else:
        console.print("Running in stdio mode...")
        mcp.run(transport="stdio")


@app.command()
def health() -> None:
    """Check configuration status and health.

    Verifies:
    - Configuration file is found
    - Database is connected
    - Google OAuth is configured
    - Encryption key is set
    """

    async def check_health() -> None:
        from gmail_mcp_server.tools.setup import check_setup_impl

        console.print("[bold]Gmail MCP Health Check[/bold]\n")

        status = await check_setup_impl()

        # Config status
        if status["config_found"]:
            console.print(f"[green]✓[/green] Config found: {status['config_path']}")
        else:
            console.print("[red]✗[/red] Config not found")

        # Database status
        if status["database_connected"]:
            console.print(
                f"[green]✓[/green] Database connected ({status['database_type']})"
            )
        else:
            console.print(
                f"[red]✗[/red] Database not connected ({status['database_type']})"
            )

        # OAuth status
        if status["google_oauth_configured"]:
            console.print("[green]✓[/green] Google OAuth configured")
        else:
            console.print("[red]✗[/red] Google OAuth not configured")

        # Encryption status
        if status["encryption_key_set"]:
            console.print("[green]✓[/green] Encryption key set")
        else:
            console.print("[red]✗[/red] Encryption key not set")

        # Issues
        if status["issues"]:
            console.print("\n[yellow]Issues:[/yellow]")
            for issue in status["issues"]:
                console.print(f"  - {issue}")

        # Overall status
        console.print()
        if status["ready"]:
            console.print("[green bold]System is ready![/green bold]")
        else:
            console.print("[red bold]System is not ready[/red bold]")
            console.print("Run 'gmail-mcp init' to create configuration")

    asyncio.run(check_health())


# Connections subcommand group
connections_app = typer.Typer(help="Manage Gmail connections")
app.add_typer(connections_app, name="connections")


@connections_app.command("list")
def connections_list(
    user_id: str | None = typer.Option(
        None,
        "--user-id",
        "-u",
        help="Filter by user ID",
    ),
    include_inactive: bool = typer.Option(
        False,
        "--include-inactive",
        "-i",
        help="Include inactive connections",
    ),
) -> None:
    """List Gmail connections."""

    async def list_connections() -> None:
        from gmail_mcp_server.tools.auth import list_connections_impl

        result = await list_connections_impl(
            user_id=user_id,
            include_inactive=include_inactive,
        )

        connections = result["connections"]

        if not connections:
            console.print("No connections found.")
            return

        table = Table(title="Gmail Connections")
        table.add_column("ID", style="cyan")
        table.add_column("User ID")
        table.add_column("Gmail Address", style="green")
        table.add_column("Active")
        table.add_column("Last Used")

        for conn in connections:
            table.add_row(
                conn["id"][:12] + "...",
                conn["user_id"] or "-",
                conn["gmail_address"],
                "✓" if conn["is_active"] else "✗",
                conn["last_used_at"] or "Never",
            )

        console.print(table)

    asyncio.run(list_connections())


@connections_app.command("revoke")
def connections_revoke(
    connection_id: str = typer.Argument(..., help="Connection ID to revoke"),
    no_google_revoke: bool = typer.Option(
        False,
        "--no-google-revoke",
        help="Don't revoke access at Google",
    ),
) -> None:
    """Revoke a Gmail connection."""

    async def revoke_connection() -> None:
        from gmail_mcp_server.tools.auth import disconnect_impl

        result = await disconnect_impl(
            connection_id=connection_id,
            revoke_google_access=not no_google_revoke,
        )

        if result["success"]:
            console.print(f"[green]✓[/green] Disconnected {result['gmail_address']}")
        else:
            console.print(
                f"[red]✗[/red] Failed to disconnect: {result.get('error', 'Unknown error')}"
            )

    asyncio.run(revoke_connection())


@connections_app.command("test")
def connections_test(
    connection_id: str = typer.Argument(..., help="Connection ID to test"),
) -> None:
    """Test a Gmail connection."""

    async def test_connection() -> None:
        from gmail_mcp_server.tools.auth import check_connection_impl

        result = await check_connection_impl(connection_id=connection_id)

        console.print(f"\n[bold]Connection: {connection_id}[/bold]\n")

        if result["valid"]:
            console.print("[green]✓[/green] Valid")
        else:
            console.print("[red]✗[/red] Invalid")

        console.print(f"Gmail: {result['gmail_address']}")
        console.print(f"Scopes: {', '.join(result['scopes'])}")

        if result["token_expires_in"]:
            console.print(f"Token expires in: {result['token_expires_in']}s")

        if result["needs_reauth"]:
            console.print("[yellow]Needs re-authorization[/yellow]")

        if result["error"]:
            console.print(f"[red]Error: {result['error']}[/red]")

    asyncio.run(test_connection())


@app.command()
def init(
    database: str = typer.Option(
        "sqlite",
        "--database",
        "-d",
        help="Database type (sqlite or supabase)",
    ),
    output: str = typer.Option(
        "./gmail_config.yaml",
        "--output",
        "-o",
        help="Output path for config file",
    ),
) -> None:
    """Create a gmail_config.yaml configuration file.

    This creates a template config file that you can customize with your
    Google OAuth credentials and storage settings.
    """

    async def create_config() -> None:
        from gmail_mcp_server.tools.setup import init_config_impl

        result = await init_config_impl(
            database_type=database,
            output_path=output,
        )

        console.print(f"[green]✓[/green] Config created: {result['config_path']}")

        if result.get("encryption_key"):
            console.print("\n[yellow]Encryption key generated[/yellow]")
            console.print("(Already saved in config file)")

        console.print("\n[bold]Next steps:[/bold]")
        for i, step in enumerate(result["next_steps"], 1):
            console.print(f"  {i}. {step}")

    asyncio.run(create_config())


@app.command()
def migrate(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be applied without running",
    ),
) -> None:
    """Run database migrations.

    For SQLite: Tables are created automatically.
    For Supabase: Shows instructions for manual migration.
    """

    async def run_migrations() -> None:
        from gmail_mcp_server.tools.setup import run_migrations_impl

        if dry_run:
            console.print("[yellow]Dry run - no changes will be made[/yellow]\n")

        result = await run_migrations_impl()

        if result.get("migrations_run"):
            console.print("[green]Migrations applied:[/green]")
            for m in result["migrations_run"]:
                console.print(f"  - {m}")

        if result.get("already_applied"):
            console.print("[blue]Already applied:[/blue]")
            for m in result["already_applied"]:
                console.print(f"  - {m}")

        if result.get("current_version"):
            console.print(f"\nCurrent version: {result['current_version']}")

        if result.get("message"):
            console.print(f"\n{result['message']}")

    asyncio.run(run_migrations())


@app.command()
def validate() -> None:
    """Validate configuration file.

    Checks for:
    - Valid encryption key
    - Google OAuth credentials
    - Storage configuration
    - Common misconfigurations
    """
    from gmail_multi_user.config import ConfigLoader

    console.print("[bold]Gmail MCP Configuration Validation[/bold]\n")

    result = ConfigLoader.validate()

    # Show issues
    errors = [i for i in result.issues if i.severity == "error"]
    warnings_issues = [i for i in result.issues if i.severity == "warning"]

    if errors:
        console.print("[red bold]Errors:[/red bold]")
        for issue in errors:
            console.print(f"[red]  ✗ {issue.field}:[/red] {issue.message}")
            if issue.suggestion:
                console.print(f"    [dim]→ {issue.suggestion}[/dim]")
        console.print()

    if warnings_issues:
        console.print("[yellow bold]Warnings:[/yellow bold]")
        for issue in warnings_issues:
            console.print(f"[yellow]  ⚠ {issue.field}:[/yellow] {issue.message}")
            if issue.suggestion:
                console.print(f"    [dim]→ {issue.suggestion}[/dim]")
        console.print()

    if result.warnings:
        console.print("[blue bold]Notes:[/blue bold]")
        for warning in result.warnings:
            console.print(f"  • {warning}")
        console.print()

    # Summary
    if result.valid:
        console.print("[green bold]✓ Configuration is valid[/green bold]")
    else:
        console.print("[red bold]✗ Configuration has errors[/red bold]")
        raise typer.Exit(code=1)


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
