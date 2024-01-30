import base64
from datetime import datetime, timedelta
import pyiotown.post_process
import redis
from urllib.parse import urlparse
import struct
import json

TAG = 'ToNumber'

def init(url, pp_name, mqtt_url, redis_url, dry_run=False):
    global iotown_url, iotown_token
    
    url_parsed = urlparse(url)
    iotown_url = f"{url_parsed.scheme}://{url_parsed.hostname}" + (f":{url_parsed.port}" if url_parsed.port is not None else "")
    iotown_token = url_parsed.password
    
    if redis_url is None:
        print(f"Redis is required for {TAG}.")
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
    #Data MUTEX
    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}:{message['key']}"
    lock = r.set(mutex_key, 'lock', ex=10, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        return None

    # param must be 'key_name:[source, start_pos, length, endian, signed]'
    # * key_name: where the converted integer is assigned to.
    # * type: int, or float
    # * source: the existing key name where byte array like (such as hex string, base64 encoded string) value is stored.
    # * start_pos: the start index of source to convert
    # * length: the length of source to convert
    # * endian: 'little' or 'big'
    # * signed: true of false
    params = json.loads('{' + param + '}')

    for k in params.keys():
        if len(params[k]) < 5:
            r.delete(mutex_key)
            raise Exception(f"The length of '{k}' ({len(params[k])}) must be grater than or equal to 5.")

        number_type = params[k][0]
        if number_type not in ['int', 'float']:
            r.delete(mutex_key)
            raise Exception(f"The type ({number_type}) must be one of 'int', or 'float'.")
        
        source_key = params[k][1]
        if source_key not in message['data'].keys():
            r.delete(mutex_key)
            raise Exception(f"The '{source_key}' is not found.")
        
        try:
            source = bytes.fromhex(message['data'][source_key])
        except:
            pass

        if source is None:
            try:
                source = base64.b64decode(message['data'][source_key])
            except:
                r.delete(mutex_key)
                raise Exception(f"The '{source}' is not a byte-like value.")

        start_pos = params[k][2]
        length = params[k][3]
        if len(source) < start_pos + length:
            r.delete(mutex_key)
            raise Exception(f"The length of the '{source_key}' ({len(source)}) must be greater than or equal to '{start_pos} + {length}'.")

        endian = params[k][4]
        if endian not in ['big', 'little']:
            r.delete(mutex_key)
            raise Exception(f"The endian value ({endian}) must be one of 'big' or 'little'.")

        signed = params[k][5]
        if type(signed) is not bool:
            r.delete(mutex_key)
            raise Exception(f"The signed value ({signed}) must be a boolean type.")

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
            raise e

    r.delete(mutex_key)
    return message
