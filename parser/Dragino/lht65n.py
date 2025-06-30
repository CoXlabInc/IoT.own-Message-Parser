import base64
from datetime import datetime, timedelta
import json
import pyiotown.post_process
import pyiotown.get
import pyiotown.delete
import pyiotown.post
import redis
from urllib.parse import urlparse
import math
import argparse

TAG = 'LHT65N'

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
    r = redis.from_url(redis_url)

    raw = base64.b64decode(message['meta']['raw'])

    fcnt = message["meta"].get("fCnt")

    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}:{fcnt}"
    
    lock = r.set(mutex_key, 'lock', ex=30, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        r.close()
        return None

    if message['meta']['fPort'] == 2:
        bat = int.from_bytes(raw[0:2], 'big', signed=False)
        message['data']['battery_mV'] = bat & 0x3FFF

        message['data']['temperature_builtin'] = int.from_bytes(raw[2:4], 'big', signed=True) / 100
        message['data']['humidity_builtin'] = int.from_bytes(raw[4:6], 'big', signed=False) / 10

        ext = raw[6]
        if ext == 0x01:
            val = int.from_bytes(raw[7:9], 'big', signed=False)
            if val & 0x8000 == 1:
                val = val - 65536
            message['data']['temperature_ext'] = val / 100
        r.close()
        return message
    else:
        r.close()
        return None

if __name__ == '__main__':
    app_desc = "IOTOWN Post Process to Parse Messages from Various Sensors"

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

    init(url, 'Dragino LHT65N', mqtt_url, args.redis_url, dry_run=dry_run).loop_forever()
