import base64

def post_process(message):
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
