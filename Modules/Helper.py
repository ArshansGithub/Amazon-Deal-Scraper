from Variables import Constants
import discord

def guild_has_support(guild):
    return any(member.id in Constants.SUPPORT_USERS for member in guild.members)

def create_sad_embed():
    sad_embed = discord.Embed(
        title="Sorry... | Amazon Deal Notification System",
        description="No **new** listings were found with your filter criteria. Maybe wait for the next couple checks."
    )
    sad_embed.color = discord.Color.random()
    sad_embed.set_footer(text=f"Developed by {Constants.AUTHOR_NAME}")

    return sad_embed

def create_listing_embed(listing_data):
    da_embed = discord.Embed(
        title=listing_data["title"]
    )
    da_embed.color = discord.Color.random()
    da_embed.set_image(url=listing_data["img_src"])

    da_embed.add_field(name="Regular Price", value=listing_data["regular_price"], inline=True)
    da_embed.add_field(name="Savings", value=listing_data["discount"], inline=True)
    da_embed.add_field(name="Discounted Price", value=listing_data["discounted_price"], inline=True)

    da_embed.add_field(name="Fulfillment", value=listing_data["fulfillment"], inline=True)
    da_embed.add_field(name="Shipping", value=str(listing_data["shipping"]), inline=True)
    da_embed.add_field(name="Category", value=listing_data["category"], inline=True)

    da_embed.add_field(name="Reviews", value=listing_data["review"], inline=True)
    da_embed.add_field(name="Review Count", value=listing_data["review_count"], inline=True)

    da_embed.set_footer(text=f"Developed by {Constants.AUTHOR_NAME}")

    return da_embed

def create_listing_embed_generic(listing_data):
    da_embed = discord.Embed(
        title=listing_data["title"]
    )
    da_embed.color = discord.Color.random()
    da_embed.set_image(url=listing_data["img_src"])

    da_embed.add_field(name="Regular Price", value=listing_data["regular_price"], inline=True)
    da_embed.add_field(name="Savings", value=listing_data["discount"], inline=True)
    da_embed.add_field(name="Discounted Price", value=listing_data["discounted_price"], inline=True)

    da_embed.add_field(name="Fulfillment", value=listing_data["fulfillment"], inline=True)

    da_embed.set_footer(text=f"Developed by {Constants.AUTHOR_NAME}")

    return da_embed

def create_filter_embed(filter_count):
    filter_embed = discord.Embed(
        title=f"{filter_count} of your filters are being checked right now!",
        description="I'm going through your filters right now and checking for any new listings.\n\n"
                    "If there aren't any new deals, you can try to change your filter criteria or wait for the next couple checks.\n\n"
                    "BTW this process occurs every 6 hours"
    )
    filter_embed.color = discord.Color.random()
    filter_embed.set_footer(text=f"Developed by {Constants.AUTHOR_NAME}")

    return filter_embed

def get_command_log_message_search(ctx, search, fulfillment, discount, category, sorting, price_beginning, price_end):
    return (
        f"**{ctx.author}** used the command **/{ctx.command.qualified_name}** in channel **{ctx.channel}** "
        f"with the following options:\nSearch: **{search}**\nFulfillment: **{fulfillment}**\nDiscount: **{discount}**"
        f"\nCategory: **{category}**\nSorting: **{sorting}**\nPrice Beginning: **{price_beginning}**\nPrice End: **{price_end}**"
    )

def get_command_log_message_without(ctx, fulfillment, discount, category, sorting, price_beginning, price_end):
    return (
        f"**{ctx.author}** used the command **/{ctx.command.qualified_name}** in channel **{ctx.channel}** "
        f"with the following options:\nFulfillment: **{fulfillment}**\nDiscount: **{discount}**\nCategory: **{category}**"
        f"\nSorting: **{sorting}**\nPrice Beginning: **{price_beginning}**\nPrice End: **{price_end}**"
    )

def map_fulfillment(fulfillment):
    return {"all": "", "merchant": "2", "amazon": "1"}.get(fulfillment, "")

def map_discount(discount):
    return "" if not discount or discount == "all" else discount

def map_sorting(sorting):
    sorting_mapping = {
        "No preference": "",
        "Low to High": "price",
        "High to Low": "price_contrary",
        "Discount High to Low": "discount",
        "Newest": "newest",
    }
    return sorting_mapping.get(sorting, "")

def map_category(category):
    categories = {
        "Arts, Crafts & Sewing": "14",
        "Automotive & Industrial": "19",
        "Baby": "16",
        "Beauty & Personal Care": "5",
        "Cell Phones & Accessories": "11",
        "Electronics": "8",
        "Health & Household": "9",
        "Home & Kitchen": "1",
        "Jewelry": "4",
        "Men Clothing, Shoes & Accessories": "15",
        "Office Products": "18",
        "Patio, Lawn & Garden": "13",
        "Pet Supplies": "17",
        "Sports & Outdoors": "12",
        "Tools & Home Improvement": "7",
        "Toys & Games": "6",
        "Watches": "3",
        "Women Clothing, Shoes & Accessories": "2",
        "Others": "20",
        "Adult Products": "10"
    }
    return categories.get(category, "")

def map_price(price_beginning, price_end):
    
    if not price_beginning and not price_end:
        return ""

    price = f"{price_beginning}-" if price_beginning else "0-"
    price += f"{price_end}" if price_end else "9999999"
    return price

def get_price_info(filter):
    price = filter["price"]
    if price == "No preference":
        return {"price_beginning": "No preference", "price_end": "No preference"}

    price_beginning, price_end = map(int, price.split("-"))
    return {"price_beginning": price_beginning, "price_end": price_end}

def create_filters_embed(filters):
    embed = discord.Embed(title="Your Filters")
    embed.color = discord.Color.random()

    for index, filter in enumerate(filters, start=1):
        price_info = get_price_info(filter)
        embed.add_field(name=f"Filter {index}",
                        value=f"Search: **{filter['search']}**\n"
                              f"Fulfillment: **{filter['fulfillment']}**\n"
                              f"Discount: **{filter['discount']}**\n"
                              f"Category: **{filter['category']}**\n"
                              f"Sorting: **{filter['sorting']}**\n"
                              f"Price Beginning: **{price_info['price_beginning']}**\n"
                              f"Price End: **{price_info['price_end']}**",
                        inline=True)

    return embed

def combine_two_dicts(dict1, dict2):
    combined_dict = dict1.copy()
    offset = len(dict1)
    for key in dict2:
        combined_dict[key + offset] = dict2[key]
    return combined_dict