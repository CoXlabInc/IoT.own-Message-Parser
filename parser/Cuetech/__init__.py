import base64

def parse_sensor_value(message_type, message_value):
  key = message_type

  if len(message_value) <= 1:
    value = 'unknown 0x' + ''.join(format(x, '02X') for x in message_value)
    return key, value

  unit = (message_value[0] & 0b01110000) >> 4
  if unit == 1:
    key += '_V'
  elif unit == 2:
    key += '_degC'
  elif unit == 3:
    key += '_%'
  elif unit == 4:
    key += '_ppm'
  elif unit == 5:
    key += '_cm'

  status = (message_value[0] & 0b00001100) >> 2
  if status == 0:
    value = int.from_bytes(message_value[1:], 'big', signed=True)

    divisor = (message_value[0] & 0b00000011)
    if divisor == 1:
      value /= 10
    elif divisor == 2:
      value /= 100
    elif divisor == 3:
      value /= 1000
      
  elif status == 1:
    value = 'NotMeasuredYet'
  elif status == 2:
    value = 'ReadFail'

  return key, value

def post_process(message):
  if message.get('lora_meta') is None or message['lora_meta'].get('raw') is None:
    print(f'[Cuetech] A message have no lora_meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]}')
    return message

  raw = base64.b64decode(message['lora_meta']['raw'])
  print(f'[Cuetech] Group ID:{message["grpid"]}, Node ID:{message["nid"]}, type:{message["ntype"]}, desc.:{message["ndesc"]}, data:{message["data"]}, raw:{raw}')

  index = 0
  while index < len(raw) - 4:
    message_type = raw[index]
    message_value = raw[(index + 2) : (index + 2 + raw[index + 1])]
    print(f"Type:0x{message_type:02X}, Value:0x{' '.join(format(x, '02X') for x in message_value)}")
    if message_type == 0xAF:
      if len(message_value) == 1 and message_value[0] == 0x01:
        message['data']['CommErr'] = 'protocol error'
      elif len(message_value) == 1 and message_value[0] == 0x02:
        message['data']['CommErr'] = 'wrong tag'
      else:
        message['data']['CommErr'] = 'unknown 0x' + ''.join(format(x, '02X') for x in message_value)
    elif message_type == 0xA6:
      message['data']['model'] = message_value.decode('utf-8')
    elif message_type == 0xA7:
      message['data']['HardwareVersion'] = message_value.decode('utf-8')
    elif message_type == 0xA8:
      message['data']['FirmwareVersion'] = message_value.decode('utf-8')
    elif message_type == 0xA9:
      message['data']['ProtocolVersion'] = message_value.decode('utf-8')
    elif message_type == 0xAA:
      message['data']['SerialNumber'] = ''.join(format(x, '02X') for x in message_value)
    elif message_type == 0xB0:
      if len(message_value) == 1:
        message['data']['LastReceived'] = message_value[0]
      else:
        message['data']['LastReceived'] = 'unknown 0x' + ''.join(format(x, '02X') for x in message_value)
    elif message_type == 0xB1:
      sensor_list = []
      for x in message_value:
        if x == 0xC1:
          sensor_list.append('BatteryVoltage')
        elif x == 0xC3:
          sensor_list.append('Status_ManholeInsideDoor')
          sensor_list.append('Status_ManholeOutsideDoor')
        elif x == 0xC6:
          sensor_list.append('DepthToWater')
        elif x == 0xC7:
          sensor_list.append('CO')
        elif x == 0xC8:
          sensor_list.append('CO2')
        elif x == 0xC9:
          sensor_list.append('CH4')
        elif x == 0xCA:
          sensor_list.append('O2')
        elif x == 0xCB:
          sensor_list.append('H2S')
        elif x == 0xCC:
          sensor_list.append('Temperature')
        elif x == 0xCD:
          sensor_list.append('Humidity')
        elif x == 0xCE:
          sensor_list.append('Smoke')
        elif x == 0xCF:
          sensor_list.append('Status_FireExtinguisher')
        elif x == 0xD0:
          sensor_list.append('H')
      message['data']['SensorList'] = sensor_list
    elif message_type == 0xB2:
      if len(message_value) == 1:
        message['data']['MeasurementTime'] = message_value[0]
      else:
        message['data']['MeasurementTime'] = 'unknown 0x' + ''.join(format(x, '02X') for x in message_value)
    elif message_type == 0xB3:
      if len(message_value) == 1:
        message['data']['NumPackets'] = message_value[0]
      else:
        message['data']['NumPackets'] = 'unknown 0x' + ''.join(format(x, '02X') for x in message_value)
    elif message_type == 0xB4:
      if len(message_value) == 1:
        message['data']['PacketIndex'] = message_value[0]
      else:
        message['data']['PacketIndex'] = 'unknown 0x' + ''.join(format(x, '02X') for x in message_value)
    elif message_type == 0xB6:
      if len(message_value) == 1 and (message_value[0] & 0b10001000) == 0:
        message['data']['Alarm_FireExtinguisher'] = (message_value[0] & (1 << 6) != 0)
        message['data']['Alarm_Fire'] = (message_value[0] & (1 << 5) != 0)
        message['data']['Alarm_ManholeInsideDoor'] = (message_value[0] & (1 << 4) != 0)
        message['data']['Alarm_WaterLevel'] = (message_value[0] & (1 << 2) != 0)
        message['data']['Alarm_ManholeOutsideDoor'] = (message_value[0] & (1 << 1) != 0)
        message['data']['Alarm_LowBattery'] = (message_value[0] & (1 << 0) != 0)
      else:
        message['data']['Alarm'] = 'unknown 0x' + ''.join(format(x, '02X') for x in message_value)
    elif message_type == 0xC1:
      key, value = parse_sensor_value('BatteryVoltage', message_value)
      message['data'][key] = value
    elif message_type == 0xC3:
      if len(message_value) == 1 and (message_value[0] & 0b11111100) == 0:
        message['data']['Status_FireExtinguisher'] = (message_value[0] & (1 << 2) != 0)
        message['data']['Status_ManholeInsideDoor'] = (message_value[0] & (1 << 1) != 0)
        message['data']['Status_ManholeOutsideDoor'] = (message_value[0] & (1 << 0) != 0)
      else:
        message['data']['Status'] = 'unknown 0x' + ''.join(format(x, '02X') for x in message_value)
    elif message_type == 0xC6:
      key, value = parse_sensor_value('DepthToWater', message_value)
      message['data'][key] = value
    elif message_type == 0xC7:
      key, value = parse_sensor_value('CO', message_value)
      message['data'][key] = value
    elif message_type == 0xC8:
      key, value = parse_sensor_value('CO2', message_value)
      message['data'][key] = value
    elif message_type == 0xC9:
      key, value = parse_sensor_value('CH4', message_value)
      message['data'][key] = value
    elif message_type == 0xCA:
      key, value = parse_sensor_value('O2', message_value)
      message['data'][key] = value
    elif message_type == 0xCB:
      key, value = parse_sensor_value('H2S', message_value)
      message['data'][key] = value
    elif message_type == 0xCC:
      key, value = parse_sensor_value('Temperature', message_value)
      message['data'][key] = value
    elif message_type == 0xCD:
      key, value = parse_sensor_value('Humidity', message_value)
      message['data'][key] = value
    elif message_type == 0xCE:
      key, value = parse_sensor_value('Smoke', message_value)
      message['data'][key] = value
    elif message_type == 0xCF:
      if len(message_value) == 1 and (message_value[0] & 0b11111110) == 0:
        message['data']['Status_FireExtinguisher'] = (message_value[0] & (1 << 0) != 0)
      else:
        message['data']['Status'] = 'unknown 0x' + ''.join(format(x, '02X') for x in message_value)
    elif message_type == 0xD0:
      key, value = parse_sensor_value('H', message_value)
      message['data'][key] = value
    else:
      message['data'][f'UnknownType_0x{message_type:02X}'] = 'unknown 0x' + ''.join(format(x, '02X') for x in message_value)
    index += (2 + len(message_value))

  print(message['data'])
  return message
