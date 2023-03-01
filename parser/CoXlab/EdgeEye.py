import base64
from datetime import datetime, timedelta

import pyiotown.post_process
import redis
from urllib.parse import urlparse

TAG = 'EdgeEye'
iotown_url = None
iotown_token = None

def init(url, pp_name, mqtt_url, redis_url, dry_run=False):
    global iotown_url, iotown_token
    
    url_parsed = urlparse(url)
    iotown_url = f"{url_parsed.scheme}://{url_parsed.hostname}" + (f":{url_parsed.port}" if url_parsed.port is not None else "")
    iotown_token = url_parsed.password
    
    if redis_url is None:
        print(f"Redis is required for EdgeEye.")
        return None

    global r
    
    try:
        r = redis.from_url(redis_url)
        if r.ping() == False:
            r = None
            raise Exception('Redis connection failed')
    except Exception as e:
        print(e)
        return None
    
    return pyiotown.post_process.connect_common(url, 'EdgeEye', post_process, mqtt_url, dry_run=dry_run)
    
def post_process(message):
    if message.get('lora_meta') is None or message['lora_meta'].get('raw') is None or message['lora_meta'].get('fPort') is None:
        print(f'[{TAG}] A message have no lora_meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]} <= lora_meta:{message.get("lora_meta")})')
        
        return message

    raw = base64.b64decode(message['lora_meta']['raw'])

    #TODO length check

    epoch = int.from_bytes(raw[0:5], 'little', signed=False)
    offset = int.from_bytes(raw[6:8], 'little', signed=False)
    flags = raw[8]
    frag = raw[9:]
    fcnt = message["lora_meta"].get("fCnt")

    #MUTEX
    mutex_key = f"EdgeEye:MUTEX:{message['grpid']}:{message['nid']}:{fcnt}"
    
    lock = r.set(mutex_key, 'lock', ex=30, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        return None

    #PRR calculation
    #TODO When should the recent number of frames be initialized to 0?
    recent_num_frames_key = f"EdgeEye:RecentNumFrames:{message['grpid']}:{message['nid']}"
    devaddr_key = f"EdgeEye:DevAddr:{message['grpid']}:{message['nid']}"
    devaddr = r.get(devaddr_key)
    if devaddr is None or fcnt == 0:
        result = pyiotown.get.node(iotown_url, iotown_token, message['nid'], group_id=message['grpid'])
        try:
            devaddr_current = result['node']['lorawan']['session']['devAddr']
        except Exception as e:
            print(e)
            return None

        r.set(devaddr_key, devaddr_current)
        if devaddr != devaddr_current:
            print(f"[{TAG}] New session detected")
            recent_num_frames = None
        else:
            recent_num_frames = r.get(recent_num_frames_key)
    else:
        recent_num_frames = r.get(recent_num_frames_key)

    if recent_num_frames is None:
        recent_num_frames = 1
    elif int(recent_num_frames) < 1000:
        recent_num_frames = int(recent_num_frames) + 1
    else:
        recent_num_frames = 1000

    r.set(recent_num_frames_key, recent_num_frames)
    
    recent_fcnts_key = f"EdgeEye:RecentFCnts:{message['grpid']}:{message['nid']}"
    recent_fcnts = r.smembers(recent_fcnts_key)

    if recent_num_frames <= fcnt:
        to_be_removed = [item for item in recent_fcnts if int(item) > fcnt or int(item) < fcnt - recent_num_frames]
    else:
        to_be_removed = [item for item in recent_fcnts if int(item) > fcnt and int(item) < (65535 - (recent_num_frames - fcnt))] 

    print(f"[{TAG}] recent num frames: {recent_num_frames}, To be removed: {to_be_removed}")
    if len(to_be_removed) > 0:
        p = r.pipeline()
        for x in to_be_removed:
            p.srem(recent_fcnts_key, x)
        p.sadd(recent_fcnts_key, fcnt)
        p.execute()
    else:
        r.sadd(recent_fcnts_key, fcnt)

    recent_fcnts = r.smembers(recent_fcnts_key)
    prr = len(recent_fcnts) / recent_num_frames
    print(f"[{TAG}] PRR: {prr} = {len(recent_fcnts)} / {recent_num_frames}")

        
    
    print(f'[{TAG}] Group ID:{message["grpid"]}, Node ID:{message["nid"]}, type:{message["device"]["type"]}, desc.:{message["device"]["desc"]}, fcnt:{fcnt}, data:{message["data"]}, Epoch:{epoch}, Offset:{offset}, Flags:0x{flags:02x}, Frag:{frag} raw:{raw}')

    print(f"[{TAG}] unknown format ({message['lora_meta']['fPort']}, {len(raw)})")

    return message
