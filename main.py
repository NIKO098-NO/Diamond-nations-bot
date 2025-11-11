import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv
from flask import Flask
import threading

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Flask app for health checks
app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running!'

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    await bot.change_presence(status=discord.Status.dnd)
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

async def load_extensions():
    await bot.load_extension('cogs.blacklist')
    await bot.load_extension('cogs.say')

if __name__ == '__main__':
    import asyncio

    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Load extensions and run bot
    asyncio.run(load_extensions())
    bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)
