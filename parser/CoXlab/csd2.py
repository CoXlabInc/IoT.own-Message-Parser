import base64
from datetime import datetime, timedelta
import pyiotown.post_process
import pyiotown.get
import pyiotown.delete
import redis.asyncio as redis
from urllib.parse import urlparse
import json
import struct
import asyncio
import threading

TAG = 'CSD2'

def init(url, pp_name, mqtt_url, redis_url, dry_run=False):
    global iotown_url, iotown_token
    
    url_parsed = urlparse(url)
    iotown_url = f"{url_parsed.scheme}://{url_parsed.hostname}" + (f":{url_parsed.port}" if url_parsed.port is not None else "")
    iotown_token = url_parsed.password
    
    if redis_url is None:
        print(f"Redis is required for {TAG}.")
        return None
    pool = redis.ConnectionPool.from_url(redis_url)

    global r
    r = redis.Redis.from_pool(pool)

    global event_loop
    event_loop = asyncio.new_event_loop()

    def event_loop_thread():
        event_loop.run_forever()
    threading.Thread(target=event_loop_thread, daemon=True).start()

    return pyiotown.post_process.connect_common(url, pp_name, post_process, mqtt_url, dry_run=dry_run)
    
async def async_post_process(message, param):
    raw = base64.b64decode(message['meta']['raw'])

    #MUTEX
    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}:{message['key']}"
    lock = await r.set(mutex_key, 'lock', ex=30, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        return None

    epoch = int.from_bytes(raw[0:5], 'little', signed=False)
    raw = raw[5:]
    message['data']['sense_time'] = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'

    prev_data_id = None
    result = await pyiotown.get.async_storage(iotown_url, iotown_token,
                                              message['nid'],
                                              group_id=message['grpid'],
                                              count=1,
                                              verify=False)
    if result[0] == True and len(result[1]['data']) > 0:
        value = result[1]['data'][0]['value']
        if value.get('sense_time') == message['data']['sense_time']:
            if raw[0] == 0xFF: # fragment
                prev_raw = base64.b64decode(value['raw'])
                next_raw = raw[1:]
                if prev_raw[-len(next_raw):] == next_raw:
                    print(f"[{TAG}] discard duplicate (last block)")
                    return None
                else:
                    prev_data_id = result[1]['data'][0]['_id']
                    raw = prev_raw + next_raw
                    message['meta']['raw'] = base64.b64encode(raw).decode('ascii')
                    raw = raw[5:]
            else:
                print(f"[{TAG}] discard duplicated ({message['data']['sense_time']})")
                return None

    print(f"[{TAG}] raw:{raw}")

    req_index = 0

    try:
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

                print(f"[{TAG}] req:{message['data'][req]}")
                
                if raw[6] == 0xFF:
                    message['data'][resp + "_time"] = -1
                    message['data'][resp] = None
                else:
                    message['data'][resp + "_time"] = epoch + raw[6]
                    v = ''
                    for x in raw[8:8+raw[7]]:
                        v += f"{x:02X}"
                    message['data'][resp] = v
                
                print(f"[{TAG}] resp:{message['data'][resp]}")
                
                raw = raw[8+raw[7]:]
            elif type == 2:
                # Analog
                message['data'][req] = 'analog'

                ch = raw[1]
                count = raw[2]
                message['data'][req] += f",{ch},{count}"

                print(f"[{TAG}] req:{message['data'][req]}")

                raw = raw[3:]
                for x in range(count):
                    message['data'][f"{req}_a{ch}_time"] = epoch + raw[0]
                    v = struct.unpack('<f', raw[1:5])[0]
                    message['data'][f"{req}_a{ch}"] = v
                    print(f"[{TAG}] resp:{v}")

                    raw = raw[5:]
                    ch += 1

                
            elif type == 3 or type == 4:
                # SLIP over 232 or 485
                message['data'][req] = 'slip' + ('232' if type == 3 else '485') + ','

                length = raw[1]
                raw = raw[2:]
            
                for x in raw[:length]:
                    message['data'][req] += f"{x:02X}"

                print(f"[{TAG}] req:{message['data'][req]}")

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

                print(f"[{TAG}] resp:{message['data'][resp]}")
            else:
                # Unknown type
                message['data'][req] = None
                break
            req_index += 1
    except:
        print(f"[{TAG}] maybe truncated")
        pass
    await r.delete(mutex_key)

    if prev_data_id is not None:
        result = await pyiotown.delete.async_data(iotown_url,
                                                  iotown_token,
                                                  _id=prev_data_id,
                                                  group_id=message['grpid'],
                                                  verify=False)
        #print(f"[{TAG}] remove id({prev_data_id}): {result}")

    return message

def post_process(message, param=None):
    return asyncio.run_coroutine_threadsafe(async_post_process(message, param), event_loop)
