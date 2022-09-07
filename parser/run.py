import argparse
from urllib.parse import urlparse

import pyiotown.post
import pyiotown.post_process
import pyiotown.get

import Milesight
import Cuetech

url = None
dry_run = False

if __name__ == '__main__':
    app_desc = "IoT.own Post Process to Parse Messages from Various Sensors"

    parser = argparse.ArgumentParser(description=app_desc)
    parser.add_argument("--url", help="IoT.own URL", required=True)
    parser.add_argument("--user", help="IoT.own user name", required=True)
    parser.add_argument("--token", help="IoT.own API Token", required=True)
    parser.add_argument("--mqtt_url", help="MQTT broker URL for IoT.own", required=False, default=None)
    parser.add_argument('--dry', help=" Do not upload data to the server", type=int, default=0)
    args = parser.parse_args()

    print(app_desc)
    print(f"URL: {args.url}")
    url = args.url.strip()

    if args.mqtt_url is not None:
        mqtt_host = urlparse(args.mqtt_url).hostname
        mqtt_port = urlparse(args.mqtt_url).port
        print(f"MQTT URL: tcp://{mqtt_host}:{mqtt_port}")
    else:
        mqtt_host = None
        mqtt_port = 8883
        
    if args.dry == 1:
        dry_run = True
        print("DRY RUNNING!")

    clients = []
    clients.append(pyiotown.post_process.connect_common(url, 'Milesight AM300', Milesight.am300.post_process, args.user.strip(), args.token.strip(), mqtt_host, mqtt_port, dry_run=dry_run))
    clients.append(pyiotown.post_process.connect_common(url, 'Milesight EM300', Milesight.em300.post_process, args.user.strip(), args.token.strip(), mqtt_host, mqtt_port, dry_run=dry_run))
    clients.append(pyiotown.post_process.connect_common(url, 'Milesight EM310-TILT', Milesight.em310_tilt.post_process, args.user.strip(), args.token.strip(), mqtt_host, mqtt_port, dry_run=dry_run))
    clients.append(pyiotown.post_process.connect_common(url, 'Milesight EM310-UDL', Milesight.em310_udl.post_process, args.user.strip(), args.token.strip(), mqtt_host, mqtt_port, dry_run=dry_run))
    clients.append(pyiotown.post_process.connect_common(url, 'Milesight EM500', Milesight.em500.post_process, args.user.strip(), args.token.strip(), mqtt_host, mqtt_port, dry_run=dry_run))

    clients.append(pyiotown.post_process.connect_common(url, 'Cuetech', Cuetech.post_process, args.user.strip(), args.token.strip(), mqtt_host, mqtt_port, dry_run=dry_run))
    
    pyiotown.post_process.loop_forever(clients)
    
