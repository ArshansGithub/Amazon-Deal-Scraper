import discord

import Modules.Helper as Helper
from Components.Feedback.View import FeedbackView
from Components.Report.View import ReportView
from Variables import Constants

class Pagination(discord.ui.View):
    def __init__(self, ctx, scraped, fulfillment, discount, category, sorting, price, scraper, bot, search: None):
        super().__init__(timeout=3600)
        self.page = 0
        self.ctx = ctx
        self.scraped = scraped
        self.innerPage = 1

        self.fulfillment = fulfillment
        self.discount = discount
        self.category = category
        self.sorting = sorting
        self.price = price
        self.search = search
        self.scraper = scraper
        self.bot = bot

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

        if self.search != None:
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
        await interaction.response.defer()
        
        # Log the command to the log channel
        logChannel = self.bot.get_channel(Constants.LOG_CHANNEL)
        successChannel = self.bot.get_channel(Constants.ANNOUNCEMENT_CHANNEL)
        await logChannel.send(
            f"**{self.ctx.author}** tried **fetching coupons** for the following amazon listing **{self.scraped[self.page]['amz_link']}**")

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
                                     description=f"**{self.ctx.author}** just saved **{self.scraped[self.page]['discount']}** on **{self.scraped[self.page]['title']}**!")
        successEmbed.color = discord.Color.random()
        successEmbed.set_footer(text=f"Developed by {Constants.AUTHOR_NAME}")
        await successChannel.send(embed=successEmbed)



        await interaction.followup.send(coupons, ephemeral=True)

    @discord.ui.button(label="Next Deal", row=0, style=discord.ButtonStyle.primary, emoji="➡️")
    async def nextCallback(self, button, interaction):
        comment = ""
        await interaction.response.defer()
        if not self.page == len(self.scraped) - 1:
            self.page += 1
        else:
            if self.search == None:
                additonal = await self.bot.loop.run_in_executor(None, self.scraper.get_coupons, self.fulfillment,
                                                                self.discount,
                                                                self.category, self.sorting, self.price,
                                                                self.innerPage + 1)

                if len(additonal["data"]) == 0:
                    await interaction.edit_original_response(content="No more results found!")
                    return

                if additonal["status"] != "success":
                    print(additonal)
                    await interaction.edit_original_response(content="Something went wrong! Please report this. (Err 3)")
                    return

                scraped = await self.bot.loop.run_in_executor(None, self.scraper.parse, additonal["data"])

                self.scraped = Helper.combine_two_dicts(self.scraped, scraped)
                self.innerPage += 1
                self.page += 1
            else:
                additonal = await self.bot.loop.run_in_executor(None, self.scraper.get_coupons_search, self.search,
                                                                self.fulfillment, self.discount, self.category,
                                                                self.sorting,
                                                                self.price, self.innerPage + 1)

                print(additonal)

                if len(additonal["data"]) == 0:
                    await interaction.edit_original_response(content="No more results found!")
                    return

                if additonal["status"] != "success":
                    print(additonal)
                    await interaction.edit_original_response(content="Something went wrong! Please report this. (Err 3)")
                    return

                scraped = await self.bot.loop.run_in_executor(None, self.scraper.parse_search, additonal["data"])

                if 0 not in scraped.keys():
                    comment = "**Could not find anymore results**\n"
                else:
                    comment = "**More results have been added** since you reached the end of the current results. ***Enjoy!🔥***\n"

                    self.scraped = Helper.combine_two_dicts(self.scraped, scraped)
                    self.innerPage += 1
                    self.page += 1

        embed = self.return_embed()

        await interaction.edit_original_response(
            content=comment + f"You are currently on deal *{self.page + 1}* out of **{len(self.scraped)}**\n{Constants.TIP}",
            embed=embed)

    @discord.ui.button(label="Go to end", row=0, style=discord.ButtonStyle.primary, emoji="🏃")
    async def lastCallback(self, button, interaction):
        await interaction.response.defer()

        self.page = len(self.scraped) - 1

        embed = self.return_embed()

        await interaction.edit_original_response(
            content=f"You are currently on deal *{self.page + 1}* out of **{len(self.scraped)}**\n{Constants.TIP}",
            embed=embed)

    @discord.ui.button(label="Save this deal!", row=1, style=discord.ButtonStyle.primary, emoji="🌟")
    async def saveIndividualCallback(self, button, interaction):
        # DM the deal to the user
        await interaction.response.send_message(
            "Check your DMs! If you don't receive anything, check your privacy settings!", ephemeral=True)

        embed = self.return_embed()

        tempCopy = self
        tempCopy.clear_items()

        tempCopy.add_item(tempCopy.getCallback)

        tempCopy.add_item(tempCopy.feedbackCallback)
        tempCopy.add_item(tempCopy.reportCallback)

        await self.ctx.author.send(f"Here is the deal you saved:\n{self.scraped[self.page]['amz_link']}", embed=embed,
                                   view=tempCopy)

    @discord.ui.button(label="Save ALL deals!", row=1, style=discord.ButtonStyle.primary, emoji="⭐")
    async def saveCallback(self, button, interaction):
        # DM the deal to the user
        await interaction.response.send_message(
            "Check your DMs! If you don't receive anything, check your privacy settings!", ephemeral=True)

        embed = self.return_embed()

        tempCopy = self
        tempCopy.clear_items()
        tempCopy.add_item(tempCopy.beginningCallback)
        tempCopy.add_item(tempCopy.prevCallback)

        tempCopy.add_item(tempCopy.getCallback)

        tempCopy.add_item(tempCopy.nextCallback)
        tempCopy.add_item(tempCopy.lastCallback)

        tempCopy.add_item(tempCopy.saveIndividualCallback)
        tempCopy.add_item(tempCopy.feedbackCallback)
        tempCopy.add_item(tempCopy.reportCallback)

        await self.ctx.author.send(f"Here are the deals you saved:\n{self.scraped[self.page]['amz_link']}", embed=embed,
                                   view=tempCopy)

    @discord.ui.button(label="Share ALL deals!", row=1, style=discord.ButtonStyle.primary, emoji="📤")
    async def shareAllCallback(self, button, interaction):
        # Send deal in public channel for everyone to see
        await interaction.response.defer()

        embed = self.return_embed()

        tempCopy = self
        tempCopy.clear_items()
        tempCopy.add_item(tempCopy.beginningCallback)
        tempCopy.add_item(tempCopy.prevCallback)

        tempCopy.add_item(tempCopy.getCallback)

        tempCopy.add_item(tempCopy.nextCallback)
        tempCopy.add_item(tempCopy.lastCallback)

        tempCopy.add_item(tempCopy.saveIndividualCallback)
        tempCopy.add_item(tempCopy.saveCallback)
        tempCopy.add_item(tempCopy.shareIndividualCallback)
        tempCopy.add_item(tempCopy.feedbackCallback)
        tempCopy.add_item(tempCopy.reportCallback)

        await self.ctx.channel.send(
            f"**{self.ctx.author}** wanted to share the following deals:\n{self.scraped[self.page]['amz_link']}",
            embed=embed, view=tempCopy)

    @discord.ui.button(label="Share this deal!", row=1, style=discord.ButtonStyle.primary, emoji="📤")
    async def shareIndividualCallback(self, button, interaction):
        # Send deal in public channel for everyone to see
        await interaction.response.defer()

        embed = self.return_embed()

        tempCopy = self
        tempCopy.clear_items()

        tempCopy.add_item(tempCopy.getCallback)

        tempCopy.add_item(tempCopy.saveIndividualCallback)
        tempCopy.add_item(tempCopy.feedbackCallback)
        tempCopy.add_item(tempCopy.reportCallback)

        # tempAgain.add_item(tempAgain.saveCallback)

        await self.ctx.channel.send(
            f"**{self.ctx.author}** wanted to share this deal:\n{self.scraped[self.page]['amz_link']}", embed=embed,
            view=tempCopy)

    @discord.ui.button(label="Feedback", row=2, style=discord.ButtonStyle.green, emoji="📝")
    async def feedbackCallback(self, button, interaction):
        # Send deal in public channel for everyone to see
        await interaction.response.send_message(
            "Check your DMs! If you don't receive anything, check your privacy settings!", ephemeral=True)

        await self.ctx.author.send("Amazon Deal Scraper Feedback Form", view=FeedbackView(self.bot))

    @discord.ui.button(label="Report an issue", row=2, style=discord.ButtonStyle.danger, emoji="😔")
    async def reportCallback(self, button, interaction):
        # Send deal in public channel for everyone to see
        await interaction.response.send_message(
            "Sent your reported listing to support. Please also fill out the report sent to your DMs.", ephemeral=True)

        # Serve the report form
        await self.ctx.author.send("Amazon Deal Scraper Report Form", view=ReportView(self.bot))

        embed = self.return_embed()

        # Send the deal to the support channel
        supportChannel = self.bot.get_channel(Constants.ERROR_CHANNEL)

        await supportChannel.send(
            f"**{self.ctx.author}** in guild **{self.ctx.guild.name}** reported the following deal\n*{self.page + 1}* out of **{len(self.scraped)}**",
            embed=embed, view=self)

