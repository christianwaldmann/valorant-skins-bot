import os
import discord
from discord.ext import tasks
import asyncio
import datetime
from store import store

from dotenv import load_dotenv


load_dotenv()


TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
USERNAME = os.getenv("VALORANT_USERNAME")
PASSWORD = os.getenv("VALORANT_PASSWORD")
REGION = os.getenv("VALORANT_REGION")


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


@get_store_and_send.before_loop
async def before():
    SECONDS_IN_A_DAY = 3600 * 24
    TIME_IN_HOURS_TO_CHECK_STORE_AND_SEND = 0
    DELAY_IN_SECONDS = 5
    await client.wait_until_ready()
    for _ in range(SECONDS_IN_A_DAY):
        if (
            datetime.datetime.now(datetime.timezone.utc).hour
            == TIME_IN_HOURS_TO_CHECK_STORE_AND_SEND
        ):
            # wait a few seconds to make sure the valorant store has updated
            await asyncio.sleep(DELAY_IN_SECONDS)
            return
        await asyncio.sleep(1)


get_store_and_send.start()
client.run(TOKEN)
