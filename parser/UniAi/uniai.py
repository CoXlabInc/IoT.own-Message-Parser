import base64
from datetime import datetime, timedelta
import pyiotown.post_process
import redis
from urllib.parse import urlparse
import struct
import json

TAG = 'UniAi'

def post_process(message):
  device = {
    'type': message['device']['type'],
  }

  device_desc = json.loads('{' + message['device']['desc'] + '}')
  for k in device_desc.keys():
    device[k] = device_desc[k]
    
  if device['type'] == 'CSD3':
    raw = base64.b64decode(message['meta']['raw'])
    print(f"[{TAG}] {raw}")
    if raw[0] == 0x01:
      if device['sensor'] == 'T9602':
        message['data']['Temperature_DegC'] = int.from_bytes(raw[1:3], 'little', signed=True) / 100
        message['data']['Humidity_%'] = int.from_bytes(raw[3:5], 'little', signed=False) / 100
      else:
        raise Exception(f"unsupported temperature sensor '{device['sensor']}'")
    elif raw[0] == 0x02:
      if device['sensor'] == 'MH-410D':
        message['data']['CO2_ppm'] = int.from_bytes(raw[1:3], 'big', signed=False)
      elif device['sensor'] == 'ZE03-NH3':
        message['data']['NH3_ppm'] = int.from_bytes(raw[1:3], 'big', signed=False)
      else:
        raise Exception(f"unsupported gas sensor '{device['sensor']}'")
  else:
    print(f"[{TAG}] unsupported type '{device['type']}'")
  return message
