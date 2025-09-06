import random
import time

import discord
from discord import app_commands
from discord.ext import commands

from utils import (
    Captcha,
    add_data,
    base_view,
    calculate_level_from_xp,
    cb,
    full_chances,
    full_multipliers,
    get_user_data,
    get_version,
    insert_data,
    moderate,
    universal_command,
)

start = time.time()
captcha_manager = Captcha()

async def check_page_requirements(user_id: int, requirement: str = None) -> bool:
    """Check if a user has completed the required tutorial"""
    if not requirement:
        return True
    
    profile = await get_user_data("profile", user_id, {})
    tutorials = profile.get("tutorials", [])
    
    return requirement in tutorials

@moderate()
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
        return await interaction.response.send_message(view=view, ephemeral=True)
    else:        
        profile_data = await get_user_data("profile", user_id)
        if profile_data:
            profile_data["last_gain"] = now
            await insert_data("profile", profile_data)

        level_info = calculate_level_from_xp(profile_data.get("xp", 0))
        level = level_info["level"]

        # == ENERGY
        multiplier = await full_multipliers("energy", user=interaction.user)

        energy_bonus = level // 2
        energy_gained = int(random.randint(1 + energy_bonus, 10 + energy_bonus) * multiplier)

        result = await add_data("currency", user_id, {"energy": energy_gained})
        total_energy = result["energy"]
        
        # == QUARKS
        quark_chance = await full_chances("quark", user=interaction.user)
        quarks_gained = 0
        
        if quark_chance > 0 and random.random() < (quark_chance / 100):
            quark_bonus = level // 3
            quarks_gained = random.randint(2 + quark_bonus, 5 + quark_bonus)
            await add_data("currency", user_id, {"quarks": quarks_gained})

        # == ELECTRONS
        electron_chance = await full_chances("energy", user=interaction.user)
        electrons_gained = 0

        if electron_chance > 0 and random.random() < (electron_chance / 100):
            electron_bonus = level // 4
            electrons_gained = random.randint(1 + electron_bonus, 3 + electron_bonus)
            await add_data("currency", user_id, {"electrons": electrons_gained})

        # == XP
        # Energy: 1 XP per
        # Quarks: 3 XP per
        total_xp = energy_gained + (quarks_gained * 3) + (electrons_gained * 25)
        await add_data("profile", user_id, {"xp": total_xp, "gains": 1})
        
        quark_result = await get_user_data("currency", user_id)
        total_quarks = quark_result.get("quarks", 0) if quark_result else 0
        total_electrons = quark_result.get("electrons", 0) if quark_result else 0
        
        gain_text = f"**Gained**:\n+{energy_gained:,} energy (total: {total_energy:,})"
        
        if quarks_gained > 0:
            gain_text += f"\n+{quarks_gained:,} quarks (total: {total_quarks:,})"

        if electrons_gained > 0:
            gain_text += f"\n+{electrons_gained:,} electrons (total: {total_electrons:,})"

        gain_text += f"\n+{total_xp:,} EXP"
        container.add_item(discord.ui.TextDisplay(gain_text))

    container.add_item(discord.ui.Separator())
    action_row = discord.ui.ActionRow()

    gain = discord.ui.Button(label="Gain")
    menu = discord.ui.Button(label="Menu")

    action_row.add_item(gain)
    action_row.add_item(menu)

    gain.callback = lambda inter: gain_cb(inter, bot)
    menu.callback = lambda inter: menu_cb(inter, bot)

    container.add_item(action_row)

    await cb(interaction, view, True)

@moderate()
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

@moderate()
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
        f"**Guilds**: {len(bot.guilds):,}\n"
        f"**Users**: {len(bot.users):,}\n"
        f"**Shards**: {bot.shard_count}\n"
        f"**Version**: {get_version()}"
    ))
    container.add_item(discord.ui.Separator())
    action_row = discord.ui.ActionRow()
    help = discord.ui.Button(label="Help")
    back = discord.ui.Button(label="Back")
    action_row.add_item(discord.ui.Button(label="Website", url="https://planck-bot.github.io/", style=discord.ButtonStyle.link))
    action_row.add_item(discord.ui.Button(label="Discord", url="https://discord.gg/SbXtQDQYhf", style=discord.ButtonStyle.link))
    action_row.add_item(discord.ui.Button(label="Invite", url="https://discord.com/oauth2/authorize?client_id=768208737013071883", style=discord.ButtonStyle.link))
    action_row.add_item(help)
    action_row.add_item(back)
    help.callback = lambda inter: help_cb(inter, bot)
    back.callback = lambda inter: menu_cb(inter, bot)
    container.add_item(action_row)
    await cb(interaction, view, is_command)

@moderate()
async def menu_cb(interaction: discord.Interaction, bot: commands.Bot = None, is_command: bool = False):
    from .shop import shop_cb
    from .subatomic import subatomic_cb
    view, container = await base_view(interaction)
    action_row = discord.ui.ActionRow()
    subatomic = discord.ui.Button(label="Subatomic")
    atomic = discord.ui.Button(label="Atomic")

    action_row.add_item(subatomic)
    if 0==1:
        # TODO: Later on include a check here
        # After a user gets their first atom?
        action_row.add_item(atomic)

    subatomic.callback = lambda inter: subatomic_cb(inter, bot)

    container.add_item(action_row)

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

@moderate()
async def multipliers_cb(interaction: discord.Interaction, bot: commands.Bot = None, is_command: bool = False):
    view, container = await base_view(interaction)

    energy = await full_multipliers("energy", user=interaction.user)
    quarks = await full_multipliers("quark", user=interaction.user)
    quarks_chance = await full_chances("quark", user=interaction.user)

    container.add_item(discord.ui.TextDisplay(
        f"**XP**: 1x\n"
        f"**Energy**: {energy:.2f}x\n"
        f"**Quarks**: {quarks:.2f}x ({quarks_chance:.2f}%)\n"
    ))
    container.add_item(discord.ui.Separator())
    action_row = discord.ui.ActionRow()
    back = discord.ui.Button(label="Back")
    action_row.add_item(back)
    back.callback = lambda inter: profile_cb(inter, bot)
    container.add_item(action_row)
    await cb(interaction, view, is_command)

# @moderate()
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
                        "┌─You will only use energy and quarks here\n"
                        "└─Upgrades may seem small, but they add up!"
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
                        "┌─Use </gain:1412981220635312249> to start gaining energy\n"
                        "├─Energy is the basic currency in this stage\n"
                        "├─Gain experience (XP) with each action to level up\n"
                        "└─ └─Higher levels unlock new features and multipliers"
                    )
                },
                "Probabilize": {
                    "title": "First steps",
                    "content": (
                        "</subatomic probabilize:1412151005088448542> is how you will gain quarks!\n\n"
                        "┌─Has a chance (5% base) to convert energy into quarks!\n"
                        "│  └─You can upgrade the chance using shop upgrades\n"
                        "│      └─Some might even allow you to get quarks from </gain:1412981220635312249>!\n"
                        "└─You will also need to **differentiate** them later!"
                    ),
                    "requirement": "probabilize_tutorial"
                },
                "Differentiate": {
                    "title": "How to tell apart quarks",
                    "content": (
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
                        "└─ └─Top Quarks: 0.001%"
                    ),
                    "requirement": "differentiate_tutorial"
                },
                "Condenser": {
                    "title": "Zip Zap Electricity",
                    "content": (
                        "</subatomic condense:1412151005088448542> is how you're going to make electrons\n\n"
                        "┌─Requires a LOT of energy (1000)\n"
                        "├─Electrons will be used to create **atoms** later!\n"
                        "└─There will also be shop items you can buy with them."
                    ),
                    "requirement": "condenser_tutorial"
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
        back.callback = lambda inter: info_cb(inter, bot)
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

    async def _create_captcha_view(self, interaction: discord.Interaction, components=None, title=None, message=None, file=None, show_regenerate=True):
        view, container = await base_view(interaction)
        
        if title or message:
            text = []
            if title:
                text.append(f"**{title}**")
            if message:
                text.append(message)
            container.add_item(discord.ui.TextDisplay("\n\n".join(text)))
        
        if components:
            container.add_item(components[0])
            container.add_item(components[1])
            container.add_item(discord.ui.TextDisplay(
                "-# Captchas are case sensitive. Make sure images are enabled in discord settings "
                "(Settings > App Settings > Chat > Display Images)"
            ))
            
        if show_regenerate:
            container.add_item(discord.ui.Separator())
            action_row = discord.ui.ActionRow()
            regen_button = discord.ui.Button(label="Regenerate Captcha")
            regen_button.callback = lambda inter: self._handle_regenerate(inter, interaction.user.id)
            action_row.add_item(regen_button)
            container.add_item(action_row)
            
        return view, container, file

    async def _handle_regenerate(self, interaction: discord.Interaction, user_id: int):
        if interaction.user.id != user_id:
            await interaction.response.send_message(
                "This is not your captcha!", ephemeral=True
            )
            return
            
        result = await captcha_manager.regenerate_captcha(user_id)
        if result["success"]:
            components, file = await captcha_manager.get_captcha_container_and_file(user_id)
            view, _, _ = await self._create_captcha_view(
                interaction,
                components=components,
                file=file
            )
            await interaction.response.edit_message(view=view, attachments=[file])
        else:
            await interaction.response.send_message(result["message"], ephemeral=True)

    @universal_command(name="verify", description="Verify a captcha or regenerate it")
    @app_commands.describe(captcha="Enter the captcha text or 'REGEN' to regenerate")
    async def verify_command(self, interaction: discord.Interaction, captcha: str):
        user_id = interaction.user.id
        
        if user_id not in captcha_manager.active_captchas:
            view, _, _ = await self._create_captcha_view(
                interaction,
                title="No Active Captcha",
                message="You don't have an active captcha.",
                show_regenerate=False
            )
            await cb(interaction, view, True)
            return
        
        if captcha.upper() == "REGEN":
            result = await captcha_manager.regenerate_captcha(user_id)
            if result["success"]:
                components, file = await captcha_manager.get_captcha_container_and_file(user_id)
                view, container, _ = await self._create_captcha_view(
                    interaction,
                    components=components,
                    title="Captcha Regenerated",
                    file=file
                )
                await interaction.response.send_message(view=view, files=[file])
            else:
                view, container, _ = await self._create_captcha_view(
                    interaction,
                    title="Regeneration Failed",
                    message=result["message"],
                    show_regenerate=False
                )
                await cb(interaction, view, True)
            return
        
        result = await captcha_manager.verify_captcha(user_id, captcha)
        action = result["action"]
        
        if action == "auto_regen":
            view, _, _ = await self._create_captcha_view(
                interaction,
                title="Auto-Regenerated",
                message=result["message"],
                show_regenerate=False
            )
            await interaction.response.send_message(view=view)
            
            components, file = await captcha_manager.get_captcha_container_and_file(user_id)
            view, _, _ = await self._create_captcha_view(
                interaction,
                components=components,
                file=file
            )
            await interaction.followup.send(view=view, files=[file])
        else:
            titles = {
                "success": "Captcha Solved",
                "banned": "Banned",
                "expired": "Captcha Expired",
                "retry": "Incorrect"
            }
            messages = {
                "success": f"{result['message']} You can now use bot commands normally.",
                "expired": f"{result['message']} Contact an administrator for a new one.",
                "banned": result["message"],
                "retry": result["message"]
            }

            view, _, _ = await self._create_captcha_view(
                interaction,
                title=titles.get(action, "Error"),
                message=messages.get(action, result.get("message", "Unknown error")),
                show_regenerate=False
            )
            await cb(interaction, view, True)

async def setup(bot: commands.Bot):
    await bot.add_cog(GlobalCog(bot))