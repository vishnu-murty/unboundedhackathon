import pravega_client
import json
import asyncio
import time
import requests
from elasticsearch import Elasticsearch, helpers
elastic_ip = "100.102.128.28"
elastic_port = "8080"
elastic_index = "pravega_telemetry"
elastic_type = "_doc"
elastic_url = "http://{}:{}/{}/{}".format(elastic_ip, elastic_port, elastic_index, elastic_type)
pravega_ip = "100.64.25.48"
pravega_port = "9090"
manager = pravega_client.StreamManager("{}:{}".format(pravega_ip, pravega_port))
reader_group = manager.create_reader_group("rg23","dell-scope5", "dell-stream5")
reader1 = reader_group.create_reader("rdr6")
async def reader():
    slice = await reader1.get_segment_slice_async()
    for event in slice:
       try:
           requests.get("http://{}:{}".format(elastic_ip, elastic_port))
           
       except Exception as e:
           #print(e)
           continue
       str_data = event.data()
       json_list_data = json.loads(str_data)
       #print(json_list_data)
       try:
           elastic = Elasticsearch("{}:{}".format(elastic_ip,elastic_port))   
           response = helpers.bulk(elastic, json_list_data, index=elastic_index)
       except Exception as e:
           #print(e)
           pass
    
while True:
    loop = asyncio.get_event_loop()
    forecast = loop.run_until_complete(reader())
    time.sleep(5)

