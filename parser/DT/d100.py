import base64
from datetime import datetime, timedelta

def post_process(message):
    if message.get('lora_meta') is None or message['lora_meta'].get('raw') is None or message['lora_meta'].get('fPort') is None:
        print(f'[DT-D100] A message have no lora_meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]} <= lora_meta:{message.get("lora_meta")})')
        
        return message

    raw = base64.b64decode(message['lora_meta']['raw'])
    print(f'[DT-D100] Group ID:{message["grpid"]}, Node ID:{message["nid"]}, type:{message["device"]["type"]}, desc.:{message["device"]["desc"]}, data:{message["data"]}, raw:{raw}')

    if message['lora_meta']['fPort'] == 1:
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
            print(f"[DT-D100] unknown format ({message['lora_meta']['fPort']}, {len(raw)})")
    elif message['lora_meta']['fPort'] == 2:
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
            print(f"[DT-D100] unknown format ({message['lora_meta']['fPort']}, {len(raw)})")
    else:
        print(f"[DT-D100] unknown format ({message['lora_meta']['fPort']}, {len(raw)})")

    return message
