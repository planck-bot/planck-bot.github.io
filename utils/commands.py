import discord
from discord import app_commands

def universal_command(name: str, description: str):
    def decorator(func):
        command = app_commands.command(name=name, description=description)(func)
        
        command.allowed_contexts = app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True)
        command.allowed_installs = app_commands.AppInstallationType(guild=True, user=True)
        
        return command
    return decorator

class UniversalGroup(app_commands.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_contexts = app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True)
        self.allowed_install = app_commands.AppInstallationType(guild=True, user=True)

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