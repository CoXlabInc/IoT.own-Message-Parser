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

TAG = 'RAK10701'

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
    if message['meta'].get('raw') is None:
        return message
    
    raw = base64.b64decode(message['meta']['raw'])

    fcnt = message["meta"].get("fCnt")

    r = redis.from_url(redis_url)
    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}:{fcnt}"
    
    lock = r.set(mutex_key, 'lock', ex=30, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        r.close()
        return None

    if message['meta']['fPort'] == 1:
        lonSign = -1 if (raw[0] >> 7) & 0x01 else 1
        lonSign = -1 if (raw[0] >> 7) & 0x01 else 1
        latSign = -1 if (raw[0] >> 6) & 0x01 else 1
        encLat = ((raw[0] & 0x3f) << 17) + (raw[1] << 9) + (raw[2] << 1) + (raw[3] >> 7)
        encLon = ((raw[3] & 0x7f) << 16) + (raw[4] << 8) + raw[5]
        hdop = raw[8] / 10
        sats = raw[9]
        maxHdop = 2
        minSats = 5

        if hdop >= maxHdop or sats < minSats:
            message['data']['error'] = f"Need more GPS precision (hdop must be < {maxHdop} & sats must be >= {minSats}) current hdop: {hdop} & sats: {sats}"
            
        message['data']['gnss'] = [
            latSign * (encLat * 108 + 53) / 10000000,  #latitude
            lonSign * (encLon * 215 + 107) / 10000000, #longitude
            ((raw[6] << 8) + raw[7]) - 1000            #altitude
        ]
        message['data']['accuracy'] = (hdop * 5 + 5) / 10
        message['data']['hdop'] = hdop
        message['data']['sats'] = sats
        message['data']['location'] = f"({message['data']['gnss'][0]},{message['data']['gnss'][1]})"

        message['data']['minRSSI'] = 0
        message['data']['maxRSSI'] = 0
        message['data']['minSNR'] = 0
        message['data']['maxSNR'] = 0
        message['data']['minDistance'] = 0
        message['data']['maxDistance'] = 0

        for gw in message['meta']['gateway']:
            
            if gw['rssi'] < message['data']['minRSSI'] or message['data']['minRSSI'] == 0:
                message['data']['minRSSI'] = gw['rssi']

            if gw['rssi'] > message['data']['maxRSSI'] or message['data']['maxRSSI'] == 0:
                message['data']['maxRSSI'] = gw['rssi']
            
            if gw['snr'] < message['data']['minSNR'] or message['data']['minSNR'] == 0:
                message['data']['minSNR'] = gw['snr']

            if gw['snr'] > message['data']['maxSNR'] or message['data']['maxSNR'] == 0:
                message['data']['maxSNR'] = gw['snr']

            if gw['location']['latitude'] != 0 or gw['location']['longitude'] != 0 or gw['location']['altitude'] != 0:
                # Calculate distance
                new_distance = distance(gw['location']['latitude'], gw['location']['longitude'], message['data']['gnss'][0], message['data']['gnss'][1])
                
                if new_distance < message['data']['minDistance'] or message['data']['minDistance'] == 0:
                    message['data']['minDistance'] = new_distance * 1000

                if new_distance > message['data']['maxDistance'] or message['data']['maxDistance'] == 0:
                    message['data']['maxDistance'] = new_distance * 1000


        message['data']['maxMod'] = message['data']['maxDistance'] // 250
        message['data']['minMod'] = message['data']['minDistance'] // 250
        message['data']['maxDistance'] = message['data']['maxMod'] * 250
        message['data']['minDistance'] = message['data']['minMod'] * 250

        if message['data']['maxDistance'] <= 1:
            message['data']['maxDistance'] = 250

        if message['data']['minDistance'] <= 1:
            message['data']['minDistance'] = 250

        buf = bytearray(6)
        buf[0] = 1
        buf[1] = int(message['data']['minRSSI'] + 200)
        buf[2] = int(message['data']['maxRSSI'] + 200)
        if message['data']['minMod'] == 0:
            buf[3] = 1
        elif message['data']['minMod'] > 255:
            buf[3] = 255
        else:
            buf[3] = int(message['data']['minMod'])

        if message['data']['maxMod'] == 0:
            buf[4] = 1
        elif message['data']['maxMod'] > 255:
            buf[4] = 255
        else:
            buf[4] = int(message['data']['maxMod'])
            
        buf[5] = len(message['meta']['gateway'])
        pyiotown.post.command(iotown_url, iotown_token,
                              message['nid'],
                              bytes(buf),
                              lorawan={ 'f_port': 2 },
                              group_id=message['grpid'],
                              verify=False)
        r.close()
        return message
    else:
        r.close()
        return None

def distance(lat1, lon1, lat2, lon2):
    if lat1 == lat2 and lon1 == lon2:
        return 0

    radlat1 = math.pi * lat1 / 180
    radlat2 = math.pi * lat2 / 180
    theta = lon1 - lon2
    radtheta = math.pi * theta / 180
    dist = math.sin(radlat1) * math.sin(radlat2) + math.cos(radlat1) * math.cos(radlat2) * math.cos(radtheta)
    if dist > 1:
        dist = 1

    dist = math.acos(dist)
    dist = dist * 180 / math.pi
    dist = dist * 60 * 1.1515
    dist = dist * 1.609344
    return dist

if __name__ == '__main__':
    app_desc = "IOTOWN Post Process for RAK10701"

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

    init(url, 'RAK10701', mqtt_url, args.redis_url, dry_run=dry_run).loop_forever()
