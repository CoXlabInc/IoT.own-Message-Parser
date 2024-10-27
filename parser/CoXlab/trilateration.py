import base64
import json
import pyiotown.get
import pyiotown.post_process
import redis
from urllib.parse import urlparse
import numpy as np
import itertools

TAG = 'Trilateration'

def init(url, pp_name, mqtt_url, r, dry_run=False):
    global iotown_url, iotown_token, redis_url
    
    url_parsed = urlparse(url)
    iotown_url = f"{url_parsed.scheme}://{url_parsed.hostname}" + (f":{url_parsed.port}" if url_parsed.port is not None else "")
    iotown_token = url_parsed.password

    redis_url = r
    if redis_url is None:
        print(f"Redis is required for {TAG}.")
        return None

    return pyiotown.post_process.connect_common(url, pp_name, post_process, mqtt_url=mqtt_url, dry_run=dry_run)

def get_anchors(obj):
    anchors = []
    for k in obj.keys():
        try:
            x = float(obj[k]['x'])
            y = float(obj[k]['y'])
            z = obj[k].get('z')
            dist = float(obj[k]['dist'])
            
            if z is not None:
                anchors.append([ x, y, float(z), dist ])
            else:
                anchors.append([ x, y, dist ])
        except:
            pass
    return anchors

def post_process(message, param=None):
    r = redis.from_url(redis_url)

    #MUTEX
    fcnt = message["meta"].get("fCnt")
    mutex_key = f"PP:{TAG}:MUTEX:{message['grpid']}:{message['nid']}:{fcnt}"
    
    lock = r.set(mutex_key, 'lock', ex=30, nx=True)
    print(f"[{TAG}] lock with '{mutex_key}': {lock}")
    if lock != True:
        r.close()
        return None

    obj = message['data']
    
    if param is None:
        r.close()
        raise Exception('Keys must be specified in the param')

    try:
        param = '{"keys":[' + param + ']}'
        param = json.loads(param)
        keys = param['keys']
    except:
        r.close()
        raise Exception(f"param error ({param})")

    for k in keys:
        ranging_set = message['data'].get(k)
        message['data'][f'{k}_estimated_3d_x'] = None
        message['data'][f'{k}_estimated_3d_y'] = None
        message['data'][f'{k}_estimated_3d_z'] = None
        message['data'][f'{k}_estimated_2d_x'] = None
        message['data'][f'{k}_estimated_2d_y'] = None

        if ranging_set is None:
            continue

        distances = get_anchors(ranging_set)
        print(f"[{TAG}] # of available anchors: {len(distances)}")
        if len(distances) == 0:
            continue

        if len(distances) == 1:
            if len(distances[0]) == 4:
                message['data'][f'{k}_estimated_3d_x'] = distances[0][0]
                message['data'][f'{k}_estimated_3d_y'] = distances[0][1]
                message['data'][f'{k}_estimated_3d_z'] = distances[0][2]
            message['data'][f'{k}_estimated_2d_x'] = distances[0][0]
            message['data'][f'{k}_estimated_2d_y'] = distances[0][1]
            continue

        if len(distances) == 2:
            if len(distances[0]) == 4 and len(distances[1]) == 4:
                message['data'][f'{k}_estimated_3d_x'] = (distances[0][0] + distances[1][0]) / 2  # TODO apply bias
                message['data'][f'{k}_estimated_3d_y'] = (distances[0][1] + distances[1][1]) / 2  # TODO apply bias
                message['data'][f'{k}_estimated_3d_z'] = (distances[0][2] + distances[1][2]) / 2  # TODO apply bias
            message['data'][f'{k}_estimated_2d_x'] = (distances[0][0] + distances[1][0]) / 2      # TODO apply bias
            message['data'][f'{k}_estimated_2d_y'] = (distances[0][1] + distances[1][1]) / 2      # TODO apply bias
            continue
        
        i = 0
        x_3d = []
        y_3d = []
        z_3d = []
        for d in list(itertools.combinations(distances, 4)):
            try:
                calculated = trilaterate3D(d)
                print(f"[{TAG}] {d} => {calculated}")
            except Exception as e:
                print(f"[{TAG}] {d} => {e}!!")
                continue

            if np.isnan(calculated[0]) == False:
                x_3d.append(calculated[0])
                
            if np.isnan(calculated[1]) == False:
                y_3d.append(calculated[1])

            if np.isnan(calculated[2]) == False:
                z_3d.append(calculated[2])
                
            i += 1

        if len(x_3d) > 0 and len(y_3d) > 0 and len(z_3d) > 0:
            message['data'][f'{k}_estimated_3d_x'] = np.mean(x_3d)
            message['data'][f'{k}_estimated_3d_y'] = np.mean(y_3d)
            message['data'][f'{k}_estimated_3d_z'] = np.mean(z_3d)

        i = 0
        x_2d = []
        y_2d = []
    
        for d in list(itertools.combinations(distances, 3)):
            try:
                calculated = trilaterate2D(d)
                print(f"[{TAG}] {d} => {calculated}")
            except Exception as e:
                print(f"[{TAG}] {d} => {e}!!")
                continue

            if np.isnan(calculated[0]) == False:
                x_2d.append(calculated[0])

            if np.isnan(calculated[1]) == False:
                y_2d.append(calculated[1])

            i += 1

        if len(x_2d) > 0 and len(y_2d) > 0:
            message['data'][f'{k}_estimated_2d_x'] = np.mean(x_2d)
            message['data'][f'{k}_estimated_2d_y'] = np.mean(y_2d)

    r.delete(mutex_key)
    r.close()
    return message

def trilaterate3D(distances):
    p1=np.array(distances[0][:3])
    p2=np.array(distances[1][:3])
    p3=np.array(distances[2][:3])
    p4=np.array(distances[3][:3])
    r1=distances[0][-1]
    r2=distances[1][-1]
    r3=distances[2][-1]
    r4=distances[3][-1]
    e_x=(p2-p1)/np.linalg.norm(p2-p1)
    i=np.dot(e_x,(p3-p1))
    e_y=(p3-p1-(i*e_x))/(np.linalg.norm(p3-p1-(i*e_x)))
    e_z=np.cross(e_x,e_y)
    d=np.linalg.norm(p2-p1)
    j=np.dot(e_y,(p3-p1))
    x=((r1**2)-(r2**2)+(d**2))/(2*d)
    y=(((r1**2)-(r3**2)+(i**2)+(j**2))/(2*j))-((i/j)*(x))
    z1=np.sqrt(r1**2-x**2-y**2)
    z2=np.sqrt(r1**2-x**2-y**2)*(-1)
    ans1=p1+(x*e_x)+(y*e_y)+(z1*e_z)
    ans2=p1+(x*e_x)+(y*e_y)+(z2*e_z)
    dist1=np.linalg.norm(p4-ans1)
    dist2=np.linalg.norm(p4-ans2)
    if np.abs(r4-dist1)<np.abs(r4-dist2):
        return ans1
    else: 
        return ans2

#def trilaterate(anchor_x, anchor_y, anchor1, anchor2, anchor3):
def trilaterate2D(distances):
    """
    @brief: Trilaterate Tag location
    @param: anchor_x - List of anchor coordinates along the X-axis
            anchor_y - List of anchor coordinates along the Y-axis
            anchor1 - Distance to the 1st Anchor
            anchor2 - Distance to the 2nd Anchor
            anchor3 - Distance to the 3rd Anchor
    @ret:   tag_coordinates - Tag Coordinates in a numpy array.
    """
    r1_sq = distances[0][-1] ** 2
    r2_sq = distances[1][-1] ** 2
    r3_sq = distances[2][-1] ** 2

    # Solve a linear matrix equation where x,y is the Tag coordinate:
    # Ax + By = C
    # Dx + Ey = F
    A = (-2*distances[0][0]) + (2*distances[1][0])
    B = (-2*distances[0][1]) + (2*distances[1][1])
    C = r1_sq - r2_sq - (distances[0][0] ** 2) + (distances[1][0] ** 2) - (distances[0][1] ** 2) + (distances[1][1] ** 2) 
    D = (-2*distances[1][0]) + (2*distances[2][0])
    E = (-2*distances[1][1]) + (2*distances[2][1])
    F = r2_sq - r3_sq - (distances[1][0] ** 2) + (distances[2][0] ** 2) - (distances[1][1] ** 2) + (distances[2][1] ** 2) 

    a = np.array([[A, B], [D, E]])
    b = np.array([C, F])
    tag_coordinates = np.linalg.solve(a, b)
    #print("Tag Coordinate:", tag_coordinates)
    return tag_coordinates.tolist()
