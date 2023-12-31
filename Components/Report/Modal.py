import discord
from Variables import Constants

class ReportModal(discord.ui.Modal):
    def __init__(self, bot, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.bot = bot

        self.add_item(
            discord.ui.InputText(label="Thoughts on the current state of the bot?", style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="What went wrong?", style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Report Results")
        embed.color = discord.Color.random()
        # Include author name and guild name
        embed.add_field(name="Author", value=interaction.user, inline=True)
        embed.add_field(name="Guild", value=interaction.guild, inline=False)
        embed.add_field(name="Thoughts on the current state of the bot?", value=self.children[0].value, inline=True)
        embed.add_field(name="What went wrong?", value=self.children[1].value, inline=True)

        embed.set_footer(text=f"Developed by {Constants.AUTHOR_NAME}")

        # Send the embed to the feedback channel
        feedbackChannel = self.bot.get_channel(Constants.FEEDBACK_CHANNEL)
        await feedbackChannel.send(content="@everyone", embed=embed)

        # Send a success message to the user
        await interaction.response.send_message("Sent! Will look into this issue ASAP!", ephemeral=True)


