import base64
from datetime import datetime, timedelta
import math

def post_process(message, param=None):
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
        elif len(raw) == 15:
            # Manhole + FW Ver
            epoch = int.from_bytes(raw[0:5], 'little', signed=False)
            message['data']['sense_time'] = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'
            message['data']['report_period'] = int.from_bytes(raw[5:7], 'little', signed=False)
            message['data']['bat_voltage'] = int.from_bytes(raw[7:9], 'little', signed=False) / 1000
            message['data']['down_dist_mm'] = int.from_bytes(raw[9:11], 'little', signed=False)
            message['data']['cover_dist_mm'] = int.from_bytes(raw[11:13], 'little', signed=False)
            fw_ver = raw[14]*100 + raw[13] 
            message['data']['fw_ver'] = fw_ver/100            
        else:
            print(f"[DT-D100] unknown format ({message['meta']['fPort']}, {len(raw)})")
    elif message['meta']['fPort'] == 5:
        if len(raw) == 19:
            # Landslide
            epoch = int.from_bytes(raw[0:4], 'little', signed=False)
            message['data']['sense_time'] = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'
            message['data']['event_flag'] = raw[4]            
            message['data']['report_period'] = int.from_bytes(raw[5:7], 'little', signed=False)
            message['data']['bat_voltage'] = int.from_bytes(raw[7:9], 'little', signed=False) / 1000
            message['data']['angle_x'] = int.from_bytes(raw[9:11], 'little', signed=False) / 100
            message['data']['angle_y'] = int.from_bytes(raw[11:13], 'little', signed=False) / 100            
            message['data']['angle_z'] = int.from_bytes(raw[13:15], 'little', signed=False) / 100 
            message['data']['crack_mv'] = int.from_bytes(raw[15:17], 'little', signed=False)
            fw_ver = raw[18]*100 + raw[17] 
            message['data']['fw_ver'] = fw_ver/100
        elif len(raw) == 25:
            # Landslide + soil
            epoch = int.from_bytes(raw[0:4], 'little', signed=False)
            message['data']['sense_time'] = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'
            message['data']['event_flag'] = raw[4]            
            message['data']['report_period'] = int.from_bytes(raw[5:7], 'little', signed=False)
            message['data']['bat_voltage'] = int.from_bytes(raw[7:9], 'little', signed=False) / 1000
            message['data']['angle_x'] = int.from_bytes(raw[9:11], 'little', signed=False) / 100
            message['data']['angle_y'] = int.from_bytes(raw[11:13], 'little', signed=False) / 100            
            message['data']['angle_z'] = int.from_bytes(raw[13:15], 'little', signed=False) / 100 
            message['data']['crack_mv'] = int.from_bytes(raw[15:17], 'little', signed=False)
            fw_ver = raw[18]*100 + raw[17] 
            message['data']['fw_ver'] = fw_ver/100
            message['data']['soil_moisture_h'] = int.from_bytes(raw[19:21], 'little', signed=False) / 10
            message['data']['soil_moisture_l'] = int.from_bytes(raw[21:23], 'little', signed=False) / 10
            message['data']['soil_temperature'] = int.from_bytes(raw[23:25], 'little', signed=True) / 10
        elif len(raw) == 31:
            # Landslide + GPS
            epoch = int.from_bytes(raw[0:4], 'little', signed=False)
            message['data']['sense_time'] = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'
            message['data']['event_flag'] = raw[4]            
            message['data']['report_period'] = int.from_bytes(raw[5:7], 'little', signed=False)
            message['data']['bat_voltage'] = int.from_bytes(raw[7:9], 'little', signed=False) / 1000
            message['data']['angle_x'] = int.from_bytes(raw[9:11], 'little', signed=False) / 100
            message['data']['angle_y'] = int.from_bytes(raw[11:13], 'little', signed=False) / 100            
            message['data']['angle_z'] = int.from_bytes(raw[13:15], 'little', signed=False) / 100 
            message['data']['crack_mv'] = int.from_bytes(raw[15:17], 'little', signed=False)
            fw_ver = raw[18]*100 + raw[17] 
            message['data']['fw_ver'] = fw_ver/100
            message['data']['gps_lat'] = int.from_bytes(raw[19:23], 'little', signed=True) / 100000
            message['data']['gps_lon'] = int.from_bytes(raw[23:27], 'little', signed=True) / 100000
            message['data']['gps_alt'] = int.from_bytes(raw[27:31], 'little', signed=False)
        elif len(raw) == 37:
            # Landslide + soil + GPS
            epoch = int.from_bytes(raw[0:4], 'little', signed=False)
            message['data']['sense_time'] = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'
            message['data']['event_flag'] = raw[4]            
            message['data']['report_period'] = int.from_bytes(raw[5:7], 'little', signed=False)
            message['data']['bat_voltage'] = int.from_bytes(raw[7:9], 'little', signed=False) / 1000
            message['data']['angle_x'] = int.from_bytes(raw[9:11], 'little', signed=False) / 100
            message['data']['angle_y'] = int.from_bytes(raw[11:13], 'little', signed=False) / 100            
            message['data']['angle_z'] = int.from_bytes(raw[13:15], 'little', signed=False) / 100 
            message['data']['crack_mv'] = int.from_bytes(raw[15:17], 'little', signed=False)
            fw_ver = raw[18]*100 + raw[17] 
            message['data']['fw_ver'] = fw_ver/100
            message['data']['soil_moisture_h'] = int.from_bytes(raw[19:21], 'little', signed=False) / 10
            message['data']['soil_moisture_l'] = int.from_bytes(raw[21:23], 'little', signed=False) / 10
            message['data']['soil_temperature'] = int.from_bytes(raw[23:25], 'little', signed=True) / 10
            message['data']['gps_lat'] = int.from_bytes(raw[25:29], 'little', signed=True) / 100000
            message['data']['gps_lon'] = int.from_bytes(raw[29:33], 'little', signed=True) / 100000
            message['data']['gps_alt'] = int.from_bytes(raw[33:37], 'little', signed=False)
        else:
            print(f"[DT-D100] unknown format ({message['meta']['fPort']}, {len(raw)})")
    elif message['meta']['fPort'] == 6:
        if len(raw) == 32:
            # Landslide2
            message['data']['sensor_type'] = raw[0]
            epoch = int.from_bytes(raw[1:5], 'big', signed=False)
            message['data']['sense_time'] = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'
            message['data']['bat_voltage'] = int.from_bytes(raw[5:7], 'big', signed=False) / 1000
            message['data']['angle_x_avg'] = int.from_bytes(raw[9:11], 'big', signed=True)
            message['data']['angle_y_avg'] = int.from_bytes(raw[11:13], 'big', signed=True)
            message['data']['angle_z_avg'] = int.from_bytes(raw[13:15], 'big', signed=True)
            message['data']['angle_x_max'] = int.from_bytes(raw[15:17], 'big', signed=True)
            message['data']['angle_y_max'] = int.from_bytes(raw[17:19], 'big', signed=True)
            message['data']['angle_z_max'] = int.from_bytes(raw[19:21], 'big', signed=True)
            message['data']['angle_x_min'] = int.from_bytes(raw[21:23], 'big', signed=True)
            message['data']['angle_y_min'] = int.from_bytes(raw[23:25], 'big', signed=True)
            message['data']['angle_z_min'] = int.from_bytes(raw[25:27], 'big', signed=True)
        else:
            print(f"[DT-D100] unknown format ({message['meta']['fPort']}, {len(raw)})")
    else:
        print(f"[DT-D100] unknown format ({message['meta']['fPort']}, {len(raw)})")

    return message

