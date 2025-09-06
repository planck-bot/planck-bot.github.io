import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from utils import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents, shard_id=0, shard_count=2)

last_modified = {}

async def register_commands():
    logger.info("Registering commands...")
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("__"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                logger.info(f"Loaded extension: {filename[:-3]}")
            except Exception as e:
                logger.error(f"Failed to load extension {filename[:-3]}: {e}")

async def reload_cog(cog_name):
    try:
        await bot.reload_extension(f"cogs.{cog_name}")
        print(f"Reloaded {cog_name}")
        await bot.tree.sync()
        print("Synced commands")
    except Exception as e:
        print(f"Error reloading {cog_name}: {e}")

async def watch_cogs():
    print(f"Watching for changes in: {os.path.abspath('./cogs')}")
    
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("__"):
            path = os.path.join("./cogs", filename)
            last_modified[path] = os.path.getmtime(path)
    
    while True:
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("__"):
                path = os.path.join("./cogs", filename)
                current_mtime = os.path.getmtime(path)
                
                if path in last_modified and current_mtime > last_modified[path]:
                    last_modified[path] = current_mtime
                    await reload_cog(filename[:-3])
        
        await asyncio.sleep(1)

async def cleanup_expired_captchas_task():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            from cogs.core import captcha_manager
            await captcha_manager.cleanup_expired_captchas()
        except Exception as e:
            print(f"Error in captcha cleanup task: {e}")
        await asyncio.sleep(30)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    logger.info(f'With {len(bot.users)} users')
    
    await register_commands()
    await bot.tree.sync()
    logger.info("Command tree synced")
    
    bot.loop.create_task(watch_cogs())
    bot.loop.create_task(cleanup_expired_captchas_task())
    logger.info("Background tasks started")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("TOKEN")
    bot.run(TOKEN)