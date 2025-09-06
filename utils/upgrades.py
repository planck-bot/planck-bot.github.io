import discord
from .formulas import calculate_level_from_xp
from .files import get_user_data

class BaseUpgradeManager:
    """
    Base class for managing user upgrades with caching functionality.
    """
    
    def __init__(self, user: discord.User):
        self.user = user
        self._upgrades = None
        self._resets = None
        self._profile_data = None
    
    async def _load_upgrades(self):
        """Load upgrades data from database if not already cached."""
        if self._upgrades is None:
            self._upgrades = await get_user_data("upgrades", self.user.id)
            if self._upgrades is None:
                self._upgrades = {}
        return self._upgrades

    async def _load_resets(self):
        """Load resets data from database if not already cached."""
        if self._resets is None:
            self._resets = await get_user_data("resets", self.user.id)
            if self._resets is None:
                self._resets = {}
        return self._resets

    async def _load_profile_data(self):
        """Load profile data from database if not already cached."""
        if self._profile_data is None:
            self._profile_data = await get_user_data("profile", self.user.id)
            if self._profile_data is None:
                self._profile_data = {}
        return self._profile_data
    
    async def get_level_info(self):
        """Get user level information."""
        profile_data = await self._load_profile_data()
        xp = profile_data.get("xp", 0)
        return calculate_level_from_xp(xp)

class MultiplierManager(BaseUpgradeManager):
    """
    Manages multiplier calculations based on user upgrades and level.
    """

    async def get_xp_multiplier(self, base: float = 1.0) -> float:
        resets = await self._load_resets()
        base += resets.get("fission", 0) * 0.1
        return base
    
    async def get_energy_multiplier(self, base: float = 1.0) -> float:
        upgrades = await self._load_upgrades()
        base += upgrades.get("energy_manipulator", 0) / 10  # 10% every upgrade (0.10) additive
        base += base * (upgrades.get("undercharged", 0) / 4)  # 25% every upgrade (0.25) compounding
        base += base * (upgrades.get("subatomic_efficiency", 0) / 2)  # 50% every upgrade (0.50) compounding

        resets = await self._load_resets()
        base += resets.get("fission", 0) * 0.1
        return base
    
    async def get_quark_multiplier(self, base: float = 1.0) -> float:
        upgrades = await self._load_upgrades()
        base += upgrades.get("quantum_manipulator", 0) / 20  # 5% every upgrade (0.05)
        base += base * (upgrades.get("electric_field", 0) / 10)  # 10% every upgrade (0.10) compounding
        base += base * (upgrades.get("subatomic_efficiency", 0) / 4)  # 25% every upgrade (0.25) compounding

        resets = await self._load_resets()
        base += resets.get("fission", 0) * 0.1
        return base

    async def get_quark_differentiation_multiplier(self, base: float) -> float:
        upgrades = await self._load_upgrades()
        base *= (2 ** upgrades.get("quark_differentiation", 0))  # doubles every upgrade

        resets = await self._load_resets()
        base *= 1 + (resets.get("fission", 0) * 0.01) # 1% per fission reset

        return base

    async def get_full_multiplier(self, multiplier_type: str, base: float = 1.0) -> float:
        if multiplier_type == "xp":
            m = await self.get_xp_multiplier(base)
        elif multiplier_type == "energy":
            m = await self.get_energy_multiplier(base)
        elif multiplier_type in ["quarks", "quark"]:
            m = await self.get_quark_multiplier(base)
        elif multiplier_type == "quark_differentiation":
            m = await self.get_quark_differentiation_multiplier(base)
        else:
            m = base
        
        level_info = await self.get_level_info()
        level = level_info["level"]

        boosted = m * (1.1 ** (level // 10)) # rather than 1% per level
        # you get the boost every 10 levels
        # however, it compounds

        return boosted

class ChanceManager(BaseUpgradeManager):
    """
    Manages chance calculations based on user upgrades.
    """
    
    async def get_quark_chance(self, base: float = 0.0) -> float:
        upgrades = await self._load_upgrades()
        base += upgrades.get("quantum_luck", 0)
        base += upgrades.get("electric_field", 0) * 2

        resets = await self._load_resets()
        base += resets.get("fission", 0) * 5
        return base

    async def get_electron_chance(self, base: float = 0.0) -> float:
        upgrades = await self._load_upgrades()
        base += upgrades.get("subatomic_efficiency", 0) * 2

        resets = await self._load_resets()
        base += resets.get("fission", 0) * 1
        return base
    
    async def get_full_chance(self, chance_type: str, base: float = 0.0) -> float:
        if chance_type == "quark":
            return await self.get_quark_chance(base)
        elif chance_type == "electron":
            return await self.get_electron_chance(base)
        
        return base


async def full_multipliers(multiplier: str, **kwargs) -> float:
    """
    Calculate full multipliers including level bonuses.
    """
    user = kwargs.get("user")
    
    if user:
        manager = MultiplierManager(user)
        return await manager.get_full_multiplier(multiplier)
    else:
        xp = kwargs.get("xp", 0)
        level_info = calculate_level_from_xp(xp)
        level = level_info["level"]
        base_multiplier = 1.0
        boosted = base_multiplier * (1 + 0.01 * (level - 1))
        return boosted


async def full_chances(chance_type: str, **kwargs) -> float:
    """
    Calculate full chances.
    """
    # I have not decided whether or not to have level affect this
    # I might in the future, however for now, I probably won't 
    # Also this returns the actual percentage added (so 1 = 1%)
    user = kwargs.get("user")
    
    if user:
        manager = ChanceManager(user)
        return await manager.get_full_chance(chance_type)
    
    return 0.0