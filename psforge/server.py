"""PSForge MCP Server - Main entry point."""

import asyncio
import sys

from loguru import logger
from mcp.server import Server
from mcp.server.stdio import stdio_server

from psforge.app import __app_name__, __version__
from psforge.registry import discover_and_register_resources, discover_and_register_tools


def setup_logging():
    """Configure logging with loguru."""
    logger.remove()  # Remove default handler

    # Add stderr handler for general logging
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    )

    # Add file handler for detailed debug logs
    logger.add(
        "psforge_debug.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
    )


async def main():
    """Main entry point for PSForge MCP Server."""
    setup_logging()

    logger.info(f"Starting {__app_name__} v{__version__}")
    logger.info("Photoshop MCP Server - AI-Powered Automation")

    # Create MCP server
    mcp = Server(__app_name__)

    # Discover and register all tools
    logger.info("Discovering and registering tools...")
    tool_names = discover_and_register_tools(mcp)

    if tool_names:
        logger.info(f"Registered {len(tool_names)} tools:")
        for name in sorted(tool_names):
            logger.info(f"  - {name}")
    else:
        logger.warning("No tools were registered!")

    # Discover and register all resources
    logger.info("Discovering and registering resources...")
    resource_uris = discover_and_register_resources(mcp)

    if resource_uris:
        logger.info(f"Registered {len(resource_uris)} resources:")
        for uri in sorted(resource_uris):
            logger.info(f"  - {uri}")
    else:
        logger.info("No resources registered (this is OK)")

    # Run the server
    logger.info("PSForge MCP Server is ready")
    logger.info("Waiting for connections...")

    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            mcp.create_initialization_options(),
        )


def run():
    """Entry point for the CLI command."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
