import time
import requests


class Emby:

    def __init__(self, server_url, user_id, api_key):
        self.server_url = server_url
        self.user_id = user_id
        self.api_key = api_key
        self.headers = {"X-MediaBrowser-Token": api_key}
        # To prevent too long URLs, queries are done in batches of n
        self.api_batch_size = 50
        self.seconds_between_requests = 2

    def get_system_info(self):
        endpoint = "/emby/System/Info"
        url = self.server_url + endpoint
        response = requests.get(url, headers=self.headers)
        return response.json()

    def get_users(self):
        user_list_endpoint = "/emby/Users"
        user_list_url = self.server_url + user_list_endpoint
        user_list_response = requests.get(user_list_url, headers=self.headers)
        user_list = user_list_response.json()
        return user_list

    def get_all_collections(self, include_contents=True):
        """
        Retrieves all collections from the Emby server.

        Parameters:
        - include_contents (bool): Flag to indicate whether to include the items within each collection.

        Returns:
        - collections_list (list): List of dictionaries representing each collection, including its name, ID, and items (if include_contents is True).
        """
        endpoint = f"/emby/users/{self.user_id}/items?Fields=ChildCount,RecursiveItemCount&Recursive=true&IncludeItemTypes=boxset"
        url = self.server_url + endpoint
        response = requests.get(url, headers=self.headers)
        items = response.json()
        collections_list = []

        for item in items["Items"]:
            items_in_collection = None
            if include_contents:
                items_in_collection = self.get_items_in_collection(item["Id"])
            collections_list.append(
                {"Name": item["Name"], "Id": item["Id"], "items": items_in_collection}
            )

        return collections_list

    def get_items_in_collection(self, collection_id):
        """
        Retrieves items in a collection based on the provided collection ID.

        Args:
            collection_id (str or int): The ID of the collection.

        Returns:
            list: A list of dictionaries containing the structured items in the collection.
                Each dictionary contains the item ID and the IMDb ID (if available).
        """
        endpoint = f"/emby/users/{self.user_id}/items?Parentid={collection_id}&Fields=ProviderIds"
        url = self.server_url + endpoint
        response = requests.get(url, headers=self.headers)
        items = response.json()
        structured_items = []
        for item in items["Items"]:
            imdb_id = item["ProviderIds"].get("Imdb") or item["ProviderIds"].get(
                "IMDB"
            )  # "Imdb" is sometimes all caps and sometimes not!
            structured_items.append({"Id": item["Id"], "Imdb": imdb_id})
        return structured_items

    def get_items_by_tag(self, tag):
        """
        Retrieves items based on the provided tag.

        Args:
            tag (str): The tag to filter by.

        Returns:
            list: A list of dictionaries containing the structured items.
                Each dictionary contains the item ID and the IMDb ID (if available).
        """
        endpoint = f"/emby/users/{self.user_id}/items?Tags={tag}&Fields=ProviderIds&Recursive=true&IncludeItemTypes=Movie,Series"
        url = self.server_url + endpoint
        response = requests.get(url, headers=self.headers)
        items = response.json()
        structured_items = []
        for item in items["Items"]:
            imdb_id = item["ProviderIds"].get("Imdb") or item["ProviderIds"].get(
                "IMDB"
            )  # "Imdb" is sometimes all caps and sometimes not!
            structured_items.append({"Id": item["Id"], "Imdb": imdb_id})
        return structured_items

    def get_tags(self):
        """
        Retrieves movies and series item tags.

        Returns:
            list: A list of tags.
        """
        endpoint = f"/Tags?Recursive=true&IncludeItemTypes=Movie,Series"
        url = self.server_url + endpoint
        response = requests.get(url, headers=self.headers)
        items = response.json()
        tags = []
        for item in items["Items"]:
            tags.append(item["Name"])
        return tags

    def create_collection(self, collection_name, item_ids) -> bool:
        """
        Check if collection exists, creates if not, then adds items to it.
        Must add at least one item when creating collection.

        Args:
            collection_name (str): The name of the collection to be created.
            item_ids (list): A list of item IDs to be added to the collection.

        Returns:
            bool: True if the collection is created successfully, False otherwise.
        """
        if item_ids is None or len(item_ids) == 0:
            print("Can't create collection, no items to add to it.")
            return None

        response = requests.post(
            f"{self.server_url}/Collections?api_key={self.api_key}&IsLocked=true&Name={collection_name}&Ids={Emby.__ids_to_str(item_ids)}"
        )

        if response.status_code != 200:
            print(f"Error creating {collection_name}, response: {response}")
            return None

        print(f"Successfully created collection {collection_name}")
        return response.json()["Id"]

    def __get_item(self, item_id) -> dict:
        endpoint = f"/emby/users/{self.user_id}/items/{item_id}"
        url = self.server_url + endpoint
        try:
            return requests.get(url, headers=self.headers).json()
        except Exception as e:
            print(f"Error occurred while getting item: {e}")
            return None

    def __update_item(self, item_id, data):
        item = self.__get_item(item_id)
        if item is None:
            return None
        if "ForcedSortName" in data and "SortName" not in item["LockedFields"]:
            # If adding "ForcedSortName" to data, we must have "SortName" in LockedFields
            # see https://emby.media/community/index.php?/topic/108814-itemupdateservice-cannot-change-the-sortname-and-forcedsortname/
            item["LockedFields"].append("SortName")
        item.update(data)
        update_item_url = (
            f"{self.server_url}/emby/Items/{item_id}?api_key={self.api_key}"
        )
        try:
            response = requests.post(update_item_url, json=item, headers=self.headers)
            return response
        except Exception as e:
            print(f"Error occurred while updating item: {e}")
            return None

    def set_item_property(self, item_id, property_name, property_value):
        return self.__update_item(item_id, {property_name: property_value})

    def __ids_to_str(ids: list) -> str:
        item_ids = [str(item_id) for item_id in ids]
        return ",".join(item_ids)

    def get_collection_id(self, collection_name):
        all_collections = self.get_all_collections(False)
        collection_found = False

        for collection in all_collections:
            if collection_name == collection["Name"]:
                collection_found = True
                collection_id = collection["Id"]
                break

        if collection_found is False:
            return None

        return collection_id

    def __add_remove_from_collection(
        self, collection_name: str, item_ids: list, operation: str
    ) -> int:

        affected_count = 0

        if len(item_ids) == 0:
            return affected_count

        collection_id = self.get_collection_id(collection_name)

        if collection_id is None:
            return affected_count

        batch_size = self.api_batch_size
        num_batches = (len(item_ids) + batch_size - 1) // batch_size

        for i in range(num_batches):
            start_index = i * batch_size
            end_index = min((i + 1) * batch_size, len(item_ids))
            batch_item_ids = item_ids[start_index:end_index]

            print(
                f"Processing Collection with operation {operation} batch {i+1} of {num_batches} with {len(batch_item_ids)} items"
            )

            if operation == "add":
                response = requests.post(
                    f"{self.server_url}/Collections/{collection_id}/Items/?api_key={self.api_key}&Ids={Emby.__ids_to_str(batch_item_ids)}"
                )
                affected_count += len(batch_item_ids)
            elif operation == "delete":
                response = requests.delete(
                    f"{self.server_url}/Collections/{collection_id}/Items/?api_key={self.api_key}&Ids={Emby.__ids_to_str(batch_item_ids)}"
                )
                affected_count += len(batch_item_ids)

            if response.status_code != 204:
                print(
                    f"Error processing collection with operation '{operation}', response: {response}"
                )
                return affected_count

            print(
                f"Successfully processed batch {i+1} of {num_batches} with {len(batch_item_ids)} items"
            )
            time.sleep(self.seconds_between_requests)

        print(
            f"Completed Collection operation '{operation}' with {len(item_ids)} items in collection {collection_name}"
        )

        return affected_count

    def add_to_collection(self, collection_name, item_ids) -> int:
        # Returns the number of items added to the collection
        return self.__add_remove_from_collection(collection_name, item_ids, "add")

    def delete_from_collection(self, collection_name, item_ids) -> int:
        # Returns the number of items deleted from the collection
        return self.__add_remove_from_collection(collection_name, item_ids, "delete")
