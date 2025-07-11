import base64
import argparse
from urllib.parse import urlparse
import pyiotown.post_process

def parse_sensor_value(message_type, message_value):
  key = message_type

  if len(message_value) <= 1:
    value = 'unknown 0x' + ''.join(format(x, '02X') for x in message_value)
    return key, value

  unit = (message_value[0] & 0b11110000) >> 4
  if unit == 1:
    key += '_V'
  elif unit == 2:
    key += '_Kelvin'
  elif unit == 3:
    key += '_%'
  elif unit == 4:
    key += '_ppm'
  elif unit == 5:
    key += '_cm'
  elif unit == 6:
    key += '_mS/cm'
  elif unit == 7:
    key += '_hPa'
  elif unit == 8:
    key += '_m/sec'
  elif unit == 9:
    key += '_deg'
  elif unit == 10:
    key += '_mm/h'
  elif unit == 11:
    key += '_W/m^2'
  elif unit == 12:
    key += '_m^3/h'

  status = (message_value[0] & 0b00001100) >> 2
  if status == 0:
    value = int.from_bytes(message_value[1:], 'big', signed=False)

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

def convert_kelvin_to_degc(key, value):
  try:
    value -= 273.1
  except Exception as e:
    pass
  return '_DegC'.join(key.rsplit('_Kelvin', 1)), value

def post_process(message, param=None):
  if message.get('meta') is None or message['meta'].get('raw') is None:
    print(f'[Cuetech] A message have no meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]}')
    return message

  raw = base64.b64decode(message['meta']['raw'])
  print(f'[Cuetech] Group ID:{message["grpid"]}, Node ID:{message["nid"]}, type:{message["device"]["type"]}, desc.:{message["device"]["desc"]}, data:{message["data"]}, raw:{raw}')

  index = 0
  while index < len(raw) - 4:
    message_type = raw[index]
    message_value = raw[(index + 2) : (index + 2 + raw[index + 1])]
    #print(f"Type:0x{message_type:02X}, Value:0x{' '.join(format(x, '02X') for x in message_value)}")
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
        elif x == 0xD1:
          sensor_list.append('1_DepthToWater')
        elif x == 0xD2:
          sensor_list.append('2_DepthToWater')
        elif x == 0xD3:
          sensor_list.append('3_DepthToWater')
        elif x == 0xD4:
          sensor_list.append('4_DepthToWater')
        elif x == 0xD5:
          sensor_list.append('1_SoilTemperature')
        elif x == 0xD6:
          sensor_list.append('1_SoilMoisture')
        elif x == 0xD7:
          sensor_list.append('1_SoilEC')
        elif x == 0xD8:
          sensor_list.append('2_SoilTemperature')
        elif x == 0xD9:
          sensor_list.append('2_SoilMoisture')
        elif x == 0xDA:
          sensor_list.append('2_SoilEC')
        elif x == 0xDB:
          sensor_list.append('GroundSurfaceTemperature')
        elif x == 0xDC:
          sensor_list.append('WindDirection')
        elif x == 0xDD:
          sensor_list.append('WindSpeed')
        elif x == 0xDE:
          sensor_list.append('AmbientTemperature')
        elif x == 0xDF:
          sensor_list.append('AmbientHumidity')
        elif x == 0xE0:
          sensor_list.append('AtmosphericPressure')
        elif x == 0xE1:
          sensor_list.append('Precipitation')
        elif x == 0xE2:
          sensor_list.append('Flux')
        elif x == 0xE3:
          sensor_list.append('1_Temperature')
        elif x == 0xE4:
          sensor_list.append('1_Humidity')
        elif x == 0xE5:
          sensor_list.append('Solar Radiation')

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
      if key.endswith('_Kelvin'):
        key, value = convert_kelvin_to_degc(key, value)
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
    elif message_type == 0xD1:
      # Workaround for sensor bug
      value = int.from_bytes(message_value[1:], 'big', signed=False)
      if value >= 0x8000 and value <= 0xFFFF:
        message_value = bytearray(len(message_value))
      key, value = parse_sensor_value('1_DepthToWater', message_value)
      message['data'][key] = value
    elif message_type == 0xD2:
      # Workaround for sensor bug
      value = int.from_bytes(message_value[1:], 'big', signed=False)
      if value >= 0x8000 and value <= 0xFFFF:
        message_value = bytearray(len(message_value))
      key, value = parse_sensor_value('2_DepthToWater', message_value)
      message['data'][key] = value
    elif message_type == 0xD3:
      # Workaround for sensor bug
      value = int.from_bytes(message_value[1:], 'big', signed=False)
      if value >= 0x8000 and value <= 0xFFFF:
        message_value = bytearray(len(message_value))
      key, value = parse_sensor_value('3_DepthToWater', message_value)
      message['data'][key] = value
    elif message_type == 0xD4:
      # Workaround for sensor bug
      value = int.from_bytes(message_value[1:], 'big', signed=False)
      if value >= 0x8000 and value <= 0xFFFF:
        message_value = bytearray(len(message_value))
      key, value = parse_sensor_value('4_DepthToWater', message_value)
      message['data'][key] = value
    elif message_type == 0xD5:
      key, value = parse_sensor_value('1_SoilTemperature', message_value)
      if key.endswith('_Kelvin'):
        key, value = convert_kelvin_to_degc(key, value)
      message['data'][key] = value
    elif message_type == 0xD6:
      key, value = parse_sensor_value('1_SoilMoisture', message_value)
      message['data'][key] = value
    elif message_type == 0xD7:
      key, value = parse_sensor_value('1_SoilEC', message_value)
      message['data'][key] = value
    elif message_type == 0xD8:
      key, value = parse_sensor_value('2_SoilTemperature', message_value)
      if key.endswith('_Kelvin'):
        key, value = convert_kelvin_to_degc(key, value)
      message['data'][key] = value
    elif message_type == 0xD9:
      key, value = parse_sensor_value('2_SoilMoisture', message_value)
      message['data'][key] = value
    elif message_type == 0xDA:
      key, value = parse_sensor_value('2_SoilEC', message_value)
      message['data'][key] = value
    elif message_type == 0xDB:
      key, value = parse_sensor_value('GroundSurfaceTemperature', message_value)
      if key.endswith('_Kelvin'):
        key, value = convert_kelvin_to_degc(key, value)
      message['data'][key] = value
    elif message_type == 0xDC:
      key, value = parse_sensor_value('WindDirection', message_value)
      message['data'][key] = value
    elif message_type == 0xDD:
      key, value = parse_sensor_value('WindSpeed', message_value)
      message['data'][key] = value
    elif message_type == 0xDE:
      key, value = parse_sensor_value('AmbientTemperature', message_value)
      if key.endswith('_Kelvin'):
        key, value = convert_kelvin_to_degc(key, value)
      message['data'][key] = value
    elif message_type == 0xDF:
      key, value = parse_sensor_value('AmbientHumidity', message_value)
      message['data'][key] = value
    elif message_type == 0xE0:
      key, value = parse_sensor_value('AtmosphericPressure', message_value)
      message['data'][key] = value
    elif message_type == 0xE1:
      key, value = parse_sensor_value('Precipitation', message_value)
      message['data'][key] = value
    elif message_type == 0xE2:
      key, value = parse_sensor_value('Flux', message_value)
      message['data'][key] = value
    elif message_type == 0xE3:
      key, value = parse_sensor_value('1_Temperature', message_value)
      if key.endswith('_Kelvin'):
        key, value = convert_kelvin_to_degc(key, value)
      message['data'][key] = value
    elif message_type == 0xE4:
      key, value = parse_sensor_value('1_Humidity', message_value)
      message['data'][key] = value
    elif message_type == 0xE5:
      key, value = parse_sensor_value('Solar Radiation', message_value)
      message['data'][key] = value
    else:
      message['data'][f'UnknownType_0x{message_type:02X}'] = 'unknown 0x' + ''.join(format(x, '02X') for x in message_value)
    index += (2 + len(message_value))

  return message

if __name__ == '__main__':
    app_desc = "IOTOWN Post Process for Cuetech devices"

    parser = argparse.ArgumentParser(description=app_desc)
    parser.add_argument("--url", help="IOTOWN URL", required=True)
    parser.add_argument("--mqtt_url", help="MQTT broker URL for IoT.own", required=False, default=None)
    parser.add_argument("--redis_url", help="Redis URL for context storage", required=False, default=None)
    parser.add_argument('--dry', help=" Do not upload data to the server", type=int, default=0)
    args = parser.parse_args()

    print(app_desc)
    url = args.url.strip()
    url_parsed = urlparse(url)

    print(f"URL: {url_parsed.scheme}://{url_parsed.hostname}" + (f":{url_parsed.port}" if url_parsed.port is not None else ""))

    mqtt_url = args.mqtt_url.strip() if args.mqtt_url is not None else None
        
    if args.dry == 1:
        dry_run = True
        print("DRY RUNNING!")
    else:
        dry_run = False

    pyiotown.post_process.connect_common(url, 'Cuetech', post_process, mqtt_url=mqtt_url, dry_run=dry_run).loop_forever()
