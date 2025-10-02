import base64
import datetime
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
import argparse

TAG = 'MagicRF'

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

def parse(data):
    try:
        bytes_data = bytes.fromhex(data)
    except (ValueError, TypeError):
        raise Exception("Invalid hexadecimal string")

    messages = []
    start = 0
    while start < len(bytes_data):
        start_idx = bytes_data.find(b'\xBB', start)
        if start_idx == -1:
            break

        end_idx = bytes_data.find(b'\x7E', start_idx)
        if end_idx == -1:
            break
        
        full_message = bytes_data[start_idx : end_idx + 1]

        if len(full_message) < 2 or full_message[1] not in [0x01, 0x02, 0xFF]:
            start = start_idx + 1
            continue

        message_content = full_message[1:-1]
        messages.append(message_content)
        
        start = end_idx + 1

    if not messages:
        raise Exception("No valid messages found")

    aggregated_result = {}
    all_tags = {}

    for msg in messages:
        if len(msg) < 4:
            continue

        frame_type = msg[0]
        command_code = msg[1]
        data_length = struct.unpack('>H', msg[2:4])[0]
        
        if data_length != len(msg) - 5:
            continue

        data_payload = msg[4:-1]

        received_checksum = msg[-1]
        calculated_checksum = sum(msg[:-1]) & 0xFF

        if received_checksum != calculated_checksum:
            continue

        if frame_type == 0x01: # response frame
            if command_code == 0x03: # module information
                value_bytes = data_payload[1:]
                try:
                    value_str = value_bytes.decode('utf-8').strip()
                except UnicodeDecodeError:
                    value_str = value_bytes.hex()
                
                if data_payload[0] == 0x00:
                    aggregated_result['hardware_version'] = value_str
                elif data_payload[0] == 0x01:
                    aggregated_result['software_version'] = value_str
                elif data_payload[0] == 0x02:
                    aggregated_result['manufacturer'] = value_str
            elif command_code == 0x07: # module information

        elif frame_type == 0x02: # notice frame
            if command_code == 0x22: # inventory
                if data_length < 15: # RSSI(1) + PC(2) + EPC(12) = 15
                    continue

                unsigned_rssi = data_payload[0]
                signed_rssi = unsigned_rssi - 256 if unsigned_rssi > 127 else unsigned_rssi
                
                pc = data_payload[1:3].hex()
                epc = data_payload[3:15].hex()

                all_tags[epc] = {
                    'pc': pc,
                    'rssi': signed_rssi,
                }

    if all_tags:
        aggregated_result['tags'] = all_tags
    
    return aggregated_result

async def async_post_process(message, param):
    try:
        keys = json.loads('[' + param + ']')
    except Exception as e:
        raise Exception('param format error') from e
    
    r = redis.Redis(connection_pool=pool)

    #MUTEX
    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}:{message['key']}"
    lock = await r.set(mutex_key, 'lock', ex=30, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        await r.aclose()
        return None

    for k in keys:
        data = message['data'].get(k)
        if data is not None:
            try:
                parsed_data = parse(data)
                # print(f"[{TAG}] Aggregated parsed data: {parsed_data}")
                for parsed_key, parsed_value in parsed_data.items():
                    message['data'][f"{k}_{parsed_key}"] = parsed_value
            except Exception as e:
                print(f"[{TAG}] Error parsing data: {e}")

    await r.delete(mutex_key)
    await r.aclose()
    
    return message

def post_process_up(message, param=None):
    return asyncio.run_coroutine_threadsafe(async_post_process(message, param), event_loop)

def post_process_down(message):
    print(f"[{TAG}] gotcha {message}")


if __name__ == '__main__':
    app_desc = f"IOTOWN Post Process for {TAG} data"

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

    init(url, TAG, mqtt_url, args.redis_url, dry_run=dry_run).loop_forever()
