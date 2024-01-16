import argparse
from urllib.parse import urlparse

import pyiotown.post
import pyiotown.post_process
import pyiotown.get

import CoXlab
import Cuetech
import Dragino
import DT
import Honeywell
import LightStar
import Milesight
import PLNetworks
import RAKWireless
import Rootech
import UniAi

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = None
dry_run = False

if __name__ == '__main__':
    app_desc = "IoT.own Post Process to Parse Messages from Various Sensors"

    parser = argparse.ArgumentParser(description=app_desc)
    parser.add_argument("--url", help="IoT.own URL", required=True)
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

    CoXlab.EdgeEye.init(url, 'EdgeEye', mqtt_url, args.redis_url, dry_run=dry_run).loop_start()
    CoXlab.csd2.init(url, 'CoXlab CSD2', mqtt_url, args.redis_url, dry_run=dry_run).loop_start()
    CoXlab.csd4.init(url, 'CoXlab CSD4', mqtt_url, args.redis_url, dry_run=dry_run).loop_start()
    CoXlab.aggregator.init(url, 'Aggregator', mqtt_url, args.redis_url, dry_run=dry_run).loop_start()
    CoXlab.mapper.init(url, 'Mapper', mqtt_url, args.redis_url, dry_run=dry_run).loop_start()
    CoXlab.multiplier.init(url, 'Multiplier', mqtt_url, args.redis_url, dry_run=dry_run).loop_start()
    CoXlab.rate_controller.init(url, 'RateController', mqtt_url, args.redis_url, dry_run=dry_run).loop_start()
    CoXlab.trilateration.init(url, 'Trilateration', mqtt_url, args.redis_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(url, 'Cuetech', Cuetech.post_process, mqtt_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(url, 'DT-D100', DT.d100.post_process, mqtt_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(url, 'Honeywell HVT', Honeywell.hvt.post_process, mqtt_url, dry_run=dry_run).loop_start()
    LightStar.init(url, 'LightStar KDX-300', mqtt_url, args.redis_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(url, 'Milesight AM300', Milesight.am300.post_process, mqtt_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(url, 'Milesight EM300', Milesight.em300.post_process, mqtt_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(url, 'Milesight EM310-TILT', Milesight.em310_tilt.post_process, mqtt_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(url, 'Milesight EM310-UDL', Milesight.em310_udl.post_process, mqtt_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(url, 'Milesight EM500', Milesight.em500.post_process, mqtt_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(url, 'PLNetworks', PLNetworks.post_process, mqtt_url, dry_run=dry_run).loop_start()
    RAKWireless.rak10701.init(url, 'RAK10701', mqtt_url, args.redis_url, dry_run=dry_run).loop_start()
    Dragino.lht65n.init(url, 'Dragino LHT65N', mqtt_url, args.redis_url, dry_run=dry_run).loop_start()
    Rootech.accura3300e.init(url, 'Rootech Accura3300e', mqtt_url, args.redis_url, dry_run=dry_run).loop_start()
    UniAi.init(url, 'UniAi', mqtt_url, args.redis_url, dry_run=dry_run).loop_forever()
