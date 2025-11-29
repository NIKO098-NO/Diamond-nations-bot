import discord
from discord.ext import commands
from discord import app_commands
import requests

class GetInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="getinfo", description="Get Roblox info of a user via Bloxlink")
    @app_commands.describe(user="The Discord user to get Roblox info for")
    async def getinfo(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer()

        # Get the Roblox ID from Bloxlink API
        bloxlink_url = f"https://api.blox.link/v4/public/discord-to-roblox/{user.id}"
        headers = {
            "Authorization": "your_bloxlink_api_key_here"  # Replace with actual API key
        }

        try:
            response = requests.get(bloxlink_url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if data.get("success"):
                roblox_id = data["roblox"]["id"]
                roblox_username = data["roblox"]["username"]

                # Get additional Roblox user info from Roblox API
                roblox_api_url = f"https://users.roblox.com/v1/users/{roblox_id}"
                roblox_response = requests.get(roblox_api_url)
                roblox_response.raise_for_status()
                roblox_data = roblox_response.json()

                embed = discord.Embed(title=f"User Info for {user.display_name}", color=discord.Color.blue())
                embed.set_author(name=user.display_name, icon_url=user.avatar.url if user.avatar else user.default_avatar.url)
                embed.set_thumbnail(url=f"https://www.roblox.com/headshot-thumbnail/image?userId={roblox_id}&width=420&height=420&format=png")
                embed.add_field(name="Discord ID", value=user.id, inline=True)
                embed.add_field(name="Roblox Username", value=roblox_username, inline=True)
                embed.add_field(name="Roblox ID", value=roblox_id, inline=True)
                embed.add_field(name="Display Name", value=roblox_data.get("displayName", "N/A"), inline=True)
                embed.add_field(name="Description", value=roblox_data.get("description", "No description") or "No description", inline=False)
                embed.add_field(name="Created", value=roblox_data.get("created", "N/A"), inline=True)
                embed.add_field(name="Banned", value="Yes" if roblox_data.get("isBanned") else "No", inline=True)

                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("No Roblox account linked to this Discord user.", ephemeral=True)

        except requests.RequestException as e:
            await interaction.followup.send(f"Error fetching Roblox info: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(GetInfo(bot))
