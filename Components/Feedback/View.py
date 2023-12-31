import discord
from Components.Feedback.Modal import FeedbackModal
class FeedbackView(discord.ui.View):
    def __init__(self, bot, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.bot = bot
    @discord.ui.button(label="Click me!", style=discord.ButtonStyle.green, emoji="📝")
    async def button_callback(self, button, interaction):
        await interaction.response.send_modal(FeedbackModal(title="Your thoughts are appreciated :)", bot=self.bot))
