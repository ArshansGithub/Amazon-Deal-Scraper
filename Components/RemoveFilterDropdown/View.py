import discord
from Components.RemoveFilterDropdown.Select import NotificationRemoveDropdown
class NotificationRemoveView(discord.ui.View):
    def __init__(self, ctx, bot, notification, filters, embed, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.embed = embed

        self.dropdown = NotificationRemoveDropdown(ctx, bot, notification ,self, filters)

        self.add_item(self.dropdown)