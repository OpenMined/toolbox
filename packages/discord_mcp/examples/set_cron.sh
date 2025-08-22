#! /bin/bash


# start every monday at 00:00
tb trigger add --name discord-cc-usage-follower -c "0 0 * * 1" -s "python ~/workspace/toolbox/packages/discord_mcp/examples/summarize_discord_channel_cron.py"