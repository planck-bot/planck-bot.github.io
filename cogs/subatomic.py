import discord
from discord import app_commands
from discord.ext import commands

import random 

from utils import UniversalGroup, base_view, add_data, get_user_data, cb, full_chances

# Probabilitize, 5% chance to get a quark. Guarenteed every 100 energy
async def probabilitize_cb(interaction: discord.Interaction, bot: commands.Bot = None, is_command: bool = False):
    view, container = await base_view(interaction)

    user_data = await get_user_data("currency", interaction.user.id)
    energy = user_data.get('energy', 0) if user_data else 0
    if energy == 0:
        container.add_item(discord.ui.TextDisplay(
            "You have no energy to probabilitize."
        ))
        return await cb(interaction, view, is_command)

    amount_modal = discord.ui.Modal(title="Probabilitize Energy", timeout=None)
    amount_modal.add_item(discord.ui.TextInput(label="Amount", placeholder="Enter amount of energy to probabilitize"))
    amount_modal.on_submit = lambda inter: probabilitize(inter, bot, amount=int(amount_modal.children[0].value))
    await interaction.response.send_modal(amount_modal)

async def probabilitize(interaction: discord.Interaction, bot: commands.Bot = None, amount: int = 0):
    view, container = await base_view(interaction)
    user_data = await get_user_data("currency", interaction.user.id)
    energy = user_data.get('energy', 0) if user_data else 0

    if amount > energy:
        container.add_item(discord.ui.TextDisplay(
            f"You do not have enough energy to probabilitize {amount} energy."
        ))
        return await interaction.response.send_message(view=view)

    await add_data("currency", interaction.user.id, {"energy": -amount})

    chance = 5 + await full_chances("quark", user=interaction.user)

    start = user_data.get("quarks", 0) if user_data else 0

    quarks = 0 
    for i in range(amount):
        if (i + 1) % 100 == 0:
            await add_data("currency", interaction.user.id, {"quarks": 1})
            quarks += 1
        elif random.random() < chance / 100:
            await add_data("currency", interaction.user.id, {"quarks": 1})
            quarks += 1

    if not start:
        container.add_item(discord.ui.TextDisplay(
            "Congrats on getting your first quark(s)!\n"
            "Quarks can be differentiated later on to make protons and neutrons!\n"
            "Have fun and keep exploring the subatomic world!"
        ))
        container.add_item(discord.ui.Separator())
        start = 0

    container.add_item(discord.ui.TextDisplay(
        f"Energy spent: {amount}\n"
        f"Quarks gained: {quarks} (total: {start + quarks})\n"
        f"Chance per: {chance}%"
    ))

    container.add_item(discord.ui.Separator())
    action_row = discord.ui.ActionRow()
    retry = discord.ui.Button(label="Retry")
    back = discord.ui.Button(label="Back")

    action_row.add_item(retry)
    action_row.add_item(back)

    retry.callback = lambda inter: probabilitize(inter, bot, amount)
    back.callback = lambda inter: subatomic_cb(inter, bot)
    container.add_item(action_row)

    await interaction.response.send_message(view=view)

async def subatomic_cb(interaction: discord.Interaction, bot: commands.Bot = None, is_command: bool = False):
    from .core import gain_cb, menu_cb
    view, container = await base_view(interaction)

    container.add_item(discord.ui.TextDisplay(
        f"**Subatomic Menu**\n"
        f"Coming soon"
    ))

    container.add_item(discord.ui.Separator())
    subatomic_row = discord.ui.ActionRow()

    probabilitize = discord.ui.Button(label="Probabilitize")

    probabilitize.callback = lambda inter: probabilitize_cb(inter, bot, is_command=False)

    subatomic_row.add_item(probabilitize)

    container.add_item(subatomic_row)

    action_row = discord.ui.ActionRow()
    gain = discord.ui.Button(label="Gain")
    back = discord.ui.Button(label="Back")

    action_row.add_item(gain)
    action_row.add_item(back)

    gain.callback = lambda inter: gain_cb(inter, bot)
    back.callback = lambda inter: menu_cb(inter, bot)
    container.add_item(action_row)

    await cb(interaction, view, is_command)

class SubatomicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    subatomic_group = UniversalGroup(name="subatomic", description="Subatomic commands")

    @subatomic_group.command(name="menu", description="Open the subatomic menu")
    async def subatomic_command(self, interaction: discord.Interaction):
        await subatomic_cb(interaction, self.bot, True)

    @subatomic_group.command(name="probabilitize", description="Attempt to create quarks")
    @app_commands.describe(amount="The amount to attempt")
    async def probabilitize_command(self, interaction: discord.Interaction, amount: int = 0):
        if amount > 0:
            await probabilitize(interaction, self.bot, amount)
        else:
            await probabilitize_cb(interaction, self.bot, True)

async def setup(bot: commands.Bot):
    await bot.add_cog(SubatomicCog(bot))