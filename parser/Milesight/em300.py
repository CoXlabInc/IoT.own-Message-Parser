import base64
import argparse
from urllib.parse import urlparse
import pyiotown.post_process

def post_process(message, param=None):
    if message.get('meta') is None or message['meta'].get('raw') is None:
        print(f'[EM300] A message have no meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]}')
        return message

    raw = base64.b64decode(message['meta']['raw'])
    print(f'[EM300] Group ID:{message["grpid"]}, Node ID:{message["nid"]}, type:{message["device"]["type"]}, desc.:{message["device"]["desc"]}, data:{message["data"]}, raw:{raw}')

    index = 0
    
    while index < len(raw):
        if raw[index + 1] == 0x00 and raw[index] == 0x05:
            if raw[index + 2] == 0x00:
                message['data'][f'CH{raw[index]}_WaterLeakage'] = 'no'
            elif raw[index + 2] == 0x01:
                message['data'][f'CH{raw[index]}_WaterLeakage'] = 'leakage'
            else:
                message['data'][f'CH{raw[index]}_WaterLeakage'] = f'unknown({raw[index + 2]})'
            index += 3
        elif raw[index + 1] == 0x00 and raw[index] == 0x06:
            if raw[index + 2] == 0x00:
                message['data'][f'CH{raw[index]}_MagnetSwitch'] = 'closed'
            elif raw[index + 2] == 0x01:
                message['data'][f'CH{raw[index]}_MagnetSwitch'] = 'opened'
            else:
                message['data'][f'CH{raw[index]}_MagnetSwitch'] = f'unknown({raw[index + 2]})'
            index += 3
        elif raw[index + 1] == 0x67:
            message['data'][f'CH{raw[index]}_Temperature_degC'] = int.from_bytes(raw[index + 2:index + 4], 'little', signed=True) * 0.1
            index += 4
        elif raw[index + 1] == 0x68:
            message['data'][f'CH{raw[index]}_Humidity_%RH'] = int.from_bytes(raw[index + 2:index + 3], 'little', signed=False) * 0.5
            index += 3
        elif raw[index + 1] == 0x75:
            message['data'][f'CH{raw[index]}_Battery_%'] = int.from_bytes(raw[index + 2:index + 3], 'little', signed=False)
            index += 3
        else:
            print(f"Unknown type 0x{raw[index + 1]:x}")
            break

    print(message['data'])
    return message

if __name__ == '__main__':
    app_desc = "IOTOWN Post Process to Parse Messages from Various Sensors"

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

    pyiotown.post_process.connect_common(url, 'Milesight EM300', post_process, mqtt_url=mqtt_url, dry_run=dry_run).loop_forever()
