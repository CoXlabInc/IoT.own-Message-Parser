import base64
from datetime import datetime, timedelta
import pyiotown.post_process
import redis
from urllib.parse import urlparse
import struct

TAG = 'Accura3300e'

def init(url, pp_name, mqtt_url, redis_url, dry_run=False):
  global iotown_url, iotown_token
  
  url_parsed = urlparse(url)
  iotown_url = f"{url_parsed.scheme}://{url_parsed.hostname}" + (f":{url_parsed.port}" if url_parsed.port is not None else "")
  iotown_token = url_parsed.password
    
  if redis_url is None:
    print(f"Redis is required for Rootech Accura3300e.")
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
  raw = base64.b64decode(message['lora_meta']['raw'])
  fcnt = message['lora_meta'].get('fCnt')
  
  #MUTEX
  mutex_key = f"RootechAccura3300e:MUTEX:{message['grpid']}:{message['nid']}:{fcnt}"

  lock = r.set(mutex_key, 'lock', ex=30, nx=True)
  print(f"[{TAG}] lock with '{mutex_key}': {lock}")
  if lock != True:
    return None

  if len(raw) < 6:
    raise Exception('Too short')
  
  epoch = int.from_bytes(raw[0:5], 'little', signed=False)
  message['data']['sense_time'] = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'


  offset = raw[5]
  if offset != 0:
    #TODO reassembly
    raise Exception('Reassembly not supported yet')

  message_length = raw[6]
  if len(raw) - (5 + 1 + 1 + 2) != message_length:
    #TODO reassembly
    raise Exception(f"Invalid number of bytes: {message_length} expected but {len(raw) - (5 + 1 + 1 + 2)}")

  address = int.from_bytes(raw[7:9], 'little', signed=False)
  index = 0

  while index < len(raw) - 9:
    name, val, size = parse_register(address + (index // 2) + 1, raw[9 + index:])
    if name is not None:
      message['data'][name] = val
      print(f"[{address + (index // 2)}] {name}: {val}")
      index += size
    else:
      raise Exception(f"Parsing error at offset {index + 9}")
  
  print(f"[{TAG}] raw:{raw}")
  return message

def parse_register(address, buf):
  if address == 11010:
    val = modbus_u16(buf)
    if val == 0 or val == 1:
      return 'Valid', (val == 1), 2
    else:
      return None, None, None
  elif address == 11011:
    return 'Aggregation count', modbus_u32(buf), 4
  elif address == 11013:
    return 'Phase sequence status', modbus_u16(buf), 2
  elif address == 11014:
    return 'Van [V]', modbus_f32(buf), 4
  elif address == 11016:
    return 'Vbn [V]', modbus_f32(buf), 4
  elif address == 11018:
    return 'Vcn [V]', modbus_f32(buf), 4
  elif address == 11020:
    return 'Vavg_ln [V]', modbus_f32(buf), 4
  elif address == 11022:
    return 'Ia [A]', modbus_f32(buf), 4
  elif address == 11024:
    return 'Ib [A]', modbus_f32(buf), 4
  elif address == 11026:
    return 'Ic [A]', modbus_f32(buf), 4
  elif address == 11028:
    return 'Iavg [A]', modbus_f32(buf), 4
  elif address == 11030:
    return 'Vab [V]', modbus_f32(buf), 4
  elif address == 11032:
    return 'Vbc [V]', modbus_f32(buf), 4
  elif address == 11034:
    return 'Vca [V]', modbus_f32(buf), 4
  elif address == 11036:
    return 'Vavg_ll [V]', modbus_f32(buf), 4
  elif address == 11038:
    return 'Pa [kW]', modbus_f32(buf), 4
  elif address == 11040:
    return 'Pb [kW]', modbus_f32(buf), 4
  elif address == 11042:
    return 'Pc [kW]', modbus_f32(buf), 4
  elif address == 11044:
    return 'Ptot [kW]', modbus_f32(buf), 4
  elif address == 11046:
    return 'Qa [kVAR]', modbus_f32(buf), 4
  elif address == 11048:
    return 'Qb [kVAR]', modbus_f32(buf), 4
  elif address == 11050:
    return 'Qc [kVAR]', modbus_f32(buf), 4
  elif address == 11052:
    return 'Qtot [kVAR]', modbus_f32(buf), 4
  elif address == 11054:
    return 'Sa [kVA]', modbus_f32(buf), 4
  elif address == 11056:
    return 'Sb [kVA]', modbus_f32(buf), 4
  elif address == 11058:
    return 'Sc [kVA]', modbus_f32(buf), 4
  elif address == 11060:
    return 'Stot [kVA]', modbus_f32(buf), 4
  elif address == 11062:
    return 'PF A', modbus_f32(buf), 4
  elif address == 11064:
    return 'PF B', modbus_f32(buf), 4
  elif address == 11066:
    return 'PF C', modbus_f32(buf), 4
  elif address == 11068:
    return 'Total PF', modbus_f32(buf), 4
  elif address == 11070:
    val = modbus_u16(buf)
    if val == 0:
      val = 'Invalid'
    elif val == 1:
      val = 'Lead angle'
    elif val == 2:
      val = 'Lag angle'
    else:
      return None, None, None
    return 'Angle of PF A', val, 2
  elif address == 11071:
    val = modbus_u16(buf)
    if val == 0:
      val = 'Invalid'
    elif val == 1:
      val = 'Lead angle'
    elif val == 2:
      val = 'Lag angle'
    else:
      return None, None, None
    return 'Angle of PF B', val, 2
  elif address == 11072:
    val = modbus_u16(buf)
    if val == 0:
      val = 'Invalid'
    elif val == 1:
      val = 'Lead angle'
    elif val == 2:
      val = 'Lag angle'
    else:
      return None, None, None
    return 'Angle of PF C', val, 2
  elif address == 11073:
    val = modbus_u16(buf)
    if val == 0:
      val = 'Invalid'
    elif val == 1:
      val = 'Lead angle'
    elif val == 2:
      val = 'Lag angle'
    else:
      return None, None, None
    return 'Angle of Total PF', val, 2
  elif address == 11074:
    return 'Received kWh [kWh]', modbus_i32(buf), 4
  elif address == 11076:
    return 'Delivered kWh [kWh]', modbus_i32(buf), 4
  elif address == 11078:
    return 'Sum kWh [kWh]', modbus_i32(buf), 4
  elif address == 11080:
    return 'Net kWh [kWh]', modbus_i32(buf), 4
  elif address == 11082:
    return 'Received kVARh [kVARh]', modbus_i32(buf), 4
  elif address == 11084:
    return 'Delivered kVARh [kVARh]', modbus_i32(buf), 4
  elif address == 11086:
    return 'Sum kVARh [kVARh]', modbus_i32(buf), 4
  elif address == 11088:
    return 'Net kVARh [kVARh]', modbus_i32(buf), 4
  elif address == 11090:
    return 'kVAh [kVAh]', modbus_i32(buf), 4
  elif address == 11092:
    return 'Received kWh A [kWh]', modbus_i32(buf), 4
  elif address == 11094:
    return 'Received kWh B [kWh]', modbus_i32(buf), 4
  elif address == 11096:
    return 'Received kWh C [kWh]', modbus_i32(buf), 4
  elif address == 11098:
    return 'Delivered kWh A [kWh]', modbus_i32(buf), 4
  elif address == 11100:
    return 'Delivered kWh B [kWh]', modbus_i32(buf), 4
  elif address == 11102:
    return 'Delivered kWh C [kWh]', modbus_i32(buf), 4
  elif address == 11104:
    return 'Received kVARh A [kVARh]', modbus_i32(buf), 4
  elif address == 11106:
    return 'Received kVARh B [kVARh]', modbus_i32(buf), 4
  elif address == 11108:
    return 'Received kVARh C [kVARh]', modbus_i32(buf), 4
  elif address == 11110:
    return 'Delivered kVARh A [kVARh]', modbus_i32(buf), 4
  elif address == 11112:
    return 'Delivered kVARh B [kVARh]', modbus_i32(buf), 4
  elif address == 11114:
    return 'Delivered kVARh C [kVARh]', modbus_i32(buf), 4
  elif address == 11116:
    return 'kVAh A [kVAh]', modbus_i32(buf), 4
  elif address == 11118:
    return 'kVAh B [kVAh]', modbus_i32(buf), 4
  elif address == 11120:
    return 'kVAh C [kVAh]', modbus_i32(buf), 4
  elif address == 11122:
    return 'Demand Pa [kW]', modbus_f32(buf), 4
  elif address == 11124:
    return 'Demand Pb [kW]', modbus_f32(buf), 4
  elif address == 11126:
    return 'Demand Pc [kW]', modbus_f32(buf), 4
  elif address == 11128:
    return 'Demand Ptot [kW]', modbus_f32(buf), 4
  elif address == 11130:
    return 'Prediction Demand Ptot [kW]', modbus_f32(buf), 4
  elif address == 11132:
    return 'Demand Qa [kVAR]', modbus_f32(buf), 4
  elif address == 11134:
    return 'Demand Qb [kVAR]', modbus_f32(buf), 4
  elif address == 11136:
    return 'Demand Qc [kVAR]', modbus_f32(buf), 4
  elif address == 11138:
    return 'Demand kVAR total [kVAR]', modbus_f32(buf), 4
  elif address == 11140:
    return 'Prediction Demand Qtot [kVAR]', modbus_f32(buf), 4
  elif address == 11142:
    return 'Demand Sa [kVA]', modbus_f32(buf), 4
  elif address == 11144:
    return 'Demand Sb [kVA]', modbus_f32(buf), 4
  elif address == 11146:
    return 'Demand Sc [kVA]', modbus_f32(buf), 4
  elif address == 11148:
    return 'Demand Stot [kVA]', modbus_f32(buf), 4
  elif address == 11150:
    return 'Prediction Demand Stot [kVA]', modbus_f32(buf), 4
  elif address == 11152:
    return 'Demand Ia [A]', modbus_f32(buf), 4
  elif address == 11154:
    return 'Demand Ib [A]', modbus_f32(buf), 4
  elif address == 11156:
    return 'Demand Ic [A]', modbus_f32(buf), 4
  elif address == 11158:
    return 'Demand Iavg [A]', modbus_f32(buf), 4
  elif address == 11160:
    return 'Prediction demand Iavg [A]', modbus_f32(buf), 4
  elif address == 11202:
    return 'Voltage Van1 [V]', modbus_f32(buf), 4
  elif address == 11204:
    return 'Voltage Vbn1 [V]', modbus_f32(buf), 4
  elif address == 11206:
    return 'Voltage Vcn1 [V]', modbus_f32(buf), 4
  elif address == 11208:
    return 'Voltage Vavg1 [V]', modbus_f32(buf), 4
  elif address == 11210:
    return 'Current Ia1 [A]', modbus_f32(buf), 4
  elif address == 11212:
    return 'Current Ib1 [A]', modbus_f32(buf), 4
  elif address == 11214:
    return 'Current Ic1 [A]', modbus_f32(buf), 4
  elif address == 11216:
    return 'Current Iavg1 [A]', modbus_f32(buf), 4
  elif address == 11218:
    return 'Voltage THD A [%]', modbus_f32(buf), 4
  elif address == 11220:
    return 'Voltage THD B [%]', modbus_f32(buf), 4
  elif address == 11222:
    return 'Voltage THD C [%]', modbus_f32(buf), 4
  elif address == 11224:
    return 'Current THD A [%]', modbus_f32(buf), 4
  elif address == 11226:
    return 'Current THD B [%]', modbus_f32(buf), 4
  elif address == 11228:
    return 'Current THD C [%]', modbus_f32(buf), 4
  elif address == 11230:
    return 'Current TDD A [%]', modbus_f32(buf), 4
  elif address == 11232:
    return 'Current TDD B [%]', modbus_f32(buf), 4
  elif address == 11234:
    return 'Current TDD C [%]', modbus_f32(buf), 4
  elif address == 11236:
    return 'Voltage Phasor Vax [V]', modbus_f32(buf), 4
  elif address == 11238:
    return 'Voltage Phasor Vay [V]', modbus_f32(buf), 4
  elif address == 11240:
    return 'Voltage Phasor Vbx [V]', modbus_f32(buf), 4
  elif address == 11242:
    return 'Voltage Phasor Vby [V]', modbus_f32(buf), 4
  elif address == 11244:
    return 'Voltage Phasor Vcx [V]', modbus_f32(buf), 4
  elif address == 11246:
    return 'Voltage Phasor Vcy [V]', modbus_f32(buf), 4
  elif address == 11248:
    return 'Current Phasor Iax [A]', modbus_f32(buf), 4
  elif address == 11250:
    return 'Current Phasor Iay [A]', modbus_f32(buf), 4
  elif address == 11252:
    return 'Current Phasor Ibx [A]', modbus_f32(buf), 4
  elif address == 11254:
    return 'Current Phasor Iby [A]', modbus_f32(buf), 4
  elif address == 11256:
    return 'Current Phasor Icx [A]', modbus_f32(buf), 4
  elif address == 11258:
    return 'Current Phasor Icy [A]', modbus_f32(buf), 4
  elif address == 11260:
    return 'Residual voltage [V]', modbus_f32(buf), 4
  elif address == 11262:
    return 'Residual current [A]', modbus_f32(buf), 4
  elif address == 11264:
    return 'Voltage Unbalance of Vln [%]', modbus_f32(buf), 4
  elif address == 11266:
    return 'Voltage Unbalance of Vll [%]', modbus_f32(buf), 4
  elif address == 11268:
    return 'Voltage U0 Unbalance [%]', modbus_f32(buf), 4
  elif address == 11270:
    return 'Voltage U2 Unbalance [%]', modbus_f32(buf), 4
  elif address == 11272:
    return 'Current Unbalance [%]', modbus_f32(buf), 4
  elif address == 11274:
    return 'Current U0 Unbalance [%]', modbus_f32(buf), 4
  elif address == 11276:
    return 'Current U2 Unbalance [%]', modbus_f32(buf), 4
  elif address == 11278:
    return 'CFa', modbus_f32(buf), 4
  elif address == 11280:
    return 'CFb', modbus_f32(buf), 4
  elif address == 11282:
    return 'CFc', modbus_f32(buf), 4
  elif address == 11284:
    return 'KFa', modbus_f32(buf), 4
  elif address == 11286:
    return 'KFb', modbus_f32(buf), 4
  elif address == 11288:
    return 'KFc', modbus_f32(buf), 4
  elif address == 11290:
    return 'Frequency [Hz]', modbus_f32(buf), 4
  elif address == 11292:
    return 'Temperature [℃]', modbus_f32(buf), 4
  else:
    return None, None, None

def modbus_u16(buf):
  return int.from_bytes(buf[0:2], 'big', signed=False)

def modbus_i16(buf):
  return int.from_bytes(buf[0:2], 'big', signed=True)

def modbus_u32(buf):
  return int.from_bytes(buf[0:4], 'big', signed=False)

def modbus_i32(buf):
  return int.from_bytes(buf[0:4], 'little', signed=True)

def modbus_f32(buf):
  return struct.unpack('>f', buf[0:4])[0]
