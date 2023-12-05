import base64

def post_process(message, param=None):
    if message.get('meta') is None or message['meta'].get('raw') is None:
        print(f'[EM310-TILT] A message have no meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]}')
        return message

    raw = base64.b64decode(message['meta']['raw'])
    print(f'[EM310-TILT] Group ID:{message["grpid"]}, Node ID:{message["nid"]}, type:{message["device"]["type"]}, desc.:{message["device"]["desc"]}, data:{message["data"]}, raw:{raw}')

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
