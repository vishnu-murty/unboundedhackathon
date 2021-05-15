import pravega_client
import json
import asyncio
import time
import requests
from elasticsearch import Elasticsearch, helpers
import settings
from utils.helper import es_connector


manager = pravega_client.StreamManager("{}:{}".format(settings.pravega.host, settings.pravega.port))
reader_group = manager.create_reader_group(settings.pravega_reader.group,settings.pravega_reader.scope, settings.pravega_reader.stream)
reader1 = reader_group.create_reader(settings.pravega_reader.reader_id)
@es_connector
async def reader():
    slice = await reader1.get_segment_slice_async()
    for event in slice:
       str_data = event.data()
       json_list_data = json.loads(str_data)
       try:
           elastic = Elasticsearch("{}:{}".format(settings.es.host,settings.es.port))   
           response = helpers.bulk(elastic, json_list_data, index=settings.es.index)
       except Exception as e:
           #print(e)
           pass
    
while True:
    loop = asyncio.get_event_loop()
    forecast = loop.run_until_complete(reader())
    time.sleep(5)

