import base64
from datetime import datetime, timedelta

def post_process(message):
    if message.get('meta') is None or message['meta'].get('raw') is None or message['meta'].get('fPort') is None:
        print(f'[DT-D100] A message have no meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]} <= meta:{message.get("meta")})')
        
        return message

    raw = base64.b64decode(message['meta']['raw'])
    print(f'[DT-D100] Group ID:{message["grpid"]}, Node ID:{message["nid"]}, type:{message["device"]["type"]}, desc.:{message["device"]["desc"]}, data:{message["data"]}, raw:{raw}')

    if message['meta']['fPort'] == 1:
        if len(raw) == 17:
            # SHT + Fire + Switch
            epoch = int.from_bytes(raw[1:5], 'little', signed=False)
            message['data']['sense_time'] = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'
        
            message['data']['nc_switch_open'] = ((raw[0] & (1 << 0)) != 0)
            message['data']['no_switch_open'] = ((raw[0] & (1 << 1)) != 0)
            message['data']['sht_valid'] = ((raw[0] & (1 << 2)) != 0)
            message['data']['fire_valid'] = ((raw[0] & (1 << 3)) != 0)
            message['data']['fire_detected'] = ((raw[0] & (1 << 4)) != 0)
            message['data']['fire_low_battery'] = ((raw[0] & (1 << 5)) != 0)
            message['data']['temperature'] = int.from_bytes(raw[5:7], 'little', signed=True) / 100
            message['data']['humidity'] = int.from_bytes(raw[7:9], 'little', signed=False) / 100
            message['data']['fire_value'] = int.from_bytes(raw[9:11], 'little', signed=False) / 10
            message['data']['fire_threshold'] = int.from_bytes(raw[11:13], 'little', signed=False) / 10
            message['data']['bat_voltage'] = int.from_bytes(raw[13:15], 'little', signed=False) / 1000
            message['data']['report_period'] = int.from_bytes(raw[15:17], 'little', signed=False)
            print(f"[DT-D100] SHT+fire+switch type: {message['data']}")
        elif len(raw) == 15:
            # SHT + Fire + Switch (errorneous firmware already deployed)
            #epoch = int.from_bytes(raw[1:5], 'little', signed=False)
            #message['data']['sense_time'] = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'
            
            #message['data']['nc_switch_open'] = ((raw[0] & (1 << 0)) != 0)
            message['data']['no_switch_open'] = ((raw[0] & (1 << 1)) != 0)
            #message['data']['sht_valid'] = ((raw[0] & (1 << 2)) != 0)
            #message['data']['fire_valid'] = ((raw[0] & (1 << 3)) != 0)
            #message['data']['fire_detected'] = ((raw[0] & (1 << 4)) != 0)
            #message['data']['fire_low_battery'] = ((raw[0] & (1 << 5)) != 0)
            message['data']['temperature'] = int.from_bytes(raw[5:7], 'little', signed=True) / 100
            message['data']['humidity'] = int.from_bytes(raw[7:9], 'little', signed=False) / 100
            message['data']['fire_value'] = int.from_bytes(raw[9:11], 'little', signed=False) / 10
            message['data']['fire_threshold'] = int.from_bytes(raw[11:13], 'little', signed=False) / 10
            message['data']['bat_voltage'] = int.from_bytes(raw[13:15], 'little', signed=False) / 1000
            #message['data']['report_period'] = int.from_bytes(raw[15:17], 'little', signed=False)
            print(f"[DT-D100] SHT+fire+switch type: {message['data']}")
        else:
            print(f"[DT-D100] unknown format ({message['meta']['fPort']}, {len(raw)})")
    elif message['meta']['fPort'] == 2:
        if len(raw) == 9:
            # Float
            epoch = int.from_bytes(raw[1:5], 'little', signed=False)
            #message['data']['sense_time'] = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'

            message['data']['door'] = ((raw[0] & (1 << 0)) == 0)
            message['data']['h'] = ((raw[0] & (1 << 1)) == 0)
            message['data']['l'] = ((raw[0] & (1 << 2)) == 0)
            message['data']['ll'] = ((raw[0] & (1 << 3)) == 0)
            message['data']['bat_voltage'] = int.from_bytes(raw[5:7], 'little', signed=False) / 1000
            message['data']['report_period'] = int.from_bytes(raw[7:9], 'little', signed=False)
            print(f"[DT-D100] float type: {message['data']}")
        else:
            print(f"[DT-D100] unknown format ({message['meta']['fPort']}, {len(raw)})")
    elif message['meta']['fPort'] == 4:
        if len(raw) == 13:
            # Manhole
            epoch = int.from_bytes(raw[0:5], 'little', signed=False)
            message['data']['sense_time'] = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'
            message['data']['report_period'] = int.from_bytes(raw[5:7], 'little', signed=False)
            message['data']['bat_voltage'] = int.from_bytes(raw[7:9], 'little', signed=False) / 1000
            message['data']['down_dist_mm'] = int.from_bytes(raw[9:11], 'little', signed=False)
            message['data']['cover_dist_mm'] = int.from_bytes(raw[11:13], 'little', signed=False)
        else:
            print(f"[DT-D100] unknown format ({message['meta']['fPort']}, {len(raw)})")
    elif message['meta']['fPort'] == 5:
        if len(raw) == 23:
            # Landslide
            epoch = int.from_bytes(raw[0:5], 'little', signed=False)
            message['data']['sense_time'] = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'
            message['data']['report_period'] = int.from_bytes(raw[5:7], 'little', signed=False)
            message['data']['bat_voltage'] = int.from_bytes(raw[7:9], 'little', signed=False) / 1000
            message['data']['acc_x'] = int.from_bytes(raw[9:11], 'little', signed=True) / 1024
            message['data']['acc_y'] = int.from_bytes(raw[11:13], 'little', signed=True) / 1024
            message['data']['acc_z'] = int.from_bytes(raw[13:15], 'little', signed=True) / 1024
            # TODO
        else:
            print(f"[DT-D100] unknown format ({message['meta']['fPort']}, {len(raw)})")
    else:
        print(f"[DT-D100] unknown format ({message['meta']['fPort']}, {len(raw)})")

    return message
