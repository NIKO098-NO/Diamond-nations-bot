from discord import app_commands
import discord
from discord.ext import commands

class GetIn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_ids = [1236801401061900288, 1105935596632952832, 1413433249518190622]

    @app_commands.command(name="get-in", description="Generates the bot's invite link for adding to multiple servers (bot owner only).")
    async def getin(self, interaction: discord.Interaction):
        if interaction.user.id not in self.allowed_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        # Generate the OAuth2 URL for inviting the bot
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=discord.Permissions(permissions=8),  # Administrator permissions, adjust as needed
            scopes=("bot", "applications.commands")
        )

        await interaction.response.send_message(f"Here's the invite link for the bot: {invite_url}\nYou can use this link to add the bot to multiple servers.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(GetIn(bot))
