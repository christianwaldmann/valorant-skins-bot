import os
import discord
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


@client.event
async def on_ready():
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


client.run(TOKEN)
