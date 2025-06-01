"""
Command Line Interface for MathTTS v3.

This module provides a CLI for processing LaTeX expressions
and converting them to speech.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infrastructure.config import get_settings, reload_settings
from infrastructure.logging import init_logger, get_logger
from infrastructure.persistence import MemoryPatternRepository
from infrastructure.cache import LRUCacheRepository
from adapters.pattern_loaders import YAMLPatternLoader
from adapters.tts_providers import EdgeTTSAdapter, TTSOptions, AudioFormat
from application.use_cases import ProcessExpressionUseCase
from application.dtos import ProcessExpressionRequest
from domain.services import PatternMatchingService
from domain.value_objects import LaTeXExpression, AudienceLevel, MathematicalDomain


console = Console()
logger = None


async def setup_application():
    """Setup application components."""
    global logger
    
    # Initialize logging
    logger = init_logger()
    logger.info("Starting MathTTS CLI")
    
    settings = get_settings()
    
    # Initialize repositories
    pattern_repo = MemoryPatternRepository()
    cache_repo = LRUCacheRepository(max_size=settings.cache.max_size)
    
    # Load patterns
    pattern_loader = YAMLPatternLoader(settings.patterns.patterns_dir)
    patterns = await pattern_loader.load_patterns()
    
    for pattern in patterns:
        await pattern_repo.add(pattern)
    
    logger.info(f"Loaded {len(patterns)} patterns")
    
    # Initialize TTS provider
    tts_provider = EdgeTTSAdapter()
    await tts_provider.initialize()
    
    # Initialize services
    pattern_service = PatternMatchingService(pattern_repo)
    
    # Initialize use case
    use_case = ProcessExpressionUseCase(
        pattern_matching_service=pattern_service,
        pattern_repository=pattern_repo,
        cache_repository=cache_repo
    )
    
    return {
        "use_case": use_case,
        "tts_provider": tts_provider,
        "pattern_repo": pattern_repo,
        "cache_repo": cache_repo
    }


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--config", type=click.Path(exists=True), help="Configuration file path")
@click.pass_context
def cli(ctx, debug: bool, config: Optional[str]):
    """MathTTS v3 - LaTeX to Speech Conversion Tool."""
    ctx.ensure_object(dict)
    
    if debug:
        console.print("[bold yellow]Debug mode enabled[/bold yellow]")
    
    if config:
        console.print(f"[blue]Using config file: {config}[/blue]")


@cli.command()
@click.argument("expression", type=str)
@click.option("--audience", type=click.Choice(["elementary", "middle_school", "high_school", "undergraduate", "research"]), 
              default="high_school", help="Target audience level")
@click.option("--domain", type=click.Choice(["algebra", "calculus", "linear_algebra", "topology", "complex_analysis"]), 
              help="Mathematical domain hint")
@click.option("--output", "-o", type=click.Path(), help="Save speech text to file")
@click.option("--speak", is_flag=True, help="Generate and play audio")
@click.option("--voice", default="en-US-AriaNeural", help="Voice ID for TTS")
def process(expression: str, audience: str, domain: Optional[str], output: Optional[str], speak: bool, voice: str):
    """Process a LaTeX expression and convert to speech text."""
    
    async def _process():
        try:
            console.print(f"[bold blue]Processing expression:[/bold blue] {expression}")
            
            # Setup application
            app_components = await setup_application()
            use_case = app_components["use_case"]
            tts_provider = app_components["tts_provider"]
            
            # Create request
            latex_expr = LaTeXExpression(expression)
            request = ProcessExpressionRequest(
                expression=latex_expr,
                audience_level=AudienceLevel(audience.upper()),
                domain=MathematicalDomain(domain.upper()) if domain else None,
                context="cli"
            )
            
            # Process expression
            with console.status("[bold green]Processing..."):
                result = await use_case.execute(request)
            
            # Display results
            console.print("\n[bold green]✓ Processing Complete[/bold green]")
            
            # Create results table
            table = Table(title="Processing Results")
            table.add_column("Property", style="cyan", no_wrap=True)
            table.add_column("Value", style="white")
            
            table.add_row("Original Expression", expression)
            table.add_row("Speech Text", result.speech_text.plain_text)
            table.add_row("Processing Time", f"{result.processing_time_ms:.2f} ms")
            table.add_row("Cached Result", "Yes" if result.cached else "No")
            table.add_row("Patterns Applied", str(result.patterns_applied))
            if result.domain_detected:
                table.add_row("Domain Detected", result.domain_detected.value)
            if result.complexity_score:
                table.add_row("Complexity Score", f"{result.complexity_score:.2f}")
            
            console.print(table)
            
            # Save to file if requested
            if output:
                Path(output).write_text(result.speech_text.plain_text)
                console.print(f"[green]Speech text saved to: {output}[/green]")
            
            # Generate audio if requested
            if speak:
                with console.status("[bold blue]Generating audio..."):
                    options = TTSOptions(
                        voice_id=voice,
                        format=AudioFormat.MP3
                    )
                    audio_data = await tts_provider.synthesize(result.speech_text, options)
                
                # Save audio to temporary file and play
                import tempfile
                import subprocess
                
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tmp.write(audio_data.data)
                    tmp_path = tmp.name
                
                console.print(f"[green]Audio generated ({audio_data.size_bytes} bytes)[/green]")
                console.print(f"[blue]Saved to: {tmp_path}[/blue]")
                
                # Try to play with system default player
                try:
                    if sys.platform.startswith('linux'):
                        subprocess.run(['xdg-open', tmp_path], check=True)
                    elif sys.platform == 'darwin':
                        subprocess.run(['open', tmp_path], check=True)
                    elif sys.platform == 'win32':
                        subprocess.run(['start', tmp_path], shell=True, check=True)
                except subprocess.CalledProcessError:
                    console.print("[yellow]Could not auto-play audio. File saved for manual playback.[/yellow]")
            
            # Cleanup
            await tts_provider.close()
            
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            if logger:
                logger.exception("CLI processing failed")
            sys.exit(1)
    
    asyncio.run(_process())


@cli.command()
@click.option("--language", help="Filter voices by language")
@click.option("--gender", type=click.Choice(["male", "female", "neutral"]), help="Filter by gender")
def voices(language: Optional[str], gender: Optional[str]):
    """List available TTS voices."""
    
    async def _list_voices():
        try:
            app_components = await setup_application()
            tts_provider = app_components["tts_provider"]
            
            with console.status("[bold green]Loading voices..."):
                voices = await tts_provider.list_voices(language=language)
            
            # Filter by gender if specified
            if gender:
                voices = [v for v in voices if v.gender.value.lower() == gender.lower()]
            
            # Create voices table
            table = Table(title=f"Available Voices ({len(voices)} total)")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="white")
            table.add_column("Language", style="green")
            table.add_column("Gender", style="magenta")
            table.add_column("Description", style="dim")
            
            for voice in voices:
                table.add_row(
                    voice.id,
                    voice.name,
                    voice.language,
                    voice.gender.value,
                    voice.description or ""
                )
            
            console.print(table)
            
            # Cleanup
            await tts_provider.close()
            
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)
    
    asyncio.run(_list_voices())


@cli.command()
@click.option("--domain", help="Filter patterns by domain")
def patterns(domain: Optional[str]):
    """List available conversion patterns."""
    
    async def _list_patterns():
        try:
            app_components = await setup_application()
            pattern_repo = app_components["pattern_repo"]
            
            with console.status("[bold green]Loading patterns..."):
                all_patterns = await pattern_repo.get_all()
            
            # Filter by domain if specified
            if domain:
                all_patterns = [p for p in all_patterns if p.domain.value.lower() == domain.lower()]
            
            # Create patterns table
            table = Table(title=f"Available Patterns ({len(all_patterns)} total)")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Pattern", style="white", max_width=30)
            table.add_column("Domain", style="green")
            table.add_column("Priority", style="magenta")
            table.add_column("Description", style="dim", max_width=40)
            
            for pattern in sorted(all_patterns, key=lambda p: p.priority.value, reverse=True):
                table.add_row(
                    pattern.id,
                    pattern.pattern[:30] + "..." if len(pattern.pattern) > 30 else pattern.pattern,
                    pattern.domain.value,
                    str(pattern.priority.value),
                    pattern.description or ""
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)
    
    asyncio.run(_list_patterns())


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--output-dir", "-o", type=click.Path(), help="Output directory for results")
def batch(file: str, output_dir: Optional[str]):
    """Process multiple expressions from a file."""
    
    async def _batch_process():
        try:
            # Read expressions from file
            expressions = []
            with open(file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        expressions.append((line_num, line))
            
            console.print(f"[blue]Processing {len(expressions)} expressions from {file}[/blue]")
            
            # Setup application
            app_components = await setup_application()
            use_case = app_components["use_case"]
            
            # Process each expression
            results = []
            for line_num, expression in expressions:
                try:
                    console.print(f"[dim]Processing line {line_num}...[/dim]")
                    
                    latex_expr = LaTeXExpression(expression)
                    request = ProcessExpressionRequest(
                        expression=latex_expr,
                        audience_level=AudienceLevel.HIGH_SCHOOL,
                        context="batch"
                    )
                    
                    result = await use_case.execute(request)
                    
                    results.append({
                        "line": line_num,
                        "expression": expression,
                        "speech_text": result.speech_text.plain_text,
                        "processing_time_ms": result.processing_time_ms,
                        "cached": result.cached,
                        "patterns_applied": result.patterns_applied
                    })
                    
                except Exception as e:
                    console.print(f"[red]Error on line {line_num}: {e}[/red]")
                    results.append({
                        "line": line_num,
                        "expression": expression,
                        "error": str(e)
                    })
            
            # Save results
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(exist_ok=True)
                
                results_file = output_path / "batch_results.json"
                with open(results_file, 'w') as f:
                    json.dump(results, f, indent=2)
                
                console.print(f"[green]Results saved to: {results_file}[/green]")
            
            # Display summary
            successful = len([r for r in results if "error" not in r])
            failed = len(results) - successful
            
            console.print(f"\n[bold green]Batch processing complete:[/bold green]")
            console.print(f"  ✓ Successful: {successful}")
            console.print(f"  ✗ Failed: {failed}")
            
        except Exception as e:
            console.print(f"[bold red]Batch processing error:[/bold red] {e}")
            sys.exit(1)
    
    asyncio.run(_batch_process())


@cli.command()
def config():
    """Show current configuration."""
    settings = get_settings()
    
    config_data = {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.environment.value,
        "debug": settings.debug,
        "log_level": settings.log_level.value,
        "cache": {
            "type": settings.cache.type,
            "max_size": settings.cache.max_size,
            "ttl_seconds": settings.cache.ttl_seconds
        },
        "tts": {
            "default_provider": settings.tts.default_provider.value,
            "default_voice": settings.tts.default_voice
        },
        "patterns": {
            "patterns_dir": str(settings.patterns.patterns_dir),
            "auto_reload": settings.patterns.auto_reload
        }
    }
    
    # Display as syntax-highlighted JSON
    syntax = Syntax(json.dumps(config_data, indent=2), "json", theme="monokai", line_numbers=True)
    panel = Panel(syntax, title="Current Configuration", border_style="blue")
    console.print(panel)


if __name__ == "__main__":
    cli()