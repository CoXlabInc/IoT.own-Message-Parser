import base64
from datetime import datetime, timedelta
import pyiotown.post_process
import redis
from urllib.parse import urlparse
import json

TAG = 'CSD4'

def init(url, pp_name, mqtt_url, r, dry_run=False):
    global iotown_url, iotown_token
    
    url_parsed = urlparse(url)
    iotown_url = f"{url_parsed.scheme}://{url_parsed.hostname}" + (f":{url_parsed.port}" if url_parsed.port is not None else "")
    iotown_token = url_parsed.password

    redis_url = r
    if redis_url is None:
        print(f"Redis is required for {TAG}.")
        return None

    return pyiotown.post_process.connect_common(url, pp_name, post_process, mqtt_url, dry_run=dry_run)
    
def post_process(message, param=None):
    raw = base64.b64decode(message['meta']['raw'])

    #MUTEX
    fcnt = message["meta"].get("fCnt")

    r = redis.from_url(redis_url)

    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}:{fcnt}"
    
    lock = r.set(mutex_key, 'lock', ex=30, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        r.close()
        return None

    epoch = int.from_bytes(raw[0:5], 'little', signed=False)
    message['data']['sense_time'] = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'
    message['data']['sys_mv'] = int.from_bytes(raw[5:7], 'little', signed=False)
    message['data']['period'] = int.from_bytes(raw[7:9], 'little', signed=False)

    message['data']['temperature'] = int.from_bytes(raw[9:11], 'little', signed=True) / 100
    message['data']['humidity'] = int.from_bytes(raw[11:13], 'little', signed=False) / 100

    raw = raw[13:]
    
    if param is not None:
        try:
            params = json.loads('{' + param + '}')
        except Exception as e:
            params = None
        print(f"[{TAG}] params: {params} <= {param}")
        
        if params is not None:
            v_ref = params.get('v_ref')
    else:
        params = None
        v_ref = None

    i = 0
    mux = 1
    ch = 1
    while i + 3 <= len(raw):
        val = int.from_bytes(raw[i:i+3], 'little', signed=True) / 0x800000

        message['data'][f'CH{mux}_{ch}'] = val
        if v_ref is not None:
            val = val * v_ref
            message['data'][f'CH{mux}_{ch}_V'] = val
        
        ch += 1
        if ch > 4:
            ch = 1
            mux += 1
        i += 3

    r.close()
    return message
