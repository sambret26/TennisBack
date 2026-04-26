from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

from config import Config
from discord import Intents
from discord.ext import commands
from discord import discordBusiness
from batchs import batchsLauncher as launcher
from logger.logger import log, BOT

scheduler = AsyncIOScheduler()

tz = timezone(Config.TIME_ZONE)

DISCORD_GUILD_ID = int(Config.DISCORD_GUILD_ID)

intent = Intents(messages=True, members=True, guilds=True, reactions=True, message_content=True)
bot = commands.Bot(command_prefix='$', description='Tennis 2025', intents=intent)

@bot.command()
async def check(ctx):
    await discordBusiness.check(ctx)

@bot.command()
async def nb(ctx):
    await discordBusiness.nb(bot, ctx)

@bot.command()
async def info(ctx, name = None):
    await discordBusiness.info(ctx, name)

@bot.command()
async def infos(ctx, name = None):
    await discordBusiness.info(ctx, name)

@bot.command()
async def pgw(ctx):
    await discordBusiness.pgw(bot)

@bot.command()
async def excel(ctx):
    await discordBusiness.excel(ctx)

@bot.command()
async def cmd(ctx):
    await discordBusiness.cmd(ctx)

@bot.command()
async def clear(ctx, nombre: int = 100):
    await discordBusiness.clear(ctx, nombre)

@bot.event
async def on_ready():
    log.info(BOT, "Connected !")
    scheduler.add_job(launcher.pgwLoop, CronTrigger(hour=8, minute=58, timezone=tz), args=[bot])
    scheduler.add_job(launcher.inscriptionsLoop, CronTrigger(second=20, timezone=tz))
    scheduler.add_job(launcher.convocationLoop, CronTrigger(second=40, timezone=tz))
    scheduler.add_job(launcher.sendNotifLoop, CronTrigger(second=0, timezone=tz), args=[bot])
    scheduler.add_job(launcher.updateMatchLoop, CronTrigger(hour=2, minute=0, timezone=tz))
    #scheduler.add_job(launcher.updateCalLoop, CronTrigger(hour=3, minute=0, timezone=tz))
    scheduler.start()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.guild.id != DISCORD_GUILD_ID:
        return
    if message.attachments:
        await discordBusiness.importFile(message)
    await bot.process_commands(message)

def main():
    bot.run(Config.DISCORD_TOKEN)