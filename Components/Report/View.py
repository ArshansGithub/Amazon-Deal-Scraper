import discord
from Components.Report.Modal import ReportModal
class ReportView(discord.ui.View):
    def __init__(self, bot, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.bot = bot
    @discord.ui.button(label="Write Report", style=discord.ButtonStyle.green, emoji="📝")
    async def button_callback(self, button, interaction):
        await interaction.response.send_modal(ReportModal(title="Uh oh, looks like something went wrong :(", bot=self.bot))
