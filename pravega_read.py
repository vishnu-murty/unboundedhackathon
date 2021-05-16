import pravega_client
import json
import asyncio
import time
import requests
from elasticsearch import Elasticsearch, helpers
import settings
from utils.helper import get_online_reader,es_reachable,store_data_es

reader1 = get_online_reader()

@es_reachable
async def reader():
    slice = await reader1.get_segment_slice_async()
    store_data_es(slice)
    
while True:
    loop = asyncio.get_event_loop()
    forecast = loop.run_until_complete(reader())
    time.sleep(5)

