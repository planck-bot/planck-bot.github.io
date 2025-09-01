import discord
from .formulas import calculate_level_from_xp
from .files import get_user_data

async def full_multipliers(multiplier: str, **kwargs) -> float:
    m = 1.0

    if multiplier == "energy":
        m = await get_energy_multiplier(kwargs.get("user"), m)

    user = kwargs.get("user")
    if user:
        profile_data = await get_user_data("profile", user.id)
        xp = profile_data.get("xp", 0) if profile_data else 0
    else:
        xp = kwargs.get("xp", 0)
    
    level_info = calculate_level_from_xp(xp)
    level = level_info["level"]

    boosted = m * (1 + 0.01 * (level - 1))
    return boosted

async def _get_all_upgrades(user: discord.User):
    upgrades = await get_user_data("upgrades", user.id)
    if upgrades is None:
        upgrades = {}
    return upgrades

async def get_energy_multiplier(user: discord.User, base: float = 1.0):
    upgrades = await _get_all_upgrades(user)

    base += upgrades.get("energy_manipulator", 0) // 10 # 10% every upgrade (0.10)

    return base