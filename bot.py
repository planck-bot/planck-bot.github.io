import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

intents = discord.Intents.default()
intents.message_content = True

# These don't really matter (other than intents)
bot = commands.Bot(command_prefix='$', intents=intents, shard_id=0, shard_count=2)

class CogFileHandler(FileSystemEventHandler):
    def __init__(self, bot_instance):
        super().__init__()
        self.bot = bot_instance
        self.reload_queue = asyncio.Queue()
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        if event.src_path.endswith('.py'):
            file_name = os.path.basename(event.src_path)
            cog_name = file_name[:-3]
            
            try:
                self.reload_queue.put_nowait(cog_name)
                print(f"Detected change in {file_name}, queued for reload")
            except asyncio.QueueFull:
                print(f"Reload queue is full, skipping {file_name}")

file_handler = None

async def register_commands():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            # if filename not in ["utils.py", "__init__.py", "buttons.py"]:
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def reload_cog(cog_name):
    try:
        # Try to reload the extension
        await bot.reload_extension(f"cogs.{cog_name}")
        print(f"Successfully reloaded {cog_name}")
    except commands.ExtensionNotLoaded:
        # If not loaded, try to load it
        try:
            # I find this useful if renamed or it just failed the first time
            await bot.load_extension(f"cogs.{cog_name}")
            print(f"Successfully loaded {cog_name}")
        except Exception as e:
            print(f"Failed to load {cog_name}: {e}")
    except Exception as e:
        # If reload fails, try unload and load
        try:
            await bot.unload_extension(f"cogs.{cog_name}")
            await bot.load_extension(f"cogs.{cog_name}")
            print(f"Successfully reloaded {cog_name} (via unload/load)")
        except Exception as reload_error:
            print(f"Failed to reload {cog_name}: {e}")
            print(f"Also failed unload/load: {reload_error}")

    # await bot.tree.sync()

async def watch_cogs():
    global file_handler
    
    observer = Observer()
    file_handler = CogFileHandler(bot)
    
    cogs_path = os.path.abspath("./cogs")
    # You can just spam save and it will activate it
    # Or it can activate it multiple times at once
    # But it shouldn't really matter for now.
    observer.schedule(file_handler, cogs_path, recursive=False)
    observer.start()
    
    print(f"Started watching for changes in: {cogs_path}")
    
    try:
        while True:
            try:
                cog_name = await asyncio.wait_for(file_handler.reload_queue.get(), timeout=1.0)
                
                await asyncio.sleep(0.5)
                await reload_cog(cog_name)
                
                try:
                    synced = await bot.tree.sync()
                    print(f"Re-synced {len(synced)} command(s) after reloading {cog_name}")
                except Exception as e:
                    print(f"Failed to sync commands after reloading {cog_name}: {e}")
                    
            except asyncio.TimeoutError:
                continue
                
    except Exception as e:
        print(f"Error in watch_cogs: {e}")
    finally:
        observer.stop()
        observer.join()

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
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    print(f'With {len(bot.users)} users')
    
    await register_commands()
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    bot.loop.create_task(watch_cogs())
    bot.loop.create_task(cleanup_expired_captchas_task())

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)

if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("TOKEN")
    bot.run(TOKEN)