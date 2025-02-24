import base64
from datetime import datetime, timedelta
import pyiotown.post_process
import redis
from urllib.parse import urlparse
import json

TAG = 'Aggregator'

def init(url, pp_name, mqtt_url, r, dry_run=False):
    global iotown_url, iotown_token, redis_url
    
    url_parsed = urlparse(url)
    iotown_url = f"{url_parsed.scheme}://{url_parsed.hostname}" + (f":{url_parsed.port}" if url_parsed.port is not None else "")
    iotown_token = url_parsed.password

    redis_url = r
    if redis_url is None:
        print(f"Redis is required for {TAG}.")
        return None

    return pyiotown.post_process.connect_common(url, pp_name, post_process, mqtt_url=mqtt_url, dry_run=dry_run)
    
def post_process(message, param=None):
    try:
        params = json.loads('{' + param + '}')
    except:
        raise Exception('param format error')

    # "id":"aggregator ID","data":{"temperature":"room1_temperature", ...},"timeout":11,"group_by":{"temperature":"avg", ...}
    # - group_by: Aggregate function per data key. The value must be one of 'avg', 'min', 'max', 'count', or 'sum' str.
    #             If it is omitted, aggregates the latest value.
    
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

    group_by = params.get('group_by')
    if group_by is not None:
        if type(group_by) is not str and type(group_by) is not dict:
            raise Exception(f"[{TAG}] The type of 'group_by' MUST be str or object.")

    r = redis.from_url(redis_url)

    #Data MUTEX
    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}:{message['key']}"
    lock = r.set(mutex_key, 'lock', ex=timeout, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        r.close()
        return None

    mapping_key = f"PP:{TAG}:Mapping:{message['grpid']}:{id}"
    mapping = r.get(mapping_key)
    try:
        mapping = json.loads(mapping)
    except:
        mapping = {}

    for k in data.keys():
        v = message['data'].get(k)
        if v is not None:
            if mapping.get(data[k]) is None:
                mapping[data[k]] = [ v ]
            else:
                mapping[data[k]].append(v)

    #Report MUTEX
    report_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{id}"
    lock = r.set(report_key, 'lock', ex=timeout, nx=True)

    #Report on lock acquisition
    if lock == True:
        aggregated_message = {}
        for k in mapping.keys():
            if type(group_by) is str:
                grouping_method = group_by
            else:
                grouping_method = group_by.get(k)
            
            print(f"[{TAG}] values:{mapping[k]}, group_by:{grouping_method}")
            if grouping_method == 'avg':
                try:
                    aggregated_message[k] = sum(mapping[k]) / len(mapping[k])
                except:
                    aggregated_message[k] = f"Error sum({mapping[k]}) / len({mapping[k]})"
            elif grouping_method == 'min':
                try:
                    aggregated_message[k] = min(mapping[k])
                except:
                    aggregated_message[k] = f"Error min({mapping[k]})"
            elif grouping_method == 'max':
                try:
                    aggregated_message[k] = max(mapping[k])
                except:
                    aggregated_message[k] = f"Error max({mapping[k]})"
            elif grouping_method == 'count':
                try:
                    aggregated_message[k] = len(mapping[k])
                except:
                    aggregated_message[k] = f"Error len({mapping[k]})"
            elif grouping_method == 'sum':
                try:
                    aggregated_message[k] = sum(mapping[k])
                except:
                    aggregated_message[k] = f"Error sum({mapping[k]})"
            else:
                try:
                    aggregated_message[k] = mapping[k][-1]
                except:
                    aggregated_message[k] = f"Error {mapping[k]}[-1]"

        print(f"[{TAG}] report {aggregated_message}")

        if pyiotown.post.data(iotown_url, iotown_token,
                              id, aggregated_message, group_id=message['grpid'],
                              verify=False) == False:
            r.close()
            raise Exception(f"[{TAG}] post data error")
        r.delete(mapping_key)
    else:
        r.set(mapping_key, json.dumps(mapping), ex=timeout)

    r.delete(mutex_key)
    r.close()
    return message
