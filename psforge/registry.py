"""Tool and resource registration system for MCP server."""

import importlib
import pkgutil
from pathlib import Path
from typing import Callable

from loguru import logger
from mcp.server.fastmcp import FastMCP


def register_tool(mcp: FastMCP, func: Callable, name: str | None = None) -> str:
    """Register a single tool function with the MCP server.

    Args:
        mcp: MCP server instance.
        func: Tool function to register.
        name: Optional tool name override (defaults to function name).

    Returns:
        The registered tool name.
    """
    tool_name = name or func.__name__
    description = func.__doc__ or f"Tool: {tool_name}"

    mcp.tool(name=tool_name, description=description.strip())(func)

    logger.debug(f"Registered tool: {tool_name}")
    return tool_name


def register_prompt(
    mcp: FastMCP,
    func: Callable,
    name: str | None = None,
    description: str | None = None,
) -> str:
    """Register a single prompt function with the MCP server.

    Args:
        mcp: MCP server instance.
        func: Prompt function to register.
        name: Optional prompt name override.
        description: Optional prompt description override.

    Returns:
        The registered prompt name.
    """
    prompt_name = name or func.__name__
    prompt_desc = description or func.__doc__ or f"Prompt: {prompt_name}"

    mcp.prompt(name=prompt_name, description=prompt_desc.strip())(func)

    logger.debug(f"Registered prompt: {prompt_name}")
    return prompt_name



def discover_and_register_tools(mcp: FastMCP) -> list[str]:
    """Automatically discover and register all tools from the tools package.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered tool names.
    """
    registered_tools = []

    # Import tools package
    try:
        import psforge.tools as tools_pkg
    except ImportError as e:
        logger.error(f"Failed to import tools package: {e}")
        return registered_tools

    # Get tools package path
    tools_path = Path(tools_pkg.__file__).parent

    # Iterate through all Python modules in tools/
    for module_info in pkgutil.iter_modules([str(tools_path)]):
        if module_info.name.startswith("_"):
            continue

        module_name = f"psforge.tools.{module_info.name}"

        try:
            module = importlib.import_module(module_name)

            # Look for register() function
            if hasattr(module, "register"):
                logger.info(f"Registering tools from: {module_name}")
                tool_names = module.register(mcp)
                registered_tools.extend(tool_names)
            else:
                logger.warning(f"Module {module_name} has no register() function")

        except Exception as e:
            logger.error(f"Failed to register tools from {module_name}: {e}")

    logger.info(f"Total tools registered: {len(registered_tools)}")
    return registered_tools


def discover_and_register_resources(mcp: FastMCP) -> list[str]:
    """Automatically discover and register all resources from the resources package.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered resource URIs.
    """
    registered_resources = []

    # Import resources package
    try:
        import psforge.resources as resources_pkg
    except ImportError as e:
        logger.error(f"Failed to import resources package: {e}")
        return registered_resources

    # Get resources package path
    resources_path = Path(resources_pkg.__file__).parent

    # Iterate through all Python modules in resources/
    for module_info in pkgutil.iter_modules([str(resources_path)]):
        if module_info.name.startswith("_"):
            continue

        module_name = f"psforge.resources.{module_info.name}"

        try:
            module = importlib.import_module(module_name)

            # Look for register() function
            if hasattr(module, "register"):
                logger.info(f"Registering resources from: {module_name}")
                resource_uris = module.register(mcp)
                registered_resources.extend(resource_uris)
            else:
                logger.warning(f"Module {module_name} has no register() function")

        except Exception as e:
            logger.error(f"Failed to register resources from {module_name}: {e}")

    logger.info(f"Total resources registered: {len(registered_resources)}")
    return registered_resources


def discover_and_register_prompts(mcp: FastMCP) -> list[str]:
    """Automatically discover and register all prompts from the prompts package.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered prompt names.
    """
    registered_prompts = []

    # Import prompts package
    try:
        import psforge.prompts as prompts_pkg
    except ImportError as e:
        logger.error(f"Failed to import prompts package: {e}")
        return registered_prompts

    # Get prompts package path
    prompts_path = Path(prompts_pkg.__file__).parent

    # Iterate through all Python modules in prompts/
    for module_info in pkgutil.iter_modules([str(prompts_path)]):
        if module_info.name.startswith("_"):
            continue

        module_name = f"psforge.prompts.{module_info.name}"

        try:
            module = importlib.import_module(module_name)

            # Look for register() function
            if hasattr(module, "register"):
                logger.info(f"Registering prompts from: {module_name}")
                prompt_names = module.register(mcp)
                registered_prompts.extend(prompt_names)
            else:
                logger.warning(f"Module {module_name} has no register() function")

        except Exception as e:
            logger.error(f"Failed to register prompts from {module_name}: {e}")

    logger.info(f"Total prompts registered: {len(registered_prompts)}")
    return registered_prompts

