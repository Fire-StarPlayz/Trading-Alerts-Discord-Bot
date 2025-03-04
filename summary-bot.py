import os
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
stock_states = {}  # Stores stock states in format: {"AAPL": "Above Threshold"}
stock_transitions = {}  # Stores transition counts per stock
last_stock = None  # Stores the last stock that triggered an update

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    weekly_status.start()  # Start the automatic status update loop

@bot.event
async def on_message(message):
    global last_stock

    if message.author == bot.user:
        return  # Ignore bot messages

    # Check for threshold messages in format: "AAPL Stocks - Above Threshold"
    parts = message.content.split()
    if len(parts) >= 6 and parts[-2] == "-":
        stock_symbol = parts[3].strip(':')  # Extract stock symbol (e.g., AAPL)
        state = " ".join(parts[-3:])  # "Above Threshold" or "Below Threshold"

        # Update tracking
        if stock_states.get(stock_symbol) != state:
            stock_transitions[stock_symbol] = stock_transitions.get(stock_symbol, 0) + 1
        
        stock_states[stock_symbol] = state
        last_stock = (stock_symbol, state)

    await bot.process_commands(message)  # Allow commands to work

@bot.command()
async def status(ctx):
    if last_stock:
        stock_symbol, state = last_stock
        transitions = stock_transitions.get(stock_symbol, 0)
        await ctx.send(f"📊 **Last Stock Update:** {stock_symbol} is **{state}**\n🔄 **Transitions:** {transitions}")
    else:
        await ctx.send("❓ No stock data has been received yet.")

@tasks.loop(minutes=1)
async def weekly_status():
    global stock_states, stock_transitions  # Ensure we're modifying the global variables

    now = datetime.now(timezone.utc) - timedelta(hours=5)  # Adjust for EST (UTC-5)
    if now.weekday() == 4 and now.hour == 15 and now.minute == 0:  # Friday at 3:00 PM
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            if stock_states:
                stock_summary = "\n".join([f"📊 **{stock}**: {state} (🔄 {stock_transitions.get(stock, 0)} transitions)" for stock, state in stock_states.items()])
            else:
                stock_summary = "❓ No stocks recorded this week."

            await channel.send(f"📢 **Weekly Update** 📅\n{stock_summary}")

            # Reset state and transition count
            stock_states = {}
            stock_transitions = {}
            await channel.send("🔄 **State and transitions have been reset for the new week!**")

# Run the bot
@weekly_status.before_loop
async def before_weekly_status():
    await bot.wait_until_ready()  # Ensure the bot is fully ready before starting the loop

# Run bot
bot.run(TOKEN)
