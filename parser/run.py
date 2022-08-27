import argparse
import pyiotown.post
import pyiotown.get
import base64

url = None

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
    return message

if __name__ == '__main__':
    app_desc = "IoT.own Post Process to Parse Messages from Various Sensors"

    parser = argparse.ArgumentParser(description=app_desc)
    parser.add_argument("--url", help="IoT.own URL", required=True)
    parser.add_argument("--user", help="IoT.own user name", required=True)
    parser.add_argument("--token", help="IoT.own API Token", required=True)
    args = parser.parse_args()

    print(app_desc)
    print(f"URL: {args.url}")
    url = args.url.strip()

    clients = []
    clients.append(pyiotown.post.postprocess_common(args.url, 'Milesight EM310-TILT', post_process_em310_tilt, args.user.strip(), args.token.strip()))
    clients.append(pyiotown.post.postprocess_common(args.url, 'Milesight EM310-UDL', post_process_em310_udl, args.user.strip(), args.token.strip()))
    clients.append(pyiotown.post.postprocess_common(args.url, 'Milesight EM500', post_process_em500, args.user.strip(), args.token.strip()))
    
    pyiotown.post.postprocess_loop_forever(clients)
    
