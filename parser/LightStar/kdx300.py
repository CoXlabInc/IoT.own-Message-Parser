import base64
from datetime import datetime, timedelta
import pyiotown.post_process
import redis
from urllib.parse import urlparse
import json

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
                 'volt_dot,volt_unit',
                 'curr_dot,reserved',
                 'watt_dot,watt_unit',
                 'wh_dot,wh_unit'
                 'V1_angle', 'V2_angle', 'V3_angle',
                 'A1_angle', 'A2_angle', 'A3_angle',
                 'V12_angle', 'V23_angle', 'V31_angle',
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
    lock = r.set(mutex_key, 'lock', ex=60, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        return None

    commands = message['data'].get('commands')
    if commands is None or type(commands) is not dict:
        raise Exception('No commands object')

    if param not in commands.keys():
        raise Exception('No req specified')

    req = commands[param].get('req')
    resp = commands[param].get('resp')
    
    if req is None or type(req) is not str or req.startswith('modbusri,') == False:
        raise Exception('Parsing request error')

    req = req.split(',')

    try:
        slave = int(req[1])
        addr = int(req[2])
        length = int(req[3]) * 2
    except Exception:
        raise Exception('Parsing request error')
    
    if resp is None or type(resp) is not str:
        raise Exception('Parsing response error')

    try:
        resp = bytes.fromhex(resp)
    except Exception:
        raise Exception('Parsing response error')
        
    if len(resp) != length:
        raise Exception('Length mismatch')

    while len(resp) > 0:
        if addr > len(register_map):
            raise Exception('Address out of range')

        name = register_map[addr]
        if name.endswith('_h') and len(resp) >= 4:
            name = name.rsplit('_h')[0]
            message['data'][f"{param}_{name}"] = int.from_bytes(resp[0:4], 'big', signed=False)
            resp = resp[4:]
            addr += 2
        elif len(name.split(',')) == 2:
            names = name.split(',')[0]
            message['data'][f"{param}_{names[0]}"] = resp[0]
            addr += 1
            resp = resp[1:]
            
            if len(resp) >= 1:
                message['data'][f"{param}_{names[1]}"] = resp[1]
                resp = resp[1:]
        elif len(resp) >= 2:
            if name != 'reserved':
                message['data'][f"{param}_{name}"] = int.from_bytes(resp[0:2], 'big', signed=False)
            resp = resp[2:]
            addr += 1
        else:
            raise Exception('Parsing response error')
        
    r.delete(mutex_key)
    return message
