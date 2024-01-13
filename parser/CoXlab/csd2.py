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
    raw = raw[5:]
    message['data']['sense_time'] = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'

    prev_data_id = None
    result = pyiotown.get.storage(iotown_url, iotown_token,
                                  message['nid'],
                                  group_id=message['grpid'],
                                  count=1,
                                  verify=False)
    try:
        if result['data'][0]['value']['sense_time'] == message['data']['sense_time']:
            prev_data_id = result['data'][0]['_id']
            print(f"[{TAG}] prev: {result}")

            prev_raw = base64.b64decode(result['data'][0]['value']['raw'])[5:]
            print(f"[{TAG}] prev:{prev_raw} + current:{raw}")
            
            raw = prev_raw + raw
            print(f"[{TAG}] raw:{raw}")
    except Exception as e:
        raise e

    req_index = 0
    
    while len(raw) > 0:
        type = raw[0]

        req = f"req{req_index}"
        resp = f"resp{req_index}"
        
        if type == 0 or type == 1:
            # Modbus read holding or input registers
            message['data'][req] = 'modbusrh' if type == 0 else 'modbusri'

            slave = raw[1]
            start_addr = int.from_bytes(raw[2:4], 'little', signed=False)
            count = int.from_bytes(raw[4:6], 'little', signed=False)
            message['data'][req] += f",{slave},{start_addr},{count}"

            if raw[6] == 0xFF:
                message['data'][resp + "_time"] = -1
                message['data'][resp] = None
            else:
                message['data'][resp + "_time"] = epoch + raw[6]
                v = ''
                for x in raw[8:8+raw[7]]:
                    v += f"{x:02X}"
                message['data'][resp] = v
                
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
        elif type == 3 or type == 4:
            # SLIP over 232 or 485
            message['data'][req] = 'slip' + ('232' if type == 3 else '485') + ','

            length = raw[1]
            raw = raw[2:]
            
            for x in raw[:length]:
                message['data'][req] += f"{x:02X}"
            raw= raw[length:]

            if raw[0] == 0xFF:
                message['data'][resp + "_time"] = -1
                message['data'][resp] = None
                raw = raw[1:]
            else:
                message['data'][resp + "_time"] = epoch + raw[0]
                raw = raw[1:]

                length = raw[0]
                raw = raw[1:]

                if length == 0:
                    v = None
                else:
                    v = ''
                    for x in raw[:length]:
                        v += f"{x:02X}"
                    
                message['data'][resp] = v
                raw = raw[length:]
        else:
            # Unknown type
            message['data'][req] = None
            break
        req_index += 1

    r.delete(mutex_key)

    if prev_data_id is not None:
        result = pyiotown.delete.data(iotown_url,
                                      iotown_token,
                                      _id=prev_data_id,
                                      group_id=message['grpid'],
                                      verify=False)
        print(f"[{TAG}] remove id({prev_data_id}): {result}")

    return message
