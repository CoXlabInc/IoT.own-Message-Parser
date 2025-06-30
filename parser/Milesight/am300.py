import base64
import argparse
from urllib.parse import urlparse
import pyiotown.post_process

def post_process(message, param=None):
    if message.get('meta') is None or message['meta'].get('raw') is None:
        print(f'[AM300] A message have no meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]}')
        return message

    raw = base64.b64decode(message['meta']['raw'])
    print(f'[AM300] Group ID:{message["grpid"]}, Node ID:{message["nid"]}, type:{message["device"]["type"]}, desc.:{message["device"]["desc"]}, data:{message["data"]}, raw:{raw}')

    index = 0
    
    while index < len(raw):
        if raw[index + 1] == 0x00 and raw[index] == 0x05:
            if raw[index + 2] == 0x00:
                message['data'][f'CH{raw[index]}_PIR'] = 'not triggered'
            elif raw[index + 2] == 0x01:
                message['data'][f'CH{raw[index]}_PIR'] = 'triggered'
            else:
                message['data'][f'CH{raw[index]}_PIR'] = f'unknown({raw[index + 2]})'
            index += 3
        elif raw[index + 1] == 0x01 and raw[index] == 0x0E:
            if raw[index + 2] == 0x00:
                message['data'][f'CH{raw[index]}_Buzzer'] = 'not beeping'
            elif raw[index + 2] == 0x01:
                message['data'][f'CH{raw[index]}_Buzzer'] = 'beeping'
            else:
                message['data'][f'CH{raw[index]}_Buzzer'] = f'unknown({raw[index + 2]})'
            index += 3
        elif raw[index + 1] == 0x67:
            message['data'][f'CH{raw[index]}_Temperature_degC'] = int.from_bytes(raw[index + 2:index + 4], 'little', signed=True) * 0.1
            index += 4
        elif raw[index + 1] == 0x68:
            message['data'][f'CH{raw[index]}_Humidity_%RH'] = int.from_bytes(raw[index + 2:index + 3], 'little', signed=False) * 0.5
            index += 3
        elif raw[index + 1] == 0x73:
            message['data'][f'CH{raw[index]}_BarometricPressure_hPa'] = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False) * 0.1
            index += 4
        elif raw[index + 1] == 0x75:
            message['data'][f'CH{raw[index]}_Battery_%'] = int.from_bytes(raw[index + 2:index + 3], 'little', signed=False)
            index += 3
        elif raw[index + 1] == 0x7D:
            if raw[index] == 0x07:
                sensor_type = f'CH{raw[index]}_CO2_ppm'
                sensor_value = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
            elif raw[index] == 0x08:
                sensor_type = f'CH{raw[index]}_TVOC'
                sensor_value = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
            elif raw[index] == 0x0A:
                sensor_type = f'CH{raw[index]}_HCHO_mg/m3'
                sensor_value = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False) * 0.01
            elif raw[index] == 0x0B:
                sensor_type = f'CH{raw[index]}_PM2.5_ug/m3'
                sensor_value = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
            elif raw[index] == 0x0C:
                sensor_type = f'CH{raw[index]}_PM10_ug/m3'
                sensor_value = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
            elif raw[index] == 0x0D:
                sensor_type = f'CH{raw[index]}_O3_ppm'
                sensor_value = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
            else:
                sensor_type = f'CH{raw[index]}_unknown'
                sensor_value = int.from_bytes(raw[index + 2:index + 4], 'little', signed=False)
                
            message['data'][sensor_type] = sensor_value
            index += 4
        elif raw[index + 1] == 0xCB:
            sensor_type = f'CH{raw[index]}_LightLevel'
            if raw[index + 2] == 0x00:
                sensor_value = '0~5 lux'
            elif raw[index + 2] == 0x01:
                sensor_value = '6~50 lux'
            elif raw[index + 2] == 0x02:
                sensor_value = '51~100 lux'
            elif raw[index + 2] == 0x03:
                sensor_value = '101~500 lux'
            elif raw[index + 2] == 0x04:
                sensor_value = '501~2000 lux'
            elif raw[index + 2] == 0x05:
                sensor_value = '>2000 lux'
            else:
                sensor_value = f'unknown({raw[index + 2]})'
            message['data'][sensor_type] = sensor_value
            index += 3
        else:
            print(f"Unknown type 0x{raw[index + 1]:x}")
            break

    print(message['data'])
    return message

if __name__ == '__main__':
    app_desc = "IOTOWN Post Process for Milesight AM300"

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

    pyiotown.post_process.connect_common(url, 'Milesight AM300', post_process, mqtt_url=mqtt_url, dry_run=dry_run).loop_forever()
