import base64
from datetime import datetime, timedelta
import pyiotown.post_process
import redis
from urllib.parse import urlparse
import json
import math
import argparse

TAG = 'KDX-300'

register_map = [ 'V12', 'V23', 'V31',
                 'V1', 'V2', 'V3',
                 'A1', 'A2', 'A3',
                 'W1', 'W2', 'W3', 'W_total',
                 'VAR1', 'VAR2', 'VAR3', 'VAR_total',
                 'reserved', 'reserved', 'reserved', 'reserved',
                 'PF1', 'PF2', 'PF3', 'PF_average',
                 'Hz',
                 'Wh_p_h', 'Wh_p_l', 'Wh_n_h', 'Wh_n_l',
                 'VARh_p_h', 'VARh_p_l', 'VARh_n_h', 'VARh_n_l',
                 'V12_max', 'V23_max', 'V31_max',
                 'V1_max', 'V2_max', 'V3_max',
                 'A1_max', 'A2_max', 'A3_max',
                 'W_max',
                 'reserved',
                 'volt_dot_unit,curr_dot',
                 'watt_dot_unit,wh_dot_unit',
                 'wh_dot,wh_unit',
                 'angle_V1', 'angle_V2', 'angle_V3',
                 'angle_A1', 'angle_A2', 'angle_A3',
                 'angle_V12', 'angle_V23', 'angle_V31',
                 'V1_THD', 'V2_THD', 'V3_THD',
                 'V1_fund', 'V2_fund', 'V3_fund',
                 'V1_hr2', 'V2_hr2', 'V3_hr2',
                 'V1_hr3', 'V2_hr3', 'V3_hr3',
                 'V1_hr4', 'V2_hr4', 'V3_hr4',
                 'V1_hr5', 'V2_hr5', 'V3_hr5',
                 'V1_hr6', 'V2_hr6', 'V3_hr6',
                 'V1_hr7', 'V2_hr7', 'V3_hr7',
                 'V1_hr8', 'V2_hr8', 'V3_hr8',
                 'V1_hr9', 'V2_hr9', 'V3_hr9',
                 'V1_hr10', 'V2_hr10', 'V3_hr10',
                 'V1_hr11', 'V2_hr11', 'V3_hr11',
                 'V1_hr12', 'V2_hr12', 'V3_hr12',
                 'V1_hr13', 'V2_hr13', 'V3_hr13',
                 'V1_hr14', 'V2_hr14', 'V3_hr14',
                 'V1_hr15', 'V2_hr15', 'V3_hr15',
                 'V1_hr16', 'V2_hr16', 'V3_hr16',
                 'V1_hr17', 'V2_hr17', 'V3_hr17',
                 'V1_hr18', 'V2_hr18', 'V3_hr18',
                 'V1_hr19', 'V2_hr19', 'V3_hr19',
                 'V1_hr20', 'V2_hr20', 'V3_hr20',
                 'V1_hr21', 'V2_hr21', 'V3_hr21',
                 'V1_hr22', 'V2_hr22', 'V3_hr22',
                 'V1_hr23', 'V2_hr23', 'V3_hr23',
                 'V1_hr24', 'V2_hr24', 'V3_hr24',
                 'V1_hr25', 'V2_hr25', 'V3_hr25',
                 'V1_hr26', 'V2_hr26', 'V3_hr26',
                 'V1_hr27', 'V2_hr27', 'V3_hr27',
                 'V1_hr28', 'V2_hr28', 'V3_hr28',
                 'V1_hr29', 'V2_hr29', 'V3_hr29',
                 'V1_hr30', 'V2_hr30', 'V3_hr30',
                 'V1_hr31', 'V2_hr31', 'V3_hr31',
                 'V1_hr32', 'V2_hr32', 'V3_hr32',
                 'A1_THD', 'A2_THD', 'A3_THD',
                 'A1_fund', 'A2_fund', 'A3_fund',
                 'A1_hr2', 'A2_hr2', 'A3_hr2',
                 'A1_hr3', 'A2_hr3', 'A3_hr3',
                 'A1_hr4', 'A2_hr4', 'A3_hr4',
                 'A1_hr5', 'A2_hr5', 'A3_hr5',
                 'A1_hr6', 'A2_hr6', 'A3_hr6',
                 'A1_hr7', 'A2_hr7', 'A3_hr7',
                 'A1_hr8', 'A2_hr8', 'A3_hr8',
                 'A1_hr9', 'A2_hr9', 'A3_hr9',
                 'A1_hr10', 'A2_hr10', 'A3_hr10',
                 'A1_hr11', 'A2_hr11', 'A3_hr11',
                 'A1_hr12', 'A2_hr12', 'A3_hr12',
                 'A1_hr13', 'A2_hr13', 'A3_hr13',
                 'A1_hr14', 'A2_hr14', 'A3_hr14',
                 'A1_hr15', 'A2_hr15', 'A3_hr15',
                 'A1_hr16', 'A2_hr16', 'A3_hr16',
                 'A1_hr17', 'A2_hr17', 'A3_hr17',
                 'A1_hr18', 'A2_hr18', 'A3_hr18',
                 'A1_hr19', 'A2_hr19', 'A3_hr19',
                 'A1_hr20', 'A2_hr20', 'A3_hr20',
                 'A1_hr21', 'A2_hr21', 'A3_hr21',
                 'A1_hr22', 'A2_hr22', 'A3_hr22',
                 'A1_hr23', 'A2_hr23', 'A3_hr23',
                 'A1_hr24', 'A2_hr24', 'A3_hr24',
                 'A1_hr25', 'A2_hr25', 'A3_hr25',
                 'A1_hr26', 'A2_hr26', 'A3_hr26',
                 'A1_hr27', 'A2_hr27', 'A3_hr27',
                 'A1_hr28', 'A2_hr28', 'A3_hr28',
                 'A1_hr29', 'A2_hr29', 'A3_hr29',
                 'A1_hr30', 'A2_hr30', 'A3_hr30',
                 'A1_hr31', 'A2_hr31', 'A3_hr31',
                 'A1_hr32', 'A2_hr32', 'A3_hr32' ]

v_keys = [ 'V12', 'V23', 'V31',
           'V1', 'V2', 'V3',
           'V12_max', 'V23_max', 'V31_max',
           'V1_max', 'V2_max', 'V3_max' ]

c_keys = [ 'A1', 'A2', 'A3',
           'A1_max', 'A2_max', 'A3_max' ]

w_keys = [ 'W1', 'W2', 'W3', 'W_total',
           'VAR1', 'VAR2', 'VAR3', 'VAR_total',
           'W_max' ]

wh_keys = [ 'Wh_p', 'Wh_n',
            'VARh_p', 'VARh_n' ]

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
    #Data MUTEX
    r = redis.from_url(redis_url)
    
    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}:{message['key']}"
    lock = r.set(mutex_key, 'lock', ex=60, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        r.close()
        return None

    commands = message['data'].get('commands')
    if commands is None or type(commands) is not dict:
        r.close()
        raise Exception('No commands object')

    if param not in commands.keys():
        r.close()
        raise Exception('No req specified')

    req = commands[param].get('req')
    resp = commands[param].get('resp')
    
    if req is None or type(req) is not str or req.startswith('modbusri,') == False:
        r.close()
        raise Exception('Parsing request error')

    req = req.split(',')

    try:
        slave = int(req[1])
        addr = int(req[2])
        length = int(req[3]) * 2
    except Exception:
        r.close()
        raise Exception('Parsing request error')
    
    if resp is None or type(resp) is not str:
        r.close()
        raise Exception('Parsing response error')

    try:
        resp = bytes.fromhex(resp)
    except Exception:
        r.close()
        raise Exception('Parsing response error')
        
    if len(resp) != length:
        r.close()
        raise Exception('Length mismatch')

    v_dot = 0
    v_unit = 0
    c_dot = 0
    w_dot = 0
    w_unit = 0
    wh_dot = 0
    wh_unit = 0
    
    while len(resp) > 0:
        if addr > len(register_map):
            r.close()
            raise Exception('Address out of range')

        name = register_map[addr]
        if name.endswith('_h') and len(resp) >= 4:
            name = name.rsplit('_h')[0]
            message['data'][f"{param}_{name}"] = int.from_bytes(resp[0:4], 'big', signed=False)
            resp = resp[4:]
            addr += 2
        elif name == 'volt_dot_unit,curr_dot':
            v_dot = resp[0] >> 4
            v_unit = resp[0] & 0x0F
            c_dot = resp[1] >> 4
            resp = resp[2:]
            addr += 1
        elif name == 'watt_dot_unit,wh_dot_unit':
            w_dot = resp[0] >> 4
            w_unit = resp[0] & 0x0F
            wh_dot = resp[1] >> 4
            wh_unit = resp[1] & 0x0F
            resp = resp[2:]
            addr += 1
        elif len(resp) >= 2:
            if name != 'reserved':
                message['data'][f"{param}_{name}"] = int.from_bytes(resp[0:2], 'big', signed=False)
            resp = resp[2:]
            addr += 1
        else:
            r.close()
            raise Exception('Parsing response error')

    for k in message['data'].keys():
        for v_suffix in v_keys:
            if k == f"{param}_{v_suffix}":
                message['data'][k] = message['data'][k] / math.pow(10.0, v_dot) * math.pow(10.0, v_unit * 3)

        for c_suffix in c_keys:
            if k == f"{param}_{c_suffix}":
                message['data'][k] /= math.pow(10.0, c_dot)

        for w_suffix in w_keys:
            if k == f"{param}_{w_suffix}":
                message['data'][k] = message['data'][k] / math.pow(10.0, w_dot) * math.pow(10.0, w_unit * 3)

        for wh_suffix in wh_keys:
            if k == f"{param}_{wh_suffix}":
                message['data'][k] = message['data'][k] / math.pow(10.0, wh_dot) * math.pow(10.0, wh_unit * 3)
            
    r.delete(mutex_key)
    r.close()
    return message

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

    init(url, 'LightStar KDX-300', mqtt_url, args.redis_url, dry_run=dry_run).loop_forever()
