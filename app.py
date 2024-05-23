import time
import configparser
from emby import Emby

## Helpful URLS for dev:
# https://swagger.emby.media/?staticview=true#/
# https://github.com/MediaBrowser/Emby/wiki
# https://dev.emby.media/doc/restapi/Browsing-the-Library.html

config_parser = configparser.ConfigParser()

# Check if config_hidden.cfg exists, if so, use that, otherwise use config.cfg
if config_parser.read("config_hidden.cfg") == []:
    config_parser.read("config.cfg")

emby_server_url = config_parser.get("admin", "emby_server_url")
emby_user_id = config_parser.get("admin", "emby_user_id")
emby_api_key = config_parser.get("admin", "emby_api_key")
hours_between_refresh = config_parser.getint("admin", "hours_between_refresh")
tag_prefix = config_parser.get("admin", "tag_prefix", fallback="")

newly_added = 0
newly_removed = 0

emby = Emby(emby_server_url, emby_user_id, emby_api_key)


def find_missing_entries_in_list(list_to_check, list_to_find):
    """
    Finds the missing entries in a list.

    Args:
        list_to_check (list): The list to check against.
        list_to_find (list): The list to find missing entries in.

    Returns:
        list: A list of missing entries found in list_to_find.
    """
    return [item for item in list_to_find if item not in list_to_check]


def process_tag(tag: dict):
    global newly_added
    global newly_removed
    collection_name = tag["collection_name"]
    tag_name = tag["tag_name"]

    collection_id = emby.get_collection_id(collection_name)

    if collection_id is None:
        print(f"Collection {collection_name} does not exist. Will create it.")

    print()
    print("=========================================")

    tagged_items = emby.get_items_by_tag(tag_name)
    tagged_items_ids = [item["Id"] for item in tagged_items]

    if len(tagged_items) == 0:
        print(
            f"ERROR! No items with tag {tag_name}."
        )
        print("=========================================")
        return

    remove_emby_ids = []

    print(f"Processing {collection_name}: {len(tagged_items)} items.")

    if collection_id is None:
        add_emby_ids = tagged_items_ids
    else:
        collection_items = emby.get_items_in_collection(collection_id)
        collection_ids = [item["Id"] for item in collection_items]
        add_emby_ids = find_missing_entries_in_list(
            collection_ids, tagged_items_ids
        )

        for item in collection_items:
            if item["Id"] not in tagged_items_ids:
                remove_emby_ids.append(item["Id"])

    print(
        f"Added {len(add_emby_ids)} new items to Collection and removed {len(remove_emby_ids)}."
    )

    if collection_id is None:
        if len(add_emby_ids) == 0:
            print(
                f"ERROR! No items to put in collection {collection_name}. Will not process."
            )
            print("=========================================")
            return
        collection_id = emby.create_collection(
            collection_name, [add_emby_ids[0]]
        )  # Create the collection with the first item since you have to create with an item
        add_emby_ids.pop(0)

    items_added = emby.add_to_collection(collection_name, add_emby_ids)
    newly_added += items_added
    newly_removed += emby.delete_from_collection(collection_name, remove_emby_ids)

    print("=========================================")


def process_list_of_tags():
    collections = []
    tags = emby.get_tags()
    for tag in tags:
        if tag.startswith(tag_prefix):
            collections.append(
                {
                    "collection_name": tag.replace(tag_prefix, '').strip(),
                    "tag_name": tag
                })

    for col in collections:
        process_tag(col)


def main():
    global newly_added
    global newly_removed
    iterations = 0

    # print(f"Emby System Info: {emby.get_system_info()}")
    # print()
    # print(f"Emby Users: {emby.get_users()}")
    # print()

    while True:
        process_list_of_tags()

        print()
        print(
            f"SUMMARY: Added {newly_added} items in total to collections and removed {newly_removed} items."
        )
        print(
            f"Waiting {hours_between_refresh} hours for next refresh. Iteration {iterations}"
        )
        newly_added = 0
        newly_removed = 0

        if hours_between_refresh == 0:
            break

        time.sleep(hours_between_refresh * 3600)
        iterations += 1


if __name__ == "__main__":
    main()
