import discord
from discord.ext import commands
import json
import datetime
import os
from discord import app_commands

BLACKLIST_FILE = 'blacklist.json'

def load_blacklist():
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, 'w') as f:
        json.dump(blacklist, f, indent=4)

class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        blacklist = load_blacklist()
        if str(member.id) in blacklist:
            try:
                ban_reason = f"Blacklisted: {blacklist[str(member.id)]['reason']}. Issued on {blacklist[str(member.id)]['date']}. To appeal, contact staff or visit the appeal server (link to be provided later)."
                await member.guild.ban(member, reason=ban_reason)
            except Exception as e:
                print(f"Error auto-banning {member.id} in {member.guild.name}: {e}")

    @app_commands.command(name="blu", description="Blacklist a user across all servers")
    @app_commands.describe(user_id="The Discord user ID to blacklist", reason="Reason for blacklisting", anonymous="Hide your identity as the moderator")
    async def blu(self, interaction: discord.Interaction, user_id: str, reason: str, anonymous: bool = False):
        # Check if user has permission (specific user IDs allowed)
        allowed_ids = [1236801401061900288, 1105935596632952832, 1413433249518190622]
        if interaction.user.id not in allowed_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        blacklist = load_blacklist()
        if user_id in blacklist:
            await interaction.response.send_message(f"User {user_id} is already blacklisted.", ephemeral=True)
            return

        moderator = None if anonymous else str(interaction.user)
        date = datetime.datetime.now().isoformat()

        blacklist[user_id] = {
            "reason": reason,
            "moderator": moderator,
            "date": date,
            "anonymous": anonymous
        }
        save_blacklist(blacklist)

        # Ban from all guilds the bot is in
        banned_count = 0
        for guild in self.bot.guilds:
            try:
                member = await guild.fetch_member(int(user_id))
                if member:
                    ban_reason = f"Blacklisted: {reason}. Issued on {date}. To appeal, contact staff or visit the appeal server (link to be provided later)."
                    await guild.ban(member, reason=ban_reason)
                    banned_count += 1
            except discord.NotFound:
                pass  # User not in guild
            except Exception as e:
                print(f"Error banning {user_id} in {guild.name}: {e}")

        response = f"User {user_id} has been blacklisted. Banned from {banned_count} server(s)."
        await interaction.response.send_message(response, ephemeral=True)

    @app_commands.command(name="checkbl", description="Check if a user ID is blacklisted")
    @app_commands.describe(user_id="The Discord user ID to check")
    async def checkbl(self, interaction: discord.Interaction, user_id: str):
        blacklist = load_blacklist()
        if user_id in blacklist:
            entry = blacklist[user_id]
            moderator = entry.get('moderator', 'Anonymous') if not entry.get('anonymous', False) else 'Anonymous'
            response = f"User {user_id} is blacklisted.\nReason: {entry['reason']}\nModerator: {moderator}\nDate: {entry['date']}"
        else:
            response = f"User {user_id} is not blacklisted."
        await interaction.response.send_message(response, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Blacklist(bot))
