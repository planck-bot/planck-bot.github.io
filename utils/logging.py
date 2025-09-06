# Currently synchronous, but may need async in future
# Since right now it's minimal

import functools
import logging
import logging.handlers
import sys
import time
import traceback
import uuid
from pathlib import Path
from typing import Callable, TypeVar

import discord
from discord.ext import commands

T = TypeVar('T')

def setup_logging(log_dir: str = "data/logs", log_level: int = logging.INFO) -> None:
    """Set up the logging configuration for the bot.
    
    Args:
        log_dir (str): Directory to store log files
        log_level (int): Logging level for the application
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)-12s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(levelname)-8s | %(name)-12s | %(message)s'
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_path / "bot.log",
        when="midnight",
        interval=1,
        backupCount=30,  # Keep 30 days of logs
        encoding="utf-8"
    )
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)

    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / "error.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.
    
    Args:
        name (str): Name for the logger, typically __name__ or module path
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)

def handle_errors():
    """
    Handles errors and reports it to log file
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            interaction = next((arg for arg in args if isinstance(arg, discord.Interaction)), None)
            if not interaction:
                return await func(*args, **kwargs)

            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger = get_logger(func.__module__)
                
                error_id = f"E{int(time.time())}-{str(uuid.uuid4())[:8]}"
                
                error_msg = f"Error ID {error_id} in {func.__name__}: {str(e)}\n{''.join(traceback.format_tb(e.__traceback__))}"
                logger.error(error_msg)

                user_msg = f"An error occurred while processing your command (Error ID: `{error_id}`). If you wish to report this, please include the error ID."
                
                if isinstance(e, commands.errors.MissingPermissions):
                    user_msg = "You don't have permission to use this command."
                elif isinstance(e, commands.errors.CommandOnCooldown):
                    user_msg = f"This command is on cooldown. Try again in {e.retry_after:.1f} seconds."
                elif isinstance(e, ValueError):
                    user_msg = "Invalid input provided. Please check your values and try again."
                
                embed = discord.Embed(
                    title="Error",
                    description=user_msg,
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Function",
                    value=f"`{func.__name__}`",
                    inline=True
                )
                if isinstance(e, ValueError):
                    embed.add_field(
                        name="Error Type",
                        value="Invalid Input",
                        inline=True
                    )

                try:
                    if interaction.response.is_done():
                        await interaction.followup.send(embed=embed, ephemeral=True)
                    else:
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                except discord.errors.InteractionResponded:
                    # If somehow we still get here, try one last time
                    try:
                        await interaction.followup.send(embed=embed, ephemeral=True)
                    except Exception as e2:
                        logger.error(f"Failed to send error message: {e2}")

        return wrapper
    return decorator