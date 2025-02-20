import discord
from discord.ext import commands
import config
import os

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True
intents.moderation = True

bot = commands.Bot(command_prefix="/", intents=intents)


@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))
    for file in os.listdir("./cogs"):
        if file.endswith(".py") and file != "__init__.py":
            await bot.load_extension(f"cogs.{file[:-3]}")
    print("Cogs loaded")


bot.run(config.TOKEN)
