import base64
from datetime import datetime, timedelta
import pyiotown.post_process
import redis
from urllib.parse import urlparse
import json

TAG = 'Aggregator'

def init(url, pp_name, mqtt_url, redis_url, dry_run=False):
    global iotown_url, iotown_token
    
    url_parsed = urlparse(url)
    iotown_url = f"{url_parsed.scheme}://{url_parsed.hostname}" + (f":{url_parsed.port}" if url_parsed.port is not None else "")
    iotown_token = url_parsed.password
    
    if redis_url is None:
        print(f"Redis is required for {TAG}.")
        return None

    global r
    
    try:
        r = redis.from_url(redis_url)
        if r.ping() == False:
            r = None
            raise Exception('Redis connection failed')
    except Exception as e:
        raise(e)

    return pyiotown.post_process.connect_common(url, pp_name, post_process, mqtt_url, dry_run=dry_run)
    
def post_process(message, param=None):
    try:
        params = json.loads('{' + param + '}')
    except:
        raise Exception('param format error')

    # "id":"aggregator ID","data":{"temperature":"room1_temperature", ...},"timeout":11
    
    id = params.get('id')
    if id is None or type(id) is not str:
        raise Exception(f"[{TAG}] The 'id' str MUST be specified.")

    data = params.get('data')
    if data is None or type(data) is not dict:
        raise Exception(f"[{TAG}] The 'data' object MUST be specified.")

    try:
        timeout = int(params.get('timeout'))
    except:
        raise Exception(f"[{TAG}] The 'timeout' number MUST be specified.")
    
    #Data MUTEX
    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}:{message['key']}"
    lock = r.set(mutex_key, 'lock', ex=timeout, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        return None

    mapping = {}
    for k in data.keys():
        v = message['data'].get(k)
        if v is not None:
            mapping[data[k]] = v

    if len(mapping.keys()) > 0:
        hash_key = f"PP:{TAG}:Data:{message['grpid']}:{id}"
        r.hset(hash_key, mapping=mapping)

    #Report MUTEX
    report_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{id}"
    lock = r.set(report_key, 'lock', ex=timeout, nx=True)

    #Report on lock acquisition
    if lock == True:
        dataset = r.hgetall(hash_key)
        aggregated_message = {}
        for bk in dataset.keys():
            k = bk.decode('utf-8')
            
            try:
                v = int(dataset[bk])
            except:
                v = None

            if v is None:
                try:
                    v = float(dataset[bk])
                except:
                    v = None

            if v is None:
                try:
                    v = bool(dataset[bk])
                except:
                    v = None

            if v is None:
                try:
                    v = str(dataset[bk])
                except:
                    v = None
                    
            aggregated_message[k] = v

        print(f"[{TAG}] report {aggregated_message}")

        if pyiotown.post.data(iotown_url, iotown_token,
                              id, aggregated_message, group_id=message['grpid'],
                              verify=False) == False:
            raise Exception(f"[{TAG}] post data error")
        r.delete(hash_key)
        
    r.delete(mutex_key)
    return message
