from discord import app_commands
import discord
from discord.ext import commands

class Say(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_ids = [1236801401061900288, 1105935596632952832, 1413433249518190622]

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

    @app_commands.command(name="tell", description="Send a message to announcement channels in all servers.")
    @app_commands.describe(message="The message to send")
    async def tell(self, interaction: discord.Interaction, message: str):
        if interaction.user.id not in self.allowed_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.send_message("Message sent to all announcement channels.", ephemeral=True)

        for guild in self.bot.guilds:
            announcement_channel = None
            for channel in guild.channels:
                if channel.type == discord.ChannelType.news:
                    announcement_channel = channel
                    break
            if announcement_channel:
                try:
                    await announcement_channel.send(message)
                except Exception as e:
                    print(f"Failed to send message to {guild.name}: {e}")

async def setup(bot):
    await bot.add_cog(Say(bot))
