import random

import discord
from discord import app_commands
from discord.ext import commands

from utils import (
    UniversalGroup,
    add_data,
    base_view,
    cb,
    full_chances,
    full_multipliers,
    get_user_data,
    moderate,
)

@moderate()
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

@moderate()
async def probabilize_cb(interaction: discord.Interaction, bot: commands.Bot = None, amount: int = 0):
    view, container = await base_view(interaction)
    user_data = await get_user_data("currency", interaction.user.id)
    energy = user_data.get('energy', 0) if user_data else 0

    if amount > energy:
        container.add_item(discord.ui.TextDisplay(
            f"You do not have enough energy to probabilize {amount} energy."
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

    profile = await get_user_data("profile", interaction.user.id, {})
    
    tutorials = profile.get("tutorials", [])
    if not isinstance(tutorials, list):
        tutorials = []
    
    if "probabilize_tutorial" not in tutorials:
        tutorials.append("probabilize_tutorial")
        await add_data("profile", interaction.user.id, {"tutorials": tutorials})
        
        container.add_item(discord.ui.TextDisplay(
            "Congrats on your first quark!\n"
            "</subatomic probabilize:1412151005088448542> is how you will gain quarks!\n\n"
            "┌─Has a chance (5% base) to convert energy into quarks!\n"
            "│  └─You can upgrade the chance using shop upgrades\n"
            "│      └─Some might even allow you to get quarks from </gain:1412981220635312249>!\n"
            "└─You will also need to **differentiate** them later!\n"
            "-# Use </help:1412981220635312252> to view this again!"
        ))
        container.add_item(discord.ui.Separator())
        start = 0

    user_data = await get_user_data("currency", interaction.user.id)
    container.add_item(discord.ui.TextDisplay(
        f"Energy spent: {amount}\n"
        f"Energy left: {user_data.get('energy', 0) if user_data else 0}\n"
        f"Quarks gained: {quarks} (total: {start + quarks})\n"
        f"Chance per: {chance}%"
    ))

    container.add_item(discord.ui.Separator())
    action_row = discord.ui.ActionRow()
    retry = discord.ui.Button(label="Retry")
    retry_amount = discord.ui.Button(label="Retry (Same Amount)")
    back = discord.ui.Button(label="Back")

    action_row.add_item(retry)
    action_row.add_item(retry_amount)
    action_row.add_item(back)

    retry.callback = lambda inter: base_modal(inter, bot, False,
                                              title="Probabilize Energy",
                                              placeholder="Enter amount of energy to probabilize",
                                              callback=probabilize_cb,
                                              currencies=["energy"])
    retry_amount.callback = lambda inter: probabilize_cb(inter, bot, amount)
    back.callback = lambda inter: subatomic_cb(inter, bot)
    container.add_item(action_row)

    user_data = await get_user_data("currency", interaction.user.id)
    retry.disabled = 1 > (user_data.get('energy', 0) if user_data else 0)
    retry_amount.disabled = amount > (user_data.get('energy', 0) if user_data else 0)

    await interaction.response.send_message(view=view)

@moderate()
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
    profile = await get_user_data("profile", interaction.user.id, {})
    
    tutorials = profile.get("tutorials", [])
    if not isinstance(tutorials, list):
        tutorials = []
    
    if "differentiate_tutorial" not in tutorials:
        tutorials.append("differentiate_tutorial")
        await add_data("profile", interaction.user.id, {"tutorials": tutorials})
        
        container.add_item(discord.ui.TextDisplay(
            "You have obtained your first differentiated quarks!\n"
            "</subatomic differentiate:1412151005088448542> is how you will tell apart quarks!\n\n"
            "┌─Allows you to create up and down quarks\n"
            "├─They will be used to create **protons** and **neutrons**\n"
            "├─You will also unlock more types of quarks later on!\n"
            "├─Here is the chance table:\n"
            "│  │─Up Quarks: 75%\n"
            "│  │─Down Quarks: 75%\n"
            "│  │─Strange Quarks: 0.1%\n"
            "│  │─Charm Quarks: 0.01%\n"
            "│  │─Bottom Quarks: 0.01%\n"
            "└─ └─Top Quarks: 0.001%\n"
            "-# Use </help:1412981220635312252> to view this again!"
        ))
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
        user_data = await get_user_data("currency", interaction.user.id)

        quark_lines = "\n".join([f"+{amount} {quark.replace('_', ' ').title()}(s)" for quark, amount in results.items()])

        container.add_item(discord.ui.TextDisplay(
            f"Energy + Quarks spent: {energy_cost} energy + {amount} quarks\n"
            f"Energy + Quarks left: {user_data.get('energy', 0) if user_data else 0} energy + {user_data.get('quarks', 0) if user_data else 0} quarks\n"
            f"Differentiated Quarks Gained:\n{quark_lines}\n"
            f"Chance Multiplier: {multiplier:.2f}x"
        ))
    else:
        user_data = await get_user_data("currency", interaction.user.id)
        container.add_item(discord.ui.TextDisplay("Unfortunately, no quarks were gained."))

    container.add_item(discord.ui.Separator())
    action_row = discord.ui.ActionRow()
    retry = discord.ui.Button(label="Retry")
    retry_amount = discord.ui.Button(label="Retry (Same Amount)")
    back = discord.ui.Button(label="Back")

    action_row.add_item(retry)
    action_row.add_item(retry_amount)
    action_row.add_item(back)

    retry.callback = lambda inter: base_modal(inter, bot, False,
                                              title="Differentiate Quarks",
                                              placeholder="Enter amount of quarks to differentiate",
                                              callback=differentiate_cb,
                                              currencies=["quarks", "energy"])
    retry_amount.callback = lambda inter: differentiate_cb(inter, bot, amount)
    back.callback = lambda inter: subatomic_cb(inter, bot)
    container.add_item(action_row)

    retry.disabled = 1 > (user_data.get('quarks', 0) if user_data else 0) or 250 > (user_data.get('energy', 0) if user_data else 0)
    retry_amount.disabled = amount > (user_data.get('quarks', 0) if user_data else 0) or energy_cost > (user_data.get('energy', 0) if user_data else 0)

    await interaction.response.send_message(view=view)

@moderate()
async def condense_cb(interaction: discord.Interaction, bot: commands.Bot = None, amount: int = 0):
    view, container = await base_view(interaction)
    user_data = await get_user_data("currency", interaction.user.id)
    energy = user_data.get('energy', 0) if user_data else 0
    energy_cost = 1000 * amount

    if energy_cost > energy:
        container.add_item(discord.ui.TextDisplay(
            f"You do not have enough energy to condense {amount} electrons."
        ))
        return await interaction.response.send_message(view=view)

    profile = await get_user_data("profile", interaction.user.id, {})
    
    tutorials = profile.get("tutorials", [])
    if not isinstance(tutorials, list):
        tutorials = []
    
    if "condenser_tutorial" not in tutorials:
        tutorials.append("condenser_tutorial")
        await add_data("profile", interaction.user.id, {"tutorials": tutorials})
        
        container.add_item(discord.ui.TextDisplay(
            "Congrats on your first electron!\n"
            "</subatomic condense:1412151005088448542> is how you're going to make electrons\n\n"
            "┌─Requires a LOT of energy (1000)\n"
            "├─Electrons will be used to create </subatomic condense:1412151005088448542>tis how you're going to make electrons\n"
            "└─There will also be shop items you can buy with them.\n"
            "-# Use </help:1412981220635312252> to view this again!"
        ))
        container.add_item(discord.ui.Separator())

    await add_data("currency", interaction.user.id, {"energy": -energy_cost, "electrons": amount})
    user_data = await get_user_data("currency", interaction.user.id)

    container.add_item(discord.ui.TextDisplay(
        f"Energy spent: {energy_cost}\n"
        f"Energy left: {user_data.get('energy', 0) if user_data else 0}\n"
        f"Electrons condensed: {amount}"
    ))

    container.add_item(discord.ui.Separator())
    action_row = discord.ui.ActionRow()
    retry = discord.ui.Button(label="Retry")
    retry_amount = discord.ui.Button(label="Retry (Same Amount)")
    back = discord.ui.Button(label="Back")

    action_row.add_item(retry)
    action_row.add_item(retry_amount)
    action_row.add_item(back)

    retry.callback = lambda inter: base_modal(inter, bot, False,
                                              title="Condense Electrons",
                                              placeholder="Enter amount of electrons to condense",
                                              callback=condense_cb,
                                              currencies=["energy"])
    retry_amount.callback = lambda inter: condense_cb(inter, bot, amount)
    back.callback = lambda inter: subatomic_cb(inter, bot)
    container.add_item(action_row)

    retry.disabled = 1000 > (user_data.get('energy', 0) if user_data else 0)
    retry_amount.disabled = energy_cost > (user_data.get('energy', 0) if user_data else 0)

    await interaction.response.send_message(view=view)

@moderate()
async def subatomic_cb(interaction: discord.Interaction, bot: commands.Bot = None, is_command: bool = False):
    from .core import gain_cb, menu_cb
    view, container = await base_view(interaction)

    container.add_item(discord.ui.TextDisplay(
        f"**Subatomic Menu**\n"
        f"Coming soon"
    ))

    user_data = await get_user_data("currency", interaction.user.id)
    energy = user_data.get('energy', 0) if user_data else 0
    quarks = user_data.get('quarks', 0) if user_data else 0

    container.add_item(discord.ui.Separator())
    subatomic_row = discord.ui.ActionRow()

    probabilize = discord.ui.Button(label="Probabilize")

    probabilize.callback = lambda inter: base_modal(inter, bot, False,
                                              title="Probabilize Energy",
                                              placeholder="Enter amount of energy to probabilize",
                                              callback=probabilize_cb,
                                              currencies=["energy"])
    
    if energy > 0:
        subatomic_row.add_item(probabilize)

    differentiate = discord.ui.Button(label="Differentiate")

    differentiate.callback = lambda inter: base_modal(inter, bot, False,
                                              title="Differentiate Quarks",
                                              placeholder="Enter amount of quarks to differentiate",
                                              callback=differentiate_cb,
                                              currencies=["quarks", "energy"])

    if quarks > 0 and energy > 249:
        subatomic_row.add_item(differentiate)

    condense = discord.ui.Button(label="Condense")

    condense.callback = lambda inter: base_modal(inter, bot, False,
                                              title="Condense Electrons",
                                              placeholder="Enter amount of electrons to condense",
                                              callback=condense_cb,
                                              currencies=["energy"])

    if energy > 999:
        subatomic_row.add_item(condense)

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

    @subatomic_group.command(name="probabilize", description="Attempt to create quarks")
    @app_commands.describe(amount="The amount to probabilize")
    async def probabilize_command(self, interaction: discord.Interaction, amount: int = 0):
        if amount > 0:
            await probabilize_cb(interaction, self.bot, amount)
        else:
            await base_modal(interaction, self.bot, False,
                             title="Probabilize Energy",
                             placeholder="Enter amount of energy to probabilize",
                             callback=probabilize_cb,
                             currencies=["energy"])

    @subatomic_group.command(name="differentiate", description="Differentiate quarks into specific types")
    @app_commands.describe(amount="The amount to differentiate (Requires 250 energy per quark)")
    async def differentiate_command(self, interaction: discord.Interaction, amount: int = 0):
        if amount > 0:
            await differentiate_cb(interaction, self.bot, amount)
        else:
            await base_modal(interaction, self.bot, False,
                             title="Differentiate Quarks",
                             placeholder="Enter amount of quarks to differentiate",
                             callback=differentiate_cb,
                             currencies=["quarks", "energy"])

    @subatomic_group.command(name="condense", description="Condense electrons into energy")
    @app_commands.describe(amount="The amount to condense (1000 energy = 1 electron)")
    async def condense_command(self, interaction: discord.Interaction, amount: int = 0):
        if amount > 0:
            await condense_cb(interaction, self.bot, amount)
        else:
            await base_modal(interaction, self.bot, False,
                             title="Condense Electrons",
                             placeholder="Enter amount of electrons to condense",
                             callback=condense_cb,
                             currencies=["energy"])

async def setup(bot: commands.Bot):
    await bot.add_cog(SubatomicCog(bot))