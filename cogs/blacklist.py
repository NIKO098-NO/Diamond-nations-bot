import discord
from discord.ext import commands
import json
import datetime
import os
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button, Select

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

    @app_commands.command(name="gbl", description="Manage blacklist for a user")
    @app_commands.describe(user_id="The Discord user ID to manage")
    async def gbl(self, interaction: discord.Interaction, user_id: str):
        # Check if user has permission (specific user IDs allowed)
        allowed_ids = [1236801401061900288, 1105935596632952832, 1413433249518190622]
        if interaction.user.id not in allowed_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        try:
            user = await self.bot.fetch_user(int(user_id))
        except discord.NotFound:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return
        except ValueError:
            await interaction.response.send_message("Invalid user ID.", ephemeral=True)
            return

        blacklist = load_blacklist()
        is_blacklisted = user_id in blacklist

        view = BlacklistManageView(self.bot, interaction, user, is_blacklisted)
        embed = await view.update_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

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

    @app_commands.command(name="gbl_all", description="List all blacklisted users with details")
    async def gbl_all(self, interaction: discord.Interaction):
        allowed_ids = [1236801401061900288, 1105935596632952832, 1413433249518190622]
        if interaction.user.id not in allowed_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        blacklist = load_blacklist()
        if not blacklist:
            await interaction.response.send_message("No blacklisted users found.", ephemeral=True)
            return

        user_ids = list(blacklist.keys())
        view = BlacklistView(self.bot, interaction, user_ids)
        embed = await view.update_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="gblr", description="Request to add a user to the blacklist")
    @app_commands.describe(user_id="The Discord user ID to request blacklist for", reason="Reason for the request")
    async def gblr(self, interaction: discord.Interaction, user_id: str, reason: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
        except discord.NotFound:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return
        except ValueError:
            await interaction.response.send_message("Invalid user ID.", ephemeral=True)
            return

        allowed_ids = [1236801401061900288, 1105935596632952832, 1413433249518190622]
        dm_sent_count = 0
        for uid in allowed_ids:
            try:
                mod_user = await self.bot.fetch_user(uid)
                dm_channel = await mod_user.create_dm()
                embed = discord.Embed(title="Blacklist Request", color=discord.Color.orange())
                embed.add_field(name="Requester", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                embed.add_field(name="Target User", value=f"{user} ({user.id})", inline=False)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Status", value="Pending", inline=False)
                view = BlacklistRequestView(self.bot, interaction.user, user, reason)
                await dm_channel.send(embed=embed, view=view)
                dm_sent_count += 1
            except Exception as e:
                print(f"Failed to DM {uid}: {e}")

        await interaction.response.send_message(f"Blacklist request sent to {dm_sent_count} moderator(s).", ephemeral=True)

class BlacklistAddModal(Modal):
    def __init__(self, view):
        super().__init__(title="Add to Blacklist")
        self.view = view
        self.reason_input = TextInput(label="Reason", placeholder="Reason for blacklisting", required=True)
        self.rb_id_input = TextInput(label="RB ID", placeholder="Roblox ID (optional)", required=False)
        self.notes_input = TextInput(label="Notes", placeholder="Additional notes (optional)", required=False, style=discord.TextStyle.paragraph)
        self.proof_input = TextInput(label="Proof", placeholder="Image links (optional)", required=False, style=discord.TextStyle.paragraph)
        self.anonymous_input = TextInput(label="Hide your identity?", placeholder="Type 'yes' to hide, 'no' to show", required=True, default="no")
        self.add_item(self.reason_input)
        self.add_item(self.rb_id_input)
        self.add_item(self.notes_input)
        self.add_item(self.proof_input)
        self.add_item(self.anonymous_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            reason = self.reason_input.value
            rb_id = self.rb_id_input.value or ""
            notes = self.notes_input.value or ""
            proof = self.proof_input.value or ""
            anonymous_str = self.anonymous_input.value.lower().strip()
            anonymous = anonymous_str == "yes"
            moderator = None if anonymous else str(interaction.user)
            date = datetime.datetime.now().isoformat()

            blacklist = load_blacklist()
            blacklist[str(self.view.user.id)] = {
                "reason": reason,
                "rb_id": rb_id,
                "notes": notes,
                "proof": proof,
                "moderator": moderator,
                "date": date,
                "anonymous": anonymous
            }
            save_blacklist(blacklist)

            # Log to channel
            await self.log_blacklist(interaction, self.view.user, reason, rb_id, notes, proof, date)

            # Ban from all guilds the bot is in
            banned_count = 0
            for guild in self.view.bot.guilds:
                try:
                    member = await guild.fetch_member(self.view.user.id)
                    if member:
                        ban_reason = f"Blacklisted: {reason}. Issued on {date}. To appeal, contact staff or visit the appeal server (link to be provided later)."
                        await guild.ban(member, reason=ban_reason)
                        banned_count += 1
                except discord.NotFound:
                    pass  # User not in guild
                except Exception as e:
                    print(f"Error banning {self.view.user.id} in {guild.name}: {e}")

            self.view.is_blacklisted = True
            embed = await self.view.update_embed()
            await self.view.interaction.edit_original_response(embed=embed, view=self.view)
        except Exception as e:
            print(f"Error in BlacklistAddModal.on_submit: {e}")
            await interaction.followup.send("An error occurred while adding to blacklist.", ephemeral=True)

    async def log_blacklist(self, interaction, user, reason, rb_id, notes, proof, date):
        channel = self.view.bot.get_channel(1413943887327662141)
        if channel:
            embed = discord.Embed(title="User Blacklisted", color=discord.Color.red())
            embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
            embed.add_field(name="Name", value=user.name, inline=True)
            embed.add_field(name="DC ID", value=str(user.id), inline=True)
            embed.add_field(name="RB ID", value=rb_id or "N/A", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Date", value=date, inline=True)
            embed.add_field(name="Notes", value=notes or "None", inline=False)
            embed.add_field(name="Proof", value=proof or "None", inline=False)
            await channel.send(embed=embed)

class BlacklistEditModal(Modal):
    def __init__(self, view):
        super().__init__(title="Edit Blacklist Entry")
        self.view = view
        blacklist = load_blacklist()
        data = blacklist[str(view.user.id)]
        self.reason_input = TextInput(label="Reason", placeholder="Reason for blacklisting", default=data['reason'], required=True)
        self.rb_id_input = TextInput(label="RB ID", placeholder="Roblox ID (optional)", default=data.get('rb_id', ''), required=False)
        self.notes_input = TextInput(label="Notes", placeholder="Additional notes (optional)", default=data.get('notes', ''), required=False, style=discord.TextStyle.paragraph)
        self.proof_input = TextInput(label="Proof", placeholder="Image links (optional)", default=data.get('proof', ''), required=False, style=discord.TextStyle.paragraph)
        default_anonymous = "yes" if data.get('anonymous', False) else "no"
        self.anonymous_input = TextInput(label="Hide your identity?", placeholder="Type 'yes' to hide, 'no' to show", required=True, default=default_anonymous)
        self.add_item(self.reason_input)
        self.add_item(self.rb_id_input)
        self.add_item(self.notes_input)
        self.add_item(self.proof_input)
        self.add_item(self.anonymous_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            reason = self.reason_input.value
            anonymous_str = self.anonymous_input.value.lower().strip()
            anonymous = anonymous_str == "yes"
            moderator = None if anonymous else str(interaction.user)
            date = datetime.datetime.now().isoformat()

            blacklist = load_blacklist()
            blacklist[str(self.view.user.id)] = {
                "reason": reason,
                "moderator": moderator,
                "date": date,
                "anonymous": anonymous
            }
            save_blacklist(blacklist)

            embed = await self.view.update_embed()
            await self.view.interaction.edit_original_response(embed=embed, view=self.view)
        except Exception as e:
            print(f"Error in BlacklistEditModal.on_submit: {e}")
            await interaction.followup.send("An error occurred while editing the blacklist entry.", ephemeral=True)

class BlacklistManageView(View):
    def __init__(self, bot, interaction, user, is_blacklisted):
        super().__init__(timeout=300)
        self.bot = bot
        self.interaction = interaction
        self.user = user
        self.is_blacklisted = is_blacklisted

    async def update_embed(self):
        embed = discord.Embed(title=f"Blacklist Management: {self.user.name}", color=discord.Color.red() if self.is_blacklisted else discord.Color.green())
        embed.set_thumbnail(url=self.user.avatar.url if self.user.avatar else self.user.default_avatar.url)
        embed.add_field(name="User ID", value=self.user.id, inline=True)
        embed.add_field(name="Username", value=self.user.name, inline=True)
        embed.add_field(name="Display Name", value=self.user.display_name, inline=True)
        if self.is_blacklisted:
            blacklist = load_blacklist()
            data = blacklist[str(self.user.id)]
            embed.add_field(name="Status", value="Blacklisted", inline=False)
            embed.add_field(name="Reason", value=data['reason'], inline=False)
            moderator = data.get('moderator', 'Anonymous') if not data.get('anonymous', False) else 'Anonymous'
            embed.add_field(name="Moderator", value=moderator, inline=True)
            embed.add_field(name="Date", value=data['date'], inline=True)
        else:
            embed.add_field(name="Status", value="Not Blacklisted", inline=False)
        return embed

    @discord.ui.button(label="Add", style=discord.ButtonStyle.danger)
    async def add_button(self, interaction: discord.Interaction, button: Button):
        print("Add button clicked")
        if self.is_blacklisted:
            await interaction.response.send_message("User is already blacklisted.", ephemeral=True)
            return
        modal = BlacklistAddModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.primary)
    async def edit_button(self, interaction: discord.Interaction, button: Button):
        if not self.is_blacklisted:
            await interaction.response.send_message("User is not blacklisted.", ephemeral=True)
            return
        modal = BlacklistEditModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Remove", style=discord.ButtonStyle.secondary)
    async def remove_button(self, interaction: discord.Interaction, button: Button):
        if not self.is_blacklisted:
            await interaction.response.send_message("User is not blacklisted.", ephemeral=True)
            return
        # Confirm removal
        view = ConfirmRemoveView(self)
        await interaction.response.send_message("Are you sure you want to remove this user from the blacklist?", view=view, ephemeral=True)

class ConfirmRemoveView(View):
    def __init__(self, parent_view):
        super().__init__(timeout=60)
        self.parent_view = parent_view

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.danger)
    async def confirm_yes(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        blacklist = load_blacklist()
        del blacklist[str(self.parent_view.user.id)]
        save_blacklist(blacklist)

        # Unban from all guilds the bot is in
        unbanned_count = 0
        for guild in self.parent_view.bot.guilds:
            try:
                await guild.unban(self.parent_view.user)
                unbanned_count += 1
            except Exception as e:
                print(f"Error unbanning {self.parent_view.user.id} in {guild.name}: {e}")

        self.parent_view.is_blacklisted = False
        embed = await self.parent_view.update_embed()
        await self.parent_view.interaction.edit_original_response(embed=embed, view=self.parent_view)
        await interaction.followup.send(f"User {self.parent_view.user.id} has been removed from the blacklist. Unbanned from {unbanned_count} server(s).", ephemeral=True)

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def confirm_no(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await interaction.followup.send("Removal cancelled.", ephemeral=True)

class BlacklistSearchModal(Modal):
    def __init__(self, view):
        super().__init__(title="Search Blacklisted User")
        self.view = view
        self.search_input = TextInput(label="Enter User ID or Username", placeholder="e.g., 123456789 or username", required=True)
        self.add_item(self.search_input)

    async def on_submit(self, interaction: discord.Interaction):
        query = self.search_input.value.lower()
        user_ids = self.view.user_ids
        found_index = None
        for i, user_id in enumerate(user_ids):
            try:
                user = await self.view.bot.fetch_user(int(user_id))
                if query == user_id or query in user.name.lower() or query in user.display_name.lower():
                    found_index = i
                    break
            except:
                if query == user_id:
                    found_index = i
                    break
        if found_index is not None:
            self.view.current_page = found_index
            embed = await self.view.update_embed()
            await interaction.response.edit_message(embed=embed, view=self.view)
        else:
            await interaction.response.send_message("User not found.", ephemeral=True)

class BlacklistView(View):
    def __init__(self, bot, interaction, user_ids):
        super().__init__(timeout=300)
        self.bot = bot
        self.interaction = interaction
        self.user_ids = user_ids
        self.current_page = 0

    async def update_embed(self):
        user_id = self.user_ids[self.current_page]
        try:
            user = await self.bot.fetch_user(int(user_id))
            embed = discord.Embed(title=f"Blacklisted User: {user.name}", color=discord.Color.red())
            embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
            embed.add_field(name="User ID", value=user_id, inline=True)
            embed.add_field(name="Username", value=user.name, inline=True)
            embed.add_field(name="Display Name", value=user.display_name, inline=True)
            blacklist = load_blacklist()
            data = blacklist[user_id]
            embed.add_field(name="Reason", value=data['reason'], inline=False)
            moderator = data.get('moderator', 'Anonymous') if not data.get('anonymous', False) else 'Anonymous'
            embed.add_field(name="Moderator", value=moderator, inline=True)
            embed.add_field(name="Date", value=data['date'], inline=True)
            embed.set_footer(text=f"Page {self.current_page + 1} of {len(self.user_ids)}")
        except discord.NotFound:
            embed = discord.Embed(title="User Not Found", description=f"User ID: {user_id}", color=discord.Color.red())
            embed.set_footer(text=f"Page {self.current_page + 1} of {len(self.user_ids)}")
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"Error fetching user {user_id}: {e}", color=discord.Color.red())
            embed.set_footer(text=f"Page {self.current_page + 1} of {len(self.user_ids)}")
        return embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
        else:
            self.current_page = len(self.user_ids) - 1
        embed = await self.update_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page < len(self.user_ids) - 1:
            self.current_page += 1
        else:
            self.current_page = 0
        embed = await self.update_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Search", style=discord.ButtonStyle.secondary)
    async def search_button(self, interaction: discord.Interaction, button: Button):
        modal = BlacklistSearchModal(self)
        await interaction.response.send_modal(modal)

class BlacklistRequestView(View):
    def __init__(self, bot, requester, target_user, reason):
        super().__init__(timeout=86400)  # 24 hours
        self.bot = bot
        self.requester = requester
        self.target_user = target_user
        self.reason = reason

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success)
    async def approve_button(self, interaction: discord.Interaction, button: Button):
        allowed_ids = [1236801401061900288, 1105935596632952832, 1413433249518190622]
        if interaction.user.id not in allowed_ids:
            await interaction.response.send_message("You do not have permission to approve requests.", ephemeral=True)
            return

        # Simulate running the gbl command: add to blacklist
        blacklist = load_blacklist()
        if str(self.target_user.id) in blacklist:
            await interaction.response.send_message("User is already blacklisted.", ephemeral=True)
            return

        date = datetime.datetime.now().isoformat()
        blacklist[str(self.target_user.id)] = {
            "reason": self.reason,
            "rb_id": "",
            "notes": "",
            "proof": "",
            "moderator": str(interaction.user),
            "date": date,
            "anonymous": False
        }
        save_blacklist(blacklist)

        # Log to channel
        await self.log_blacklist_request(interaction, self.target_user, self.reason, "", "", "", date)

        # Ban from all guilds
        banned_count = 0
        for guild in self.bot.guilds:
            try:
                member = await guild.fetch_member(self.target_user.id)
                if member:
                    ban_reason = f"Blacklisted: {self.reason}. Issued on {date}. To appeal, contact staff or visit the appeal server (link to be provided later)."
                    await guild.ban(member, reason=ban_reason)
                    banned_count += 1
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"Error banning {self.target_user.id} in {guild.name}: {e}")

        # Update embed
        embed = interaction.message.embeds[0]
        embed.set_field_at(3, name="Status", value="Approved", inline=False)
        await interaction.message.edit(embed=embed, view=None)

        await interaction.response.send_message(f"Request approved. User added to blacklist and banned from {banned_count} server(s).", ephemeral=True)

        # Notify requester
        try:
            dm_channel = await self.requester.create_dm()
            embed_req = discord.Embed(title="Blacklist Request Approved", color=discord.Color.green())
            embed_req.add_field(name="Target User", value=f"{self.target_user} ({self.target_user.id})", inline=False)
            embed_req.add_field(name="Reason", value=self.reason, inline=False)
            await dm_channel.send(embed=embed_req)
        except Exception as e:
            print(f"Failed to notify requester: {e}")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
    async def deny_button(self, interaction: discord.Interaction, button: Button):
        allowed_ids = [1236801401061900288, 1105935596632952832, 1413433249518190622]
        if interaction.user.id not in allowed_ids:
            await interaction.response.send_message("You do not have permission to deny requests.", ephemeral=True)
            return

        modal = DenyReasonModal(self)
        await interaction.response.send_modal(modal)

class DenyReasonModal(Modal):
    def __init__(self, view):
        super().__init__(title="Deny Blacklist Request")
        self.view = view
        self.deny_reason_input = TextInput(label="Reason for Denial", placeholder="Provide a reason for denying the request", required=True)
        self.add_item(self.deny_reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        deny_reason = self.deny_reason_input.value

        # Update embed
        embed = interaction.message.embeds[0]
        embed.set_field_at(3, name="Status", value=f"Denied: {deny_reason}", inline=False)
        await interaction.message.edit(embed=embed, view=None)

        await interaction.followup.send("Request denied.", ephemeral=True)

        # Notify requester
        try:
            dm_channel = await self.view.requester.create_dm()
            embed_req = discord.Embed(title="Blacklist Request Denied", color=discord.Color.red())
            embed_req.add_field(name="Target User", value=f"{self.view.target_user} ({self.view.target_user.id})", inline=False)
            embed_req.add_field(name="Denial Reason", value=deny_reason, inline=False)
            await dm_channel.send(embed=embed_req)
        except Exception as e:
            print(f"Failed to notify requester: {e}")

async def setup(bot):
    await bot.add_cog(Blacklist(bot))
