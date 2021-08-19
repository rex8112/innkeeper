import datetime
import discord
import json

def dumps(obj):
    return json.dumps(obj, default=serialize)

def serialize(obj):
    try:
        return obj.serialize()
    except AttributeError:
        pass
    if isinstance(obj, (discord.User, discord.Member, discord.Guild, discord.TextChannel)):
        return obj.id
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()