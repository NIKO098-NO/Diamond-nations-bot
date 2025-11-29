import discord
from discord.ext import commands
import json
import datetime
import os
import asyncio
from discord import app_commands

SERVER_BLACKLIST_FILE = 'server_blacklist.json'

def load_server_blacklist():
    if os.path.exists(SERVER_BLACKLIST_FILE):
        with open(SERVER_BLACKLIST_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_server_blacklist(blacklist):
    with open(SERVER_BLACKLIST_FILE, 'w') as f:
        json.dump(blacklist, f, indent=4)

class ServerBlacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        server_blacklist = load_server_blacklist()
        if str(member.guild.id) in server_blacklist:
            # Send DM warning
            try:
                dm_channel = await member.create_dm()
                embed = discord.Embed(title="Warning: Blacklisted Server", color=discord.Color.orange())
                embed.add_field(name="Server", value=f"{member.guild.name} ({member.guild.id})", inline=False)
                embed.add_field(name="Reason", value=server_blacklist[str(member.guild.id)]['reason'], inline=False)
                embed.add_field(name="Warning", value="You have 1 minute to leave this server or you will be blacklisted.", inline=False)
                await dm_channel.send(embed=embed)
            except Exception as e:
                print(f"Failed to DM {member.id}: {e}")

            # Wait 1 minute
            await asyncio.sleep(60)

            # Check if still in server
            try:
                member_check = await member.guild.fetch_member(member.id)
                if member_check:
                    # Add to user blacklist
                    from cogs.blacklist import load_blacklist, save_blacklist
                    user_blacklist = load_blacklist()
                    reason = f"Joined blacklisted server: {member.guild.name} ({member.guild.id}) - {server_blacklist[str(member.guild.id)]['reason']}"
                    date = datetime.datetime.now().isoformat()
                    user_blacklist[str(member.id)] = {
                        "reason": reason,
                        "rb_id": "",
                        "notes": "",
                        "proof": "",
                        "moderator": "Auto (Server Blacklist)",
                        "date": date,
                        "anonymous": True
                    }
                    save_blacklist(user_blacklist)

                    # Ban from all guilds
                    banned_count = 0
                    for guild in self.bot.guilds:
                        try:
                            mem = await guild.fetch_member(member.id)
                            if mem:
                                ban_reason = f"Blacklisted: {reason}. Issued on {date}. To appeal, contact staff or visit the appeal server (link to be provided later)."
                                await guild.ban(mem, reason=ban_reason)
                                banned_count += 1
                        except discord.NotFound:
                            pass
                        except Exception as e:
                            print(f"Error banning {member.id} in {guild.name}: {e}")

                    print(f"Auto-blacklisted {member.id} for joining blacklisted server. Banned from {banned_count} servers.")
            except discord.NotFound:
                pass  # Member left, no action

    @app_commands.command(name="sgbl", description="Manage server blacklist")
    @app_commands.describe(server_id="The Discord server ID to manage", reason="Reason for blacklisting (required if adding)")
    async def sgbl(self, interaction: discord.Interaction, server_id: str, reason: str = None):
        allowed_ids = [1236801401061900288, 1105935596632952832, 1413433249518190622]
        if interaction.user.id not in allowed_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        try:
            guild_id = int(server_id)
        except ValueError:
            await interaction.response.send_message("Invalid server ID.", ephemeral=True)
            return

        server_blacklist = load_server_blacklist()
        if str(guild_id) in server_blacklist:
            # Remove from blacklist
            del server_blacklist[str(guild_id)]
            save_server_blacklist(server_blacklist)
            await interaction.response.send_message(f"Server {guild_id} has been removed from the blacklist.", ephemeral=True)
        else:
            # Add to blacklist
            if not reason:
                await interaction.response.send_message("Reason is required to add a server to the blacklist.", ephemeral=True)
                return
            date = datetime.datetime.now().isoformat()
            try:
                guild = self.bot.get_guild(guild_id)
                guild_name = guild.name if guild else "Unknown"
            except:
                guild_name = "Unknown"
            server_blacklist[str(guild_id)] = {
                "name": guild_name,
                "reason": reason,
                "date": date
            }
            save_server_blacklist(server_blacklist)

            # Log to channel
            channel = self.bot.get_channel(1413943887327662141)
            if channel:
                embed = discord.Embed(title="Server Blacklisted", color=discord.Color.red())
                embed.add_field(name="Server Name", value=guild_name, inline=False)
                embed.add_field(name="Server ID", value=str(guild_id), inline=False)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Date", value=date, inline=True)
                await channel.send(embed=embed)

            await interaction.response.send_message(f"Server {guild_id} has been added to the blacklist.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerBlacklist(bot))
