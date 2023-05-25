import os
from dotenv import load_dotenv
from bot import (
    DiscordBot,
    DiscordBotConfig,
    Username,
    Password,
    ChannelId,
    CommandPrefix,
)
from valorant import ValorantClient


if __name__ == "__main__":
    # Load secrets
    load_dotenv()

    # Build config
    config = DiscordBotConfig(
        command_prefix=CommandPrefix("!"),
        valorant_username=Username(os.getenv("VALORANT_USERNAME")),
        valorant_password=Password(os.getenv("VALORANT_PASSWORD")),
        channel_id=ChannelId(int(os.getenv("DISCORD_CHANNEL_ID"))),
    )

    # Start discord bot
    valorant_client = ValorantClient()
    bot = DiscordBot(valorant_client=valorant_client, config=config)
    bot.run(os.getenv("DISCORD_TOKEN"))
