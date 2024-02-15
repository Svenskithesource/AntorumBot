from packets.item import ItemResource
from utils import BufferReader
from os import path

PATH = path.expandvars(r"%userprofile%\AppData\LocalLow\ratwizard\Antorum")


def get_resources():
    with open(PATH + r"\cache\items.cdata", "rb") as f:
        reader = BufferReader(f.read())

    version = reader.read_int64()
    resources = {}
    for _ in range(reader.read_int64()):
        resource_id = reader.read_int64()
        item_resource = ItemResource(reader)
        resources[resource_id] = item_resource
        
    return resources


resources = get_resources()
