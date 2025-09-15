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
import pynmea2

TAG = 'GNSS'

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

def parse_nmea(data):
    import decimal
    import pynmea2
    import datetime

    parsed = {}
    sv_list = []

    if not isinstance(data, str):
        return parsed

    last_msg_was_gsv = False
    for line in data.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            msg = pynmea2.parse(line)

            if msg.sentence_type == 'GSV':
                if not last_msg_was_gsv:
                    sv_list = []
                
                for i in range(1, 5):
                    prn = getattr(msg, f'sv_prn_num_{i}', None)
                    if prn is not None and prn != '':
                        sv_info = {
                            'prn': prn,
                            'elevation': getattr(msg, f'elevation_deg_{i}', None),
                            'azimuth': getattr(msg, f'azimuth_{i}', None),
                            'snr': getattr(msg, f'snr_{i}', None),
                        }
                        sv_list.append({k: v for k, v in sv_info.items() if v is not None and v != ''})
                
                last_msg_was_gsv = True
                continue
            else:
                last_msg_was_gsv = False

            msg_dict = {}
            if hasattr(msg, 'fields'):
                for field in msg.fields:
                    field_attr = field[1]
                    if hasattr(msg, field_attr):
                        value = getattr(msg, field_attr)
                        if value is not None and value != '':
                            msg_dict[field_attr] = value

            useful_attrs = ['latitude', 'longitude', 'altitude', 'datetime', 'is_valid', 'true_course', 'mag_course']
            for attr in useful_attrs:
                if hasattr(msg, attr):
                    value = getattr(msg, attr)
                    if value is not None and value != '':
                        msg_dict[attr] = value
            
            parsed.update(msg_dict)

        except (pynmea2.ParseError, AttributeError, IndexError, ValueError):
            last_msg_was_gsv = False
            pass

    # --- Post-processing after all lines are read ---

    if sv_list:
        sv_map = {str(sv['prn']): sv for sv in sv_list}
        parsed['sv'] = list(sv_map.values())

    # --- Clean up, coalesce, and structure fields ---

    # Coalesce speed-in-knots fields into 'spd_over_grnd_kts'
    if 'spd_over_grnd' in parsed:  # From RMC (knots)
        if 'spd_over_grnd_kts' not in parsed:
            parsed['spd_over_grnd_kts'] = parsed['spd_over_grnd']
        parsed.pop('spd_over_grnd')

    if 'faa_mode' in parsed:
        if 'mode_indicator' not in parsed:
            parsed['mode_indicator'] = parsed['faa_mode']
        parsed.pop('faa_mode')

    if 'longitude' in parsed and 'latitude' in parsed:
        coords = [parsed['longitude'], parsed['latitude']]
        if 'altitude' in parsed:
            coords.append(parsed['altitude'])
        parsed['gnss'] = coords
        
        for key in ['latitude', 'longitude', 'altitude', 'lat', 'lon', 'lat_dir', 'lon_dir']:
            parsed.pop(key, None)

    if 'datetime' in parsed:
        parsed.pop('datestamp', None)
        parsed.pop('timestamp', None)

    for i in range(1, 13):
        parsed.pop(f'sv_id{i:02d}', None)

    fields_to_remove = [
        'true_track_sym',
        'mag_track_sym',
        'spd_over_grnd_kts_sym',
        'spd_over_grnd_kmph_sym',
        'geo_sep_units',
    ]
    for field in fields_to_remove:
        parsed.pop(field, None)

    # Final type conversion for JSON compatibility
    final_parsed = {}
    for key, value in parsed.items():
        if key == 'sv' or key == 'gnss':
            final_parsed[key] = value
            continue
        
        if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
            final_parsed[key] = value.isoformat()
        elif isinstance(value, decimal.Decimal):
            final_parsed[key] = float(value)
        elif isinstance(value, (int, float, str, bool)):
            final_parsed[key] = value
        else:
            final_parsed[key] = str(value)

    return final_parsed

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
            parsed = parse_nmea(data)
            for parsed_key in parsed.keys():
                if parsed_key == 'gnss':
                    message['data'][k + '_gnss'] = parsed[parsed_key]
                else:
                    message['data'][k + '_gnss_' + parsed_key] = parsed[parsed_key]

    await r.delete(mutex_key)
    await r.aclose()
    
    return message

def post_process_up(message, param=None):
    return asyncio.run_coroutine_threadsafe(async_post_process(message, param), event_loop)

def post_process_down(message):
    print(f"[{TAG}] gotcha {message}")


if __name__ == '__main__':
    app_desc = "IOTOWN Post Process for GNSS data"

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

    init(url, 'GNSS', mqtt_url, args.redis_url, dry_run=dry_run).loop_forever()
