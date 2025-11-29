import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
import sys
import asyncio
import subprocess
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

allowed_ids = [1236801401061900288, 1105935596632952832, 1413433249518190622]

@bot.tree.command(name="refresh", description="Restart the bot after a short delay")
async def refresh(interaction: discord.Interaction):
    if interaction.user.id not in allowed_ids:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    await interaction.response.send_message("Restarting bot in 10 seconds...", ephemeral=True)
    await asyncio.sleep(10)
    await bot.close()
    sys.exit(0)

@bot.tree.command(name="rest", description="Delete everything on the server (Owner only)")
async def rest(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("Only the server owner can use this command.", ephemeral=True)
        return
    await interaction.response.defer()
    await interaction.followup.send("Starting server wipe... This will delete all channels and roles.", ephemeral=True)
    # Delete all channels
    for channel in interaction.guild.channels:
        try:
            await channel.delete()
        except Exception as e:
            print(f"Failed to delete channel {channel.name}: {e}")
    # Delete all roles except @everyone
    for role in interaction.guild.roles:
        if role != interaction.guild.default_role:
            try:
                await role.delete()
            except Exception as e:
                print(f"Failed to delete role {role.name}: {e}")
    await interaction.followup.send("Server wipe complete. All channels and roles have been deleted.", ephemeral=True)

@bot.tree.command(name="test", description="Test command for bot maker only")
async def test(interaction: discord.Interaction):
    if interaction.user.id != 1413433249518190622:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    await interaction.response.send_message("Test successful!", ephemeral=True)

async def cycle_status():
    while True:
        # Activity 1: "Made by ArcForge Studios"
        await bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name="Made by ArcForge Studios"))
        await asyncio.sleep(14400)  # 4 hours

        # Activity 2: Watching {server count}
        server_count = len(bot.guilds)
        await bot.change_presence(status=discord.Status.dnd, activity=discord.Activity(type=discord.ActivityType.watching, name=f"{server_count} servers"))
        await asyncio.sleep(14400)

        # Activity 3: "DNS ON TOP"
        await bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name="DNS ON TOP"))
        await asyncio.sleep(14400)

        # Activity 4: Watching {number of members in all servers (disregard bots)}
        total_members = sum(len([m for m in g.members if not m.bot]) for g in bot.guilds)
        await bot.change_presence(status=discord.Status.dnd, activity=discord.Activity(type=discord.ActivityType.watching, name=f"{total_members} members"))
        await asyncio.sleep(14400)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    print(f"Guilds: {[g.id for g in bot.guilds]}")
    bot.loop.create_task(cycle_status())
    if bot.guilds:
        try:
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} global command(s)")
        except Exception as e:
            print(f"Error syncing commands: {e}")
    else:
        print("Bot is not in any guild, skipping command sync. Invite the bot to a guild to sync commands.")

async def load_extensions():
    await bot.load_extension('cogs.blacklist')
    await bot.load_extension('cogs.say')
    await bot.load_extension('cogs.globalkick')
    await bot.load_extension('cogs.leaveguild')
    await bot.load_extension('cogs.getin')
    await bot.load_extension('cogs.getinfo')
    await bot.load_extension('cogs.sgbl')
    await bot.load_extension('cogs.supervision')

if __name__ == '__main__':
    import asyncio

    # Load extensions and run bot
    asyncio.run(load_extensions())
    bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)
