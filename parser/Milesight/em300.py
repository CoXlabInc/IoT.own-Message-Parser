import base64

def post_process(message):
    if message.get('meta') is None or message['meta'].get('raw') is None:
        print(f'[EM300] A message have no meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]}')
        return message

    raw = base64.b64decode(message['meta']['raw'])
    print(f'[EM300] Group ID:{message["grpid"]}, Node ID:{message["nid"]}, type:{message["device"]["type"]}, desc.:{message["device"]["desc"]}, data:{message["data"]}, raw:{raw}')

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
    return message
