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
        base_xp = 30 # level 1 xp
        
        # Apply 10% increase for each level
        xp_for_next_level = base_xp * (1.1 ** (lvl - 1))
        
        # Every 10 levels (10, 20, 30, etc.), double the base
        tens_multiplier = 2 ** (lvl // 10)
        xp_for_next_level *= tens_multiplier
        
        # Every 11th level (11, 21, 31, etc.), apply permanent 1.5x multiplier
        # Count how many times we've passed an 11th level
        elevens_passed = (lvl - 1) // 10 
        elevens_multiplier = 1.5 ** elevens_passed
        xp_for_next_level *= elevens_multiplier
        
        total_xp += math.floor(xp_for_next_level)
    
    # i feel like this would be better if 
    # you gained a boost every 10 levels
    # which is what I have
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
            "xp_for_next_level": 30,
            "xp_progress": 0,
            "xp_needed": 30
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
