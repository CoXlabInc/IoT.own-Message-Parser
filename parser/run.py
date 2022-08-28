import argparse
import pyiotown.post
import pyiotown.get
import base64

url = None
dry_run = False

def post_process_am300(message):
    if message.get('lora_meta') is None or message['lora_meta'].get('raw') is None:
        print(f'[AM300] A message have no lora_meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]}')
        return message

    raw = base64.b64decode(message['lora_meta']['raw'])
    print(f'[AM300] Group ID:{message["grpid"]}, Node ID:{message["nid"]}, type:{message["ntype"]}, desc.:{message["ndesc"]}, data:{message["data"]}, raw:{raw}')

    index = 0
    
    while index < len(raw):
        if raw[index + 1] == 0x00 and raw[index] == 0x05:
            if raw[index + 2] == 0x00:
                message['data'][f'CH{raw[index]}_PIR'] = 'not triggered'
            elif raw[index + 2] == 0x01:
                message['data'][f'CH{raw[index]}_PIR'] = 'triggered'
            else:
                message['data'][f'CH{raw[index]}_PIR'] = f'unknown({raw[index + 2]})'
            index += 3
        elif raw[index + 1] == 0x01 and raw[index] == 0x0E:
            if raw[index + 2] == 0x00:
                message['data'][f'CH{raw[index]}_Buzzer'] = 'not beeping'
            elif raw[index + 2] == 0x01:
                message['data'][f'CH{raw[index]}_Buzzer'] = 'beeping'
            else:
                message['data'][f'CH{raw[index]}_Buzzer'] = f'unknown({raw[index + 2]})'
            index += 3
        elif raw[index + 1] == 0x67:
            message['data'][f'CH{raw[index]}_Temperature_degC'] = int.from_bytes(raw[index + 2:index + 4], 'little', signed=True) * 0.1
            index += 4
        elif raw[index + 1] == 0x68:
            message['data'][f'CH{raw[index]}_Humidity_%RH'] = int.from_bytes(raw[index + 2:index + 3], 'little', signed=False) * 0.5
            index += 3
        elif raw[index + 1] == 0x73:
            message['data'][f'CH{raw[index]}_BarometricPressure_hPa'] = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False) * 0.1
            index += 4
        elif raw[index + 1] == 0x75:
            message['data'][f'CH{raw[index]}_Battery_%'] = int.from_bytes(raw[index + 2:index + 3], 'little', signed=False)
            index += 3
        elif raw[index + 1] == 0x7D:
            if raw[index] == 0x07:
                sensor_type = f'CH{raw[index]}_CO2_ppm'
                sensor_value = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
            elif raw[index] == 0x08:
                sensor_type = f'CH{raw[index]}_TVOC'
                sensor_value = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
            elif raw[index] == 0x0A:
                sensor_type = f'CH{raw[index]}_HCHO_mg/m3'
                sensor_value = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False) * 0.01
            elif raw[index] == 0x0B:
                sensor_type = f'CH{raw[index]}_PM2.5_ug/m3'
                sensor_value = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
            elif raw[index] == 0x0C:
                sensor_type = f'CH{raw[index]}_PM10_ug/m3'
                sensor_value = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
            elif raw[index] == 0x0D:
                sensor_type = f'CH{raw[index]}_O3_ppm'
                sensor_value = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
            else:
                sensor_type = f'CH{raw[index]}_unknown'
                sensor_value = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
                
            message['data'][sensor_type] = sensor_value
            index += 4
        elif raw[index + 1] == 0xCB:
            sensor_type = f'CH{raw[index]}_LightLevel'
            if raw[index + 2] == 0x00:
                sensor_value = '0~5 lux'
            elif raw[index + 2] == 0x01:
                sensor_value = '6~50 lux'
            elif raw[index + 2] == 0x02:
                sensor_value = '51~100 lux'
            elif raw[index + 2] == 0x03:
                sensor_value = '101~500 lux'
            elif raw[index + 2] == 0x04:
                sensor_value = '501~2000 lux'
            elif raw[index + 2] == 0x05:
                sensor_value = '>2000 lux'
            else:
                sensor_value = f'unknown({raw[index + 2]})'
            message['data'][sensor_type] = sensor_value
            index += 3
        else:
            print(f"Unknown type 0x{raw[index + 1]:x}")
            break

    print(message['data'])

    if dry_run:
        return None
    else:
        return message

def post_process_em300(message):
    if message.get('lora_meta') is None or message['lora_meta'].get('raw') is None:
        print(f'[EM300] A message have no lora_meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]}')
        return message

    raw = base64.b64decode(message['lora_meta']['raw'])
    print(f'[EM300] Group ID:{message["grpid"]}, Node ID:{message["nid"]}, type:{message["ntype"]}, desc.:{message["ndesc"]}, data:{message["data"]}, raw:{raw}')

    index = 0
    
    while index < len(raw):
        if raw[index + 1] == 0x00 and raw[index] == 0x05:
            if raw[index + 2] == 0x00:
                message['data'][f'CH{raw[index]}_WaterLeakage'] = 'no'
            elif raw[index + 2] == 0x01:
                message['data'][f'CH{raw[index]}_WaterLeakage'] = 'leakage'
            else:
                message['data'][f'CH{raw[index]}_WaterLeakage'] = f'unknown({raw[index + 2]})'
            index += 3
        elif raw[index + 1] == 0x00 and raw[index] == 0x06:
            if raw[index + 2] == 0x00:
                message['data'][f'CH{raw[index]}_MagnetSwitch'] = 'closed'
            elif raw[index + 2] == 0x01:
                message['data'][f'CH{raw[index]}_MagnetSwitch'] = 'opened'
            else:
                message['data'][f'CH{raw[index]}_MagnetSwitch'] = f'unknown({raw[index + 2]})'
            index += 3
        elif raw[index + 1] == 0x67:
            message['data'][f'CH{raw[index]}_Temperature_degC'] = int.from_bytes(raw[index + 2:index + 4], 'little', signed=True) * 0.1
            index += 4
        elif raw[index + 1] == 0x68:
            message['data'][f'CH{raw[index]}_Humidity_%RH'] = int.from_bytes(raw[index + 2:index + 3], 'little', signed=False) * 0.5
            index += 3
        elif raw[index + 1] == 0x75:
            message['data'][f'CH{raw[index]}_Battery_%'] = int.from_bytes(raw[index + 2:index + 3], 'little', signed=False)
            index += 3
        else:
            print(f"Unknown type 0x{raw[index + 1]:x}")
            break

    print(message['data'])

    if dry_run:
        return None
    else:
        return message

def post_process_em310_tilt(message):
    if message.get('lora_meta') is None or message['lora_meta'].get('raw') is None:
        print(f'[EM310-TILT] A message have no lora_meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]}')
        return message

    raw = base64.b64decode(message['lora_meta']['raw'])
    print(f'[EM310-TILT] Group ID:{message["grpid"]}, Node ID:{message["nid"]}, type:{message["ntype"]}, desc.:{message["ndesc"]}, data:{message["data"]}, raw:{raw}')

    index = 0
    
    while index < len(raw):
        if raw[index + 1] == 0x75:
            message['data'][f'CH{raw[index]}_Battery_%'] = int.from_bytes(raw[index + 2:index + 3], 'little', signed=False)
            index += 3
        elif raw[index + 1] == 0xCF:
            message['data'][f'CH{raw[index]}_Angle_X_deg'] = int.from_bytes(raw[index + 2:index + 4], 'little', signed=True) * 0.01
            message['data'][f'CH{raw[index]}_Angle_Y_deg'] = int.from_bytes(raw[index + 4:index + 6], 'little', signed=True) * 0.01
            message['data'][f'CH{raw[index]}_Angle_Z_deg'] = int.from_bytes(raw[index + 6:index + 8], 'little', signed=True) * 0.01
            message['data'][f'CH{raw[index]}_Angle_X_flag'] = (raw[index + 8] & 0x01 != 0)
            message['data'][f'CH{raw[index]}_Angle_Y_flag'] = (raw[index + 8] & 0x02 != 0)
            message['data'][f'CH{raw[index]}_Angle_Z_flag'] = (raw[index + 8] & 0x04 != 0)
            index += 9
        else:
            print(f"Unknown type 0x{raw[index + 1]:x}")
            break

    print(message['data'])

    if dry_run:
        return None
    else:
        return message

def post_process_em310_udl(message):
    if message.get('lora_meta') is None or message['lora_meta'].get('raw') is None:
        print(f'[EM310-UDL] A message have no lora_meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]}')
        return message

    raw = base64.b64decode(message['lora_meta']['raw'])
    print(f'[EM310-UDL] Group ID:{message["grpid"]}, Node ID:{message["nid"]}, type:{message["ntype"]}, desc.:{message["ndesc"]}, data:{message["data"]}, raw:{raw}')

    index = 0
    
    while index < len(raw):
        if raw[index + 1] == 0x00:
            if raw[index + 2] == 0x00:
                message['data'][f'CH{raw[index]}_DevicePosition'] = 'normal'
            elif raw[index + 2] == 0x01:
                message['data'][f'CH{raw[index]}_DevicePosition'] = 'tilt'
            else:
                message['data'][f'CH{raw[index]}_DevicePosition'] = f'unknown({raw[index + 2]})'
            index += 3
        elif raw[index + 1] == 0x75:
            message['data'][f'CH{raw[index]}_Battery_%'] = int.from_bytes(raw[index + 2:index + 3], 'little', signed=False)
            index += 3
        elif raw[index + 1] == 0x82:
            message['data'][f'CH{raw[index]}_Distance_mm'] = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
            index += 4
        else:
            print(f"Unknown type 0x{raw[index + 1]:x}")
            break

    print(message['data'])

    if dry_run:
        return None
    else:
        return message

def post_process_em500(message):
    if message.get('lora_meta') is None or message['lora_meta'].get('raw') is None:
        print(f'[EM500]A message have no lora_meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]}')
        return message

    raw = base64.b64decode(message['lora_meta']['raw'])
    print(f'[EM500]Group ID:{message["grpid"]}, Node ID:{message["nid"]}, type:{message["ntype"]}, desc.:{message["ndesc"]}, data:{message["data"]}, raw:{raw}')

    index = 0
    
    while index < len(raw):
        if raw[index + 1] == 0x67:
            message['data'][f'CH{raw[index]}_Temperature_degC'] = int.from_bytes(raw[index + 2:index + 4], 'little', signed=True) * 0.1
            index += 4
        elif raw[index + 1] == 0x68:
            message['data'][f'CH{raw[index]}_Humidity_%RH'] = int.from_bytes(raw[index + 2:index + 3], 'little', signed=False) * 0.5
            index += 3
        elif raw[index + 1] == 0x73:
            message['data'][f'CH{raw[index]}_BarometricPressure_hPa'] = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False) * 0.1
            index += 4
        elif raw[index + 1] == 0x75:
            message['data'][f'CH{raw[index]}_Battery_%'] = int.from_bytes(raw[index + 2:index + 3], 'little', signed=False)
            index += 3
        elif raw[index + 1] == 0x77:
            message['data'][f'CH{raw[index]}_Depth_cm'] = int.from_bytes(raw[index + 2:index + 4], 'little', signed=True)
            index += 4
        elif raw[index + 1] == 0x7B:
            message['data'][f'CH{raw[index]}_Pressure_kPa'] = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
            index += 4
        elif raw[index + 1] == 0x7D:
            message['data'][f'CH{raw[index]}_Concentration_ppm'] = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
            index += 4
        elif raw[index + 1] == 0x7F:
            message['data'][f'CH{raw[index]}_Conductivity_us/cm'] = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
            index += 4
        elif raw[index + 1] == 0x82:
            message['data'][f'CH{raw[index]}_Distance_mm'] = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
            index += 4
        elif raw[index + 1] == 0x94:
            message['data'][f'CH{raw[index]}_Light_Lux'] = int.from_bytes(raw[index + 2:index + 6], 'little', signed=False)
            index += 6
        elif raw[index + 1] == 0xCA:
            message['data'][f'CH{raw[index]}_SoilMoisture_%RH'] = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False) * 0.01
            index += 4
        else:
            print(f"Unknown type 0x{raw[index + 1]}")
            break

    print(message['data'])

    if dry_run:
        return None
    else:
        return message

if __name__ == '__main__':
    app_desc = "IoT.own Post Process to Parse Messages from Various Sensors"

    parser = argparse.ArgumentParser(description=app_desc)
    parser.add_argument("--url", help="IoT.own URL", required=True)
    parser.add_argument("--user", help="IoT.own user name", required=True)
    parser.add_argument("--token", help="IoT.own API Token", required=True)
    parser.add_argument('--dry', help=" Do not upload data to the server", type=int, default=0)
    args = parser.parse_args()

    print(app_desc)
    print(f"URL: {args.url}")
    url = args.url.strip()

    if args.dry == 1:
        dry_run = True
        print("DRY RUNNING!")

    clients = []
    clients.append(pyiotown.post.postprocess_common(args.url, 'Milesight AM300', post_process_am300, args.user.strip(), args.token.strip()))
    clients.append(pyiotown.post.postprocess_common(args.url, 'Milesight EM300', post_process_em300, args.user.strip(), args.token.strip()))
    clients.append(pyiotown.post.postprocess_common(args.url, 'Milesight EM310-TILT', post_process_em310_tilt, args.user.strip(), args.token.strip()))
    clients.append(pyiotown.post.postprocess_common(args.url, 'Milesight EM310-UDL', post_process_em310_udl, args.user.strip(), args.token.strip()))
    clients.append(pyiotown.post.postprocess_common(args.url, 'Milesight EM500', post_process_em500, args.user.strip(), args.token.strip()))
    
    pyiotown.post.postprocess_loop_forever(clients)
    
