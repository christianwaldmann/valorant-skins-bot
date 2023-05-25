from typing import NewType
import time
import discord
from discord.ext import commands
from datetime import datetime
from valorant import ValorantClient
from dataclasses import dataclass


ChannelId = NewType("ChannelId", int)
Username = NewType("Username", str)
Password = NewType("Password", str)
CommandPrefix = NewType("CommandPrefix", str)


@dataclass
class DiscordBotConfig:
    command_prefix: str
    valorant_username: Username
    valorant_password: Password
    channel_id: ChannelId


class DiscordBot(commands.Bot):
    def __init__(
        self, valorant_client: ValorantClient, config: DiscordBotConfig
    ) -> None:
        super().__init__(config.command_prefix, self_bot=False)
        self.unauth_valorant_client = valorant_client
        self.config = config

    async def on_ready(self) -> None:
        self.valorant_client = await self.unauth_valorant_client.authenticate(
            self.config.valorant_username, self.config.valorant_password
        )
        await self.post_store_offers(self.config.channel_id)
        await self.close()

    async def post_store_offers(self, channel_id: ChannelId) -> None:
        # Get store
        store = await self.valorant_client.get_store()
        current_date_string = datetime.utcnow().strftime("%d.%m.%Y")

        # Post message about user and time remaining
        time_left_string = time.strftime(
            "%H hours and %M minutes", time.gmtime(store.remaining_duration_in_seconds)
        )
        embed = discord.Embed(
            title=f"{self.config.valorant_username}'s store ({current_date_string})",
            description=f"Offer ends in {time_left_string}",
            color=discord.Color.red(),
        )
        channel = self.get_channel(channel_id)
        await channel.send(embed=embed)

        # Post message for every offer in store
        for offer in store.offers:
            embed = discord.Embed(
                title=offer.skin.name,
                description=f"Price: {offer.cost} VP",
                color=discord.Color.red(),
            )
            embed.set_thumbnail(url=offer.image_url)
            await channel.send(embed=embed)
