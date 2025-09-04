import discord

from typing import Tuple, List, Optional
from .files import get_user_data, user_exists, insert_data

async def base_container(interaction: discord.Interaction) -> discord.ui.Container:
    container = discord.ui.Container()
    container.add_item(discord.ui.TextDisplay(f"-# {interaction.user.name}"))
    container.add_item(discord.ui.Separator())

    color = await get_color(interaction)
    container.accent_color = color
    return container

async def base_view(interaction: discord.Interaction) -> Tuple[discord.ui.LayoutView, discord.ui.Container]:
    view = discord.ui.LayoutView(timeout=None)
    container = await base_container(interaction)
    if not await user_exists("currency", interaction.user.id):
        await insert_data("profile", {"id": interaction.user.id})
        container.add_item(discord.ui.TextDisplay(
            f"Welcome {interaction.user.mention}!\n"
            f"Use </gain:1411612232399327293> to start.\n"
            "**Rules**:\n"
            "-# 1. No macroing. This will result in a permanent ban.\n"
            "-# 2. No exploiting bugs. Ban reason depends on the severity.\n"
            "You may report bugs/appeal bans using </ticket:1411940922333200497>"
        ))
        container.add_item(discord.ui.Separator())

    view.add_item(container)
    return view, container

class Paginator:
    def __init__(self, interaction: discord.Interaction, items: List[discord.ui.Container], per_page: int, header_container: discord.ui.Container = None, footer_components: List[discord.ui.ActionRow] = None):
        self.interaction = interaction
        self.items = items
        self.per_page = per_page
        self.current_page = 0
        self.header_container = header_container
        self.footer_components = footer_components or []

    async def get_view(self) -> discord.ui.LayoutView:
        view = discord.ui.LayoutView(timeout=None)
        
        main_container = await base_container(self.interaction)
        
        if self.header_container:
            for component in self.header_container.children:
                main_container.add_item(component)
            main_container.add_item(discord.ui.Separator())
        
        start = self.current_page * self.per_page
        end = start + self.per_page
        current_items = self.items[start:end]
        
        for i, item in enumerate(current_items):
            for component in item.children:
                main_container.add_item(component)
            
            if i < len(current_items) - 1:
                main_container.add_item(discord.ui.Separator())
        
        if len(self.items) > self.per_page:
            main_container.add_item(discord.ui.Separator())
            action_row = discord.ui.ActionRow()
            
            prev_button = discord.ui.Button(
                label="Previous", 
                disabled=not self.has_previous_page(),
                style=discord.ButtonStyle.secondary
            )
            prev_button.callback = self._previous_callback
            
            total_pages = (len(self.items) - 1) // self.per_page + 1
            page_info = discord.ui.Button(
                label=f"{self.current_page + 1}/{total_pages}",
                disabled=True,
                style=discord.ButtonStyle.secondary
            )
            
            next_button = discord.ui.Button(
                label="Next", 
                disabled=not self.has_next_page(),
                style=discord.ButtonStyle.secondary
            )
            next_button.callback = self._next_callback
            
            action_row.add_item(prev_button)
            action_row.add_item(page_info)
            action_row.add_item(next_button)
            main_container.add_item(action_row)
        
        if self.footer_components:
            main_container.add_item(discord.ui.Separator())
            for footer_component in self.footer_components:
                main_container.add_item(footer_component)
        
        view.add_item(main_container)
        return view

    def has_next_page(self) -> bool:
        return (self.current_page + 1) * self.per_page < len(self.items)

    def has_previous_page(self) -> bool:
        return self.current_page > 0

    async def _next_callback(self, interaction: discord.Interaction):
        if self.has_next_page():
            self.current_page += 1
            new_view = await self.get_view()
            await interaction.response.edit_message(view=new_view)

    async def _previous_callback(self, interaction: discord.Interaction):
        if self.has_previous_page():
            self.current_page -= 1
            new_view = await self.get_view()
            await interaction.response.edit_message(view=new_view)

    async def send(self, is_command: bool = False):
        """Send the paginated message"""
        view = await self.get_view()
        if is_command:
            if self.interaction.response.is_done():
                await self.interaction.followup.send(view=view)
            else:
                await self.interaction.response.send_message(view=view)
        else:
            if self.interaction.response.is_done():
                await self.interaction.followup.edit_message(view=view)
            else:
                await self.interaction.response.edit_message(view=view)

async def get_color(interaction: discord.Interaction) -> Optional[discord.Color]:
    user_id = interaction.user.id
    profile_data = await get_user_data("profile", user_id)
    
    if profile_data:
        return profile_data.get("color", None)
    else:
        return None