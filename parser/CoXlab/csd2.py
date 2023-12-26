import base64
from datetime import datetime, timedelta
import pyiotown.post_process
import redis
from urllib.parse import urlparse
import json
import struct

TAG = 'CSD2'

def init(url, pp_name, mqtt_url, redis_url, dry_run=False):
    global iotown_url, iotown_token
    
    url_parsed = urlparse(url)
    iotown_url = f"{url_parsed.scheme}://{url_parsed.hostname}" + (f":{url_parsed.port}" if url_parsed.port is not None else "")
    iotown_token = url_parsed.password
    
    if redis_url is None:
        print(f"Redis is required for EdgeEye.")
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
    raw = base64.b64decode(message['meta']['raw'])

    #MUTEX
    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}:{message['key']}"
    lock = r.set(mutex_key, 'lock', ex=30, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        return None

    epoch = int.from_bytes(raw[0:5], 'little', signed=False)
    message['data']['sense_time'] = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'
    message['data']['commands'] = {}
    raw = raw[5:]
    req_index = 0
    
    while len(raw) > 0:
        type = raw[0]

        req = f"req{req_index}"
        if type == 0 or type == 1:
            # Modbus read holding or input registers
            message['data'][req] = 'modbusrh' if type == 0 else 'modbusri'

            slave = raw[1]
            start_addr = int.from_bytes(raw[2:4], 'little', signed=False)
            count = int.from_bytes(raw[4:6], 'little', signed=False)
            message['data'][req] += f",{slave},{start_addr},{count}"
            message['data'][req + '_time'] = epoch + raw[6]

            if raw[7] == 0:
                message['data'][f"resp{req_index}"] = None
            else:
                resp = ''
                for x in raw[8:8+raw[7]]:
                    resp += f"{x:02X}"
                message['data'][f"resp{req_index}"] = resp
                
            raw = raw[8+raw[7]:]
        elif type == 2:
            # Analog
            message['data'][req] = 'analog'

            ch = raw[1]
            count = raw[2]
            message['data'][req] += f",{ch},{count}"

            raw = raw[3:]
            for x in range(count):
                message['data'][f"{req}_a{ch}_time"] = epoch + raw[0]
                v = struct.unpack('<f', raw[1:5])[0]
                message['data'][f"{req}_a{ch}"] = v
                raw = raw[5:]
                ch += 1
        else:
            # Unknown type
            message['data'][req] = None
            break
        req_index += 1

    r.delete(mutex_key)
    return message
