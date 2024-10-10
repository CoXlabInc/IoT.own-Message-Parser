import base64
from datetime import datetime, timedelta
import pyiotown.post_process
import redis
from urllib.parse import urlparse
import json

TAG = 'RateController'

def init(url, pp_name, mqtt_url, r, dry_run=False):
    global iotown_url, iotown_token, redis_url
    
    url_parsed = urlparse(url)
    iotown_url = f"{url_parsed.scheme}://{url_parsed.hostname}" + (f":{url_parsed.port}" if url_parsed.port is not None else "")
    iotown_token = url_parsed.password

    redis_url = r
    if redis_url is None:
        print(f"Redis is required for {TAG}.")
        return None

    return pyiotown.post_process.connect_common(url, pp_name, post_process, mqtt_url, dry_run=dry_run)
    
def post_process(message, param=None):
    if param is None:
        raise Exception('param not found')

    try:
        timeout = int(param)
    except:
        raise Exception(f"invalid param ({param})")

    r = redis.from_url(redis_url)

    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}"
    lock = r.set(mutex_key, 'lock', ex=timeout, nx=True)
    if lock != True:
        print(f"[{TAG}] lock failed with '{mutex_key}': {lock}")
        r.close()
        return None

    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    r.close()
    return message
