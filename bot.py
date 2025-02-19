import discord
from discord.ext import commands
import config
import os

intents = discord.Intents.default()
intents.members = True
intents.messages = True


@bot.event()
async def on_ready():
    print('Logged in as {0.user}'.format(bot))
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f"cogs.{file[:-3]}")
    print("Cogs loaded")


bot.run(config.TOKEN)
