from discord import app_commands
import discord
from discord.ext import commands

class GlobalKick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_ids = [1236801401061900288, 1105935596632952832, 1413433249518190622]

    @app_commands.command(name="globalkick", description="Kicks a user from all servers the bot is in.")
    @app_commands.describe(user="The user to kick")
    async def globalkick(self, interaction: discord.Interaction, user: discord.Member):
        if interaction.user.id not in self.allowed_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        kicked_guilds = []
        failed_guilds = []

        for guild in self.bot.guilds:
            try:
                member = guild.get_member(user.id)
                if member:
                    await guild.kick(member, reason=f"Globally kicked by {interaction.user}")
                    kicked_guilds.append(guild.name)
                else:
                    failed_guilds.append(f"{guild.name} (user not in guild)")
            except discord.Forbidden:
                failed_guilds.append(f"{guild.name} (insufficient permissions)")
            except Exception as e:
                failed_guilds.append(f"{guild.name} (error: {str(e)})")

        response = f"**Global Kick Results for {user.mention}:**\n"
        if kicked_guilds:
            response += f"✅ Kicked from: {', '.join(kicked_guilds)}\n"
        if failed_guilds:
            response += f"❌ Failed in: {', '.join(failed_guilds)}"

        await interaction.followup.send(response, ephemeral=True)

async def setup(bot):
    await bot.add_cog(GlobalKick(bot))
