import base64
from datetime import datetime, timedelta
import pyiotown.post_process
import redis
from urllib.parse import urlparse
import struct
import json
import argparse

TAG = 'ToNumber'

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

    #Data MUTEX
    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}:{message['key']}"
    lock = r.set(mutex_key, 'lock', ex=10, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        r.close()
        return None

    # param must be 'key_name:[source, start_pos, length, endian, signed]'
    # * key_name: where the converted integer is assigned to.
    # * type: int, or float
    # * source: the existing key name where byte array like (such as hex string, base64 encoded string) value is stored.
    # * start_pos: the start index of source to convert
    # * length: the length of source to convert
    # * endian: 'little' or 'big'
    # * signed: true of false (optional only for int, default: true)
    params = json.loads('{' + param + '}')

    for k in params.keys():
        if len(params[k]) < 5:
            r.delete(mutex_key)
            r.close()
            raise Exception(f"The length of '{k}' ({len(params[k])}) must be grater than or equal to 5.")

        number_type = params[k][0]
        if number_type not in ['int', 'float']:
            r.delete(mutex_key)
            r.close()
            raise Exception(f"The type ({number_type}) must be one of 'int', or 'float'.")
        
        source_key = params[k][1]
        if source_key is None:
            source_encoded = message['meta']['raw']
        elif source_key not in message['data'].keys():
            r.delete(mutex_key)
            r.close()
            raise Exception(f"The '{source_key}' is not found.")
        else:
            source_encoded = message['data'][source_key]

        try:
            source = bytearray.fromhex(source_encoded)
        except:
            source = None

        if source is None:
            try:
                source = bytearray(base64.b64decode(source_encoded))
            except:
                r.delete(mutex_key)
                r.close()
                raise Exception(f"The '{source}' is not a byte-like value.")

        start_pos = params[k][2]
        length = params[k][3]
        if len(source) < start_pos + length:
            r.delete(mutex_key)
            r.close()
            raise Exception(f"The length of the '{source_key}' ({len(source)}) must be greater than or equal to '{start_pos} + {length}'.")

        endian = params[k][4]
        if endian not in ['big', 'little', 'CDAB', 'BADC']:
            r.delete(mutex_key)
            r.close()
            raise Exception(f"The endian value ({endian}) must be one of 'big' or 'little'.")

        if number_type == 'int':
            if len(params[k]) >= 6:
                signed = params[k][5]
                if type(signed) is not bool:
                    r.delete(mutex_key)
                    r.close()
                    raise Exception(f"The signed value ({signed}) must be a boolean type.")
            else:
                signed = True

        if endian in ['CDAB', 'BADC']:
            if length != 4:
                r.delete(mutex_key)
                r.close()
                raise Exception(f"The endian value ({endian}) is for 4-byte data.")

            source_dup = source[start_pos : start_pos+length]

            # 'CDAB' -> 'DCBA'
            # 'BADC' -> 'ABCD'
            source[start_pos+0] = source_dup[1]
            source[start_pos+1] = source_dup[0]
            source[start_pos+2] = source_dup[3]
            source[start_pos+3] = source_dup[2]

            if endian == 'CDAB':
                endian = 'little'
            else:
                endian = 'big'

        fmt = '<' if endian == 'little' else '>'
        if number_type == 'float':
            if length >= 8:
                fmt += 'd'
            elif length >= 4:
                fmt += 'f'
            else:
                fmt += 'e'
        else:
            if signed:
                if length >= 8:
                    fmt += 'q'
                elif length >= 4:
                    fmt += 'l'
                elif length >= 2:
                    fmt += 'h'
                else:
                    fmt += 'b'
            else:
                if length >= 8:
                    fmt += 'Q'
                elif length >= 4:
                    fmt += 'L'
                elif length >= 2:
                    fmt += 'H'
                else:
                    fmt += 'B'

        try:
            message['data'][k] = struct.unpack_from(fmt, source[start_pos:start_pos+length])[0]
        except Exception as e:
            r.delete(mutex_key)
            r.close()
            raise e

    r.delete(mutex_key)
    r.close()
    return message

if __name__ == '__main__':
    app_desc = "IOTOWN Post Process to extract number values from data"

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

    init(url, 'ToNumber', mqtt_url, args.redis_url, dry_run=dry_run).loop_forever()
