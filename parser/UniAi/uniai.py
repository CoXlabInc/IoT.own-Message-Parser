import base64
from datetime import datetime, timedelta
from time import time
import pyiotown.post_process
import redis
from urllib.parse import urlparse
import struct
import json

TAG = 'UniAi'

def init(url, pp_name, mqtt_url, redis_url, dry_run=False):
  global iotown_url, iotown_token
  
  url_parsed = urlparse(url)
  iotown_url = f"{url_parsed.scheme}://{url_parsed.hostname}" + (f":{url_parsed.port}" if url_parsed.port is not None else "")
  iotown_token = url_parsed.password
    
  if redis_url is None:
    print(f"[{TAG}] Redis is required.")
    return None

  global r
  
  try:
    r = redis.from_url(redis_url)
    if r.ping() == False:
      r = None
      raise Exception('Redis connection failed')
  except Exception as e:
    raise(e)
      
  return pyiotown.post_process.connect_common(url, pp_name, post_process, mqtt_url, dry_run=dry_run)

def post_process(message):
  mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['key']}"

  lock = r.set(mutex_key, 'lock', ex=30, nx=True)
  if lock != True:
    return None

  print(f"[{TAG}] lock with '{mutex_key}': {lock}")

  device = {
    'type': message['device']['type'],
  }

  if type(message['device']['desc']) is str:
    device_desc = json.loads('{' + message['device']['desc'] + '}')
  elif type(message['device']['desc']) is dict:
    device_desc = message['device']['desc']
  else:
    device_desc = {}
    
  for k in device_desc.keys():
    device[k] = device_desc[k]

  min_interval = device.get('min_interval')
  if min_interval is not None:
    last_report_key = f"PP:{TAG}:last_report:{message['grpid']}:{message['nid']}"
    
    last_report = r.get(last_report_key)
    now = time()
    if last_report is not None:
      last_report = float(last_report)
      interval = now - last_report
      if interval < min_interval:
        print(f"[{TAG}] interval is too short ({now} (now) - {last_report} (last_report) = {interval} < {min_interval}")
        return None
    
  if device['type'] == 'CSD3':
    raw = base64.b64decode(message['meta']['raw'])
    if len(raw) == 0:
      raise Exception("no message")

    sensor_type = raw[0]
    if sensor_type == 0x01:
      if device['sensor'] == 'T9602':
        if len(raw) < 5:
          raise Exception(f"invalid message length ({len(raw)}) for T9602")
        message['data']['Temperature_DegC'] = int.from_bytes(raw[1:3], 'little', signed=True) / 100
        message['data']['Humidity_%'] = int.from_bytes(raw[3:5], 'little', signed=False) / 100
      else:
        raise Exception(f"unsupported temperature sensor '{device['sensor']}'")
    elif sensor_type == 0x02:
      if device['sensor'] == 'MH-410D':
        if len(raw) < 3:
          raise Exception(f"invalid message length ({len(raw)}) for MH-410D")
        message['data']['CO2_ppm'] = int.from_bytes(raw[1:3], 'big', signed=False)
      elif device['sensor'] == 'ZE03-NH3':
        if len(raw) < 3:
          raise Exception(f"invalid message length ({len(raw)}) for ZE03-NH3")
        message['data']['NH3_ppm'] = int.from_bytes(raw[1:3], 'big', signed=False)
      else:
        raise Exception(f"unsupported gas sensor '{device['sensor']}'")
  else:
    print(f"[{TAG}] unsupported type '{device['type']}'")

  if min_interval is not None:
    r.set(last_report_key, now, ex=min_interval + 1)
    
  return message
