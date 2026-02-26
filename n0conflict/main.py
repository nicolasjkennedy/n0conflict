from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

from . import __version__
from .conflict import has_conflicts, parse_conflicts
from .git import detect_language, get_conflicted_files
from .resolver import AIResolver

app = typer.Typer(
    name="n0conflict",
    help="AI-powered Git merge conflict resolver.",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_resolver() -> AIResolver:
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("N0CONFLICT_API_KEY")
    if not api_key:
        rprint(
            "[bold red]Error:[/] No API key found.\n"
            "Set [bold]ANTHROPIC_API_KEY[/] or [bold]N0CONFLICT_API_KEY[/] "
            "in your environment and try again."
        )
        raise typer.Exit(code=1)
    return AIResolver(api_key)


def _version_callback(value: bool) -> None:
    if value:
        rprint(f"n0conflict [bold cyan]v{__version__}[/]")
        raise typer.Exit()


# ---------------------------------------------------------------------------
# Global options
# ---------------------------------------------------------------------------

@app.callback()
def _callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    pass


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@app.command()
def resolve(
    file: Path = typer.Argument(..., help="File containing merge conflicts."),
    write: bool = typer.Option(False, "--write", "-w", help="Write resolved output back to the file."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview the resolved file without writing."),
) -> None:
    """Resolve merge conflicts in FILE using AI.

    By default the result is printed as a summary. Use [bold]--write[/] to
    save changes in place or [bold]--dry-run[/] to preview the full output.
    """
    if not file.exists():
        rprint(f"[bold red]Error:[/] File not found: {file}")
        raise typer.Exit(code=1)

    if not has_conflicts(file):
        rprint(f"[green]✓[/] No conflicts found in [bold]{file}[/]")
        return

    content = file.read_text(encoding="utf-8")
    conflicts = parse_conflicts(content)

    if not conflicts:
        rprint(f"[green]✓[/] No conflicts found in [bold]{file}[/]")
        return

    language = detect_language(file)
    resolver = _get_resolver()

    rprint(f"\n[bold]n0conflict[/] — [cyan]{file}[/]")
    rprint(f"  Found [yellow]{len(conflicts)}[/] conflict block(s)\n")

    resolved_content = content
    all_resolved = True

    for idx, conflict in enumerate(conflicts, start=1):
        with Progress(
            SpinnerColumn(),
            TextColumn(f"[progress.description]Resolving conflict {idx}/{len(conflicts)}..."),
            transient=True,
            console=console,
        ) as progress:
            progress.add_task("resolve", total=None)
            result = resolver.resolve(conflict, language=language)

        if result.resolved:
            rprint(f"  [green]✓[/] Conflict {idx}: {result.explanation}")
            resolved_content = resolved_content.replace(conflict.raw, result.content, 1)
        else:
            all_resolved = False
            rprint(f"  [red]✗[/] Conflict {idx}: cannot be resolved automatically")
            console.print(
                Panel(
                    result.explanation,
                    title="[red]Why it can't be resolved[/]",
                    border_style="red",
                )
            )

    if not all_resolved:
        rprint("\n[yellow]Some conflicts require manual resolution.[/]")
        return

    if dry_run:
        lexer = language.lower().split()[0] if language else "text"
        syntax = Syntax(resolved_content, lexer, theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"[green]Preview: {file}[/]", border_style="green"))
    elif write:
        file.write_text(resolved_content, encoding="utf-8")
        rprint(f"\n[bold green]✓[/] Written to [bold]{file}[/]")
    else:
        rprint(
            "\n[dim]Tip: use [bold]--write[/] to save changes or "
            "[bold]--dry-run[/] to preview the result.[/dim]"
        )


@app.command()
def scan(
    path: Path = typer.Argument(Path("."), help="Repository root to scan (default: current directory)."),
) -> None:
    """Scan a repository for all files containing merge conflicts."""
    # Prefer Git index (accurate) with a text-scan fallback.
    conflicted = get_conflicted_files(path)

    if not conflicted:
        conflicted = [
            f
            for f in path.rglob("*")
            if f.is_file()
            and not any(part.startswith(".") for part in f.parts)
            and has_conflicts(f)
        ]

    if not conflicted:
        rprint("[green]✓[/] No merge conflicts found.")
        return

    table = Table(
        title="Conflicted Files",
        show_header=True,
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("File", style="cyan", no_wrap=True)
    table.add_column("Conflicts", justify="right", style="yellow")

    for f in sorted(conflicted):
        try:
            count = len(parse_conflicts(f.read_text(encoding="utf-8", errors="replace")))
            table.add_row(str(f.relative_to(path)), str(count))
        except OSError:
            pass

    console.print(table)
    rprint(
        f"\n  Run [bold cyan]n0conflict resolve <file>[/] to resolve each conflict."
    )


@app.command()
def explain(
    file: Path = typer.Argument(..., help="File with merge conflicts to explain."),
) -> None:
    """Display the conflicting sections of FILE without resolving them."""
    if not file.exists():
        rprint(f"[bold red]Error:[/] File not found: {file}")
        raise typer.Exit(code=1)

    if not has_conflicts(file):
        rprint(f"[green]✓[/] No conflicts found in [bold]{file}[/]")
        return

    content = file.read_text(encoding="utf-8")
    conflicts = parse_conflicts(content)

    rprint(
        f"\n[bold]{len(conflicts)} conflict block(s)[/] in [cyan]{file}[/] "
        f"(lines {conflicts[0].start}–{conflicts[-1].end})\n"
    )

    for idx, conflict in enumerate(conflicts, start=1):
        console.print(
            Panel(
                f"[bold green]Ours[/]   [dim]({conflict.ours_label})[/]\n"
                f"[green]{conflict.ours.strip()}[/]\n\n"
                f"[bold red]Theirs[/] [dim]({conflict.theirs_label})[/]\n"
                f"[red]{conflict.theirs.strip()}[/]",
                title=f"[yellow]Conflict {idx}[/]  [dim]lines {conflict.start}–{conflict.end}[/]",
                border_style="yellow",
            )
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    app()


if __name__ == "__main__":
    main()
