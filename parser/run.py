import argparse
from urllib.parse import urlparse

import pyiotown.post
import pyiotown.post_process
import pyiotown.get

import CoXlab
import Cuetech
import Dragino
import DT
import EPEVER
import Honeywell
import LightStar
import Milesight
import PLNetworks
import RAKWireless
import Rootech

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main(iotown_url, mqtt_url, redis_url, dry_run):
    CoXlab.csd2.init(iotown_url, 'CoXlab CSD2', mqtt_url, redis_url, dry_run=dry_run).loop_start()
    CoXlab.csd4.init(iotown_url, 'CoXlab CSD4', mqtt_url, redis_url, dry_run=dry_run).loop_start()
    CoXlab.aggregator.init(iotown_url, 'Aggregator', mqtt_url, redis_url, dry_run=dry_run).loop_start()
    CoXlab.mapper.init(iotown_url, 'Mapper', mqtt_url, redis_url, dry_run=dry_run).loop_start()
    CoXlab.multiplier.init(iotown_url, 'Multiplier', mqtt_url, redis_url, dry_run=dry_run).loop_start()
    CoXlab.rate_controller.init(iotown_url, 'RateController', mqtt_url, redis_url, dry_run=dry_run).loop_start()
    CoXlab.trilateration.init(iotown_url, 'Trilateration', mqtt_url, redis_url, dry_run=dry_run).loop_start()
    CoXlab.to_number.init(iotown_url, 'ToNumber', mqtt_url, redis_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(iotown_url, 'Cuetech', Cuetech.post_process, mqtt_url=mqtt_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(iotown_url, 'DT-D100', DT.d100.post_process, mqtt_url=mqtt_url, dry_run=dry_run).loop_start()
    EPEVER.init(url, 'EPEVER ChargeController', mqtt_url, args.redis_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(iotown_url, 'Honeywell HVT', Honeywell.hvt.post_process, mqtt_url=mqtt_url, dry_run=dry_run).loop_start()
    LightStar.init(iotown_url, 'LightStar KDX-300', mqtt_url, redis_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(iotown_url, 'Milesight AM300', Milesight.am300.post_process, mqtt_url=mqtt_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(iotown_url, 'Milesight EM300', Milesight.em300.post_process, mqtt_url=mqtt_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(iotown_url, 'Milesight EM310-TILT', Milesight.em310_tilt.post_process, mqtt_url=mqtt_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(iotown_url, 'Milesight EM310-UDL', Milesight.em310_udl.post_process, mqtt_url=mqtt_url, dry_run=dry_run).loop_start()
    pyiotown.post_process.connect_common(iotown_url, 'Milesight EM500', Milesight.em500.post_process, mqtt_url=mqtt_url, dry_run=dry_run).loop_start()
    PLNetworks.init(iotown_url, 'PLNetworks', mqtt_url, redis_url, dry_run=dry_run).loop_start()
    RAKWireless.rak10701.init(iotown_url, 'RAK10701', mqtt_url, redis_url, dry_run=dry_run).loop_start()
    Dragino.lht65n.init(iotown_url, 'Dragino LHT65N', mqtt_url, redis_url, dry_run=dry_run).loop_start()
    Rootech.accura3300e.init(iotown_url, 'Rootech Accura3300e', mqtt_url, redis_url, dry_run=dry_run).loop_forever()

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
    else:
        dry_run = False

    main(url, mqtt_url, args.redis_url, dry_run)
