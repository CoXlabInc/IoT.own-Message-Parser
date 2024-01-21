import os
import sys
import base64
import json
import pyiotown.get
import pyiotown.post_process
import subprocess
import redis
from urllib.parse import urlparse

TAG = 'PLN'

ps = subprocess.Popen(['node', os.path.join(os.path.dirname(__file__), 'glue.js')], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

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
    if message.get('meta') is None or message['meta'].get('raw') is None:
        print(f'[PLN] A message have no meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]}')
        return message

    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}:{message['key']}"
    lock = r.set(mutex_key, 'lock', ex=10, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        return None

    raw = base64.b64decode(message['meta']['raw'])
    if raw[0] >= 0 and raw[0] <= 15:
        # Filter out duplicate
        seq_key = f"PP:{TAG}:SEQ:{message['grpid']}:{message['nid']}:{message['key']}"
        seq_last = r.get(seq_key)

        if seq_last is None:
            # check from DB
            result = pyiotown.get.storage(iotown_url, iotown_token,
                                          message['nid'],
                                          group_id=message['grpid'],
                                          count=1,
                                          verify=False)
            try:
                seq_last = result['data'][0]['value']['seq']
            except:
                pass
        else:
            seq_last = int(seq_last)

        r.set(seq_key, raw[0], ex=3600*24)
        if raw[0] != 0 and seq_last == raw[0]:
            r.delete(mutex_key)
            return None
        
        message['data']['seq'] = raw[0]

    input_data = { "data": message['meta']['raw'],
                   "node": message['device'],
                   "gateway": message['gateway'] }

    ps.stdin.write(json.dumps(input_data).encode('ascii'))
    ps.stdin.flush()
    
    result = ps.stdout.readline()
    # print(result)
    
    result_dict = json.loads(result)
    for key in result_dict.keys():
    	message['data'][key] = result_dict[key]

    for key in message['data']:
        if key.startswith('scan_') and message['data'][key].get('method') == 'UWB':
            for anchor in message['data'][key].keys():
                if anchor == 'method':
                    continue
                result = pyiotown.get.node(iotown_url, iotown_token,
                                           f"LW112211221133{anchor}",
                                           group_id=message['grpid'],
                                           verify=False)
                try:
                    pos = result['node']['node_desc'].split(',')
                    x = float(pos[0])
                    y = float(pos[1])
                    z = float(pos[2])
                    message['data'][key][anchor]['x'] = x
                    message['data'][key][anchor]['y'] = y
                    message['data'][key][anchor]['z'] = z
                except Exception as e:
                    print(e, file=sys.stderr)
                    pass
                    
    r.delete(mutex_key)
    return message

if __name__ == '__main__':
    raw = 'BcwEAgAAZM0VAgACNAADFQIAAjQAAxYCAAI0AAMX'

    test_input = '{"data":"' + raw + '","node":{},"gateway":{}}'
    ps.stdin.write(test_input.encode('ascii'))
    ps.stdin.flush()
    out = ps.stdout.readline()
    print(out)
