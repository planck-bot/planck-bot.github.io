import discord
from discord import app_commands
from discord.ext import commands

import random 

from utils import UniversalGroup, base_view, add_data, get_user_data, cb, full_chances, full_multipliers

async def base_modal(interaction: discord.Interaction, bot: commands.Bot, is_command: bool = False, *, title: str, placeholder: str, callback, currencies: list):
    view, container = await base_view(interaction)

    user_data = await get_user_data("currency", interaction.user.id)
    for currency in currencies:
        amount = user_data.get(currency, 0) if user_data else 0
        if amount == 0:
            container.add_item(discord.ui.TextDisplay(
                f"You have no {currency} to {title.lower()}."
            ))
            return await cb(interaction, view, is_command)

    amount_modal = discord.ui.Modal(title=title, timeout=None)
    amount_modal.add_item(discord.ui.TextInput(label="Amount", placeholder=placeholder))
    amount_modal.on_submit = lambda inter: callback(inter, bot, amount=int(amount_modal.children[0].value))
    await interaction.response.send_modal(amount_modal)
    
async def probabilitize_cb(interaction: discord.Interaction, bot: commands.Bot = None, amount: int = 0):
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
            quarks += 1
        elif random.random() < chance / 100:
            quarks += 1
    
    if quarks > 0:
        await add_data("currency", interaction.user.id, {"quarks": quarks})

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

    retry.callback = lambda inter: base_modal(inter, bot, False,
                                              title="Probabilitize Energy",
                                              placeholder="Enter amount of energy to probabilitize",
                                              callback=probabilitize_cb,
                                              currencies=["energy"])
    back.callback = lambda inter: subatomic_cb(inter, bot)
    container.add_item(action_row)

    await interaction.response.send_message(view=view)

async def differentiate_cb(interaction: discord.Interaction, bot: commands.Bot = None, amount: int = 0):
    view, container = await base_view(interaction)
    user_data = await get_user_data("currency", interaction.user.id)
    energy = user_data.get('energy', 0) if user_data else 0
    energy_cost = 250 * amount

    if energy_cost > energy:
        container.add_item(discord.ui.TextDisplay(
            f"You do not have enough energy to differentiate {amount} quarks."
        ))
        return await interaction.response.send_message(view=view)
    
    quarks = user_data.get('quarks', 0) if user_data else 0

    if amount > quarks:
        container.add_item(discord.ui.TextDisplay(
            f"You do not have enough quarks to differentiate {amount} quarks."
        ))
        return await interaction.response.send_message(view=view)

    QUARK_CHANCES = {
        "up_quark": 75,
        "down_quark": 75,
        "strange_quark": 0.1,
        "charm_quark": 0.01,
        "bottom_quark": 0.01,
        "top_quark": 0.001
    }
    await add_data("currency", interaction.user.id, {"energy": -energy_cost, "quarks": -amount})

    results = {}
    multiplier = await full_multipliers("quark_differentiation", user=interaction.user)

    for _ in range(amount):
        for quark, chance in QUARK_CHANCES.items():
            chance *= multiplier
            guaranteed = int(chance // 100)
            remainder = float(chance % 100)

            results[quark] = results.get(quark, 0) + guaranteed

            if random.random() < remainder / 100:
                results[quark] = results.get(quark, 0) + 1

    if results:
        await add_data("currency", interaction.user.id, results)
        container.add_item(discord.ui.TextDisplay(
            f"Energy + Quarks spent: {energy_cost} energy + {amount} quarks\n"
            f"Differentiated Quarks Gained:\n" + "\n".join([f"+{amount} {quark.replace("_", " ").title()}(s)" for quark, amount in results.items()]) + "\n"
            f"Chance Multiplier: {multiplier:.2f}x"
        ))
    else:
        container.add_item(discord.ui.TextDisplay("Unfortunately, no quarks were gained."))

    container.add_item(discord.ui.Separator())
    action_row = discord.ui.ActionRow()
    retry = discord.ui.Button(label="Retry")
    back = discord.ui.Button(label="Back")

    action_row.add_item(retry)
    action_row.add_item(back)

    retry.callback = lambda inter: base_modal(inter, bot, False,
                                              title="Differentiate Quarks",
                                              placeholder="Enter amount of quarks to differentiate",
                                              callback=differentiate_cb,
                                              currencies=["quarks", "energy"])
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

    probabilitize.callback = lambda inter: base_modal(inter, bot, False,
                                              title="Probabilitize Energy",
                                              placeholder="Enter amount of energy to probabilitize",
                                              callback=probabilitize_cb,
                                              currencies=["energy"])

    subatomic_row.add_item(probabilitize)

    differentiate = discord.ui.Button(label="Differentiate")

    differentiate.callback = lambda inter: base_modal(inter, bot, False,
                                              title="Differentiate Quarks",
                                              placeholder="Enter amount of quarks to differentiate",
                                              callback=differentiate_cb,
                                              currencies=["quarks", "energy"])

    subatomic_row.add_item(differentiate)

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
            await base_modal(interaction, self.bot, False,
                             title="Probabilitize Energy",
                             placeholder="Enter amount of energy to probabilitize",
                             callback=probabilitize_cb,
                             currencies=["energy"])
        else:
            await probabilitize_cb(interaction, self.bot, True)

    @subatomic_group.command(name="differentiate", description="Differentiate quarks into specific types")
    @app_commands.describe(amount="The amount to differentiate")
    async def differentiate_command(self, interaction: discord.Interaction, amount: int = 0):
        if amount > 0:
            await base_modal(interaction, self.bot, False,
                             title="Differentiate Quarks",
                             placeholder="Enter amount of quarks to differentiate",
                             callback=differentiate_cb,
                             currencies=["quarks", "energy"])
        else:
            await differentiate_cb(interaction, self.bot, True)

async def setup(bot: commands.Bot):
    await bot.add_cog(SubatomicCog(bot))