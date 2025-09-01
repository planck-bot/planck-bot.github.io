import discord
from discord import app_commands
from discord.ext import commands
import functools

commands = []

def universal_command(name: str, description: str):
    def decorator(func):
        # Create a wrapper that properly handles the self parameter
        @functools.wraps(func)
        async def wrapper(interaction: discord.Interaction):
            # Since we're creating global commands, we need to find the cog instance
            # from the bot to call the original method
            for cog in interaction.client.cogs.values():
                if hasattr(cog, func.__name__):
                    return await func(cog, interaction)
            raise RuntimeError(f"Could not find cog with method {func.__name__}")
        
        command = app_commands.Command(name=name, description=description, callback=wrapper)
        command.allowed_contexts = app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True)
        command.allowed_install = app_commands.AppInstallationType(guild=True, user=True)
        commands.append(command)
        # print(f"Registered function {func.__name__} as command {name}")
        return func
    return decorator

class UniversalGroup(app_commands.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_contexts = app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True)
        self.allowed_install = app_commands.AppInstallationType(guild=True, user=True)

def get_registered_commands():
    return commands

async def cb(interaction: discord.Interaction, view = discord.ui.LayoutView, is_command: bool = False):
    if is_command:
        if interaction.response.is_done():
            await interaction.followup.send(view=view)
        else:
            await interaction.response.send_message(view=view)
    else:
        if interaction.response.is_done():
            await interaction.followup.edit_message(view=view)
        else:
            await interaction.response.edit_message(view=view)