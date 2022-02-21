import os
import discord
from discord.ext import tasks
import asyncio
import datetime
from store import store, nightmarket

from dotenv import load_dotenv


load_dotenv()


TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
USERNAME = os.getenv("VALORANT_USERNAME")
PASSWORD = os.getenv("VALORANT_PASSWORD")
REGION = os.getenv("VALORANT_REGION")
COMMAND_PREFIX = "!"


client = discord.Client()


@tasks.loop(hours=24)
async def get_store_and_send():
    channel = client.get_channel(CHANNEL_ID)
    current_date = datetime.datetime.now(datetime.timezone.utc)
    current_date_string = current_date.strftime("%d.%m.%Y")

    skins, time = await store(USERNAME, PASSWORD, REGION)
    embed = discord.Embed(
        title=f"{USERNAME}'s store ({current_date_string})",
        description=f"Offer ends in {time}",
        color=discord.Color.red(),
    )
    await channel.send(embed=embed)
    for item in skins:
        embed = discord.Embed(
            title=item[0], description=f"Price: {item[1]} VP", color=discord.Color.red()
        )
        embed.set_thumbnail(url=item[2])
        await channel.send(embed=embed)


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower().startswith(f"{COMMAND_PREFIX}nightmarket"):
        current_date = datetime.datetime.now(datetime.timezone.utc)
        current_date_string = current_date.strftime("%d.%m.%Y")
        skins, time = await nightmarket(USERNAME, PASSWORD, REGION)
        embed = discord.Embed(
            title=f"{USERNAME}'s nightmarket ({current_date_string})",
            description=f"Offer ends in {time}",
            color=discord.Color.red(),
        )
        await message.channel.send(embed=embed)
        for item in skins:
            embed = discord.Embed(
                title=item[0],
                description=f"Price: ~~{item[4]}~~ {item[1]} VP (-{item[3]}%)",
                color=discord.Color.red(),
            )
            embed.set_thumbnail(url=item[2])
            await message.channel.send(embed=embed)


@get_store_and_send.before_loop
async def before():
    SECONDS_IN_A_DAY = 3600 * 24
    TIME_IN_HOURS_TO_CHECK_STORE_AND_SEND = 0
    TIME_IN_MINUTES_TO_CHECK_STORE_AND_SEND = 0
    TIME_IN_SECONDS_TO_CHECK_STORE_AND_SEND = (
        5  # wait a few seconds to make sure the valorant store has updated
    )
    await client.wait_until_ready()
    for _ in range(SECONDS_IN_A_DAY):
        now = datetime.datetime.now(datetime.timezone.utc)
        if (
            now.hour == TIME_IN_HOURS_TO_CHECK_STORE_AND_SEND
            and now.minute == TIME_IN_MINUTES_TO_CHECK_STORE_AND_SEND
            and now.second == TIME_IN_SECONDS_TO_CHECK_STORE_AND_SEND
        ):
            return
        await asyncio.sleep(0.5)


get_store_and_send.start()
client.run(TOKEN)
