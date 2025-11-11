from discord import app_commands
import discord
from discord.ext import commands

class Say(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="say", description="Make the bot say something anonymously.")
    @app_commands.describe(message="The message you want the bot to say anonymously")
    async def say(self, interaction: discord.Interaction, message: str):
        # First, acknowledge to the user so Discord doesn't consider the interaction unresponded
        await interaction.response.send_message("Your Message Was sent", ephemeral=True)

        # Then send the actual message to the channel as the bot (anonymous to other users)
        # use a small sleep to ensure the interaction response is processed first in rare race cases
        try:
            await interaction.channel.send(message)
        except Exception:
            # If sending to the channel fails, notify the user privately
            try:
                await interaction.followup.send("❌ Failed to send the anonymous message.", ephemeral=True)
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(Say(bot))