import logging
import requests
import settings
import json
import time

def es_connector(func):
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
