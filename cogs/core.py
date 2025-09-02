import discord
from discord import app_commands
from discord.ext import commands

import time
import random

from utils import universal_command, base_view, add_data, insert_data, calculate_level_from_xp, get_user_data, full_multipliers, cb, get_version
start = time.time()

async def check_page_requirements(user_id: int, requirements: dict) -> bool:
    """Check if a user meets the currency requirements for a page"""
    if not requirements:
        return True
    
    user_currency = await get_user_data("currency", user_id)
    if not user_currency:
        return False
    
    for currency, required_amount in requirements.items():
        user_amount = user_currency.get(currency, 0)
        if user_amount < required_amount:
            return False
    
    return True

async def gain_cb(interaction: discord.Interaction, bot: commands.Bot = None):
    user_id = interaction.user.id
    view, container = await base_view(interaction)

    profile_data = await get_user_data("profile", user_id)
    now = time.time()
    last_gain = profile_data.get("last_gain", 0) if profile_data else 0

    if now - last_gain < 2:
        container.add_item(discord.ui.TextDisplay(
            f"Please wait {2 - (now - last_gain):.2f}s before gaining again."
        ))
        ephemeral = True
    else:
        await add_data("profile", user_id, {"xp": 1, "gains": 1})
        
        profile_data = await get_user_data("profile", user_id)
        if profile_data:
            profile_data["last_gain"] = now
            await insert_data("profile", profile_data)

        multiplier = await full_multipliers("energy", user=interaction.user)
        energy_gained = int(random.randint(1, 10) * multiplier)

        result = await add_data("currency", user_id, {"energy": energy_gained})
        total_energy = result["energy"]
        
        container.add_item(discord.ui.TextDisplay(
            f"**Gained**:\n"
            f"+{energy_gained} energy (total: {total_energy})\n"
            f"+1 EXP"
        ))
        ephemeral = False

    container.add_item(discord.ui.Separator())
    action_row = discord.ui.ActionRow()

    gain = discord.ui.Button(label="Gain")
    menu = discord.ui.Button(label="Menu")

    action_row.add_item(gain)
    action_row.add_item(menu)

    gain.callback = lambda inter: gain_cb(inter, bot)
    menu.callback = lambda inter: menu_cb(inter, bot)

    container.add_item(action_row)
    if interaction.response.is_done():
        await interaction.followup.send(view=view, ephemeral=ephemeral)
    else:
        await interaction.response.send_message(view=view, ephemeral=ephemeral)

async def profile_cb(interaction: discord.Interaction, bot: commands.Bot = None, is_command: bool = False):
    user_id = interaction.user.id
    
    profile_data = await get_user_data("profile", user_id)
    if profile_data is None:
        profile_data = {"xp": 1, "gains": 1}
    
    level_info = calculate_level_from_xp(profile_data.get("xp", 0))
    
    view, container = await base_view(interaction)
    container.add_item(discord.ui.TextDisplay(
        f"**{interaction.user.display_name}'s Profile**\n"
        f"**Level:** {level_info['level']} ({level_info['xp_progress']:,} / {level_info['xp_needed'] + level_info['xp_progress']:,})\n"
        f"**Gains:** {profile_data.get('gains', 0):,}"
    ))
    container.add_item(discord.ui.Separator())
    action_row = discord.ui.ActionRow()

    multipliers = discord.ui.Button(label="Multipliers")
    back = discord.ui.Button(label="Back")

    action_row.add_item(multipliers)
    action_row.add_item(back)

    multipliers.callback = lambda inter: multipliers_cb(inter, bot)
    back.callback = lambda inter: menu_cb(inter, bot)
    container.add_item(action_row)
    await cb(interaction, view, is_command)

async def info_cb(interaction: discord.Interaction, bot: commands.Bot = None, is_command: bool = False):
    view, container = await base_view(interaction)

    def runtime(seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours}h {minutes}m {seconds}s"
    
    container.add_item(discord.ui.TextDisplay(
        "This bot is developed by <@721151215010054165>\n"
        f"**Runtime**: {runtime(int(time.time() - start))}\n"
        f"**Guilds**: {len(bot.guilds)}\n"
        f"**Users**: {len(bot.users)}\n"
        f"**Shards**: {bot.shard_count}\n"
        f"**Version**: {get_version()}"
    ))
    container.add_item(discord.ui.Separator())
    action_row = discord.ui.ActionRow()
    back = discord.ui.Button(label="Back")
    action_row.add_item(back)
    back.callback = lambda inter: menu_cb(inter, bot)
    container.add_item(action_row)
    await cb(interaction, view, is_command)

async def menu_cb(interaction: discord.Interaction, bot: commands.Bot = None, is_command: bool = False):
    from .shop import shop_cb
    view, container = await base_view(interaction)
    action_row = discord.ui.ActionRow()

    gain = discord.ui.Button(label="Gain")
    profile = discord.ui.Button(label="Profile")
    info = discord.ui.Button(label="Info")
    leaderboard = discord.ui.Button(label="Leaderboard")
    shop = discord.ui.Button(label="Shop")

    action_row.add_item(gain)
    action_row.add_item(profile)
    action_row.add_item(info)
    action_row.add_item(leaderboard)
    action_row.add_item(shop)

    gain.callback = lambda inter: gain_cb(inter, bot)
    profile.callback = lambda inter: profile_cb(inter, bot)
    info.callback = lambda inter: info_cb(inter, bot)
    leaderboard.disabled = True
    shop.callback = lambda inter: shop_cb(inter, bot)
    # leaderboard.callback = lambda inter: leaderboard_cb(inter)

    container.add_item(action_row)
    await cb(interaction, view, is_command)

async def multipliers_cb(interaction: discord.Interaction, bot: commands.Bot = None, is_command: bool = False):
    view, container = await base_view(interaction)

    energy = await full_multipliers("energy", user=interaction.user)
    container.add_item(discord.ui.TextDisplay(
        f"**Energy**: {energy:.2f}x"
    ))
    container.add_item(discord.ui.Separator())
    action_row = discord.ui.ActionRow()
    back = discord.ui.Button(label="Back")
    action_row.add_item(back)
    back.callback = lambda inter: profile_cb(inter, bot)
    container.add_item(action_row)
    await cb(interaction, view, is_command)

async def help_cb(interaction: discord.Interaction, bot: commands.Bot = None, is_command: bool = False, stage: str = None, page = "Main"):
    view, container = await base_view(interaction)

    help_content = {
        "main": {
            "title": "Help",
            "description": (
                "**Main Commands:**\n"
                "</gain:1411612232399327293> - Gain matter. This is the command you will use to get anything\n"
                "</profile:1411619125154811966> - View your profile\n"
                "</info:1411592664331190384> - Get information about the bot\n"
                "</ticket:1411940922333200497> - Create a ticket either to report or appeal\n\n"
                "Select a stage below to get specific help for that stage!"
            )
        },
        "shop": {
            "title": "Shop",
            "pages": {
                "Regular": {
                    "title": "Regular Shop",
                    "content": (
                        "This is the regular shop!\n\n"
                        "🔹 You will only use energy and quarks here\n"
                        "🔹 Upgrades may seem small, but they add up!"
                    )
                }
            }
        },
        "subatomic": {
            "title": "Subatomic",
            "pages": {
                "Main": {
                    "title": "Getting Started",
                    "content": (
                        "Welcome to the subatomic stage! This is the beginning of the game.\n\n"
                        "🔹 Use </gain:1411612232399327293> to start gaining energy\n"
                        "🔹 Energy is the basic currency in this stage\n"
                        "🔹 Gain experience (XP) with each action to level up\n"
                        "🔹 Higher levels unlock new features and multipliers"
                    )
                },
                "Probabilitize": {
                    "title": "First steps",
                    "content": (
                        "**Probabilitize** is how you will gain quarks:\n\n"
                        "🔹 Has a chance to convert energy into quarks!\n"
                        "🔹 You can upgrade the chance later on\n"
                        "🔹 You will also need to **differentiate** them later!\n"
                    ),
                    "requirement": {
                        "energy": 1
                    }
                },
                "Differentiate": {
                    "title": "How to tell apart quarks",
                    "content": (
                        "**Differentiating** is how you will tell apart quarks!\n\n"
                        "🔹 Allows you to create up and down quarks\n"
                        "🔹 They will be used to create **protons** and **neutrons**\n"
                        "🔹 You will also unlock more types of quarks later on!"
                    ),
                    "requirement": {
                        "quarks": 1
                    }
                }
            }
        }
    }

    if stage is None:
        content = help_content["main"]
        container.add_item(discord.ui.TextDisplay(
            f"**{content['title']}**\n\n{content['description']}"
        ))
        
        container.add_item(discord.ui.Separator())
        stage_row = discord.ui.ActionRow()
        stage_select = discord.ui.Select(
            placeholder="Select a stage for specific help...",
            options=[
                discord.SelectOption(
                    label="Subatomic", 
                    description="The beginning game! Good luck, have fun!", 
                    value="subatomic", 
                    emoji="<:energy:1412139064559140956>"
                ),
                discord.SelectOption(
                    label="Shop", 
                    description="The shop provides many important upgrades!", 
                    value="shop", 
                    emoji="🏪"
                ),
            ]
        )
        stage_select.callback = lambda inter: help_stage_select_cb(inter, bot)
        stage_row.add_item(stage_select)
        container.add_item(stage_row)
        
        back_row = discord.ui.ActionRow()
        back = discord.ui.Button(label="Back")
        back.callback = lambda inter: menu_cb(inter, bot)
        back_row.add_item(back)
        container.add_item(back_row)
        
    else:
        stage_data = help_content.get(stage, {})
        pages = stage_data.get("pages", {})
        
        user_id = interaction.user.id
        accessible_pages = {}
        for page_key, page_data in pages.items():
            requirements = page_data.get("requirement", {})
            if await check_page_requirements(user_id, requirements):
                accessible_pages[page_key] = page_data
        
        page_keys = list(accessible_pages.keys())
        total_pages = len(accessible_pages)
        
        if isinstance(page, int):
            if 1 <= page <= len(page_keys):
                current_page_key = page_keys[page - 1]
            else:
                current_page_key = page_keys[0] if page_keys else None
        else:
            current_page_key = page if page in accessible_pages else (page_keys[0] if page_keys else None)
        
        if current_page_key and current_page_key in accessible_pages:
            page_data = accessible_pages[current_page_key]
            current_page_index = page_keys.index(current_page_key) + 1
            container.add_item(discord.ui.TextDisplay(
                f"**{stage_data['title']}**\n\n"
                f"**{page_data['title']}**\n{page_data['content']}\n\n"
                f"Page {current_page_index}/{total_pages} ({current_page_key})"
            ))
        else:
            current_page_key = None
            container.add_item(discord.ui.TextDisplay(
                f"**{stage_data['title']}**\n\nPage not found!"
            ))
        
        container.add_item(discord.ui.Separator())
        stage_row = discord.ui.ActionRow()
        stage_select = discord.ui.Select(
            placeholder="Switch to another stage...",
            options=[
                discord.SelectOption(
                    label="Subatomic", 
                    description="The beginning game! Good luck, have fun!", 
                    value="subatomic", 
                    emoji="<:energy:1412139064559140956>"
                ),
                discord.SelectOption(
                    label="Main Help", 
                    description="Go back to the main help page", 
                    value="main", 
                    emoji="📚"
                ),
                discord.SelectOption(
                    label="Shop", 
                    description="The shop provides many important upgrades!", 
                    value="shop", 
                    emoji="🏪"
                ),
            ]
        )
        stage_select.callback = lambda inter: help_stage_select_cb(inter, bot)
        stage_row.add_item(stage_select)
        container.add_item(stage_row)
        
        if total_pages > 1:
            page_keys_to_show = page_keys[:20]
            
            for row_start in range(0, len(page_keys_to_show), 5):
                page_row = discord.ui.ActionRow()
                row_page_keys = page_keys_to_show[row_start:row_start + 5]
                
                for page_key in row_page_keys:
                    btn_style = discord.ButtonStyle.primary if page_key == current_page_key else discord.ButtonStyle.secondary
                    page_btn = discord.ui.Button(
                        label=page_key,
                        style=btn_style,
                        disabled=(page_key == current_page_key)
                    )
                    page_btn.callback = lambda inter, p=page_key: help_cb(inter, bot, False, stage, p)
                    page_row.add_item(page_btn)
                
                container.add_item(page_row)
        
        back_row = discord.ui.ActionRow()
        back = discord.ui.Button(label="Back")
        back.callback = lambda inter: help_cb(inter, bot, False)
        back_row.add_item(back)
        container.add_item(back_row)

    if is_command:
        if interaction.response.is_done():
            await interaction.followup.send(view=view)
        else:
            await interaction.response.send_message(view=view)
    else:
        # unreliable is_done()
        await cb(interaction, view, is_command)

async def help_stage_select_cb(interaction: discord.Interaction, bot: commands.Bot):
    """Handle stage selection from the dropdown"""
    stage = interaction.data["values"][0]
    
    if stage == "main":
        await help_cb(interaction, bot, False)
    else:
        await help_cb(interaction, bot, False, stage)

class GlobalCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @universal_command(name="ping", description="Check the bot ping")
    # @cooldown(15.0)
    async def ping_command(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{self.bot.latency * 1000:.2f} ms")

    @universal_command(name="gain", description="Gain matter")
    async def gain_command(self, interaction: discord.Interaction):
        await gain_cb(interaction, self.bot)

    @universal_command(name="profile", description="View your profile")
    async def profile_command(self, interaction: discord.Interaction):
        await profile_cb(interaction, self.bot, True)

    @universal_command(name="info", description="Get information about the bot")
    async def info_command(self, interaction: discord.Interaction):
        await info_cb(interaction, self.bot, True)

    @universal_command(name="help", description="Use this command if you are stuck at a stage")
    async def help_command(self, interaction: discord.Interaction):
        await help_cb(interaction, self.bot, True)

    @universal_command(name="ticket", description="Create a ticket either to report or appeal")
    @app_commands.describe(report_type="The type of ticket (report/appeal)", reason_or_evidence="The reason or evidence for the ticket")
    async def ticket_command(self, interaction: discord.Interaction, report_type: str, reason_or_evidence: str):
        ...

async def setup(bot: commands.Bot):
    await bot.add_cog(GlobalCog(bot))