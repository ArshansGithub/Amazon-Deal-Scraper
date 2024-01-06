# Amazon Deal Scraper - Discord Bot

![GitHub License](https://img.shields.io/badge/license-GNU-blue.svg)

Amazon-Deal-Scraper is an open-source Python and Discord-based utility that enables you to scrape coupon data using a 3rd party reverse engineered API (myvipon.com). You can use this tool to find great deals, coupons, and more on various products. This project is perfect for developers, data enthusiasts, or anyone interested in getting a good deal on Amazon. 
![DiscordCanary_hJxLKMhium](https://github.com/ArshansGithub/Amazon-Deal-Scraper/assets/111618520/21479030-6fb7-4295-8c32-822f5efb7431)

## Table of Contents
- [Background](#background)
- [Features](#features)
- [Goals](#goals)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Background
This project was created to be sold to online entrepreneurship groups but I ultimately decided that this should go towards my public portfolio and for anyone to use.

## Features

- Search for Amazon deals via keywords or without keywords
- Notification system that routinely checks every 6 hours for new deals and DMs user
- Beautiful GUI based on discord bots
- Filter results  by many robust options
- Reverse Engineered API + Built-in captcha solving
- Uses MongoDB database for persistent data
- Admin commands used within private discord server
- If "support" discord users are not in the same server as the bot then the bot blacklists that server (security)

### Goals
- [ ] Fix captcha solving
- [ ] Make wiki/documentation

## Getting Started
Before using AmazonScraper, make sure you have the following dependencies installed:

- Python 3.8+
- `pip install -r requirements.txt`
  
- Within constants file add your discord user ID as a support user and guild
- Set channel IDs for different logging channels
- Set the location of your tesseract executable
- Add proxy in the format accepted by python requests. Make sure proxy is self rotating.
- Add account/session cookies into data/cookies.txt in format of a python dictionary
- Set database hostname and port
- Create database called 'AmazonDealScraper' and two collections within, 'noti-pref' and 'settings'

## Usage
This bot uses discord slash commands!
Within "support" discord servers (selected within constants file) you can manipulate the blacklist and whitelist. Add channels you want to be used for the bot to the whitelist. Ensure all "support" users are in the guild of the bot. 

**/search_without_keywords**
fulfillment - Merchant means amazon doesnt ship it, Amazon means amazon ships it
discount - Pick a range for discounts meaning if you select 80-101 it returns only products that much percent off
category - Self explanatory
sorting - Low to High is in terms of price, same for high to low, discount high to low just shows the highest discounts first, and then newest for newest
price_beginning - pick a beginning range for price (if price_end is left empty then it resorts to the highest value)
price_end - pick a end range for price (if price_beginning is left empty then it resorts to zero)

Example -> Discount High to Low
Tree 1: $300 off
Tree 2: $400 off
Tree 3: $100 off
When using discount high to low option it sorts based on the amount of money saved (the discount) so it shows in order of tree 2 then tree 1, then tree 3

Example -> Discount Low to High
Tree 1: $200 (after discounts)
Tree 2: $100 (after discounts)
Tree 3: $150 (after discounts)
When using low to high option it sorts based on the cost of the product AFTER discounts so in this case it goes tree 2, tree 3, tree 1

**/search_with_keywords**
Basically same filter options but with a "search" option for placing keywords 

**/add_filter**
You can add queries to be checked every 6 hours so if you're looking for a laundry basket 90+ percent off, you can add that specific filter then every 6 hours it will check for new deals and DM any new ones to you 
Some child commands to this are: **/list_filters ** and **/remove_filter**

## Contributing

Contributions are welcome. You can contribute by reporting issues, suggesting improvements, or submitting pull requests. To get started:

    Fork this repository.
    Create a new branch for your feature or bug fix: git checkout -b feature/your-feature.
    Make your changes and commit them.
    Push to your fork: git push origin feature/your-feature.
    Create a pull request.

Please ensure your code adheres to proper coding standards and includes relevant tests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

If you have any questions or need assistance, feel free to reach out to the project maintainers.
