import discord

from Variables import Constants
from Components.Report.View import ReportView

class PaginationScheduler(discord.ui.View):
    def __init__(self, scraper, scraped, bot, embed2Store):
        super().__init__(timeout=86400)

        self.page = 0
        self.scraped = scraped
        self.innerPage = 1
        self.embed2Store = embed2Store

        self.bot = bot
        self.scraper = scraper

    def return_embed(self):
        daEmbed = discord.Embed(title=self.scraped[self.page]["title"])
        daEmbed.color = discord.Color.random()
        daEmbed.set_image(url=self.scraped[self.page]["img_src"])
        daEmbed.add_field(name="Regular Price", value=self.scraped[self.page]["regular_price"], inline=True)
        daEmbed.add_field(name="Savings", value=self.scraped[self.page]["discount"], inline=True)
        daEmbed.add_field(name="Discounted Price", value=self.scraped[self.page]["discounted_price"], inline=True)

        # b4Price = self.scraped[self.page]["regular_price"].replace("$", "")
        # afterPrice = self.scraped[self.page]["discounted_price"].replace("$", "").replace("FREE", "0.00")

        daEmbed.add_field(name="Fulfillment", value=self.scraped[self.page]["fulfillment"], inline=True)
        daEmbed.add_field(name="Amazon Listing", value=self.scraped[self.page]["amz_link"], inline=True)

        daEmbed.add_field(name="Shipping", value=str(self.scraped[self.page]["shipping"]), inline=True)
        daEmbed.add_field(name="Category", value=self.scraped[self.page]["category"], inline=True)
        daEmbed.add_field(name="Reviews", value=self.scraped[self.page]["review"], inline=True)
        daEmbed.add_field(name="Review Count", value=self.scraped[self.page]["review_count"], inline=True)

        daEmbed.set_footer(text=f"Developed by {Constants.AUTHOR_NAME}")

        return daEmbed

    @discord.ui.button(label="Go to Beginning", row=0, style=discord.ButtonStyle.primary, emoji="🏃")
    async def beginningCallback(self, button, interaction):
        await interaction.response.defer()

        self.page = 0

        embed = self.return_embed()

        await interaction.edit_original_response(
            content=f"You are currently on deal *{self.page + 1}* out of **{len(self.scraped)}**\n{Constants.TIP}",
            embed=embed)

    @discord.ui.button(label="Previous Deal", row=0, style=discord.ButtonStyle.primary, emoji="⬅️")
    async def prevCallback(self, button, interaction):
        await interaction.response.defer()
        if not self.page == 0:
            self.page -= 1

        embed = self.return_embed()

        await interaction.edit_original_response(
            content=f"You are currently on deal *{self.page + 1}* out of **{len(self.scraped)}**\n{Constants.TIP}",
            embed=embed)

    @discord.ui.button(label="Get Coupon(s)", row=0, style=discord.ButtonStyle.success, emoji="🎟️")
    async def getCallback(self, button, interaction):

        # Log the command to the log channel
        logChannel = self.bot.get_channel(Constants.LOG_CHANNEL)
        showOffChannel = self.bot.get_channel(Constants.ANNOUNCEMENT_CHANNEL)

        await logChannel.send(
            f"**{interaction.user}** tried **fetching coupons** for the following amazon listing **{self.scraped[self.page]['amz_link']}**")

        coupons = self.scraper.get_code(self.scraped[self.page]["id"])

        if type(coupons) != str:
            if "This deal has ran out of vouchers" in coupons:
                await interaction.followup.send("This deal has ran out of vouchers. Sorry!", ephemeral=True)
                return
            # print(coupons)
            await interaction.followup.send("Something went wrong! Please report this.", ephemeral=True)
            return
        coupons = coupons.replace("You have requested this code previously. CODE: ", "")
        coupons = coupons.replace("CODE: ", "")

        # Show off by sending a success message publicly also showing off how much they saved
        successEmbed = discord.Embed(title="Congrats!",
                                     description=f"**{interaction.user}** just saved **{self.scraped[self.page]['discount']}** on **{self.scraped[self.page]['title']}**!")
        successEmbed.color = discord.Color.random()
        successEmbed.set_footer(text=f"Developed by {Constants.AUTHOR_NAME}")
        await showOffChannel.send(embed=successEmbed)

        await interaction.followup.send(coupons, ephemeral=True)

    @discord.ui.button(label="Next Deal", row=0, style=discord.ButtonStyle.primary, emoji="➡️")
    async def nextCallback(self, button, interaction):
        await interaction.response.defer()
        if not self.page == len(self.scraped) - 1:
            self.page += 1

        embed = self.return_embed()

        await interaction.edit_original_response(
            content=f"You are currently on deal *{self.page + 1}* out of **{len(self.scraped)}**\n{Constants.TIP}",
            embed=embed)

    @discord.ui.button(label="Go to end", row=0, style=discord.ButtonStyle.primary, emoji="🏃")
    async def lastCallback(self, button, interaction):
        await interaction.response.defer()

        self.page = len(self.scraped) - 1

        embed = self.return_embed()

        await interaction.edit_original_response(
            content=f"You are currently on deal *{self.page + 1}* out of **{len(self.scraped)}**\n{Constants.TIP}",
            embed=embed)

    @discord.ui.button(label="Which filter was this?", row=1, style=discord.ButtonStyle.primary, emoji="🤔")
    async def filterCallback(self, button, interaction):
        await interaction.response.send_message(embed=self.embed2Store, ephemeral=True)

    @discord.ui.button(label="Feedback", row=2, style=discord.ButtonStyle.green, emoji="📝")
    async def feedbackCallback(self, button, interaction):

        await interaction.response.send_message("Amazon Deal Scraper Feedback Form", view=FeedbackView(self.bot))

    @discord.ui.button(label="Report an issue", row=2, style=discord.ButtonStyle.danger, emoji="😔")
    async def reportCallback(self, button, interaction):
        # Send deal in public channel for everyone to see
        await interaction.response.send_message(
            "Sent your reported listing to support. Please also fill out the report", ephemeral=True, view=ReportView(self.bot))

        embed = self.return_embed()

        # Send the deal to the support channel
        supportChannel = self.bot.get_channel(Constants.ERROR_CHANNEL)

        await supportChannel.send(
            f"**{interaction.user}** in **DMs** reported the following deal\n*{self.page + 1}* out of **{len(self.scraped)}**",
            embed=embed, view=self)
