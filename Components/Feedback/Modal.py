import discord
from Variables import Constants
class FeedbackModal(discord.ui.Modal):
    def __init__(self, bot, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.bot = bot

        self.add_item(
            discord.ui.InputText(label="Thoughts on the current state of the bot?", style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Any ideas for new features?", style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Feedback Results")
        embed.color = discord.Color.random()
        # Include author name and guild name
        embed.add_field(name="Author", value=interaction.user, inline=True)
        embed.add_field(name="Guild", value=interaction.guild, inline=False)
        embed.add_field(name="Thoughts on the current state of the bot?", value=self.children[0].value, inline=True)
        embed.add_field(name="Any ideas for new features?", value=self.children[1].value, inline=True)

        embed.set_footer(text=f"Developed by {Constants.AUTHOR_NAME}")

        # Send the embed to the feedback channel
        feedbackChannel = self.bot.get_channel(Constants.FEEDBACK_CHANNEL)
        await feedbackChannel.send(embed=embed)

        # Send a success message to the user
        await interaction.response.send_message("Sent! Thank you for your feedback!", ephemeral=True)
