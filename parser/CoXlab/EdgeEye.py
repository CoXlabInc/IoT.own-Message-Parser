import base64
from datetime import datetime, timedelta
import json
import pyiotown.post_process
import redis
from urllib.parse import urlparse

TAG = 'EdgeEye'

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
        raise(e)
    
    return pyiotown.post_process.connect_common(url, pp_name, post_process, mqtt_url, dry_run=dry_run)
    
def post_process(message):
    raw = base64.b64decode(message['meta']['raw'])

    #TODO length check

    epoch = int.from_bytes(raw[0:5], 'little', signed=False)
    offset = int.from_bytes(raw[6:8], 'little', signed=False)
    flags = raw[8]
    frag = raw[9:]
    fcnt = message["meta"].get("fCnt")

    #MUTEX
    mutex_key = f"PP:EdgeEye:MUTEX:{message['grpid']}:{message['nid']}:{fcnt}"
    
    lock = r.set(mutex_key, 'lock', ex=30, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        return None

    #PRR calculation
    #TODO When should the recent number of frames be initialized to 0?
    recent_num_frames_key = f"PP:EdgeEye:RecentNumFrames:{message['grpid']}:{message['nid']}"
    devaddr_key = f"PP:EdgeEye:DevAddr:{message['grpid']}:{message['nid']}"
    devaddr = r.get(devaddr_key)
    if devaddr is None or fcnt == 0:
        # FIXME The sensor can start with empty frames. So it can enters into here with fcnt > 0.
        result = pyiotown.get.node(iotown_url, iotown_token, message['nid'], group_id=message['grpid'], verify=False)
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
    
    recent_fcnts_key = f"PP:EdgeEye:RecentFCnts:{message['grpid']}:{message['nid']}"
    recent_fcnts = r.smembers(recent_fcnts_key)

    if recent_num_frames <= fcnt:
        to_be_removed = [item for item in recent_fcnts if int(item) > fcnt or int(item) < fcnt - recent_num_frames]
    else:
        to_be_removed = [item for item in recent_fcnts if int(item) > fcnt and int(item) < (65535 - (recent_num_frames - fcnt))] 

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
    print(f"[{TAG}] recent num frames: {recent_num_frames}, To be removed: {to_be_removed}, PRR: {prr} = {len(recent_fcnts)} / {recent_num_frames}")

    epoch = int.from_bytes(raw[1:6], 'little', signed=False)
    sense_time = datetime.utcfromtimestamp(epoch).isoformat() + 'Z'

    total_size_key = f"PP:EdgeEye:size:{message['nid']}:{epoch}"
    first_frag = (((raw[0] >> 0) & (1 << 0)) != 0)
    if first_frag:
        offset = 0
        total_size = int.from_bytes(raw[6:9], 'little', signed=False)
        r.set(total_size_key, total_size)
    else:
        offset = int.from_bytes(raw[6:9], 'little', signed=False)
        total_size = r.get(total_size_key)
        if total_size is not None:
            total_size = int(total_size)
        else:
            print(f"[{TAG}] GET '{total_size_key}' returned None")
            total_size = 0

    offset_key = f"PP:EdgeEye:offset:{message['nid']}:{epoch}"
    offset_next = r.get(offset_key)
    if offset_next is None:
        offset_next = 0
    else:
        offset_next = int(offset_next)

    if offset > offset_next:
        print(f"[{TAG}] There was packet loss. (nid: {message['nid']}, offset {offset_next} is expected but {offset})")
        #TODO How can I notify it to the sensor?
        return message

    meta_key = f"PP:EdgeEye:meta:{message['nid']}:{epoch}"
    meta = r.get(meta_key)
    if meta is None:
        meta = []
    else:
        meta = json.loads(meta.decode('ascii'))

    l = message['meta']
    del l['raw']
    meta.append(l)
    
    image_buffer_key = f"PP:EdgeEye:buffer:{message['nid']}:{epoch}"
    rtsp_buffer_key = f"ImageToRtsp:{message['nid']}:image:buffer"
    rtsp_last_buffer_key = rtsp_buffer_key + ':last'
    
    last_frag = (((raw[0] >> 0) & (1 << 1)) != 0)
    if last_frag:
        image = r.get(image_buffer_key)
        image += raw[9:]

        r.set(rtsp_buffer_key, image, timedelta(hours=24))
        r.copy(image_buffer_key, rtsp_last_buffer_key, replace=True)
        r.expire(rtsp_last_buffer_key, timedelta(hours=24))

        message['data']['image'] = {
            'raw': image,
            'file_type': 'image',
            'file_ext': 'jpeg',
            'file_size': total_size,
            'sense_time': sense_time,
            'meta_total': meta,
        }
        r.delete(image_buffer_key)
        r.delete(offset_key)
        r.delete(meta_key)
        r.delete(total_size_key)
        print(f"[{TAG}] image reassembly completed (nid:{message['nid']}, size:{len(image)})")
    else:
        r.setrange(image_buffer_key, offset, raw[9:])
        offset += len(raw) - 9
        r.set(offset_key, offset)
        r.set(meta_key, json.dumps(meta))
        r.expire(image_buffer_key, timedelta(minutes=1))
        r.expire(offset_key, timedelta(minutes=1))
        r.expire(meta_key, timedelta(minutes=1))
        r.expire(total_size_key, timedelta(minutes=1))
        print(f"[{TAG}] image reassembly in progress (nid:{message['nid']}, +{len(raw) - 9} bytes, {offset}/{total_size} ({offset / total_size * 100}))")

        r.copy(image_buffer_key, rtsp_buffer_key, replace=True)
        r.expire(rtsp_buffer_key, timedelta(hours=24))

    return message if last_frag else None
