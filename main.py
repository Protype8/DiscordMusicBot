import discord
from discord.ext import commands
import muisc
import random
import aiohttp
from settings import *
cogs = [muisc]
intents = discord.Intents.all()
intents.voice_states = True
bot = commands.Bot(command_prefix='-',intents=intents)
@bot.command(aliases=["r","R"])
async def roulette(ctx,role=""):
    if(role != ""):
        if(role in agents):
            l = random.choice(agents[role])
        else:
            await ctx.send("Baka!")
            return
    else:
        l = random.choice(random.choices([non_duelists,duelists],weights=[0.9,0.1])[0])
    await ctx.send(ctx.message.author.mention+" got "+l+"!")
@bot.event
async def on_ready():
    for cog in range(len(cogs)):
        await cogs[cog].setup(bot)
print("Running Ina!")
bot.run(token)