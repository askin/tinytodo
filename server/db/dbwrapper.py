import abc

class DBWrapper(abc.ABC):
    @abc.abstractmethod
    async def insert_one(self, table_name: str, item_dict: dict):
        pass

    @abc.abstractmethod
    async def find_one(self, table_name: str, search_params: dict):
        pass

    @abc.abstractmethod
    async def update_one(self, table_name: str, search_params: dict, data: dict):
        pass

    @abc.abstractmethod
    async def find(self, table_name: str, search_params: dict):
        pass

    @abc.abstractmethod
    async def delete_one(self, table_name: str, search_params: dict):
        pass
