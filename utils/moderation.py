import discord
import random
import time
import io
import functools
from PIL import Image, ImageFont, ImageDraw, ImageFilter

from .files import get_user_data, insert_data, update_data

def moderate():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            from utils import base_view
            
            user_id = interaction.user.id
            
            ban_info = await BanManager.get_ban_info(user_id)
            if ban_info["banned"]:
                view, container = await base_view(interaction)
                
                if ban_info["permanent"]:
                    container.add_item(discord.ui.TextDisplay(
                        f"**You are permanently banned**\n\n"
                        f"**Reason:** {ban_info['reason']}\n\n"
                        f"If you believe this is a mistake, please use </ticket:1412764339823443973> to appeal it."
                    ))
                else:
                    container.add_item(discord.ui.TextDisplay(
                        f"**You are temporarily banned**\n\n"
                        f"**Reason:** {ban_info['reason']}\n"
                        f"**Time remaining:** {ban_info['days']}d {ban_info['hours']}h {ban_info['minutes']}m\n\n"
                        f"Please wait for your ban to expire or use </ticket:1412764339823443973> to appeal it."
                    ))

                await interaction.response.send_message(view=view)
                return
            
            from cogs.core import captcha_manager

            if await captcha_manager.should_get_captcha(user_id):
                if user_id not in captcha_manager.active_captchas:
                    await captcha_manager.create_captcha(user_id)

            if user_id in captcha_manager.active_captchas:
                view, container = await base_view(interaction)
                
                captcha_data = captcha_manager.active_captchas[user_id]
                
                container.add_item(discord.ui.TextDisplay(
                    f"**Captcha Required**\n\n"
                    f"You have an active captcha that needs to be solved before you can continue.\n"
                    f"Use </verify:1412764339823443974> to enter your captcha answer or use the button below to regenerate it.\n\n"
                    f"**Attempts remaining:** {5 - captcha_data['attempts']}\n"
                    f"**Regenerations remaining:** {5 - captcha_data['regenerations']}\n\n"
                    f"This captcha will expire in 5 minutes."
                ))
                
                image_bytes = await captcha_manager._generate_captcha_image(captcha_data["text"])
                file = discord.File(io.BytesIO(image_bytes), filename="captcha.png")
                
                media_gallery = discord.ui.MediaGallery()
                media_gallery.add_item(media="attachment://captcha.png")
                container.add_item(media_gallery)
                
                container.add_item(discord.ui.TextDisplay("-# Captchas are case sensitive. Make sure images are enabled in discord settings (Settings > App Settings > Chat > Display Images)"))

                container.add_item(discord.ui.Separator())
                action_row = discord.ui.ActionRow()
                
                regen_button = discord.ui.Button(label="Regenerate Captcha")
                
                async def regenerate_captcha_callback(inter):
                    if inter.user.id != user_id:
                        await inter.response.send_message("This is not your captcha!")
                        return
                        
                    result = await captcha_manager.regenerate_captcha(user_id)
                    if result["success"]:
                        new_image_bytes = await captcha_manager._generate_captcha_image(result["captcha_text"])
                        new_file = discord.File(io.BytesIO(new_image_bytes), filename="captcha.png")
                        
                        new_view, new_container = await base_view(inter)
                        
                        new_container.add_item(discord.ui.TextDisplay(
                            f"**Captcha Verification**\n\n"
                            f"Please solve this captcha by typing the text you see in the image.\n\n"
                            f"**Attempts remaining:** {5 - result['attempts']}\n"
                            f"**Regenerations remaining:** {5 - result['regenerations']}\n\n"
                            f"This captcha will expire in 5 minutes."
                        ))
                        
                        new_media_gallery = discord.ui.MediaGallery()
                        new_media_gallery.add_item(media="attachment://captcha.png")
                        new_container.add_item(new_media_gallery)

                        new_container.add_item(discord.ui.TextDisplay("-# Captchas are case sensitive. Make sure images are enabled in discord settings (Settings > App Settings > Chat > Display Images)"))
                        
                        new_container.add_item(discord.ui.Separator())
                        new_action_row = discord.ui.ActionRow()
                        new_regen_button = discord.ui.Button(label="Regenerate Captcha")
                        new_regen_button.callback = regenerate_captcha_callback
                        new_action_row.add_item(new_regen_button)

                        new_container.add_item(new_action_row)
                        
                        await inter.response.edit_message(view=new_view, attachments=[new_file])
                    else:
                        await inter.response.send_message(result["message"])
                
                regen_button.callback = regenerate_captcha_callback
                action_row.add_item(regen_button)

                container.add_item(action_row)

                return await interaction.response.send_message(
                    view=view, 
                    files=[file]
                )

            
            return await func(interaction, *args, **kwargs)
        return wrapper
    return decorator

class Captcha:
    def __init__(self):
        self.active_captchas = {}  # {user_id: {"text": str, "attempts": int, "regenerations": int, "created_at": float}}
        self.last_captcha_time = {}  # {user_id: last_captcha_timestamp}
    
    async def should_get_captcha(self, user_id: int) -> bool:
        if user_id not in self.last_captcha_time:
            return True
        time_since_last = time.time() - self.last_captcha_time[user_id]
        if time_since_last < 1800:
            return False

        extra_minutes = (time_since_last - 1800) // 60
        chance = min(1.0, 0.50 + 0.05 * extra_minutes)
        return random.random() < chance
    
    async def get_time_until_next_captcha(self, user_id: int) -> int:
        if user_id not in self.last_captcha_time:
            return 0
        
        min_interval = 1800
        time_since_last = time.time() - self.last_captcha_time[user_id]
        remaining = min_interval - time_since_last
        return max(0, int(remaining))
    
    async def _generate_captcha_text(self) -> str:
        forbidden_words = ["regen"] # might add more in the future
        
        while True:
            length = random.randint(5, 7)
            
            uppercase = 'ABCDEFGHJKMNPQRSTUVWXYZ'  # Removed  I, L, O
            lowercase = 'abcdefghjkmnpqrstuvwxyz'  # Removed  i, l, o
            numbers = '23456789'  # Removed 0, 1
            
            captcha_chars = []
            for i in range(length):
                char_type = random.choice(['upper', 'lower', 'number'])
                if char_type == 'upper':
                    captcha_chars.append(random.choice(uppercase))
                elif char_type == 'lower':
                    captcha_chars.append(random.choice(lowercase))
                else:
                    captcha_chars.append(random.choice(numbers))
            
            captcha_text = ''.join(captcha_chars)
            
            has_upper = any(c.isupper() for c in captcha_text)
            has_lower = any(c.islower() for c in captcha_text)
            has_digit = any(c.isdigit() for c in captcha_text)
            
            if (has_upper and has_lower and 
                not any(forbidden.lower() in captcha_text.lower() for forbidden in forbidden_words)):
                return captcha_text

    async def _generate_captcha_image(self, captcha_text: str) -> bytes:
        width, height = 320, 120
        
        bg_colors = [(245, 245, 245), (250, 250, 250), (240, 240, 240), (248, 248, 248)]
        bg_color = random.choice(bg_colors)
        image = Image.new("RGB", (width, height), color=bg_color)
        draw = ImageDraw.Draw(image)
        
        for _ in range(random.randint(100, 200)):
            x = random.randint(0, width)
            y = random.randint(0, height)
            dot_color = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
            draw.point((x, y), fill=dot_color)
        
        for _ in range(random.randint(8, 15)):
            points = []
            for _ in range(random.randint(3, 6)):
                points.append((random.randint(0, width), random.randint(0, height)))
            line_color = (random.randint(180, 220), random.randint(180, 220), random.randint(180, 220))
            if len(points) >= 2:
                for i in range(len(points) - 1):
                    draw.line([points[i], points[i + 1]], fill=line_color, width=random.randint(1, 2))

        fonts = []
        font_names = ["arial.ttf", "calibri.ttf", "times.ttf", "tahoma.ttf", "verdana.ttf"] # from the system
        for font_name in font_names:
            try:
                fonts.append(ImageFont.truetype(font_name, random.randint(28, 36)))
            except:
                continue
        
        if not fonts:
            try:
                fonts.append(ImageFont.truetype("arial.ttf", 32))
            except:
                default_font = ImageFont.load_default()
                font = default_font.font_variant(size=32)
                fonts.append(font)
        
        font = random.choice(fonts)
        
        bbox = draw.textbbox((0, 0), captcha_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        total_width_with_spacing = text_width + (len(captcha_text) - 1) * 10
        base_x = (width - total_width_with_spacing) // 2
        base_y = (height - text_height) // 2
        
        char_spacing = (text_width // len(captcha_text)) + 10 if len(captcha_text) > 0 else 35
        
        for i, char in enumerate(captcha_text):
            char_font = random.choice(fonts)
            char_x = base_x + (i * char_spacing) + random.randint(-4, 4)
            char_y = base_y + random.randint(-5, 5)
            
            char_image = Image.new("RGBA", (50, 50), (255, 255, 255, 0))
            char_draw = ImageDraw.Draw(char_image)
            
            char_colors = [
                (random.randint(0, 80), random.randint(0, 80), random.randint(0, 80)),
                (random.randint(20, 100), random.randint(20, 100), random.randint(20, 100)),
                (random.randint(40, 120), random.randint(40, 120), random.randint(40, 120))
            ]
            char_color = random.choice(char_colors)
            
            char_draw.text((10, 10), char, fill=char_color, font=char_font)
            
            rotation_angle = random.randint(-18, 18)
            rotated_char = char_image.rotate(rotation_angle, expand=True)
            
            paste_x = max(0, min(width - rotated_char.width, char_x))
            paste_y = max(0, min(height - rotated_char.height, char_y))
            
            if rotated_char.mode == 'RGBA':
                image.paste(rotated_char, (paste_x, paste_y), rotated_char)
            else:
                image.paste(rotated_char, (paste_x, paste_y))
        
        for _ in range(random.randint(5, 10)):
            start = (random.randint(0, width), random.randint(0, height))
            end = (random.randint(0, width), random.randint(0, height))
            line_color = (random.randint(150, 200), random.randint(150, 200), random.randint(150, 200))
            draw.line([start, end], fill=line_color, width=random.randint(1, 3))
        
        for _ in range(random.randint(3, 8)):
            shape_type = random.choice(['rectangle', 'ellipse'])
            x1, y1 = random.randint(0, width//2), random.randint(0, height//2)
            x2, y2 = x1 + random.randint(10, 30), y1 + random.randint(10, 30)
            shape_color = (random.randint(200, 240), random.randint(200, 240), random.randint(200, 240))
            
            if shape_type == 'rectangle':
                draw.rectangle([x1, y1, x2, y2], outline=shape_color, width=1)
            else:
                draw.ellipse([x1, y1, x2, y2], outline=shape_color, width=1)
        
        distortion_effects = [
            lambda img: img.filter(ImageFilter.GaussianBlur(radius=0.5)),
            lambda img: img, # no effect/s
            lambda img: img.filter(ImageFilter.SMOOTH),
            lambda img: img.filter(ImageFilter.SMOOTH_MORE),
        ]
        
        distortion = random.choice(distortion_effects)
        image = distortion(image)
        
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()

    async def create_captcha(self, user_id: int, force: bool = False) -> dict:
        """Create a new captcha for user"""
        ban_info = await BanManager.get_ban_info(user_id)
        if ban_info["banned"]:
            if ban_info["permanent"]:
                return {
                    "success": False,
                    "message": f"You are permanently banned: {ban_info['reason']}",
                    "banned": True
                }
            else:
                return {
                    "success": False,
                    "message": f"You are banned for {ban_info['days']}d {ban_info['hours']}h {ban_info['minutes']}m. Reason: {ban_info['reason']}",
                    "banned": True
                }
        
        if not force and not await self.should_get_captcha(user_id):
            remaining = await self.get_time_until_next_captcha(user_id)
            minutes = remaining // 60
            seconds = remaining % 60
            return {
                "success": False,
                "message": f"You can get a new captcha in {minutes}m {seconds}s.",
                "cooldown": True
            }
        
        captcha_text = await self._generate_captcha_text()
        current_time = time.time()
        
        self.active_captchas[user_id] = {
            "text": captcha_text,
            "attempts": 0,
            "regenerations": 0,
            "created_at": current_time
        }
        
        if force or user_id not in self.last_captcha_time:
            self.last_captcha_time[user_id] = current_time
        
        return {
            "success": True,
            "captcha_text": captcha_text,
            "attempts": 0,
            "regenerations": 0
        }

    async def regenerate_captcha(self, user_id: int) -> dict:
        """Regenerate captcha for user"""
        if user_id not in self.active_captchas:
            return {"success": False, "message": "No active captcha found."}
        
        captcha_data = self.active_captchas[user_id]
        
        if captcha_data["regenerations"] >= 5:
            return {"success": False, "message": "Maximum regenerations reached (5/5)."}
        
        captcha_data["regenerations"] += 1
        captcha_data["attempts"] = 0
        captcha_data["text"] = await self._generate_captcha_text()
        captcha_data["created_at"] = time.time()
        
        return {
            "success": True,
            "captcha_text": captcha_data["text"],
            "attempts": captcha_data["attempts"],
            "regenerations": captcha_data["regenerations"]
        }

    async def verify_captcha(self, user_id: int, user_input: str) -> dict:
        """Verify captcha input"""
        if user_id not in self.active_captchas:
            return {"success": False, "message": "No active captcha found.", "action": "none"}
        
        captcha_data = self.active_captchas[user_id]
        
        if time.time() - captcha_data["created_at"] > 300:
            await self._ban_user_for_captcha_expiry(user_id)
            del self.active_captchas[user_id]
            return {"success": False, "message": "Captcha has expired. You have been banned for 30 days.", "action": "expired_banned"}
        
        if user_input.strip() == captcha_data["text"]:
            del self.active_captchas[user_id]

            self.last_captcha_time[user_id] = time.time()
            return {"success": True, "message": "Captcha solved successfully!", "action": "success"}
        
        captcha_data["attempts"] += 1
        
        if captcha_data["attempts"] >= 5:
            if captcha_data["regenerations"] < 5:
                regen_result = await self.regenerate_captcha(user_id)
                if regen_result["success"]:
                    return {
                        "success": False,
                        "message": f"Incorrect! Maximum attempts reached. Auto-regenerating captcha ({captcha_data['regenerations']}/5).",
                        "action": "auto_regen",
                        "captcha_text": regen_result["captcha_text"],
                        "attempts": 0,
                        "regenerations": captcha_data["regenerations"]
                    }
            
            await self._ban_user_for_captcha_failure(user_id)
            del self.active_captchas[user_id]
            return {
                "success": False,
                "message": "Maximum attempts and regenerations reached. You have been banned for 30 days.",
                "action": "banned"
            }
        
        return {
            "success": False,
            "message": f"Incorrect! Attempts remaining: {5 - captcha_data['attempts']}",
            "action": "retry",
            "attempts": captcha_data["attempts"],
            "regenerations": captcha_data["regenerations"]
        }

    async def _ban_user_for_captcha_failure(self, user_id: int):
        """Ban user for 30 days due to captcha failure"""
        ban_until = time.time() + (30 * 24 * 60 * 60)
        await BanManager.ban_user(user_id, int(ban_until), "Captcha failure - exceeded maximum attempts")

    async def _ban_user_for_captcha_expiry(self, user_id: int):
        """Ban user for 7 days due to captcha expiry"""
        ban_until = time.time() + (30 * 24 * 60 * 60) # might seem harsh, but they can appeal it.
        await BanManager.ban_user(user_id, int(ban_until), "Captcha expiry - failed to solve captcha within time limit")

    async def cleanup_expired_captchas(self):
        current_time = time.time()
        expired_users = [
            user_id for user_id, data in self.active_captchas.items()
            if current_time - data["created_at"] > 300
        ]
        for user_id in expired_users:
            await self._ban_user_for_captcha_expiry(user_id)
            del self.active_captchas[user_id] 


class BanManager:
    # Table: ban
    # id | ban_until (0 for unbanned, -1 for permanent) | reason
    # 123 | 0 | ""
    # 456 | 170000000 | "Captcha failure"
    # 789 | -1 | "Spamming"

    @staticmethod
    async def is_user_banned(user_id: int) -> bool:
        ban_data = await get_user_data("ban", user_id)
        if ban_data:
            ban_until = ban_data.get("ban_until", 0)
            if ban_until == -1:  # Permanent ban
                return True
            return ban_until > time.time()
        return False

    @staticmethod
    async def ban_user(user_id: int, duration: int, reason: str = "") -> None:
        await insert_data("ban", {"id": user_id, "ban_until": duration, "reason": reason})

    @staticmethod
    async def unban_user(user_id: int) -> None:
        await update_data("ban", {"ban_until": 0, "reason": ""}, "id", user_id)

    @staticmethod
    async def change_ban_duration(user_id: int, duration: int, reason: str = None) -> None:
        update_data_dict = {"ban_until": duration}
        if reason is not None:
            update_data_dict["reason"] = reason
        await update_data("ban", update_data_dict, "id", user_id)
    
    @staticmethod
    async def get_ban_info(user_id: int) -> dict:
        """Get ban information including reason and duration"""
        ban_data = await get_user_data("ban", user_id)
        if not ban_data:
            return {"banned": False}
        
        ban_until = ban_data.get("ban_until", 0)
        reason = ban_data.get("reason", "No reason provided")
        
        if ban_until == 0:
            return {"banned": False}
        elif ban_until == -1:
            return {
                "banned": True,
                "permanent": True,
                "reason": reason
            }
        else:
            remaining_time = ban_until - time.time()
            if remaining_time <= 0:
                return {"banned": False}
            
            days = int(remaining_time // 86400)
            hours = int((remaining_time % 86400) // 3600)
            minutes = int((remaining_time % 3600) // 60)
            
            return {
                "banned": True,
                "permanent": False,
                "reason": reason,
                "remaining_time": remaining_time,
                "days": days,
                "hours": hours,
                "minutes": minutes
            }