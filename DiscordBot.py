import json
import discord
from discord.ext import tasks

from Variables import Constants
from Modules.AmazonScraper import AmazonScraper
from Notification.DatabaseHandler import DatabaseHandler
import Modules.Helper as Helper
from Components.Pagination.PaginationView import Pagination
from Components.Pagination.PaginationSchedulerView import PaginationScheduler
from Components.RemoveFilterDropdown.View import NotificationRemoveView

async def mandatory_check(ctx):
    allowed = await Notification.get_whitelist(True)
    disallowed = await Notification.get_blacklist(True)
    
    if str(ctx.channel.id) not in allowed: return "This command is not allowed to be used in this channel!"
    if ctx.guild is None: return "This command can only be used in a server!"
    if str(ctx.guild.id) in disallowed: return "This guild has been blacklisted from using this bot. Please contact support if you believe this is a mistake."
    if Constants.MAINTENANCE and ctx.author.id not in Constants.SUPPORT_USERS: return "Bot is currently in maintenance mode. Please try again later."
    return None

@tasks.loop(seconds=3600.0)
async def regularly_check():
    print("Starting regular check")
    
    whitelisted = await Notification.get_whitelist(True)
    disallowed = await Notification.get_blacklist(True)
        
    for guild in bot.guilds:
        # print("checking")
        if not Helper.guild_has_support(guild):
            await Notification.add_blacklist(guild.id)
            for channel in guild.channels:
                if str(channel.id) in whitelisted:
                    bot.loop.create_task(channel.send(
                        "This guild has been blacklisted from using this bot. Please contact support if you believe this is a mistake."))
                    break
        else:
            if str(guild.id) in disallowed:
                await Notification.remove_blacklist(guild.id)

init = True

scraper = AmazonScraper(Constants.TESSERACT_LOCATION, proxy=Constants.PROXY)

Notification = DatabaseHandler()

categories = list(scraper.categories.keys())
categories.append("all")

accounts = open("data/cookies.txt", "r").read().split("\n")

for account in accounts:
    account = json.loads(account)
    scraper.load_account(account)

scraper.rotate_accounts()

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    if Constants.MAINTENANCE:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name=" new features come to life! (Maintenance Mode)"
            )
        )
    else:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing, name="with amazon deals!"
            )
        )
    print(f'We have logged in as {bot.user}')
    
    Notification_Routine.start()
    
    if not Constants.OVERRIDE_BLACKLIST:
        await regularly_check.start()

@tasks.loop(seconds=21600.0)
async def Notification_Routine():

    disallowed = await Notification.get_blacklist(True)

    print("Starting Notification Routine")

    all_users = await Notification.get_all_users()

    if not all_users:
        return

    for user_data in all_users:
        if str(user_data["guild"]) in disallowed:
            bot.loop.create_task(bot.get_user(user_data["user"]).send("The guild you were in has been blacklisted from using this bot. Your notification task will not be fulfilled due to this. Please contact support if you believe this is a mistake."))
            continue
        if user_data["filters"] is None:
            continue
        await process_user_data(user_data)

async def send_notification(user_id, username, filter_embed):
    await bot.get_user(user_id).send(
        content=f"Hey {username}! It's me! The Amazon Deal Notification System!",
        embed=filter_embed
    )

async def process_user_data(user_data):
    user_id = user_data["user"]
    username = user_data["name"]
    filters = user_data["filters"]
    already_checked = user_data["already_checked"]

    filter_embed = Helper.create_filter_embed(len(filters))

    await send_notification(user_id, username, filter_embed)

    for filter_data in filters:
        index = filters.index(filter_data)

        already_checked = already_checked

        to_send_to_user = await process_filter(user_id, filter_data, already_checked, index)

        if to_send_to_user:
            embed_to_store = await create_filter_store_embed(user_id, filter_data, filters.index(filter_data))
            listing_embed = Helper.create_listing_embed(to_send_to_user[0])

            await send_listing_notification(user_id, listing_embed, embed_to_store, to_send_to_user)
        else:
            await send_no_listings_notification(user_id)


async def process_filter(user_id, filter_data, already_checked, index):
    to_send_to_user = []
    inner_page = 1
    still_more_listings = True

    already_checked = already_checked[index]

    while True:
        listings = scraper.get_coupons_search(filter_data["search"], filter_data["fulfillment"],
                                              filter_data["discount"], filter_data["category"],
                                              filter_data["sorting"], filter_data["price"], inner_page)

        parsed = scraper.parse_search(listings["data"])

        if not listings["data"] or not parsed:
            break

        for listing in parsed.values():
            if listing["id"] not in already_checked and listing["id"] != -1:
                to_send_to_user.append(listing)
                await Notification.add_already_checked(user_id, index, listing["id"])

        if inner_page > 50:
            break

        inner_page += 1

    return to_send_to_user


async def send_listing_notification(user_id, listing_embed, embed_to_store, scraped_data):
    await bot.get_user(user_id).send(
        content=f"Wake up! Found some new goodies for you :)\n\n{Constants.TIP}",
        embed=listing_embed,
        view=PaginationScheduler(scraper, scraped_data, bot, embed_to_store)
    )


async def send_no_listings_notification(user_id):
    sad_embed = Helper.create_sad_embed()
    await bot.get_user(user_id).send(embed=sad_embed)

async def create_filter_store_embed(user_id, filter_data, the_index):
    human_readable_filter = await Notification.get_filter_by_index(user_id, True, the_index)

    embed_to_store = discord.Embed(
        title=f"Filter {the_index + 1} | Amazon Deal Notification System"
    )

    embed_to_store.color = discord.Color.random()

    embed_to_store.add_field(name="Search", value=human_readable_filter["search"], inline=True)
    embed_to_store.add_field(name="Fulfillment", value=human_readable_filter["fulfillment"], inline=True)
    embed_to_store.add_field(name="Discount", value=human_readable_filter["discount"], inline=True)
    embed_to_store.add_field(name="Category", value=human_readable_filter["category"], inline=True)
    embed_to_store.add_field(name="Sorting", value=human_readable_filter["sorting"], inline=True)

    if human_readable_filter["price"] == "No preference":
        embed_to_store.add_field(name="Price Beginning", value="No preference", inline=True)
        embed_to_store.add_field(name="Price End", value="No preference", inline=True)
    else:
        embed_to_store.add_field(name="Price Beginning", value=human_readable_filter["price_beginning"],
                                 inline=True)
        embed_to_store.add_field(name="Price End", value=human_readable_filter["price_end"], inline=True)

    embed_to_store.set_footer(text=f"Developed by {Constants.AUTHOR_NAME}")

    return embed_to_store

@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    if isinstance(error, discord.Forbidden):
        await ctx.respond("I was unable to send a message to you. Please check your privacy settings.", ephemeral=True)
    else:
        raise error

@bot.command(description="Clear someone's already checked stuff", guild_ids=Constants.SUPPORT_GUILD)
async def admin_clear_already_checked(
    ctx,
    user_id: discord.Option(str, description="Who am I addressing?", required=True),

):
    await ctx.defer(ephemeral=True)

    if ctx.author.id not in Constants.SUPPORT_USERS:
        await ctx.interaction.followup.send("You are not authorized to use this command!", ephemeral=True)
        return

    await ctx.interaction.followup.send(await Notification.clear_already_checked(user_id), ephemeral=True)

@bot.command(description="Force restart the notification routine", guild_ids=Constants.SUPPORT_GUILD)
async def admin_force_restart(
    ctx
):
    await ctx.defer(ephemeral=True)

    if ctx.author.id not in Constants.SUPPORT_USERS:
        await ctx.interaction.followup.send("You are not authorized to use this command!", ephemeral=True)
        return

    if Notification_Routine.is_running():
        Notification_Routine.cancel()


    try:
        Notification_Routine.restart()
    except Exception as e:
        await ctx.interaction.followup.send(f"Something went wrong!\n\n{e}", ephemeral=True)

    await ctx.interaction.followup.send("Successfully restarted the notification routine!", ephemeral=True)

@bot.command(description="Add a channel to whitelist", guild_ids=Constants.SUPPORT_GUILD)
async def add_whitelist(
    ctx,
    channel: discord.Option(str, description="Channel to whitelist", required=True)
):
    await ctx.defer(ephemeral=True)

    if ctx.author.id not in Constants.SUPPORT_USERS:
        await ctx.interaction.followup.send("You are not authorized to use this command!", ephemeral=True)
        return

    toDo = await Notification.add_channel(channel)
    await ctx.interaction.followup.send(toDo, ephemeral=True)

@bot.command(description="Remove a channel from whitelist", guild_ids=Constants.SUPPORT_GUILD)
async def remove_whitelist(
    ctx,
    channel: discord.Option(str, description="Channel to remove from whitelist", required=True)
):
    await ctx.defer(ephemeral=True)

    if ctx.author.id not in Constants.SUPPORT_USERS:
        await ctx.interaction.followup.send("You are not authorized to use this command!", ephemeral=True)
        return

    toDo = await Notification.remove_channel(channel)
    await ctx.interaction.followup.send(toDo, ephemeral=True)


@bot.command(description="Get whitelist", guild_ids=Constants.SUPPORT_GUILD)
async def get_whitelist(
    ctx
):
    await ctx.defer(ephemeral=True)

    if ctx.author.id not in Constants.SUPPORT_USERS:
        await ctx.interaction.followup.send("You are not authorized to use this command!", ephemeral=True)
        return

    whitelist = await Notification.get_whitelist()
    await ctx.interaction.followup.send(whitelist, ephemeral=True)
    
@bot.command(description="Get blacklist", guild_ids=Constants.SUPPORT_GUILD)
async def get_blacklist(
    ctx
):
    await ctx.defer(ephemeral=True)

    if ctx.author.id not in Constants.SUPPORT_USERS:
        await ctx.interaction.followup.send("You are not authorized to use this command!", ephemeral=True)
        return

    blacklist = await Notification.get_blacklist()
    await ctx.interaction.followup.send(blacklist, ephemeral=True)
    
@bot.command(description="Add a guild to blacklist", guild_ids=Constants.SUPPORT_GUILD)
async def add_blacklist(
    ctx,
    guild: discord.Option(str, description="Guild to blacklist", required=True)
):
    await ctx.defer(ephemeral=True)

    if ctx.author.id not in Constants.SUPPORT_USERS:
        await ctx.interaction.followup.send("You are not authorized to use this command!", ephemeral=True)
        return

    toDo = await Notification.add_blacklist(guild)
    await ctx.interaction.followup.send(toDo, ephemeral=True)
    
@bot.command(description="Remove a guild from blacklist", guild_ids=Constants.SUPPORT_GUILD)
async def remove_blacklist(
    ctx,
    guild: discord.Option(str, description="Guild to remove from blacklist", required=True)
):
    await ctx.defer(ephemeral=True)

    if ctx.author.id not in Constants.SUPPORT_USERS:
        await ctx.interaction.followup.send("You are not authorized to use this command!", ephemeral=True)
        return

    toDo = await Notification.remove_blacklist(guild)
    await ctx.interaction.followup.send(toDo, ephemeral=True)

@bot.command(description="Find Amazon Deals without needing keywords!")
async def search_without_keywords(
    ctx,
    fulfillment: discord.Option(str, description="Fulfillment Type", choices=["merchant", "amazon", "all"], default="all"),
    discount: discord.Option(str, description="Discount Type (Percentage)", choices=["all", "20-49", "50-79", "80-101"], default="all"),
    category: discord.Option(str, description="Category", choices=categories, default="all"),
    sorting: discord.Option(str, description="Sorting", choices=["No preference", "Low to High", "High to Low", "Discount High to Low", "Newest"], default="No preference"),
    price_beginning: discord.Option(int, min_value=0, description="Price Range Beginning", default=None),
    price_end: discord.Option(int, max_value=9999999, description="Price Range End", default=None)
):
    await ctx.defer(ephemeral=True)

    # Log the command to the log channel
    log_channel = bot.get_channel(Constants.LOG_CHANNEL)
    await log_channel.send(Helper.get_command_log_message_without(ctx, fulfillment, discount, category, sorting, price_beginning, price_end))

    check_result = await mandatory_check(ctx)
    if check_result is not None:
        await ctx.interaction.followup.send(check_result, ephemeral=True)
        return

    fulfillment = Helper.map_fulfillment(fulfillment)
    discount = Helper.map_discount(discount)
    sorting = Helper.map_sorting(sorting)
    category = Helper.map_category(category)

    price = Helper.map_price(price_beginning, price_end)

    page = 1

    coupons_data = await bot.loop.run_in_executor(None, scraper.get_coupons, fulfillment, discount, category, sorting, price, page)

    if coupons_data["status"] != "success":
        print(coupons_data)
        await ctx.interaction.followup.send("Something went wrong! Please report this.", ephemeral=True)
        return

    if not coupons_data["data"]:
        await ctx.interaction.followup.send("No results found!", ephemeral=True)
        return

    scraped = await bot.loop.run_in_executor(None, scraper.parse, coupons_data["data"])

    da_embed = Helper.create_listing_embed_generic(scraped[0])

    await ctx.interaction.followup.send(
        f"You are currently on deal *1* out of **{len(scraped)}**\n{Constants.TIP}",
        embed=da_embed,
        view=Pagination(ctx, scraped, fulfillment, discount, category, sorting, price, scraper, bot, None),
        ephemeral=True
    )

@bot.command(description="Find Amazon Deals based on keywords! (Preferred)")
async def search_with_keywords(
        ctx,
        search: discord.Option(str, description="What to search?!", required=True),
        fulfillment: discord.Option(str, description="Fulfillment Type", choices=["merchant", "amazon", "all"],
                                    default="all"),
        discount: discord.Option(str, description="Discount Type (Percentage)",
                                 choices=["all", "20-49", "50-79", "80-101"], default="all"),
        category: discord.Option(str, description="Category", choices=categories, default="all"),
        sorting: discord.Option(str, description="Sorting",
                                choices=["No preference", "Low to High", "High to Low", "Discount High to Low",
                                         "Newest"], default="No preference"),
        price_beginning: discord.Option(int, min_value=1, description="Price Range Beginning", default=None),
        price_end: discord.Option(int, max_value=9999999, description="Price Range End", default=None)
):
    await ctx.defer(ephemeral=True)

    # Log the command to the log channel
    log_channel = bot.get_channel(Constants.LOG_CHANNEL)
    await log_channel.send(
        f"**{ctx.author}** used the command **/{ctx.command.qualified_name}** in channel **{ctx.channel}** with the following options:\nSearch: **{search}**\nFulfillment: **{fulfillment}**\nDiscount: **{discount}**\nCategory: **{category}**\nSorting: **{sorting}**\nPrice Beginning: **{price_beginning}**\nPrice End: **{price_end}**")

    check = await mandatory_check(ctx)
    if check is not None:
        await ctx.interaction.followup.send(check, ephemeral=True)
        return

    comment = ""
    
    fulfillment = Helper.map_fulfillment(fulfillment)
    discount = Helper.map_discount(discount)
    sorting = Helper.map_sorting(sorting)
    category = Helper.map_category(category)

    price = Helper.map_price(price_beginning, price_end)
    
    search = search or ""

    page = 1

    coupons_data = await bot.loop.run_in_executor(None, scraper.get_coupons_search, search, fulfillment, discount,
                                                  category, sorting, price, page)

    if not coupons_data["data"]:
        await ctx.interaction.followup.send("No results found!", ephemeral=True)
        return

    if coupons_data["status"] != "success":
        print(coupons_data)
        await ctx.respond("Something went wrong! Please report this.", ephemeral=True)
        return

    scraped = await bot.loop.run_in_executor(None, scraper.parse_search, coupons_data["data"])

    if not scraped:
        await ctx.interaction.followup.send("No results found!", ephemeral=True)
        return

    da_embed = Helper.create_listing_embed(scraped[0])

    await ctx.interaction.followup.send(
        f"You are currently on deal *1* out of **{len(scraped)}**\n{Constants.TIP}" + comment,
        embed=da_embed,
        view=Pagination(ctx, scraped, fulfillment, discount, category, sorting, price, scraper, bot, search),
        ephemeral=True)


@bot.command(description="Add a notification filter!")
async def add_filter(
    ctx,
    search: discord.Option(str, description="What to search?!", required=True),
    fulfillment: discord.Option(
        str, description="Fulfillment Type", choices=["merchant", "amazon", "all"], default="all"
    ),
    discount: discord.Option(
        str, description="Discount Type (Percentage)", choices=["all", "20-49", "50-79", "80-101"], default="all"
    ),
    category: discord.Option(str, description="Category", choices=categories, default="all"),
    sorting: discord.Option(
        str,
        description="Sorting",
        choices=["No preference", "Low to High", "High to Low", "Discount High to Low", "Newest"],
        default="No preference",
    ),
    price_beginning: discord.Option(int, min_value=1, description="Price Range Beginning", default=None),
    price_end: discord.Option(int, max_value=9999999, description="Price Range End", default=None),
):
    await ctx.defer(ephemeral=True)

    log_channel = bot.get_channel(Constants.LOG_CHANNEL)
    await log_channel.send(Helper.get_command_log_message_search(ctx, search, fulfillment, discount, category, sorting, price_beginning, price_end))

    check_result = await mandatory_check(ctx)
    if check_result is not None:
        await ctx.interaction.followup.send(check_result, ephemeral=True)
        return


    # Check if user already has 3 filters
    if len(await Notification.get_filters(ctx.author.id)) >= Notification.MAX_FILTERS:
        await ctx.interaction.followup.send("You already have 3 filters!", ephemeral=True)
        return

    fulfillment = Helper.map_fulfillment(fulfillment)
    discount = Helper.map_discount(discount)
    sorting = Helper.map_sorting(sorting)
    category = Helper.map_category(category)
    price = Helper.map_price(price_beginning, price_end)

    filter = {
        "search": search,
        "fulfillment": fulfillment,
        "discount": discount,
        "category": category,
        "sorting": sorting,
        "price": price,
    }

    if not await Notification.check_user_exists(ctx.author.id):
        await Notification.add_user(ctx.author.id, ctx.author.name, ctx.guild.id)

    if not await Notification.add_filter(ctx.author.id, filter):
        await ctx.interaction.followup.send("You already have this filter!", ephemeral=True)
        return

    await ctx.interaction.followup.send("Successfully added filter!", ephemeral=True)

# Get list of filters
@bot.command(description="Get a list of your filters!")
async def list_filters(ctx):
    await ctx.defer(ephemeral=True)

    log_channel = bot.get_channel(Constants.LOG_CHANNEL)
    await log_channel.send(
        f"**{ctx.author}** used the command **/{ctx.command.qualified_name}** in channel **{ctx.channel}**")

    check = await mandatory_check(ctx)
    if check:
        await ctx.interaction.followup.send(check, ephemeral=True)
        return

    if not await Notification.check_user_exists(ctx.author.id):
        embed = discord.Embed(title="You have no filters!", description="Add one using **/amazon notifications add**")
    else:
        filters = await Notification.get_filters(ctx.author.id, True)

        if len(filters) == 0:
            embed = discord.Embed(title="You have no filters!", description="Add one using **/amazon notifications add**")
        else:
            embed = Helper.create_filters_embed(filters)

    embed.color = discord.Color.random()
    embed.set_footer(text=f"Developed by {Constants.AUTHOR_NAME}")

    await ctx.interaction.followup.send(embed=embed, ephemeral=True)

@bot.command(description="Remove a filter!")
async def remove_filters(ctx):
    global filters
    await ctx.defer(ephemeral=True)

    log_channel = bot.get_channel(Constants.LOG_CHANNEL)
    await log_channel.send(
        f"**{ctx.author}** used the command **/{ctx.command.qualified_name}** in channel **{ctx.channel}**")

    check = await mandatory_check(ctx)
    if check:
        await ctx.interaction.followup.send(check, ephemeral=True)
        return

    user_exists = await Notification.check_user_exists(ctx.author.id)
    if not user_exists:
        embed = discord.Embed(title="You have no filters!", description="Add one using **/amazon notifications add**")
    else:
        filters = await Notification.get_filters(ctx.author.id, True)
        if not filters:
            embed = discord.Embed(title="You have no filters!", description="Add one using **/amazon notifications add**")
        else:
            embed = Helper.create_filters_embed(filters)

    embed.color = discord.Color.random()
    embed.set_footer(text=f"Developed by {Constants.AUTHOR_NAME}")

    if not user_exists or not filters:
        await ctx.interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await ctx.interaction.followup.send(embed=embed, view=NotificationRemoveView(ctx, bot, Notification, filters, embed), ephemeral=True)



try:
    bot.run(Constants.TOKEN)
except KeyboardInterrupt:
    exit()
