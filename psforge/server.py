"""PSForge MCP Server - Main entry point."""

import sys

from loguru import logger
from mcp.server.fastmcp import FastMCP

from psforge.app import __app_name__, __version__
from psforge.registry import (
    discover_and_register_prompts,
    discover_and_register_resources,
    discover_and_register_tools,
)


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


def run():
    """Entry point for the CLI command."""
    setup_logging()

    logger.info(f"Starting {__app_name__} v{__version__}")
    logger.info("Photoshop MCP Server - AI-Powered Automation")

    # Create MCP server using FastMCP
    mcp = FastMCP(__app_name__)

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

    # Discover and register all prompts
    logger.info("Discovering and registering prompts...")
    prompt_names = discover_and_register_prompts(mcp)

    if prompt_names:
        logger.info(f"Registered {len(prompt_names)} prompts:")
        for name in sorted(prompt_names):
            logger.info(f"  - {name}")
    else:
        logger.info("No prompts registered (this is OK)")

    # Run the server
    logger.info("PSForge MCP Server is ready")
    logger.info("Waiting for connections...")

    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
