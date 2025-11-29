import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button

class IgnServers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ignservers", description="List all Diamond Nation servers the bot is in")
    async def ignservers(self, interaction: discord.Interaction):
        allowed_ids = [1236801401061900288, 1105935596632952832, 1413433249518190622]
        if interaction.user.id not in allowed_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        guilds = self.bot.guilds
        if not guilds:
            await interaction.response.send_message("The bot is not in any servers.", ephemeral=True)
            return

        guild_ids = [str(g.id) for g in guilds]
        view = IgnServersView(self.bot, interaction, guild_ids)
        embed = await view.update_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class IgnServersSearchModal(Modal):
    def __init__(self, view):
        super().__init__(title="Search Server")
        self.view = view
        self.search_input = TextInput(label="Enter Server ID or Name", placeholder="e.g., 123456789 or server name", required=True)
        self.add_item(self.search_input)

    async def on_submit(self, interaction: discord.Interaction):
        query = self.search_input.value.lower()
        guild_ids = self.view.guild_ids
        found_index = None
        for i, guild_id in enumerate(guild_ids):
            guild = self.view.bot.get_guild(int(guild_id))
            if guild:
                if query == guild_id or query in guild.name.lower():
                    found_index = i
                    break
        if found_index is not None:
            self.view.current_page = found_index
            embed = await self.view.update_embed()
            await interaction.response.edit_message(embed=embed, view=self.view)
        else:
            await interaction.response.send_message("Server not found.", ephemeral=True)

class IgnServersView(View):
    def __init__(self, bot, interaction, guild_ids):
        super().__init__(timeout=300)
        self.bot = bot
        self.interaction = interaction
        self.guild_ids = guild_ids
        self.current_page = 0

    async def update_embed(self):
        guild_id = self.guild_ids[self.current_page]
        guild = self.bot.get_guild(int(guild_id))
        if guild:
            embed = discord.Embed(title=f"Server: {guild.name}", color=discord.Color.blue())
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            embed.add_field(name="Server ID", value=guild_id, inline=True)
            embed.add_field(name="Member Count", value=guild.member_count, inline=True)
            embed.add_field(name="Owner", value=f"{guild.owner} ({guild.owner_id})", inline=False)
            embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
            embed.set_footer(text=f"Page {self.current_page + 1} of {len(self.guild_ids)}")
        else:
            embed = discord.Embed(title="Server Not Found", description=f"Server ID: {guild_id}", color=discord.Color.red())
            embed.set_footer(text=f"Page {self.current_page + 1} of {len(self.guild_ids)}")
        return embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
        else:
            self.current_page = len(self.guild_ids) - 1
        embed = await self.update_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page < len(self.guild_ids) - 1:
            self.current_page += 1
        else:
            self.current_page = 0
        embed = await self.update_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Search", style=discord.ButtonStyle.secondary)
    async def search_button(self, interaction: discord.Interaction, button: Button):
        modal = IgnServersSearchModal(self)
        await interaction.response.send_modal(modal)

async def setup(bot):
    await bot.add_cog(IgnServers(bot))
