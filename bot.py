import discord
from discord.ext import commands

from dotenv import load_dotenv
import os

from utils import get_registered_commands

intents = discord.Intents.default()
intents.message_content = True

# These don't really matter (other than intents)
bot = commands.Bot(command_prefix='!', intents=intents, shard_id=0, shard_count=2)

async def register_commands():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            # if filename not in ["utils.py", "__init__.py", "buttons.py"]:
            await bot.load_extension(f"cogs.{filename[:-3]}")

    registered_commands = get_registered_commands()
    # print(f"Found {len(registered_commands)} commands to register")
    
    for command in registered_commands:
        try:
            bot.tree.add_command(command)
            # print(f"Successfully registered command: {command.name}")
        except Exception as e:
            print(f"Failed to register {command.name}: {e}")

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

if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("TOKEN")
    bot.run(TOKEN)