from db.dbwrapper import DBWrapper
from motor import motor_asyncio

class MongoDBWrapper(DBWrapper):
    def __init__(self, connection_str: str, database: str):
        self.db = motor_asyncio.AsyncIOMotorClient(connection_str)[database]

    async def insert_one(self, table_name: str, item_dict: dict):
        collection = self.db.get_collection(table_name)
        await collection.insert_one(item_dict)

    async def find_one(self, table_name: str, search_params: dict):
        collection = self.db.get_collection(table_name)
        item = await collection.find_one(search_params)
        return item

    async def update_one(self, table_name: str, search_params: dict, data: dict):
        collection = self.db.get_collection(table_name)
        rt = await collection.update_one(search_params, {"$set": data})
        return rt

    async def delete_one(self, table_name: str, search_params: dict):
        collection = self.db.get_collection(table_name)
        return await collection.delete_one(search_params)

    async def find(self, table_name: str, search_params: dict):
        collection = self.db.get_collection(table_name)
        cursor = collection.find(search_params)
        rt = []
        for row in await cursor.to_list(length=100):
            rt.append(row)

        return rt
