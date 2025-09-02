import math

def calculate_xp_for_level(level: int) -> int:
    """
    Calculate total XP required to reach a specific level from level 1.
    
    Args:
        level: The target level
        
    Returns:
        Total XP required to reach that level
    """
    if level <= 1:
        return 0
    
    total_xp = 0
    for lvl in range(1, level):
        # Much harder formula: exponential growth with higher base costs
        xp_for_next_level = math.floor(15 * (lvl ** 1.8) + (50 * lvl) + 100)
        total_xp += xp_for_next_level
    
    return total_xp

def calculate_level_from_xp(current_xp: int) -> dict:
    """
    Calculate current level and progress from total XP.
    
    Args:
        current_xp: Current total XP
        
    Returns:
        Dictionary with level, xp_for_current_level, xp_for_next_level, and xp_progress
    """
    if current_xp <= 0:
        return {
            "level": 1,
            "xp_for_current_level": 0,
            "xp_for_next_level": math.floor(15 * (1 ** 1.8) + (50 * 1) + 100),
            "xp_progress": 0
        }
    
    level = 1
    while True:
        xp_needed_for_next = calculate_xp_for_level(level + 1)
        if current_xp < xp_needed_for_next:
            break
        level += 1
        
        if level > 1000:
            break
    
    xp_for_current_level = calculate_xp_for_level(level)
    xp_for_next_level = calculate_xp_for_level(level + 1)
    xp_progress = current_xp - xp_for_current_level
    xp_needed_for_next = xp_for_next_level - current_xp
    
    return {
        "level": level,
        "xp_for_current_level": xp_for_current_level,
        "xp_for_next_level": xp_for_next_level,
        "xp_progress": xp_progress,
        "xp_needed": xp_needed_for_next
    }