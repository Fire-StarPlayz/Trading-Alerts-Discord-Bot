vimport os
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta

# Bot setup
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = 1345816439915024396  # Replace with your Discord channel ID

intents = discord.Intents.default()
intents.messages = True  # Enable message tracking
intents.message_content = True  # Allow reading message content

bot = commands.Bot(command_prefix="!", intents=intents)

# Track state
current_state = None
transition_count = 0

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    weekly_status.start()  # Start the automatic status update loop

@bot.event
async def on_message(message):
    global current_state, transition_count

    if message.author == bot.user:
        return  # Ignore bot messages

    # Check for threshold messages
    if "Stocks - Above Threshold" in message.content:
        if current_state != "Above Threshold":
            transition_count += 1
        current_state = "Above Threshold"

    elif "Stocks - Below Threshold" in message.content:
        if current_state != "Below Threshold":
            transition_count += 1
        current_state = "Below Threshold"

    await bot.process_commands(message)  # Allow commands to work

@bot.command()
async def status(ctx):
    state = current_state if current_state else "Unknown"
    await ctx.send(f"📊 **Current State:** {state}\n🔄 **Transitions:** {transition_count}")

@tasks.loop(minutes=1)
async def weekly_status():
    global current_state, transition_count  # Ensure we're modifying the global variables

    now = datetime.now(timezone.utc) - timedelta(hours=5)  # Adjust for EST (UTC-5)
    if now.weekday() == 4 and now.hour == 15 and now.minute == 0:  # Friday at 3:00 PM
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            state = current_state if current_state else "Unknown"
            await channel.send(f"📢 **Weekly Update** 📅\n📊 **Current State:** {state}\n🔄 **Transitions:** {transition_count}")

            # Reset state and transition count
            current_state = None
            transition_count = 0
            await channel.send("🔄 **State and transitions have been reset for the new week!**")
                        
# Run the bot
@weekly_status.before_loop
async def before_weekly_status():
    await bot.wait_until_ready()  # Ensure the bot is fully ready before starting the loop

# Run bot
bot.run(TOKEN)
