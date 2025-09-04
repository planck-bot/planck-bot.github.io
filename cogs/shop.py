import discord
from discord import app_commands
from discord.ext import commands

from typing import Tuple, Optional

from utils import UniversalGroup, read_json, base_view, add_data, calculate_level_from_xp, get_user_data, cb, Paginator, moderate

def sanitize_item_name(item_name: str) -> str:
    """Convert item name to database-safe format (lowercase with underscores)"""
    return item_name.lower().replace(" ", "_").replace("-", "_")

async def get_unlocked_items(user: discord.User) -> list:
    user_data = await get_user_data("profile", user.id)
    if user_data is None:
        user_data = {"xp": 1, "gains": 1}
    
    level_info = calculate_level_from_xp(user_data.get("xp", 0))

    unlocked_items = []
    shop_data = await read_json("data/shop.json")
    for item, data in shop_data["regular"].items():
        if level_info['level'] >= data["requirements"]["level"]:
            unlocked_items.append(item)

    return unlocked_items

async def get_user_upgrade_count(user_id: int, item: str) -> int:
    """Get how many times a user has bought a specific upgrade"""
    user_data = await get_user_data("upgrades", user_id)
    if user_data is None:
        return 0
    db_item_name = sanitize_item_name(item)
    return user_data.get(db_item_name, 0)

async def calculate_current_price(item_data: dict, current_count: int) -> dict:
    """Calculate the current price based on how many times the item was bought"""
    current_prices = {}
    
    for currency, base_price in item_data["price"].items():
        increment = item_data["increments"][currency]
        
        if increment.startswith("+"):
            # Additive increment: +10 means +10 each time
            add_amount = int(increment[1:])
            current_prices[currency] = base_price + (add_amount * current_count)
        elif increment.startswith("x"):
            # Multiplicative increment: x2 means double each time
            multiplier = float(increment[1:])
            current_prices[currency] = int(base_price * (multiplier ** current_count))
        elif increment.startswith("%"):
            # Percentage increment: %20 means +20% each time
            percentage = float(increment[1:]) / 100
            current_prices[currency] = int(base_price * ((1 + percentage) ** current_count))
        else:
            current_prices[currency] = base_price
    
    return current_prices

async def buy_item(user: discord.User, item: str) -> Tuple[bool, Optional[str]]:
    unlocked_items = await get_unlocked_items(user)
    if item not in unlocked_items:
        return False, "You have not unlocked this item."

    shop_data = await read_json("data/shop.json")
    item_data = shop_data["regular"].get(item)
    if not item_data:
        return False, "Item not found."

    user_id = user.id
    current_count = await get_user_upgrade_count(user_id, item)
    
    if current_count >= item_data["max"]:
        return False, "You have reached the maximum purchases for this item."
    
    current_prices = await calculate_current_price(item_data, current_count)
    user_currency = await get_user_data("currency", user_id)
    
    if user_currency is None:
        return False, "You do not have any currency."
    
    for currency, price in current_prices.items():
        if user_currency.get(currency, 0) < price:
            return False, f"You do not have enough {currency} for this upgrade."

    currency_deductions = {currency: -price for currency, price in current_prices.items()}
    await add_data("currency", user_id, currency_deductions)

    db_item_name = sanitize_item_name(item)
    await add_data("upgrades", user_id, {db_item_name: 1})
    return True, None

@moderate()
async def shop_cb(interaction: discord.Interaction, bot: commands.Bot, is_command: bool = False, preserve_page: int = 0):
    user_id = interaction.user.id
    unlocked_items = await get_unlocked_items(interaction.user)
    shop_data = await read_json("data/shop.json")
    user_currency = await get_user_data("currency", user_id)
    current_energy = user_currency.get("energy", 0) if user_currency else 0
    current_quarks = user_currency.get("quarks", 0) if user_currency else 0
    current_electrons = user_currency.get("electrons", 0) if user_currency else 0

    header_container = discord.ui.Container()
    header_container.add_item(discord.ui.TextDisplay(
        f"**Currencies:**\n"
        f"Energy: {current_energy:,}\n"
        f"Quarks: {current_quarks:,}\n"
        f"Electrons: {current_electrons:,}\n"
    ))

    item_containers = []
    for item_name in unlocked_items:
        item_data = shop_data["regular"][item_name]
        current_count = await get_user_upgrade_count(user_id, item_name)
        current_prices = await calculate_current_price(item_data, current_count)
        
        container = discord.ui.Container()
        
        price_text = []
        for currency, price in current_prices.items():
            price_text.append(f"{price:,} {currency}")
        price_display = " + ".join(price_text)
        
        is_maxed = current_count >= item_data["max"]
        has_enough_currency = True
        
        if user_currency:
            for currency, price in current_prices.items():
                if user_currency.get(currency, 0) < price:
                    has_enough_currency = False
                    break
        else:
            has_enough_currency = False
        
        if is_maxed:
            buy_button = discord.ui.Button(
                label="MAX",
                style=discord.ButtonStyle.success,
                disabled=True
            )
        elif not has_enough_currency:
            buy_button = discord.ui.Button(
                label=f"Need {price_display}",
                style=discord.ButtonStyle.danger,
                disabled=True
            )
        else:
            buy_button = discord.ui.Button(
                label=f"{price_display}",
                style=discord.ButtonStyle.primary,
                disabled=False
            )
        
        section = discord.ui.Section(accessory=buy_button)
        
        section.add_item(discord.ui.TextDisplay(
            f"**{item_name.title()}** ({current_count}/{item_data['max']})\n"
            f"{item_data['description']}\n"
        ))
        
        def create_buy_callback(item, paginator_ref):
            async def buy_callback(inter):
                success, message = await buy_item(inter.user, item)
                if success:
                    current_page = paginator_ref[0].current_page if paginator_ref[0] else 0
                    await shop_cb(inter, bot, False, current_page)
                else:
                    await inter.response.send_message(f"❌ {message}", ephemeral=True)
            return buy_callback
        
        container._buy_callback_item = item_name
        container.add_item(section)
        container._buy_button = buy_button
        
        item_containers.append(container)
    
    if not item_containers:
        view, container = await base_view(interaction)
        container.add_item(discord.ui.TextDisplay("No items available at your current level."))
        await cb(interaction, view, is_command)
        return
    
    ITEMS_PER_PAGE = 5 # in case i forget
    
    footer_components = []
    
    button_row = discord.ui.ActionRow()

    gain = discord.ui.Button(label="Gain")
    back = discord.ui.Button(label="Back")
    button_row.add_item(gain)
    button_row.add_item(back)

    from .core import gain_cb, menu_cb
    gain.callback = lambda inter: gain_cb(inter, bot)
    back.callback = lambda inter: menu_cb(inter, bot)

    footer_components.append(button_row)
        
    shop_type_select = discord.ui.Select(
        placeholder="Choose shop type...",
        options=[
            discord.SelectOption(
                label="Regular",
                description="Standard shop items",
                value="regular",
                default=True
            )
        ]
    )
    
    async def shop_type_callback(interaction_select: discord.Interaction):
        current_page = paginator.current_page if 'paginator' in locals() else 0
        await shop_cb(interaction_select, bot, False, current_page)
    
    shop_type_select.callback = shop_type_callback
    
    select_row = discord.ui.ActionRow()
    select_row.add_item(shop_type_select)
    footer_components.append(select_row)
    
    paginator = Paginator(interaction, item_containers, ITEMS_PER_PAGE, header_container, footer_components)
    
    if preserve_page > 0:
        paginator.current_page = min(preserve_page, (len(item_containers) - 1) // ITEMS_PER_PAGE)
    
    paginator_ref = [paginator]
    for container in item_containers:
        if hasattr(container, '_buy_button') and hasattr(container, '_buy_callback_item'):
            container._buy_button.callback = create_buy_callback(container._buy_callback_item, paginator_ref)
    
    await paginator.send(is_command)

class ShopCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    shop_cog = UniversalGroup(name="shop", description="Shop related commands")

    @shop_cog.command(name="regular", description="Show the regular shop")
    async def regular_shop(self, interaction: discord.Interaction):
        await shop_cb(interaction, self.bot, True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ShopCog(bot))