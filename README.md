# valorant-skins-bot

bot to post your current offers from the valorant store to a discord channel

## Prerequisites

1. Create `.env` file and fill in the placeholders
````commandline
VALORANT_USERNAME=<insert your valorant username>
VALORANT_PASSWORD=<insert your valorant password>
DISCORD_TOKEN=<insert your discord token for the bot>
DISCORD_CHANNEL_ID=<insert the unique id of the discord channel where the messages will be posted>
````
2. Install dependencies: `pip install -r requirements.txt`

## Usage
`python main.py`

This will run the bot which will get your current offers in the valorant store and post them to a discord channel.
