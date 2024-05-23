# Emby Tag to Collection Creator

This Python script allows you to automatically create and maintain collections for your Movies and Series using your own tags.

Used [jonjonsson](https://github.com/jonjonsson) wonderful script [Emby-MDBList-Collection-Creator](https://github.com/jonjonsson/Emby-MDBList-Collection-Creator) as base, any credits to them. 

Many thanks =)

## Why?

I've been using Emby for years and once in a while something unexpected messes with my collections. 

As I handle my nfo files with tinyMediaManager, thanks to this script I can easily maintain or recreate all the collections on any Emby server.

## Prerequisites:

To use this script, you need:

* Python installed on your system
* "Requests" Python package (install with `pip install requests`)
* Admin privileges on Emby
* The script has been tested with Emby Version 4.8.7.0, but other recent versions should also be compatible

## Usage

### Configuring the Admin Section

In the `config.cfg` file, fill in the following details:

* Emby server URL
* Emby admin user ID
* Emby API key

Refer to the comments in `config.cfg` for additional information.

### Running the Script

Navigate to the project directory and execute the following commands:

```bash
pip install requests
python app.py
```

## Creating Emby Collections

Nothing fancy here, just set any desired tag prefix in `config.cfg` and run the script.

* E.g.: Setting a prefix like "Set:" and having a tag named "Set: Godfather" will create a collection named "Godfather".

## Frequently Asked Questions

- **What happens if I do not set a prefix?**
  - All of your tags will be used to create collections. 

- **What happens if I rename my collection in Emby?**
  - A new collection will be created with the tag name sans the prefix specified in `config.cfg`, if any.
  
- **Does this affect my manually created collection?**
  - This will only affect collections which name matches the tag.
  
- **Do I need a server to use this script?**
  - No, you can run it on your PC and keep it open. The script refreshes the collections every n hours.
  
- **Do the collections show for all Emby users?**
  - Yes, the collections will be visible to all Emby users.
