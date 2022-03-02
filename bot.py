import os
import discord
import asyncio
from datetime import datetime, time, timedelta
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


async def get_store_and_send():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    current_date = datetime.utcnow()
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
        current_date = datetime.utcnow()
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


def calc_seconds_until_tomorrow_midnight():
    now = datetime.utcnow()
    tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
    return (tomorrow - now).total_seconds()


def calc_seconds_until_target_time(TIME_IN_DAY_TO_SEND):
    now = datetime.utcnow()
    target_time = datetime.combine(now.date(), TIME_IN_DAY_TO_SEND)
    return (target_time - now).total_seconds()


async def main():
    TIME_IN_DAY_TO_SEND = time(0, 0, 5)
    now = datetime.utcnow()
    # Make sure loop doesn't start after TIME_IN_DAY_TO_SEND as then it will send immediately the first time because negative seconds will make the sleep yield instantly
    if now.time() > TIME_IN_DAY_TO_SEND:
        await asyncio.sleep(calc_seconds_until_tomorrow_midnight())
    while True:
        await asyncio.sleep(calc_seconds_until_target_time(TIME_IN_DAY_TO_SEND))
        await get_store_and_send()
        await asyncio.sleep(calc_seconds_until_tomorrow_midnight())


client.loop.create_task(main())
client.run(TOKEN)
