import os
import sys
import base64
import json
import pyiotown.get
import pyiotown.post_process
import subprocess
import redis.asyncio as redis
from urllib.parse import urlparse
import asyncio
import threading

TAG = 'PLN'

ps = subprocess.Popen(['node', os.path.join(os.path.dirname(__file__), 'glue.js')], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def init(url, pp_name, mqtt_url, redis_url, dry_run=False):
    global iotown_url, iotown_token
    
    url_parsed = urlparse(url)
    iotown_url = f"{url_parsed.scheme}://{url_parsed.hostname}" + (f":{url_parsed.port}" if url_parsed.port is not None else "")
    iotown_token = url_parsed.password
    
    if redis_url is None:
        print(f"Redis is required for {TAG}.")
        return None

    global pool
    pool = redis.ConnectionPool.from_url(redis_url)

    global event_loop
    event_loop = asyncio.new_event_loop()

    def event_loop_thread():
        event_loop.run_forever()
    threading.Thread(target=event_loop_thread, daemon=True).start()
    
    return pyiotown.post_process.connect_common(url, pp_name, post_process, mqtt_url=mqtt_url, dry_run=dry_run)

def append_error(message, error):
    if error is None or len(error) == 0:
        return
    
    if message['data'].get('errors') is None:
        message['data']['errors'] = ''

    if len(message['data']['errors']) > 0:
        message['data']['errors'] += '\n'

    message['data']['errors'] += error
    
async def async_post_process(message):
    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}:{message['key']}"

    #r = redis.Redis.from_pool(pool)
    r = redis.Redis(connection_pool=pool)
    
    lock = await r.set(mutex_key, 'lock', ex=10, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        await r.aclose()
        return None

    raw = base64.b64decode(message['meta']['raw'])
    if raw[0] >= 0 and raw[0] <= 15:
        # Filter out duplicate
        seq_key = f"PP:{TAG}:SEQ:{message['grpid']}:{message['nid']}:{message['key']}"
        seq_last = await r.get(seq_key)

        if seq_last is None:
            # check from DB
            result = await pyiotown.get.async_storage(iotown_url, iotown_token,
                                                      message['nid'],
                                                      group_id=message['grpid'],
                                                      count=1,
                                                      verify=False)
            if result[0] == True and len(result[1]['data']) > 0:
                seq_last = result[1]['data'][0]['value'].get('seq')
        else:
            seq_last = int(seq_last)

        await r.set(seq_key, raw[0], ex=3600*24)
        if raw[0] != 0 and seq_last == raw[0]:
            await r.delete(mutex_key)
            await r.aclose()
            return None
        
        message['data']['seq'] = raw[0]

    input_data = { "data": message['meta']['raw'],
                   "node": message['device'],
                   "gateway": message['gateway'] }

    print(f"Input:{input_data}")
    ps.stdin.write(json.dumps(input_data).encode('ascii'))
    ps.stdin.flush()
    
    result = ps.stdout.readline()
    print(f"Output:{result.decode('utf-8')}")#
    print(f"Error:{ps.stderr.readline().decode('utf-8')}")
    
    result_dict = json.loads(result)
    for key in result_dict.keys():
    	message['data'][key] = result_dict[key]

    for key in message['data']:
        if key.startswith('uwb'):
            anchors = message['data'][key].copy().keys()
            for anchor in anchors:
                async def get_anchor_desc(anchor_id):
                    result = await pyiotown.get.async_node(iotown_url, iotown_token,
                                                           anchor_id,
                                                           group_id=message['grpid'],
                                                           verify=False)
                    if result[0] == True:
                        try:
                            return json.loads('{' + result[1]['node_desc'] + '}')
                        except Exception as e:
                            print(f"[PLN] exception: {e}", file=sys.stderr)
                            await r.aclose()
                            return None
                    else:
                        print(f"[PLN] error: {result[1]}", file=sys.stderr)
                        await r.aclose()
                        return None

                anchor_id = f'LW140C5BFFFF{anchor.upper()}'
                anchor_desc = await get_anchor_desc(anchor_id)
                if anchor_desc is None:
                    print(f"[PLN] {anchor_id} is not found. (nid:{message['nid']})")
                    anchor_id = f'LW140C5BEFFF{anchor.upper()}'
                    anchor_desc = await get_anchor_desc(anchor_id)

                if anchor_desc is None:
                    print(f"[PLN] {anchor_id} is not found. (nid:{message['nid']})")
                    append_error(message, f"'{anchor}' is not found.")
                    del message['data'][key][anchor]
                elif anchor_desc.get('installed') == False:
                    print(f"[PLN] {anchor_id} is not installed. (nid:{message['nid']})")
                    append_error(message, f"'{anchor_id}' is not installed.")
                    del message['data'][key][anchor]
                elif anchor_desc.get('coord') is None:
                    print(f"[PLN] {anchor_id} coordinate is not specified. (nid:{message['nid']})")
                    append_error(message, f"'{anchor_id}' coordinate is not specified.")
                    del message['data'][key][anchor]
                else:
                    coord = anchor_desc.get('xy_coord')
                    message['data'][key][anchor_id] = {
                        'coord': anchor_desc.get('coord'),
                        'x': float(coord[0]),
                        'y': float(coord[1]),
                        'floor': anchor_desc.get('floor'),
                        'dist': message['data'][key][anchor].get('dist')
                    }
                    del message['data'][key][anchor]
    await r.delete(mutex_key)
    await r.aclose()
    return message

def post_process(message, param=None):
    if message.get('meta') is None or message['meta'].get('raw') is None:
        print(f'[PLN] A message have no meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]}')
        return message

    return asyncio.run_coroutine_threadsafe(async_post_process(message), event_loop)

if __name__ == '__main__':
    raw = 'BcwEAgAAZM0VAgACNAADFQIAAjQAAxYCAAI0AAMX'

    test_input = '{"data":"' + raw + '","node":{},"gateway":{}}'
    ps.stdin.write(test_input.encode('ascii'))
    ps.stdin.flush()
    out = ps.stdout.readline()
    print(out)
