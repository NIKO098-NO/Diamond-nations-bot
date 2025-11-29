from discord import app_commands
import discord
from discord.ext import commands

class LeaveGuild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_ids = [1236801401061900288, 1105935596632952832, 1413433249518190622]

    @app_commands.command(name="leaveguild", description="Makes the bot leave this server (bot owner only).")
    async def leaveguild(self, interaction: discord.Interaction):
        if interaction.user.id not in self.allowed_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.send_message("Leaving the server...", ephemeral=True)
        await interaction.guild.leave()

async def setup(bot):
    await bot.add_cog(LeaveGuild(bot))
