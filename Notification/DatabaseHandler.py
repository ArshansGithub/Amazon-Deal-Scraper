import asyncio
import copy

import motor.motor_asyncio
from pymongo.errors import DuplicateKeyError
from Variables import Constants

class DatabaseHandler:
    def __init__(self):
        # Constants
        self.MAX_FILTERS = 3

        # Connect to MongoDB asynchronously
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Constants.HOST, Constants.PORT)
        self.client.get_io_loop = asyncio.get_running_loop
        self.db = self.client['AmazonDealScraper']
        self.collection = self.db['noti-pref']
        self.settings = self.db['settings']

    async def add_user(self, user_id, name, guild_id):
        try:
            await self.collection.insert_one({"user": user_id, "name": name, "guild": guild_id, "filters": [], "already_checked": []})
        except DuplicateKeyError:
            pass

    async def check_user_exists(self, user_id):
        e = await self.collection.find_one({"user": user_id}) is not None
        return e

    async def get_filters(self, user_id, user_readable=False):
        document = await self.collection.find_one({"user": user_id})

        if not document or document["filters"] is None:
            return []

        toReturn = copy.deepcopy(document)

        if user_readable:
            # Convert empty string or None to "No preference"
            for i, filter in enumerate(document["filters"]):
                for key, value in filter.items():
                    if not bool(value):
                        toReturn["filters"][i][key] = "No preference"
                    elif "price" in key:
                        if not bool(value):
                            toReturn["filters"][i]["price_beginning"] = "No preference"
                            toReturn["filters"][i]["price_end"] = "No preference"
                        else:
                            toReturn["filters"][i]["price_beginning"] = value.split("-")[0]
                            toReturn["filters"][i]["price_end"] = value.split("-")[1]

        return toReturn["filters"]

    async def get_filter_by_index(self, user_id, user_readable, index: int):
        filters = await self.get_filters(user_id, user_readable)
        if index >= len(filters):
            return False

        return filters[index]

    async def add_filter(self, user_id, filter):
        if len(await self.get_filters(user_id)) >= self.MAX_FILTERS:
            return False

        if filter in await self.get_filters(user_id):
            return False

        await self.collection.update_one({"user": user_id}, {"$push": {"filters": filter}})

        await self.collection.update_one({"user": user_id}, {"$push": {"already_checked": []}})

        return True

    async def remove_filter(self, user_id, filter):
        if filter not in await self.get_filters(user_id):
            return False

        # Get index of filter and remove it from already_checked
        index = await self.get_index_of_filter(user_id, filter)

        if index is False:
            return False

        # Remove filter from already_checked by index
        await self.collection.update_one({"user": user_id}, {"$unset": {f"already_checked.{index}": 1}})
        await self.collection.update_one({"user": user_id}, {"$pull": {f"already_checked": None}})

        await self.collection.update_one({"user": user_id}, {"$pull": {"filters": filter}})

        return True

    async def remove_filter_by_index(self, user_id, index: int):
        filters = await self.get_filters(user_id)

        if index >= len(filters):
            return False

        remove = await self.remove_filter(user_id, filters[index])

        if remove:
            return True
        else:
            return False

    async def remove_all_filters(self, user_id):
        await self.collection.update_one({"user": user_id}, {"$set": {"filters": []}})

        # Set already_checked to empty list
        await self.collection.update_one({"user": user_id}, {"$set": {"already_checked": []}})

    async def get_index_of_filter(self, user_id, filter):
        filters = await self.get_filters(user_id)

        if filter not in filters:
            return False

        return filters.index(filter)
    async def get_already_checked(self, user_id, filterIndex):
        document = await self.collection.find_one({"user": user_id})
        return document["already_checked"][filterIndex] if document else []

    async def already_checked(self, user_id, listing_id, filterIndex):
        return listing_id in await self.get_already_checked(user_id, filterIndex)

    async def add_already_checked(self, user_id, filterIndex, listing_id):
        await self.collection.update_one({"user": user_id}, {"$push": {f"already_checked.{filterIndex}": listing_id}})

    async def get_all_users(self):
        docs = []
        async for document in self.collection.find():
            docs.append(document)
        return docs

    async def get_user(self, user_id):
        e = await self.collection.find_one({"user": user_id})
        return e

    async def clear_already_checked(self, user_id):
        try:
            # clear filters
            await self.collection.update_one({"user": user_id}, {"$set": {"filters": []}})
            # clear already_checked
            await self.collection.update_one({"user": user_id}, {"$set": {"already_checked": []}})
            return "Successfully cleared!"
        except Exception as e:
            return e
        
    async def add_channel(self, channel_id):
        # check if document for whitelist exists
        if await self.get_whitelist() == "Something went wrong!":
            await self.settings.insert_one({"whitelist": [], "blacklist": []})

        try:
            int(channel_id)
        except ValueError:
            return "Invalid channel ID!"
        
        # check if channel is already in whitelist
        if channel_id in await self.get_whitelist():
            return "Already in whitelist!"
        
        # add channel to whitelist
        await self.settings.update_one({}, {"$push": {"whitelist": channel_id}})
        
        return "Successfully added!"
        
    async def remove_channel(self, channel_id):
        if await self.get_whitelist() == "Something went wrong!":
            await self.settings.insert_one({"whitelist": [], "blacklist": []})

        try:
            int(channel_id)
        except ValueError:
            return "Invalid channel ID!"
        
        if channel_id not in await self.get_whitelist():
            return "Not in whitelist!"
        
        await self.settings.update_one({}, {"$pull": {"whitelist": channel_id}})
        
        return "Successfully removed!"
    
    
    async def get_whitelist(self, returnList=False):
        try:
            document = await self.settings.find_one({})
        except Exception as e:
            print(e)
            return "Something went wrong!"
        
        if returnList:
            return document["whitelist"] if document else "Something went wrong!"
        
        if len(document["whitelist"]) == 0:
            return "No channels in whitelist!"
        
        return ", ".join(str(each) for each in document["whitelist"]) if document else "Something went wrong!"
        
    async def add_blacklist(self, channel_id):
        # check if document for blacklist exists
        if await self.get_blacklist() == "Something went wrong!":
            await self.settings.insert_one({"whitelist": [], "blacklist": []})

        try:
            int(channel_id)
        except ValueError:
            return "Invalid channel ID!"
        
        # check if channel is already in blacklist
        if str(channel_id) in await self.get_blacklist():
            return "Already in blacklist!"
        
        # add channel to blacklist
        await self.settings.update_one({}, {"$push": {"blacklist": str(channel_id)}})
        
        return "Successfully added!"
    
    async def remove_blacklist(self, channel_id):
        if await self.get_blacklist() == "Something went wrong!":
            await self.settings.insert_one({"whitelist": [], "blacklist": []})

        try:
            int(channel_id)
        except ValueError:
            return "Invalid channel ID!"
        
        if str(channel_id) not in await self.get_blacklist():
            return "Not in blacklist!"
        
        a = await self.settings.update_one({}, {"$pull": {"blacklist": str(channel_id)}})
        print(a)
        print(await self.get_blacklist())
        return "Successfully removed!"
    
    async def get_blacklist(self, returnList=False):
        try:
            document = await self.settings.find_one({})
        except Exception as e:
            print(e)
            return "Something went wrong!"
        
        if len(document["blacklist"]) == 0:
            return "No channels in whitelist!"
        
        if returnList:
            return document["blacklist"] if document else "Something went wrong!"
        return ", ".join(str(each) for each in document["blacklist"]) if document else "Something went wrong!"