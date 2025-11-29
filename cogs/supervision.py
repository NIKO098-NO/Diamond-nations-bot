import discord
from discord.ext import commands
import json
import datetime
import os
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button
import asyncio

SUPERVISED_USERS_FILE = 'supervised_users.json'

def load_supervised_users():
    if os.path.exists(SUPERVISED_USERS_FILE):
        with open(SUPERVISED_USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_supervised_users(supervised):
    with open(SUPERVISED_USERS_FILE, 'w') as f:
        json.dump(supervised, f, indent=4)

class Supervision(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_counts = {}  # {user_id: [timestamps]}
        self.join_times = {}  # {user_id: [join_timestamps]}

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self, '_task_started'):
            self._task_started = True
            self.bot.loop.create_task(self.check_long_term_supervision())

    @app_commands.command(name="supervise", description="Manage supervision for a user")
    @app_commands.describe(user_id="The Discord user ID to manage", reason="Reason for supervision (required if adding)")
    async def supervise(self, interaction: discord.Interaction, user_id: str, reason: str = None):
        allowed_ids = [1236801401061900288, 1105935596632952832, 1413433249518190622]
        if interaction.user.id not in allowed_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        try:
            user = await self.bot.fetch_user(int(user_id))
        except discord.NotFound:
            embed = discord.Embed(title="Error", description="User not found.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        except ValueError:
            embed = discord.Embed(title="Error", description="Invalid user ID.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        supervised = load_supervised_users()
        is_supervised = user_id in supervised

        if reason and not is_supervised:
            # Add to supervision
            date = datetime.datetime.now().isoformat()
            supervised[user_id] = {
                "reason": reason,
                "date": date,
                "moderator": str(interaction.user),
                "supervisor": str(interaction.user.id)
            }
            save_supervised_users(supervised)
            embed = discord.Embed(title="Supervision Added", description=f"User {user.mention} ({user_id}) is now under supervision.", color=discord.Color.green())
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Date", value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), inline=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif is_supervised and not reason:
            # Remove from supervision
            del supervised[user_id]
            save_supervised_users(supervised)
            embed = discord.Embed(title="Supervision Removed", description=f"User {user.mention} ({user_id}) is no longer under supervision.", color=discord.Color.blue())
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Date", value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), inline=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="Error", description="Invalid operation. Provide reason to add, or omit to remove.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        supervised = load_supervised_users()
        if user_id not in supervised:
            return

        # Log the message for supervised users and send to supervisor
        log_entry = f"[{datetime.datetime.now().isoformat()}] {message.author} ({user_id}) in {message.guild.name if message.guild else 'DM'}: {message.content}"
        with open('supervised_logs.txt', 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')

        # Send log to supervisor
        supervisor_id = supervised[user_id].get('supervisor')
        if supervisor_id:
            try:
                supervisor = await self.bot.fetch_user(int(supervisor_id))
                embed = discord.Embed(title="Supervised User Log", description=log_entry, color=discord.Color.blue())
                embed.set_footer(text=f"User ID: {user_id}")
                await supervisor.send(embed=embed)
            except discord.Forbidden:
                print(f"Could not send log to supervisor {supervisor_id}: Forbidden")
            except Exception as e:
                print(f"Error sending log to supervisor {supervisor_id}: {e}")

        # Track messages for spam detection
        now = datetime.datetime.now().timestamp()
        if user_id not in self.message_counts:
            self.message_counts[user_id] = []
        self.message_counts[user_id].append(now)
        # Keep only last 60 seconds
        self.message_counts[user_id] = [t for t in self.message_counts[user_id] if now - t < 60]

        if len(self.message_counts[user_id]) > 10:  # More than 10 messages in 60 seconds
            await self.trigger_gbl(user_id, "Suspected raiding/spamming: rapid messaging")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        user_id = str(member.id)
        supervised = load_supervised_users()
        if user_id not in supervised:
            return

        # Track joins for raid detection
        now = datetime.datetime.now().timestamp()
        if user_id not in self.join_times:
            self.join_times[user_id] = []
        self.join_times[user_id].append(now)
        # Keep only last 300 seconds (5 minutes)
        self.join_times[user_id] = [t for t in self.join_times[user_id] if now - t < 300]

        if len(self.join_times[user_id]) > 3:  # Joined more than 3 servers in 5 minutes
            await self.trigger_gbl(user_id, "Suspected raiding: joining multiple servers quickly")

    async def trigger_gbl(self, user_id, reason):
        # Remove from supervision
        supervised = load_supervised_users()
        if user_id in supervised:
            del supervised[user_id]
            save_supervised_users(supervised)

        # Add to blacklist
        from cogs.blacklist import load_blacklist, save_blacklist
        blacklist = load_blacklist()
        date = datetime.datetime.now().isoformat()
        blacklist[user_id] = {
            "reason": reason,
            "rb_id": "",
            "notes": "Auto-detected during supervision",
            "proof": "",
            "moderator": "Auto (Supervision)",
            "date": date,
            "anonymous": True
        }
        save_blacklist(blacklist)

        # Ban from all guilds
        banned_count = 0
        for guild in self.bot.guilds:
            try:
                mem = await guild.fetch_member(int(user_id))
                if mem:
                    ban_reason = f"Blacklisted: {reason}. Issued on {date}. To appeal, contact staff or visit the appeal server (link to be provided later)."
                    await guild.ban(mem, reason=ban_reason)
                    banned_count += 1
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"Error banning {user_id} in {guild.name}: {e}")

        print(f"Auto-blacklisted {user_id} for {reason}. Banned from {banned_count} servers.")

    async def check_long_term_supervision(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            supervised = load_supervised_users()
            now = datetime.datetime.now()
            for user_id, data in supervised.items():
                supervision_date = datetime.datetime.fromisoformat(data['date'])
                if (now - supervision_date).days >= 30:
                    try:
                        user = await self.bot.fetch_user(int(user_id))
                        warning_message = f"You have been under supervision for over 30 days. Reason: {data['reason']}. Please review your behavior."
                        await user.send(warning_message)
                    except discord.Forbidden:
                        print(f"Could not send warning to {user_id}: Forbidden")
                    except Exception as e:
                        print(f"Error sending warning to {user_id}: {e}")
            await asyncio.sleep(86400)  # Check daily

async def setup(bot):
    await bot.add_cog(Supervision(bot))
