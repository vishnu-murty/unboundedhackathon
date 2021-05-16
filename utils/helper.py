import logging
import requests
import settings
import json
import time
import random
import pravega_client
from elasticsearch import Elasticsearch, helpers

def es_reachable(func):
    def with_connection_(*args, **kwargs):
        try:
            requests.get("http://{}:{}".format(settings.es.host, settings.es.port))
            rv = func( *args, **kwargs)
        except Exception:
            logging.error("ES connection error")
            time.sleep(5)
            with_connection_(*args, **kwargs)
        return rv

    return with_connection_

def get_suffix():
    suffix = str(random.randint(0, 100))
    return suffix

def get_online_reader():
    manager = pravega_client.StreamManager("{}:{}".format(settings.pravega.host, settings.pravega.port))
    reader_group = manager.create_reader_group(settings.pravega.group,settings.pravega.scope, settings.pravega.stream)
    while True:
        try:
            reader = reader_group.create_reader(settings.pravega.reader_id+get_suffix())
            break
        except:
            pass
    return reader

def store_data_es(slice):
    for event in slice:
        str_data = event.data()
        json_list_data = json.loads(str_data)
        try:
            elastic = Elasticsearch("{}:{}".format(settings.es.host,settings.es.port))
            response = helpers.bulk(elastic, json_list_data, index=settings.es.index)
        except Exception as e:
            #print(e)
            pass
