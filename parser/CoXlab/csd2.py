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
import traceback

TAG = 'CSD2'

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

    return pyiotown.post_process.connect_common(url, pp_name, post_process_up, post_process_down, mqtt_url=mqtt_url, dry_run=dry_run)
    
async def async_post_process(message, param):
    raw = base64.b64decode(message['meta']['raw'])
    
    #r = redis.Redis.from_pool(pool)
    r = redis.Redis(connection_pool=pool)

    #MUTEX
    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}:{message['key']}"
    lock = await r.set(mutex_key, 'lock', ex=30, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        await r.aclose()
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
            if len(raw) > 0 and raw[0] == 0xFF: # fragment
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
                await r.aclose()
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

                print(f"[{TAG}] {req}:{message['data'][req]}")
                
                if raw[6] == 0xFF:
                    message['data'][resp + "_time"] = -1
                    message['data'][resp] = None
                    raw = raw[7:]
                else:
                    message['data'][resp + "_time"] = datetime.utcfromtimestamp(epoch + raw[6]).isoformat() + 'Z'
                    v = ''
                    for x in raw[8:8+raw[7]]:
                        v += f"{x:02X}"
                    message['data'][resp] = v
                    raw = raw[8+raw[7]:]
                
                print(f"[{TAG}] {resp}:{message['data'][resp]}")
                
            elif type == 2:
                # Analog
                message['data'][req] = 'analog'

                ch = raw[1]
                count = raw[2]
                message['data'][req] += f",{ch},{count}"

                print(f"[{TAG}] {req}:{message['data'][req]}")

                raw = raw[3:]
                for x in range(count):
                    message['data'][f"{resp}_a{ch}_time"] = datetime.utcfromtimestamp(epoch + raw[0]).isoformat() + 'Z'
                    v = struct.unpack('<f', raw[1:5])[0]
                    message['data'][f"{resp}_a{ch}"] = v
                    print(f"[{TAG}] {resp}:{v}")

                    raw = raw[5:]
                    ch += 1

                
            elif type in [ 3, 4, 8, 9]:
                # SLIP, raw over 232, 485
                if type == 3:
                    message['data'][req] = 'slip232,'
                elif type == 4:
                    message['data'][req] = 'slip485,'
                elif type == 8:
                    message['data'][req] = 'raw232,'
                else:
                    message['data'][req] = 'raw485,'

                length = raw[1]
                raw = raw[2:]
            
                for x in raw[:length]:
                    message['data'][req] += f"{x:02X}"

                print(f"[{TAG}] {req}:{message['data'][req]}")

                raw= raw[length:]

                if raw[0] == 0xFF:
                    message['data'][resp + "_time"] = -1
                    message['data'][resp] = None
                    raw = raw[1:]
                else:
                    message['data'][resp + "_time"] = datetime.utcfromtimestamp(epoch + raw[0]).isoformat() + 'Z'
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

                print(f"[{TAG}] {resp}:{message['data'][resp]}")
            elif type in [ 5, 6, 7 ]:
                # Digital input
                if type == 5:
                    message['data'][req] = 'digital,'
                elif type == 6:
                    message['data'][req] = 'digitalpu,'
                elif type == 7:
                    message['data'][req] = 'digitalpd,'

                ch = raw[1]
                count = raw[2]

                message['data'][req] += f"{ch},{count}"

                raw = raw[3:]

                for x in range(count):
                    message['data'][f"{resp}_d{ch}_time"] = datetime.utcfromtimestamp(epoch + raw[0]).isoformat() + 'Z'
                    message['data'][f"{resp}_d{ch}"] = raw[1]
                    raw = raw[2:]
                    ch += 1
                
            elif type in [ 10, 11, 12, 13 ]:
                # Digital output
                if type == 10:
                    message['data'][req] = 'digitalout,'
                elif type == 11:
                    message['data'][req] = 'digitaloutod,'
                elif type == 12:
                    message['data'][req] = 'digitaloutodpu,'
                elif type == 13:
                    message['data'][req] = 'digitaloutodpd,'

                ch = raw[1]
                state = raw[2]
                delay = raw[3]

                message['data'][req] += f"{ch},{state},{delay}"

                message['data'][f"{resp}_d{ch}_time"] = datetime.utcfromtimestamp(epoch + raw[4]).isoformat() + 'Z'
                message['data'][f"{resp}_d{ch}"] = raw[5]
                raw = raw[6:]
            elif type == 14:
                # I2C
                device = int.from_bytes(raw[1:3], 'little', signed=False)
                device_list = [ 'SHT' ]

                message['data'][req] = device_list[device] if device < len(device_list) else None
                if message['data'][req] == 'SHT':
                    message['data'][f"{resp}_time"] = datetime.utcfromtimestamp(epoch + raw[3]).isoformat() + 'Z'

                    length = raw[4]
                    
                    sht_types = [ 'AUTO_DETECT', 'SHT3X', 'SHT85', 'SHT3X_ALT', 'SHTC1', 'SHTC3', 'SHTW1', 'SHTW2', 'SHT4X' ]
                    message['data'][f"{resp}_type"] = sht_types[raw[5]]
                    if length == 5:
                        message['data'][f"{resp}_temperature"] = int.from_bytes(raw[6:8], 'little', signed=True) / 100
                        message['data'][f"{resp}_humidity"] = int.from_bytes(raw[8:10], 'little', signed=False) / 100
                    else:
                        message['data'][f"{resp}_temperature"] = None
                        message['data'][f"{resp}_humidity"] = None
                    raw = raw[4 + length + 1:]
                else:
                    device
            else:
                # Unknown type
                message['data'][req] = None
                break
            req_index += 1
    except Exception:
        print(f"[{TAG}] {traceback.format_exc()}")
        
    await r.delete(mutex_key)
    await r.aclose()
    
    if prev_data_id is not None:
        result = await pyiotown.delete.async_data(iotown_url,
                                                  iotown_token,
                                                  _id=prev_data_id,
                                                  group_id=message['grpid'],
                                                  verify=False)
        #print(f"[{TAG}] remove id({prev_data_id}): {result}")

    return message

def post_process_up(message, param=None):
    if message['meta']['fPort'] == 1:
        return asyncio.run_coroutine_threadsafe(async_post_process(message, param), event_loop)
    else:
        return message

def post_process_down(message):
    print(f"[{TAG}] gotcha {message}")
