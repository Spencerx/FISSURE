#!/usr/bin/env python3
"""TPMS Capture

Capture TPMS using rtl_433 and RTL2832U

For FISSURE database identification, add the following row to the `attacks` table.

"protocol","attack_name","modulation_type","hardware","attack_type","filename","category_name","version"
"TPMS","Receive","FSK","RTL2832U","Python3 Script","TPMS_RTLSDR_Receive.py","Sniffing/Snooping","maint-3.10"

Returns
-------
_type_
    _description_
"""
import sys
import socket
import time
import json
import subprocess
from multiprocessing import Process
from datetime import datetime, timezone

DEVICE = 0 # device index
FREQUENCY = 315e6 # or 433e6
GAIN = 49 # rx gain
NOTES = 'Use rtl_433 to capture TPMS messages'

def main(device: int=DEVICE, frequency: float=FREQUENCY, gain: float=GAIN):
    # launch tpms receiver
    cmd = ['rtl_433', '-d', '%d'%device, '-M', 'level', '-f', '%d'%frequency, '-g', '%d'%gain, '-v', '-F', 'syslog:127.0.0.1:1514']
    p = Process(target=subprocess.run, args=(' '.join(cmd),), kwargs={'shell': True})
    p.start()
    time.sleep(1) # let rtl_433 start

    # create message parser
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.bind(('localhost', 1514))
        while True:
            time.sleep(0.1)
            data = client_socket.recvfrom(512)
            data = data[0].decode('utf-8')
            data = json.loads(data[data.index('rtl_433 - - - {') + 14:])
            sys.stdout.write(json.dumps({
                'msg': 'tak',
                'uid': data.get('id'),
                'lat': '%(latitude)f',
                'lon': '%(longitude)f',
                'alt': '%(altitude)f',
                'time': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%fZ'),
                'remarks': json.dumps({
                    'type': data.get('type'),
                    'model': data.get('model'),
                    'status': data.get('status'),
                    'pressure_PSI': data.get('pressure_PSI'),
                    'temperature_C': data.get('temperature_C'),
                    'mic': data.get('mic'),
                    'mod': data.get('mod'),
                    'freq1': data.get('freq1'),
                    'freq2': data.get('freq2'),
                    'rssi': data.get('rssi'),
                    'snr': data.get('snr'),
                    'noise': data.get('noise'),
                })
            }) + '\n')
            sys.stdout.flush()
    except Exception as e:
        print('ERROR:' + e)
        client_socket.close()
        p.terminate()

def getArguments():
    device = DEVICE
    frequency = FREQUENCY
    gain = GAIN
    notes = NOTES

    return (
        ['device', 'frequency', 'gain', 'notes'],
        [device, frequency, gain, notes]
    )

if __name__ == '__main__':
    # get default values
    (device, frequency, gain, notes) = getArguments()[1]

    # handle input
    nargs = len(sys.argv)
    device = float(sys.argv[1]) if nargs > 1 else device
    frequency = float(sys.argv[2]) if nargs > 2 else frequency
    gain = float(sys.argv[3]) if nargs > 3 else gain

    # run
    main(device, frequency, gain)