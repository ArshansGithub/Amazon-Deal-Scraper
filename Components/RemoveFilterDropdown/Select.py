import discord

from Variables import Constants


class NotificationRemoveDropdown(discord.ui.Select):
    def __init__(self, ctx, bot, notification, parent, filters, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.ctx = ctx
        self.bot = bot
        self.notificationSystem = notification
        self.filters = filters
        self.parent = parent

        self.add_option(label="All", value="all")
        for index, filter in enumerate(self.filters):
            self.add_option(label=f"Filter {index + 1}", value=str(index))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if self.values[0] == "all":
            happened = await self.notificationSystem.remove_all_filters(self.ctx.author.id)
            self.disabled = True
            successEmbed = discord.Embed(title="Success!",
                                         description="Removed ALL filters successfully!",
                                         color=discord.Color.green()).set_footer(
                text=f"Developed by {Constants.AUTHOR_NAME}")
            if happened:
                await interaction.edit_original_response(embed=successEmbed, view=self.parent)
            else:
                await interaction.followup.send("Could not remove filters! Please report this!",
                                                        ephemeral=True)
            return

        result = await self.notificationSystem.remove_filter_by_index(self.ctx.author.id, int(self.values[0]))

        if result:
            self.disabled = True
            successEmbed = discord.Embed(title="Success!",
                                         description="Removed filter successfully!",
                                         color=discord.Color.green()).set_footer(
                text=f"Developed by {Constants.AUTHOR_NAME}")

            await interaction.edit_original_response(embed=successEmbed, view=self.parent)
        else:
            await interaction.response.send_message("Could not remove filter! Please report this!",
                                                    ephemeral=True)



