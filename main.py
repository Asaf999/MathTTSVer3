"""
Main entry point for MathTTS v3.

This script provides multiple ways to run the application:
- Web API server
- CLI interface
- Development server with auto-reload
"""

import sys
import asyncio
from pathlib import Path
import click

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.infrastructure.config import get_settings
from src.infrastructure.logging import init_logger


@click.group()
def main():
    """MathTTS v3 - LaTeX to Speech Conversion System."""
    pass


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--workers", default=1, help="Number of worker processes")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def api(host: str, port: int, workers: int, reload: bool):
    """Start the API server."""
    import uvicorn
    
    # Initialize logging
    init_logger()
    
    settings = get_settings()
    
    # Override settings from CLI args
    actual_host = host if host != "0.0.0.0" else settings.api.host
    actual_port = port if port != 8000 else settings.api.port
    actual_workers = workers if workers != 1 else settings.api.workers
    
    click.echo(f"Starting MathTTS API server on {actual_host}:{actual_port}")
    click.echo(f"Environment: {settings.environment.value}")
    click.echo(f"Debug mode: {settings.debug}")
    
    uvicorn.run(
        "src.presentation.api.app:app",
        host=actual_host,
        port=actual_port,
        workers=actual_workers if not reload else 1,
        reload=reload,
        log_level=settings.log_level.value.lower(),
        access_log=True
    )


@main.command()
@click.pass_context
def cli(ctx):
    """Start the CLI interface."""
    from src.presentation.cli.main import cli as cli_app
    
    # Initialize logging
    init_logger()
    
    # Pass through any additional arguments
    sys.argv = ["mathtts"] + sys.argv[2:]  # Remove 'main.py cli' from argv
    cli_app()


@main.command()
def version():
    """Show version information."""
    settings = get_settings()
    
    click.echo(f"MathTTS v{settings.app_version}")
    click.echo(f"Environment: {settings.environment.value}")
    
    # Show component versions
    try:
        import fastapi
        click.echo(f"FastAPI: {fastapi.__version__}")
    except ImportError:
        click.echo("FastAPI: Not installed")
    
    try:
        import edge_tts
        click.echo("Edge-TTS: Available")
    except ImportError:
        click.echo("Edge-TTS: Not installed")
    
    try:
        import pydantic
        click.echo(f"Pydantic: {pydantic.__version__}")
    except ImportError:
        click.echo("Pydantic: Not installed")


@main.command()
def health():
    """Check application health."""
    
    async def _health_check():
        try:
            # Import after path setup
            from src.presentation.api.dependencies import startup_event
            from src.adapters.tts_providers import EdgeTTSAdapter
            from src.infrastructure.persistence import MemoryPatternRepository
            
            click.echo("Checking application health...")
            
            # Test basic imports
            click.echo("✓ Core modules imported successfully")
            
            # Test configuration
            settings = get_settings()
            click.echo(f"✓ Configuration loaded (env: {settings.environment.value})")
            
            # Test pattern loading
            try:
                from src.adapters.pattern_loaders import YAMLPatternLoader
                loader = YAMLPatternLoader(settings.patterns.patterns_dir)
                patterns = await loader.load_patterns()
                click.echo(f"✓ Patterns loaded ({len(patterns)} patterns)")
            except Exception as e:
                click.echo(f"✗ Pattern loading failed: {e}")
                return False
            
            # Test TTS provider
            try:
                tts = EdgeTTSAdapter()
                await tts.initialize()
                if tts.is_available():
                    click.echo("✓ TTS provider available")
                else:
                    click.echo("✗ TTS provider not available")
                await tts.close()
            except Exception as e:
                click.echo(f"✗ TTS provider failed: {e}")
                return False
            
            click.echo("✓ All health checks passed")
            return True
            
        except Exception as e:
            click.echo(f"✗ Health check failed: {e}")
            return False
    
    success = asyncio.run(_health_check())
    if not success:
        sys.exit(1)


@main.command()
def setup():
    """Setup the application (create directories, check dependencies)."""
    settings = get_settings()
    
    click.echo("Setting up MathTTS v3...")
    
    # Create directories
    directories = [
        settings.patterns.patterns_dir,
        Path("logs"),
        Path("data"),
        Path("cache")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        click.echo(f"✓ Created directory: {directory}")
    
    # Check dependencies
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "structlog",
        "click",
        "rich",
        "edge-tts"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            click.echo(f"✓ {package}")
        except ImportError:
            click.echo(f"✗ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        click.echo(f"\nMissing packages: {', '.join(missing_packages)}")
        click.echo("Install them with: pip install " + " ".join(missing_packages))
        sys.exit(1)
    else:
        click.echo("\n✓ All dependencies satisfied")
        click.echo("✓ Setup complete")


if __name__ == "__main__":
    main()