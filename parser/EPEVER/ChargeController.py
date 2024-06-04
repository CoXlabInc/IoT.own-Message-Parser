import base64
from datetime import datetime, timedelta
import pyiotown.post_process
import redis
from urllib.parse import urlparse
import json
import math

TAG = 'EPEVER Charge Controller'

def init(url, pp_name, mqtt_url, redis_url, dry_run=False):
    global iotown_url, iotown_token
    
    url_parsed = urlparse(url)
    iotown_url = f"{url_parsed.scheme}://{url_parsed.hostname}" + (f":{url_parsed.port}" if url_parsed.port is not None else "")
    iotown_token = url_parsed.password
    
    if redis_url is None:
        print(f"Redis is required for {TAG}.")
        return None

    global r
    
    r = redis.from_url(redis_url)
    if r.ping() == False:
        r = None
        raise Exception('Redis connection failed')

    return pyiotown.post_process.connect_common(url, pp_name, post_process, mqtt_url, dry_run=dry_run)

def add_data(data, address, value):
    if address == 0x2000:
        data['over_temperature_inside_device'] = (value == 1)
    elif address == 0x200C:
        data['day_night'] = 'Day' if value == 0 else 'Night'
    elif address == 0x3100:
        data['pv_array_input_voltage_V'] = value / 100
    elif address == 0x3101:
        data['pv_array_input_current_A'] = value / 100
    elif address == 0x3102:
        data['pv_array_input_power_W_L'] = value / 100
    elif address == 0x3103:
        data['pv_array_input_power_W_H'] = value / 100
    elif address == 0x310C:
        data['load_voltage_V'] = value / 100
    elif address == 0x310D:
        data['load_current_A'] = value / 100
    elif address == 0x310E:
        data['load_power_W_L'] = value / 100
    elif address == 0x310F:
        data['load_power_W_H'] = value / 100
    elif address == 0x3110:
        data['battery_temperature_DegC'] = value / 100
    elif address == 0x3111:
        data['device_temperature_DegC'] = value / 100
    elif address == 0x311A:
        data['battery_soc_%'] = value
    elif address == 0x311D:
        data['battery_real_rated_voltage_V'] = value / 100
    elif address == 0x3200:
        status = ''
        d3_0 = value & 0x000F
        if d3_0 == 1:
            status += ',Over Voltage'
        elif d3_0 == 2:
            status += ',Under Voltage'
        elif d3_0 == 3:
            status += ',Over Discharge'
        elif d3_0 == 4:
            status += ',Fault'
        d7_4 = (value & 0x00F0) >> 8
        if d7_4 == 1:
            status += ',Over Temp'
        elif d7_4 == 2:
            status += ',Low Temp'
        if value & 0x0100 != 0:
            status += ',Inner Resistance Abnormal'
        if value & 0x8000 != 0:
            status += ',Wrong Identification for Rated Voltage'
            
        if status == '':
            data['battery_status_str'] = 'Normal'
        else:
            data['battery_status_str'] = status[1:]
        data['battery_status'] = value
    elif address == 0x3201:
        if value & (1 << 0) == 0:
            status = 'Standby'
        else:
            status = 'Running'
        if value & (1 << 1) != 0:
            status += ',Fault'
        d3_2 = value & (0b11 << 2)
        if d3_2 == 0:
            status += ',No Charging'
        elif d3_2 == 1:
            status += ',Float'
        elif d3_2 == 2:
            status += ',Boost'
        elif d3_2 == 3:
            status += ',Equalization'
        if value & (1 << 4) != 0:
            status += ',PV Input is Short Circuit'
        if value & (1 << 6) != 0:
            status += ',Disequilibrium in Three Circuits'
        if value & (1 << 7) != 0:
            status += ',Load MOSFET is Short Circuit'
        if value & (1 << 8) != 0:
            status += ',Load is Short Circuit'
        if value & (1 << 9) != 0:
            status += ',Load is Over Current'
        if value & (1 << 10) != 0:
            status += ',Input is Over Current'
        if value & (1 << 11) != 0:
            status += ',Anti-reverse MOSFET is Short Circuit'
        if value & (1 << 12) != 0:
            status += ',Charging or Anti-reverse MOSFET is Open Circuit'
        if value & (1 << 13) != 0:
            status += ',Charging MOSFET is Short Circuit'
        d15_14 = value & (0b11 << 14)
        if d15_14 == 1:
            status += ',No Input Power Connected'
        elif d15_14 == 2:
            status += ',Higher Input Voltage'
        elif d15_14 == 3:
            status += ',Input Voltage Error'
        data['charging_equipment_status_str'] = status
        data['charging_equipment_status'] = value
    elif address == 0x3202:
        if value & (1 << 0) == 0:
            status = 'Standby'
        else:
            status = 'Running'
        if value & (1 << 1) != 0:
            status += ',Fault'
        if value & (1 << 4) != 0:
            status += ',Output Over Voltage'
        if value & (1 << 5) != 0:
            status += ',Boost Over Voltage'
        if value & (1 << 6) != 0:
            status += ',Short Circuit in High Voltage Side'
        if value & (1 << 7) != 0:
            status += ',Input Over Voltage'
        if value & (1 << 8) != 0:
            status += ',Output Voltage Abnormal'
        if value & (1 << 9) != 0:
            status += ',Unable to Stop Discharging'
        if value & (1 << 10) != 0:
            status += ',Unable to Discharge'
        if value & (1 << 11) != 0:
            status += ',Short Circuit'
        d13_12 = value & (0b11 << 12)
        if d13_12 == 0:
            status += ',Light Load'
        elif d3_2 == 1:
            status += ',Moderate'
        elif d3_2 == 2:
            status += ',Rated'
        elif d3_2 == 3:
            status += ',Overload'
        d15_14 = value & (0b11 << 14)
        if d15_14 == 1:
            status += ',Input Voltage Low'
        elif d15_14 == 2:
            status += ',Input Voltage High'
        elif d15_14 == 3:
            status += ',No Access'
        data['discharging_equipment_status_str'] = status
        data['discharging_equipment_status'] = value
    elif address == 0x3302:
        data['maximum_battery_voltage_today_V'] = value / 100
    elif address == 0x3303:
        data['minimum_battery_voltage_today_V'] = value / 100
    elif address == 0x3304:
        data['consumed_energy_today_kWh_L'] = value / 100
    elif address == 0x3305:
        data['consumed_energy_today_kWh_H'] = value / 100
    elif address == 0x3306:
        data['consumed_energy_month_kWh_L'] = value / 100
    elif address == 0x3307:
        data['consumed_energy_month_kWh_H'] = value / 100
    elif address == 0x3308:
        data['consumed_energy_year_kWh_L'] = value / 100
    elif address == 0x3309:
        data['consumed_energy_year_kWh_H'] = value / 100
    elif address == 0x330A:
        data['consumed_energy_total_kWh_L'] = value / 100
    elif address == 0x330B:
        data['consumed_energy_total_kWh_H'] = value / 100
    elif address == 0x330C:
        data['generated_energy_today_kWh_L'] = value / 100
    elif address == 0x330D:
        data['generated_energy_today_kWh_H'] = value / 100
    elif address == 0x330E:
        data['generated_energy_month_kWh_L'] = value / 100
    elif address == 0x330F:
        data['generated_energy_month_kWh_H'] = value / 100
    elif address == 0x3310:
        data['generated_energy_year_kWh_L'] = value / 100
    elif address == 0x3311:
        data['generated_energy_year_kWh_H'] = value / 100
    elif address == 0x3312:
        data['generated_energy_total_kWh_L'] = value / 100
    elif address == 0x3313:
        data['generated_energy_total_kWh_H'] = value / 100
    elif address == 0x331A:
        data['battery_voltage_V'] = value / 100
    elif address == 0x331B:
        data['battery_current_A_L'] = value / 100
    elif address == 0x331C:
        data['battery_current_A_H'] = value / 100

def post_process(message, param=None):
    #Data MUTEX
    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}:{message['key']}"
    lock = r.set(mutex_key, 'lock', ex=60, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        return None

    if param is None or type(param) is not str:
        r.delete(mutex_key)
        raise Exception("Valid param is required")
    
    params = []
    try:
        params = json.loads('[' + param + ']')
    except Exception as e:
        r.delete(mutex_key)
        raise e

    data = {}
    
    for index in params:
        req = message['data'].get(f'req{index}')

        resp = message['data'].get(f'resp{index}')

        data[f'req{index}'] = req
        data[f'resp{index}'] = resp
        
        if req is None:
            message['pp_warning'] += f",'req{index}' not found"
            continue
        if resp is None:
            message['pp_warning'] += f",'resp{index}' not found"
            continue

        try:
            req_blocks = req.split(',')  # command type, device ID, register address, count
            command_type = req_blocks[0]
            device_id = int(req_blocks[1])
            register_addr = int(req_blocks[2])
            count = int(req_blocks[3])
        except Exception as e:
            raise Exception("Invalid request format")

        try:
            resp = bytes.fromhex(resp)
        except Exception as e:
            r.delete(mutex_key)
            raise Exception("Invalid response format")
        
        if command_type == 'modbusrd':
            for i in range(count):
                add_data(data, register_addr + i, (resp[i // 8] >> (i % 8)) & 1)
        elif command_type == 'modbusri':
            for i in range(count):
                add_data(data, register_addr + i, int.from_bytes(resp[(i*2):(i*2) + 2], 'big', signed=False))
        else:
            r.delete(mutex_key)
            raise Exception("Unsupported function '{req_blocks[0]}'")

    message['data'] = data
    r.delete(mutex_key)

    if len(message['pp_warning']) > 0:
        message['pp_warning'] = message['pp_warning'][1:] # remove the first comma
    return message
