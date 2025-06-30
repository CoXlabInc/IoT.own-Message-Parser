import base64
from datetime import datetime, timedelta
from dateutil.parser import isoparse
import pyiotown.post_process
import redis
from urllib.parse import urlparse
import json
import argparse

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
    # - id: Aggregator ID. If it is omitted, the aggregated data will be posted as the device's.
    # - group_by: Aggregate function per data key. The value must be one of 'avg', 'min', 'max', 'count', or 'sum' str.
    #             If it is omitted, aggregates the latest value.
    
    id = params.get('id')
    if id is not None and type(id) is not str:
        raise Exception(f"[{TAG}] The type of 'id' MUST be str.")

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

    mapping_key = f"PP:{TAG}:Mapping:{message['grpid']}:"
    if id is not None:
        mapping_key += id
    else:
        mapping_key += message['nid']

    mapping = r.get(mapping_key)
    try:
        mapping = json.loads(mapping)
    except:
        mapping = {}

    valid_values = {}
    for k in data.keys():
        v = message['data'].get(k)
        if v is None:
            continue
        
        try:
            t = isoparse(message['data'].get('sense_time')).timestamp()
        except:
            t = isoparse(message['key'].split(':', maxsplit=1)[1]).timestamp()
        tv = {
            't': t,
            'v': v
        }
        if mapping.get(data[k]) is None:
            mapping[data[k]] = [ tv ]
        else:
            mapping[data[k]].append(tv)

        only_valids = []
        for tv in mapping[data[k]]:
            if tv['t'] > t - timeout:
                only_valids.append(tv)
                if valid_values.get(k) is None:
                    valid_values[k] = [ tv['v'] ]
                else:
                    valid_values[k].append(tv['v'])
        mapping[data[k]] = only_valids

    #Report MUTEX
    if id is not None:
        report_key = f"PP:{TAG}:Report:{message['grpid']}:{id}"

        lock = r.set(report_key, 'lock', ex=timeout, nx=True)

        #Report on lock acquisition
        if lock == True:
            aggregated_message = {}
            for k in valid_values.keys():
                if type(group_by) is str:
                    grouping_method = group_by
                else:
                    grouping_method = group_by.get(k)
            
                print(f"[{TAG}] values:{valid_values[k]}, group_by:{grouping_method}")
                if grouping_method == 'avg':
                    try:
                        aggregated_message[data[k]] = sum(valid_values[k]) / len(valid_values[k])
                    except:
                        aggregated_message[data[k]] = f"Error sum({valid_values[k]}) / len({valid_values[k]})"
                elif grouping_method == 'min':
                    try:
                        aggregated_message[data[k]] = min(valid_values[k])
                    except:
                        aggregated_message[data[k]] = f"Error min({valid_values[k]})"
                elif grouping_method == 'max':
                    try:
                        aggregated_message[data[k]] = max(valid_values[k])
                    except:
                        aggregated_message[data[k]] = f"Error max({valid_values[k]})"
                elif grouping_method == 'count':
                    try:
                        aggregated_message[data[k]] = len(valid_values[k])
                    except:
                        aggregated_message[data[k]] = f"Error len({valid_values[k]})"
                elif grouping_method == 'sum':
                    try:
                        aggregated_message[data[k]] = sum(valid_values[k])
                    except:
                        aggregated_message[data[k]] = f"Error sum({valid_values[k]})"
                else:
                    try:
                        aggregated_message[data[k]] = valid_values[k][-1]
                    except:
                        aggregated_message[data[k]] = f"Error {valid_values[k]}[-1]"

            print(f"[{TAG}] report {aggregated_message}")

            result = pyiotown.post.data(iotown_url, iotown_token,
                                        id, aggregated_message, group_id=message['grpid'],
                                        verify=False)
            if result[0] == False:
                r.close()
                raise Exception(f"[{TAG}] post data error")
            r.delete(mapping_key)
        else:
            r.set(mapping_key, json.dumps(mapping), ex=timeout)
    else:
        r.set(mapping_key, json.dumps(mapping), ex=timeout)

        for k in valid_values.keys():
            if type(group_by) is str:
                grouping_method = group_by
            else:
                grouping_method = group_by.get(k)

            if grouping_method == 'avg':
                try:
                    message['data'][data[k]] = sum(valid_values[k]) / len(valid_values[k])
                except:
                    message['data'][data[k]] = f"Error sum({valid_values[k]}) / len({valid_values[k]})"
            elif grouping_method == 'min':
                try:
                    message['data'][data[k]] = min(valid_values[k])
                except:
                    message['data'][data[k]] = f"Error min({valid_values[k]})"
            elif grouping_method == 'max':
                try:
                    message['data'][data[k]] = max(valid_values[k])
                except:
                    message['data'][data[k]] = f"Error max({valid_values[k]})"
            elif grouping_method == 'count':
                try:
                    message['data'][data[k]] = len(valid_values[k])
                except:
                    message['data'][data[k]] = f"Error len({valid_values[k]})"
            elif grouping_method == 'sum':
                try:
                    message['data'][data[k]] = sum(valid_values[k])
                except:
                    message['data'][data[k]] = f"Error sum({valid_values[k]})"
            else:
                try:
                    message['data'][data[k]] = valid_values[k][-1]
                except:
                    message['data'][data[k]] = f"Error {valid_values[k]}[-1]"

            print(f"[{TAG}] {k} values:{valid_values[k]}, group_by:{grouping_method}, to {data[k]}:{message['data'][data[k]]}")

    r.delete(mutex_key)
    r.close()
    return message

if __name__ == '__main__':
    app_desc = "IOTOWN Post Process to Aggregate values"

    parser = argparse.ArgumentParser(description=app_desc)
    parser.add_argument("--url", help="IOTOWN URL", required=True)
    parser.add_argument("--mqtt_url", help="MQTT broker URL for IoT.own", required=False, default=None)
    parser.add_argument("--redis_url", help="Redis URL for context storage", required=False, default=None)
    parser.add_argument('--dry', help=" Do not upload data to the server", type=int, default=0)
    args = parser.parse_args()

    print(app_desc)
    url = args.url.strip()
    url_parsed = urlparse(url)

    print(f"URL: {url_parsed.scheme}://{url_parsed.hostname}" + (f":{url_parsed.port}" if url_parsed.port is not None else ""))

    mqtt_url = args.mqtt_url.strip() if args.mqtt_url is not None else None

    if args.dry == 1:
        dry_run = True
        print("DRY RUNNING!")
    else:
        dry_run = False

    init(url, 'Aggregator', mqtt_url, args.redis_url, dry_run=dry_run).loop_forever()
