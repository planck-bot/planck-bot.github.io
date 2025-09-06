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
    handle_errors,
    get_logger
)

logger = get_logger(__name__)

@moderate()
@handle_errors()
async def base_modal(interaction: discord.Interaction, bot: commands.Bot, is_command: bool = False, *, title: str, callback, currencies: list = None, inputs: list = None, selects: list = None):
    """
    Allows for select menus and multiple text inputs in a modal.

    Args:
        interaction (discord.Interaction): The interaction object
        bot (commands.Bot): The bot instance
        is_command (bool, optional): Whether this was triggered by a command. Defaults to False.
        title (str): The title of the modal
        callback (function): The callback function to execute when the modal is submitted
        currencies (list, optional): List of currencies to check. Defaults to None.
        inputs (list, optional): List of dictionaries containing text input configurations. Each dict should have:
            - label (str): Label for the text input
            - placeholder (str, optional): Placeholder text
            - min_length (int, optional): Minimum length of input
            - max_length (int, optional): Maximum length of input
            - required (bool, optional): Whether the input is required
            - style (discord.TextStyle, optional): The style of the text input
            - default (str, optional): Default value for the input
        selects (list, optional): List of dictionaries containing select configurations. Each dict should have:
            - label (str): Label for the select menu
            - options (list): List of dictionaries containing:
                - label (str): The label for the option
                - value (str): The value for the option
                - description (str, optional): Description for the option
            - min_values (int, optional): Minimum number of values that must be selected
            - max_values (int, optional): Maximum number of values that can be selected
            - placeholder (str, optional): Placeholder text when nothing is selected
    """
    view, container = await base_view(interaction)

    if currencies:
        user_data = await get_user_data("currency", interaction.user.id)
        for currency in currencies:
            amount = user_data.get(currency, 0) if user_data else 0
            if amount == 0:
                container.add_item(discord.ui.TextDisplay(
                    f"You have no {currency} to {title.lower()}."
                ))
                return await cb(interaction, view, is_command)

    modal = discord.ui.Modal(title=title, timeout=None)
    
    if inputs:
        for input_config in inputs:
            text_input = discord.ui.TextInput(
                label=input_config["label"],
                placeholder=input_config.get("placeholder", None),
                min_length=input_config.get("min_length", None),
                max_length=input_config.get("max_length", None),
                required=input_config.get("required", True),
                style=input_config.get("style", discord.TextStyle.short),
                default=input_config.get("default", None)
            )
            modal.add_item(text_input)
    
    if selects:
        for select_config in selects:
            select = discord.ui.Select(
                placeholder=select_config.get("placeholder", None),
                min_values=select_config.get("min_values", 1),
                max_values=select_config.get("max_values", 1),
                options=[
                    discord.SelectOption(
                        label=option["label"],
                        value=option["value"],
                        description=option.get("description", None)
                    ) for option in select_config["options"]
                ],
                required=True
            )

            modal.add_item(select)

    async def submit_callback(inter):
        values = {}
        
        if inputs:
            for i, input_config in enumerate(inputs):
                key = input_config.get("key", f"input_{i}")
                value = modal.children[i].value

                if value.isdigit():
                    value = int(value)
                values[key] = value
        
        if selects:
            start_idx = len(inputs) if inputs else 0
            for i, select_config in enumerate(selects, start=start_idx):
                key = select_config.get("key", f"select_{i}")
                values[key] = modal.children[i].values

        await callback(inter, bot, **values)

    modal.on_submit = submit_callback
    await interaction.response.send_modal(modal)

@moderate()
@handle_errors()
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
                                              callback=probabilize_cb,
                                              currencies=["energy"],
                                              inputs=[{
                                                  "label": "Amount",
                                                  "placeholder": "Enter amount of energy to probabilize",
                                                  "key": "amount"
                                              }])
    retry_amount.callback = lambda inter: probabilize_cb(inter, bot, amount)
    back.callback = lambda inter: subatomic_cb(inter, bot)
    container.add_item(action_row)

    user_data = await get_user_data("currency", interaction.user.id)
    retry.disabled = 1 > (user_data.get('energy', 0) if user_data else 0)
    retry_amount.disabled = amount > (user_data.get('energy', 0) if user_data else 0)

    await interaction.response.send_message(view=view)

@moderate()
@handle_errors()
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
                                              callback=differentiate_cb,
                                              currencies=["quarks", "energy"],
                                              inputs=[{
                                                  "label": "Amount",
                                                  "placeholder": "Enter amount of quarks to differentiate",
                                                  "key": "amount"
                                              }])
    retry_amount.callback = lambda inter: differentiate_cb(inter, bot, amount)
    back.callback = lambda inter: subatomic_cb(inter, bot)
    container.add_item(action_row)

    retry.disabled = 1 > (user_data.get('quarks', 0) if user_data else 0) or 250 > (user_data.get('energy', 0) if user_data else 0)
    retry_amount.disabled = amount > (user_data.get('quarks', 0) if user_data else 0) or energy_cost > (user_data.get('energy', 0) if user_data else 0)

    await interaction.response.send_message(view=view)

@moderate()
@handle_errors()
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
                                              callback=condense_cb,
                                              currencies=["energy"],
                                              inputs=[{
                                                  "label": "Amount",
                                                  "placeholder": "Enter amount of electrons to condense",
                                                  "key": "amount"
                                              }])
    retry_amount.callback = lambda inter: condense_cb(inter, bot, amount)
    back.callback = lambda inter: subatomic_cb(inter, bot)
    container.add_item(action_row)

    retry.disabled = 1000 > (user_data.get('energy', 0) if user_data else 0)
    retry_amount.disabled = energy_cost > (user_data.get('energy', 0) if user_data else 0)

    await interaction.response.send_message(view=view)

@handle_errors()
async def hadronize_cb(interaction: discord.Interaction, bot: commands.Bot = None, protons: int = 0, neutrons: int = 0):
    view, container = await base_view(interaction)
    user_data = await get_user_data("currency", interaction.user.id)
    proton = {"up_quark": 2, "down_quark": 1}
    neutron = {"up_quark": 1, "down_quark": 2}
    energy_cost = 2500 * (protons + neutrons)

    required_quarks = {}
    for quark, amount in proton.items():
        required_quarks[quark] = required_quarks.get(quark, 0) + amount * protons
    for quark, amount in neutron.items():
        required_quarks[quark] = required_quarks.get(quark, 0) + amount * neutrons

    for quark, amount in required_quarks.items():
        if (user_data.get(quark, 0) if user_data else 0) < amount:
            container.add_item(discord.ui.TextDisplay(
                f"You do not have enough {quark.replace('_', ' ')}s to hadronize {protons} protons and {neutrons} neutrons."
            ))
            return await interaction.response.send_message(view=view)
        
    if energy_cost > (user_data.get('energy', 0) if user_data else 0):
        container.add_item(discord.ui.TextDisplay(
            f"You do not have enough energy to hadronize {protons} protons and {neutrons} neutrons."
        ))
        return await interaction.response.send_message(view=view)


    profile = await get_user_data("profile", interaction.user.id, {})
    
    tutorials = profile.get("tutorials", [])
    if not isinstance(tutorials, list):
        tutorials = []

    if "hadronization_tutorial" not in tutorials:
        tutorials.append("hadronization_tutorial")
        await add_data("profile", interaction.user.id, {"tutorials": tutorials})

        container.add_item(discord.ui.TextDisplay(
            "You have created your first protons and neutrons!\n"
            "</subatomic hadronize:1412151005088448542> is how you will create protons and neutrons!\n\n"
            "┌─Requires up and down quarks\n"
            "├─Protons require 2 up quarks and 1 down quark\n"
            "├─Neutrons require 1 up quark and 2 down quarks\n"
            "└─ └─You will need these to make atoms later on!"
            "-# Use </help:1412981220635312252> to view this again!"
        ))

        container.add_item(discord.ui.Separator())
            
    await add_data("currency", interaction.user.id, {quark: -amount for quark, amount in required_quarks.items()})
    await add_data("currency", interaction.user.id, {"energy": -energy_cost, "protons": protons, "neutrons": neutrons})
    user_data = await get_user_data("currency", interaction.user.id)

    container.add_item(discord.ui.TextDisplay(
        f"Protons gained: {protons} (total: {user_data.get('protons', 0) if user_data else 0})\n"
        f"Neutrons gained: {neutrons} (total: {user_data.get('neutrons', 0) if user_data else 0})\n"
        f"Quarks spent: {', '.join([f'{amount} {quark.replace('_', ' ')}(s)' for quark, amount in required_quarks.items()])}"
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
                                              title="Hadronize Protons and Neutrons",
                                              callback=hadronize_cb,
                                              currencies=["energy"],
                                              inputs=[{
                                                  "label": "Protons",
                                                  "placeholder": "Enter amount of protons to hadronize",
                                                  "key": "protons"
                                              }, {
                                                  "label": "Neutrons",
                                                  "placeholder": "Enter amount of neutrons to hadronize",
                                                  "key": "neutrons"
                                              }])
    retry_amount.callback = lambda inter: hadronize_cb(inter, bot, amount)
    back.callback = lambda inter: subatomic_cb(inter, bot)
    container.add_item(action_row)

    retry.disabled = 2500 > (user_data.get('energy', 0) if user_data else 0) and 1 > (user_data.get('protons', 0) if user_data else 0) and 1 > (user_data.get('neutrons', 0) if user_data else 0)
    retry_amount.disabled = energy_cost > (user_data.get('energy', 0) if user_data else 0) and protons > (user_data.get('protons', 0) if user_data else 0) and neutrons > (user_data.get('neutrons', 0) if user_data else 0)

    await interaction.response.send_message(view=view)

ATOMS = {
    "hydrogen": {"protons": 1, "neutrons": 0, "electrons": 1},
    "lithium": {"protons": 3, "neutrons": 4, "electrons": 3},
    "carbon": {"protons": 6, "neutrons": 6, "electrons": 6},
    "nitrogen": {"protons": 7, "neutrons": 7, "electrons": 7},
    "oxygen": {"protons": 8, "neutrons": 8, "electrons": 8},
    "sodium": {"protons": 11, "neutrons": 12, "electrons": 11},
    "magnesium": {"protons": 12, "neutrons": 12, "electrons": 12},
    "aluminum": {"protons": 13, "neutrons": 14, "electrons": 13},
    "chlorine": {"protons": 17, "neutrons": 18, "electrons": 17},
    "bromine": {"protons": 35, "neutrons": 45, "electrons": 35},
    "iodine": {"protons": 53, "neutrons": 74, "electrons": 53},
    "uranium": {"protons": 92, "neutrons": 146, "electrons": 92}
}

COMPOUNDS = {
    "water": {"hydrogen": 2, "oxygen": 1},                               # Boosts energy by 0.1%
    "carbon_dioxide": {"carbon": 1, "oxygen": 2},                        # Boosts quarks by 0.2%
    "methane": {"carbon": 1, "hydrogen": 4},                             # Boosts energy by 0.3%
    "ammonia": {"nitrogen": 1, "hydrogen": 3},                           # Boosts quarks by 0.4%
    "glucose": {"carbon": 6, "hydrogen": 12, "oxygen": 6},               # Boosts energy by 0.7%
    "sodium_chloride": {"sodium": 1, "chlorine": 1},                     # Boosts quarks by 1.0%
    "magnesium_hydroxide": {"magnesium": 1, "hydrogen": 2, "oxygen": 2}, # Boosts energy by 1.2%
    "aluminum_oxide": {"aluminum": 2, "oxygen": 3},                      # Boosts quarks by 1.5%
    "calcium_carbonate": {"calcium": 1, "carbon": 1, "oxygen": 3},       # Boosts energy by 2.0%
    "sulfuric_acid": {"hydrogen": 2, "sulfur": 1, "oxygen": 4},          # Boosts quarks by 2.5%
    "uranium_dioxide": {"uranium": 1, "oxygen": 2}                       # Boosts energy by 5.0%
}

@handle_errors()
async def nucleosynthesis_cb(interaction: discord.Interaction, bot: commands.Bot = None, *, atom: str, amount: int = 1):
    view, container = await base_view(interaction)
    user_data = await get_user_data("currency", interaction.user.id)
    if atom not in ATOMS:
        container.add_item(discord.ui.TextDisplay(
            f"{atom} is not a valid atom to synthesize."
        ))
        return await interaction.response.send_message(view=view)
    
    energy_required = (5000 * ATOMS[atom]["protons"] + 5000 * ATOMS[atom]["neutrons"]) * amount
    electrons_required = ATOMS[atom]["electrons"] * amount
    protons_required = ATOMS[atom]["protons"] * amount
    neutrons_required = ATOMS[atom]["neutrons"] * amount

    energy = user_data.get('energy', 0) if user_data else 0
    electrons = user_data.get('electrons', 0) if user_data else 0
    protons = user_data.get('protons', 0) if user_data else 0
    neutrons = user_data.get('neutrons', 0) if user_data else 0

    def missing_resources():
        missing = []
        if energy_required > energy:
            missing.append(f"{energy_required - energy} more energy")
        if electrons_required > electrons:
            missing.append(f"{electrons_required - electrons} more electrons")
        if protons_required > protons:
            missing.append(f"{protons_required - protons} more protons")
        if neutrons_required > neutrons:
            missing.append(f"{neutrons_required - neutrons} more neutrons")
        return missing

    missing = missing_resources()
    if missing:
        container.add_item(discord.ui.TextDisplay(
            f"You do not have enough resources to synthesize {amount} {atom}(s). You need {', '.join(missing)}."
        ))
        return await interaction.response.send_message(view=view)

    profile = await get_user_data("profile", interaction.user.id, {})

    tutorials = profile.get("tutorials", [])
    if not isinstance(tutorials, list):
        tutorials = []

    if "nucleosynthesis_tutorial" not in tutorials:
        tutorials.append("nucleosynthesis_tutorial")
        await add_data("profile", interaction.user.id, {"tutorials": tutorials})

        container.add_item(discord.ui.TextDisplay(
            "You have created your first atom!\n"
            "</subatomic nucleosynthesize:1412151005088448542> is how you're going to make atoms!\n\n"
            "┌─Requires protons, neutrons, and electrons\n"
            "├─ └─1 proton + 1 neutron + 1 electron = Hydrogen\n"
            "└─Atoms are the final product of this stage"
            "-# Use </help:1412981220635312252> to view this again!"
        ))

        container.add_item(discord.ui.Separator())

    # currency table atoms: {"hydrogen": 1, etc}
    await add_data("currency", interaction.user.id, {
        "energy": -energy_required,
        "electrons": -electrons_required,
        "protons": -protons_required,
        "neutrons": -neutrons_required,
        "atoms": {atom: amount}
    })

    container.add_item(discord.ui.TextDisplay(
        f"Synthesized {amount} {atom}(s)!\n"
        f"Energy spent: {energy_required}\n"
        f"Electrons spent: {electrons_required}\n"
        f"Protons spent: {protons_required}\n"
        f"Neutrons spent: {neutrons_required}\n"
    ))

    await interaction.response.send_message(view=view)

@moderate()
@handle_errors()
async def fission_cb(interaction: discord.Interaction, bot: commands.Bot = None, confirmed: bool = False):
    view, container = await base_view(interaction)

    user_data = await get_user_data("currency", interaction.user.id) or {}
    resets = await get_user_data("resets", interaction.user.id) or {}
    atoms = user_data.get("atoms", {})
    energy = user_data.get("energy", 0)
    fission_resets = resets.get("fission", 0)

    atoms_list = list(ATOMS.keys())
    fission_cost = 2 ** fission_resets * 1_000_000
    fission_atom = atoms_list[min(fission_resets, len(atoms_list) - 1)]
    fission_atom_amount = (
        2 ** (fission_resets - (len(atoms_list) - 1))
        if fission_atom == "uranium"
        else 1
    )

    if atoms.get(fission_atom, 0) < fission_atom_amount:
        container.add_item(discord.ui.TextDisplay(
            f"You need {fission_atom_amount} {fission_atom}(s) to do fission."
        ))
        return await interaction.response.send_message(view=view)

    if energy < fission_cost:
        container.add_item(discord.ui.TextDisplay(
            f"You need {fission_cost} energy to do fission."
        ))
        return await interaction.response.send_message(view=view)

    if not confirmed:
        next_photon = fission_resets + 1
        first_time = fission_resets == 0
        container.add_item(discord.ui.TextDisplay(
            "**WARNING**: Performing fission will reset:\n"
            "- All XP and levels\n"
            "- All regular shop upgrades\n"
            "- All currencies EXCEPT atoms and quarks\n\n"
            f"This will consume {fission_atom_amount} {fission_atom}(s) and {fission_cost:,} energy.\n\n"
            "You will gain:\n"
            f"- {next_photon} Photon{'s' if next_photon > 1 else ''}\n"
            "- 10% boost to energy and quarks gain (compounds with previous fissions)\n"
            "- All differentiated quarks become 1% more common\n"
            "- You gain 10% more XP\n" +
            ("- 5% chance to get quarks (one-time bonus)\n"
             "- 1% chance to get electrons (one-time bonus)\n" if first_time else "") +
            "\nAre you sure you want to continue?"
        ))
        
        action_row = discord.ui.ActionRow()
        confirm = discord.ui.Button(label="Yes, perform fission", style=discord.ButtonStyle.danger)
        cancel = discord.ui.Button(label="No, cancel", style=discord.ButtonStyle.secondary)
        
        action_row.add_item(confirm)
        action_row.add_item(cancel)
        
        confirm.callback = lambda inter: fission_cb(inter, bot, confirmed=True)
        cancel.callback = lambda inter: subatomic_cb(inter, bot)
        
        container.add_item(action_row)
        return await interaction.response.send_message(view=view)

    upgrade_data = await get_user_data("upgrades", interaction.user.id) or {}
    profile_data = await get_user_data("profile", interaction.user.id) or {}

    user_data = await get_user_data("currency", interaction.user.id) or {}
    resets = await get_user_data("resets", interaction.user.id) or {}
    upgrade_data = await get_user_data("upgrades", interaction.user.id) or {}
    profile_data = await get_user_data("profile", interaction.user.id) or {}

    atoms = user_data.get("atoms", {})
    energy = user_data.get("energy", 0)
    fission_resets = resets.get("fission", 0)

    atoms_list = list(ATOMS.keys())
    fission_cost = 2 ** fission_resets * 1_000_000
    fission_atom = atoms_list[min(fission_resets, len(atoms_list) - 1)]

    fission_atom_amount = (
        2 ** (fission_resets - (len(atoms_list) - 1))
        if fission_atom == "uranium"
        else 1
    )

    if atoms.get(fission_atom, 0) < fission_atom_amount:
        container.add_item(discord.ui.TextDisplay(
            f"You need {fission_atom_amount} {fission_atom}(s) to do fission."
        ))
        return await interaction.response.send_message(view=view)

    if energy < fission_cost:
        container.add_item(discord.ui.TextDisplay(
            f"You need {fission_cost} energy to do fission."
        ))
        return await interaction.response.send_message(view=view)

    await add_data("currency", interaction.user.id, {
        "energy": -energy,
        "quarks": -user_data.get("quarks", 0),
        "up_quark": -user_data.get("up_quark", 0),
        "down_quark": -user_data.get("down_quark", 0),
        "electrons": -user_data.get("electrons", 0),
        "protons": -user_data.get("protons", 0),
        "neutrons": -user_data.get("neutrons", 0),
    })

    await add_data("upgrades", interaction.user.id, {
        "energy_manipulator": -upgrade_data.get("energy_manipulator", 0),
        "quantum_luck": -upgrade_data.get("quantum_luck", 0),
        "quantum_manipulator": -upgrade_data.get("quantum_manipulator", 0),
        "quantum_lenses": -upgrade_data.get("quantum_lens", 0),
        "undercharged": -upgrade_data.get("undercharged", 0),
        "electric_field": -upgrade_data.get("electric_field", 0),
        "subatomic_efficiency": -upgrade_data.get("subatomic_efficiency", 0),
    })

    await add_data("profile", interaction.user.id, {"xp": -profile_data.get("xp", 0)})

    total_resets = await add_data("resets", interaction.user.id, {"fission": 1})
    await add_data("currency", interaction.user.id, {"photons": total_resets["fission"]})

    atoms[fission_atom] = atoms.get(fission_atom, 0) - fission_atom_amount
    await add_data("currency", interaction.user.id, {"atoms": atoms})

    tutorials = profile_data.get("tutorials", [])
    if not isinstance(tutorials, list):
        tutorials = []

    if "fission_tutorial" not in tutorials:
        tutorials.append("fission_tutorial")
        await add_data("profile", interaction.user.id, {"tutorials": tutorials})

        container.add_item(discord.ui.TextDisplay(
            "You have successfully performed fission for the first time!\n"
            "</subatomic fission:1412151005088448542> is the first reset layer.\n\n"
            "┌─Fission will reset all currencies except atoms and special quarks\n"
            "├─It will also reset all upgrades and XP (previous to fission)\n"
            "├─You will gain photons (depends on your fission amount), which boost energy and quark gain by 10% each\n"
            "├─ └─You will be able to spend photons using the </shop photons:1412981220635312257>\n"
            "├─Differentiated quarks become 1% more common per fission\n"
            "├─You will also gain 10% more XP per fission\n"
            "├─Your next fissions require atoms that cost more\n"
            "├─ └─The cost of fission also increases exponentially\n"
            "├─As a one time bonus, you get 5% quark chance and 1% electron chance\n"
            "└─ └─This is only for your first fission\n"
            "-# Use </help:1412981220635312252> to view this again!"
        ))
        container.add_item(discord.ui.Separator())

    user_data = await get_user_data("currency", interaction.user.id)
    container.add_item(discord.ui.TextDisplay(
        f"You have successfully performed fission!\n"
        f"Fission resets: {total_resets['fission']}\n"
        f"Photons gained: {total_resets['fission']} (total: {user_data.get('photons', 0)})\n"
        f"Energy, Quarks, Electrons, Protons, and Neutrons have been reset to 0.\n"
        f"Your upgrades have also been reset, along with XP.\n"
        f"{fission_atom_amount} {fission_atom}(s) have been consumed."
    ))

    await interaction.response.send_message(view=view)

@moderate()
@handle_errors()
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
    up_quarks  = user_data.get('up_quark', 0) if user_data else 0
    down_quarks = user_data.get('down_quark', 0) if user_data else 0
    electrons = user_data.get('electrons', 0) if user_data else 0
    protons = user_data.get('protons', 0) if user_data else 0
    neutrons = user_data.get('neutrons', 0) if user_data else 0
    atoms = user_data.get('atoms', {}) if user_data else {}

    container.add_item(discord.ui.Separator())
    subatomic_row = discord.ui.ActionRow()

    probabilize = discord.ui.Button(label="Probabilize")

    probabilize.callback = lambda inter: base_modal(inter, bot, False,
                                                   title="Probabilize Energy",
                                                   callback=probabilize_cb,
                                                   currencies=["energy"],
                                                   inputs=[{
                                                       "label": "Amount",
                                                       "placeholder": "Enter amount of energy to probabilize",
                                                       "key": "amount"
                                                   }])
    
    if energy > 0:
        subatomic_row.add_item(probabilize)

    differentiate = discord.ui.Button(label="Differentiate")

    differentiate.callback = lambda inter: base_modal(inter, bot, False,
                                              title="Differentiate Quarks",
                                              callback=differentiate_cb,
                                              currencies=["quarks", "energy"],
                                              inputs=[{
                                                  "label": "Amount",
                                                  "placeholder": "Enter amount of quarks to differentiate",
                                                  "key": "amount"
                                              }])

    if quarks > 0 and energy > 249:
        subatomic_row.add_item(differentiate)

    condense = discord.ui.Button(label="Condense")

    condense.callback = lambda inter: base_modal(inter, bot, False,
                                              title="Condense Electrons",
                                              callback=condense_cb,
                                              currencies=["energy"],
                                              inputs=[{
                                                  "label": "Amount",
                                                  "placeholder": "Enter amount of electrons to condense",
                                                  "key": "amount"
                                              }])

    if energy > 999:
        subatomic_row.add_item(condense)

    hadronize = discord.ui.Button(label="Hadronize")

    hadronize.callback = lambda inter: base_modal(inter, bot, False,
                                              title="Hadronize Protons and Neutrons",
                                              callback=hadronize_cb,
                                              currencies=["up_quark", "down_quark", "energy"],
                                              inputs=[{
                                                  "label": "Protons",
                                                  "placeholder": "Enter amount of protons to hadronize",
                                                  "key": "protons"
                                              },
                                              {
                                                  "label": "Neutrons",
                                                  "placeholder": "Enter amount of neutrons to hadronize",
                                                  "key": "neutrons"
                                              }])

    hadronize.disabled = True # TODO
    if up_quarks > 1 and down_quarks > 0 and energy > 2499:
        subatomic_row.add_item(hadronize)

    nucleosynthesize = discord.ui.Button(label="Nucleosynthesize")

    nucleosynthesize.callback = lambda inter: base_modal(inter, bot, False,
                                              title="Nucleosynthesis",
                                              callback=nucleosynthesis_cb,
                                              currencies=["energy", "electrons", "protons", "neutrons"],
                                              selects=[{
                                                  "label": "Atom",
                                                  "options": [{"label": atom.title(), "value": atom} for atom in ATOMS.keys()],
                                                  "key": "atom"
                                              }],
                                              inputs=[{
                                                  "label": "Amount",
                                                  "placeholder": "Enter amount of atoms to synthesize",
                                                  "key": "amount"
                                              }])

    nucleosynthesize.disabled = True # TODO
    if protons > 0 and neutrons > 0 and electrons > 0 and energy > 4999:
        subatomic_row.add_item(nucleosynthesize)    

    container.add_item(subatomic_row)

    action_row = discord.ui.ActionRow()
    gain = discord.ui.Button(label="Gain")
    back = discord.ui.Button(label="Back")
    fission = discord.ui.Button(label="Fission", style=discord.ButtonStyle.danger) # TODO

    action_row.add_item(gain)
    action_row.add_item(back)
    
    if energy >= 1_000_000 and atoms.get(list(ATOMS.keys())[0], 0) >= 1: # at least 1 hydrogen
        action_row.add_item(fission)

    gain.callback = lambda inter: gain_cb(inter, bot)
    back.callback = lambda inter: menu_cb(inter, bot)
    fission.callback = lambda inter: fission_cb(inter, bot, confirmed=False)
    container.add_item(action_row)

    await cb(interaction, view, is_command)

class SubatomicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    subatomic_group = UniversalGroup(name="subatomic", description="Subatomic commands")

    @subatomic_group.command(name="menu", description="Open the subatomic menu")
    @handle_errors()
    async def subatomic_command(self, interaction: discord.Interaction):
        await subatomic_cb(interaction, self.bot, True)

    @subatomic_group.command(name="probabilize", description="Attempt to create quarks")
    @app_commands.describe(amount="The amount to probabilize")
    @handle_errors()
    async def probabilize_command(self, interaction: discord.Interaction, amount: int = 0):
        if amount > 0:
            await probabilize_cb(interaction, self.bot, amount)
        else:
            await base_modal(interaction, self.bot, False,
                             title="Probabilize Energy",
                             callback=probabilize_cb,
                             currencies=["energy"],
                             inputs=[{
                                 "label": "Amount",
                                 "placeholder": "Enter amount of energy to probabilize",
                                 "key": "amount"
                             }])

    @subatomic_group.command(name="differentiate", description="Differentiate quarks into specific types")
    @app_commands.describe(amount="The amount to differentiate (Requires 250 energy per quark)")
    @handle_errors()
    async def differentiate_command(self, interaction: discord.Interaction, amount: int = 0):
        if amount > 0:
            await differentiate_cb(interaction, self.bot, amount)
        else:
            await base_modal(interaction, self.bot, False,
                             title="Differentiate Quarks",
                             callback=differentiate_cb,
                             currencies=["quarks", "energy"],
                             inputs=[{
                                 "label": "Amount",
                                 "placeholder": "Enter amount of quarks to differentiate",
                                 "key": "amount"
                             }])

    @subatomic_group.command(name="condense", description="Condense electrons into energy")
    @app_commands.describe(amount="The amount to condense (1000 energy = 1 electron)")
    @handle_errors()
    async def condense_command(self, interaction: discord.Interaction, amount: int = 0):
        if amount > 0:
            await condense_cb(interaction, self.bot, amount)
        else:
            await base_modal(interaction, self.bot, False,
                             title="Condense Electrons",
                             callback=condense_cb,
                             currencies=["energy"],
                             inputs=[{
                                 "label": "Amount",
                                 "placeholder": "Enter amount of electrons to condense",
                                 "key": "amount"
                             }])

    @subatomic_group.command(name="hadronize", description="Hadronize protons and neutrons from quarks")
    @app_commands.describe(protons="The amount of protons to hadronize", neutrons="The amount of neutrons to hadronize")
    @handle_errors()
    async def hadronize_command(self, interaction: discord.Interaction, protons: int = 0, neutrons: int = 0):
        if protons > 0 or neutrons > 0:
            await hadronize_cb(interaction, self.bot, protons, neutrons)
        else:
            await base_modal(interaction, self.bot, False,
                             title="Hadronize Protons and Neutrons",
                             callback=hadronize_cb,
                             currencies=["energy"],
                             inputs=[{
                                 "label": "Protons",
                                 "placeholder": "Enter amount of protons to hadronize",
                                 "key": "protons"
                             }, {
                                 "label": "Neutrons",
                                 "placeholder": "Enter amount of neutrons to hadronize",
                                 "key": "neutrons"
                             }]) 

    @subatomic_group.command(name="nucleosynthesis", description="Synthesize atoms from protons, neutrons, and electrons")
    @app_commands.describe(atom="The atom to synthesize")
    @app_commands.choices(atom=[app_commands.Choice(name=atom.title(), value=atom) for atom in ATOMS.keys()]) # Should be less than 25
    @handle_errors()
    async def nucleosynthesis_command(self, interaction: discord.Interaction, atom: str = ""):
        if atom:
            await nucleosynthesis_cb(interaction, self.bot, atom=atom.lower())
        else:
            await interaction.response.send_message("This feature comes out at least September 10th")
            # https://discord.com/channels/613425648685547541/1040031099860045854/1413566013634646200
            
            """
            options = [{"label": atom.title(), "value": atom} for atom in ATOMS.keys()]
            await base_modal(interaction, self.bot, False,
                            title="Nucleosynthesis",
                            callback=nucleosynthesis_cb,
                            currencies=["energy", "electrons", "protons", "neutrons"],
                            selects=[{
                                "label": "Atom",
                                "options": options,
                                "min_values": 1,
                                "max_values": 1,
                                "placeholder": "Select an atom to synthesize",
                                "key": "atom"
                            }])
            """

    @subatomic_group.command(name="fission", description="Perform fission to reset your progress for photons")
    @handle_errors()
    async def fission_command(self, interaction: discord.Interaction):
        await fission_cb(interaction, self.bot, confirmed=False)
                        
async def setup(bot: commands.Bot):
    await bot.add_cog(SubatomicCog(bot))