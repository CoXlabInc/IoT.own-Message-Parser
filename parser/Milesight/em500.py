import base64

def post_process(message, param=None):
    if message.get('meta') is None or message['meta'].get('raw') is None:
        print(f'[EM500]A message have no meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]}')
        return message

    raw = base64.b64decode(message['meta']['raw'])
    print(f'[EM500]Group ID:{message["grpid"]}, Node ID:{message["nid"]}, type:{message["device"]["type"]}, desc.:{message["device"]["desc"]}, data:{message["data"]}, raw:{raw}')

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
