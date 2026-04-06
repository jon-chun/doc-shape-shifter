"""Command-line interface for doc-shape-shifter."""

import sys
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console(stderr=True)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("input_file", type=click.Path(exists=True), required=False)
@click.argument("output_file", type=click.Path(), required=False)
@click.option("-t", "--to", "target_format",
              help="Target format (pdf, docx, md, txt, html, json, csv, latex, epub, rtf)")
@click.option("-b", "--backend",
              help="Force a specific backend (pandoc, docling, pymupdf, markitdown, etc.)")
@click.option("--no-fallback", is_flag=True, default=False,
              help="Don't try alternate backends on failure")
@click.option("--list-backends", is_flag=True, default=False,
              help="List all backends with availability status")
@click.option("--list-formats", is_flag=True, default=False,
              help="List all supported conversion pairs")
@click.option("-v", "--verbose", count=True,
              help="Increase verbosity (-v for INFO, -vv for DEBUG)")
@click.version_option(package_name="doc-shape-shifter")
def main(
    input_file: str | None,
    output_file: str | None,
    target_format: str | None,
    backend: str | None,
    no_fallback: bool,
    list_backends: bool,
    list_formats: bool,
    verbose: int,
):
    """Doc-Shape-Shifter: Convert documents between formats intelligently.

    \b
    Examples:
        dss report.pdf report.md          # PDF to Markdown
        dss paper.tex --to docx           # LaTeX to Word
        dss data.csv --to json            # CSV to JSON
        dss doc.docx --to md -b pandoc    # Force Pandoc backend
        dss --list-backends               # Show installed backends
        dss --list-formats                # Show supported conversions
    """
    # Initialize logging
    from .utils.logging_config import setup_logging
    setup_logging(verbose)

    # --- Info commands (no input file needed) ---
    if list_backends:
        _show_backends()
        return

    if list_formats:
        _show_formats()
        return

    # --- Conversion requires input file ---
    if not input_file:
        console.print("[red]Error:[/] No input file specified. Use --help for usage.", highlight=False)
        console.print("  dss <input_file> [output_file] [--to FORMAT]", highlight=False)
        sys.exit(1)

    if not target_format and not output_file:
        console.print(
            "[red]Error:[/] Target format required. Specify output file or use --to.",
            highlight=False,
        )
        sys.exit(1)

    # --- Execute conversion ---
    from .converter import convert

    console.print(f"[bold]Converting:[/] {input_file}", highlight=False)

    result = convert(
        input_path=input_file,
        output_path=output_file,
        target_format=target_format,
        backend=backend,
        fallback=not no_fallback,
    )

    if result.success:
        size_str = _format_size(result.file_size_bytes) if result.file_size_bytes else "?"
        console.print(
            f"[green]Success:[/] {result.source_format} → {result.target_format} "
            f"via [bold]{result.backend_name}[/] "
            f"({result.duration_seconds:.2f}s, {size_str})",
            highlight=False,
        )
        console.print(f"[bold]Output:[/] {result.output_path}", highlight=False)

        for warning in result.warnings:
            console.print(f"[yellow]Warning:[/] {warning}", highlight=False)
    else:
        console.print(
            f"[red]Failed:[/] {result.source_format} → {result.target_format}",
            highlight=False,
        )
        console.print(f"[red]Error:[/] {result.error_message}", highlight=False)
        sys.exit(1)


def _show_backends():
    """Display a table of all backends and their availability."""
    from .backends import list_backends

    table = Table(title="Doc-Shape-Shifter Backends", show_lines=False)
    table.add_column("Backend", style="bold")
    table.add_column("Available", justify="center")
    table.add_column("Version")

    for name, available in list_backends():
        status = "[green]Yes[/]" if available else "[red]No[/]"
        # Get version info
        from .backends import get_backend
        try:
            be = get_backend(name)
            version = be.version_info()
        except Exception:
            version = "?"
        table.add_row(name, status, version)

    console.print(table)


def _show_formats():
    """Display all supported conversion pairs."""
    from .router import list_supported_conversions

    table = Table(title="Supported Conversions", show_lines=False)
    table.add_column("Source", style="bold cyan")
    table.add_column("Target", style="bold green")
    table.add_column("Backends (priority order)")

    for src, tgt, backends in list_supported_conversions():
        table.add_row(src, tgt, " → ".join(backends))

    console.print(table)
    console.print(
        f"\n[dim]Total: {len(list_supported_conversions())} conversion pairs defined[/]"
    )


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable units."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


if __name__ == "__main__":
    main()
