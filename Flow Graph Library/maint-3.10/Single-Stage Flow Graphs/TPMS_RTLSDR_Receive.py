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

FREQUENCY = 315e6 # or 433e6
GAIN = 49
NOTES = 'Use rtl_433 to capture TPMS messages'

def main(frequency: float=FREQUENCY, gain: float=GAIN):
    # launch tpms receiver
    p = Process(target=subprocess.run, args=(['rtl_433', '-M', 'level', '-f', '%d'%frequency, '-g', '%d'%gain, '-F', 'syslog:127.0.0.1:1514'],), kwargs={'shell': True})
    p.start()
    time.sleep(1) # let rtl_433 start

    # create message parser
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.bind(('localhost', 1514))
        while True:
            time.sleep(0.1)
            data = client_socket.recvfrom(512)
            print(data)
            data = data[0].decode('utf-8')
            data = json.loads(data[data.index('rtl_433 - - - {') + 14:])
            print('DATA:' + str(data))
            #sys.stdout.write(data.get('type') + ', ID=' + data.get('id') + ', snr=' + data.get('snr') + ', model=' + data.get('model'))
            sys.stdout.write(json.dumps({
                'msg': 'alert',
                'text': time.strftime('%Y-%m-%d %H:%M:%S') + ' TPMS: id=' + data.get('id') + ' snr=' + str(data.get('snr')) + ' latitude=%(latitude)f longitude=%(longitude)f altitude=%(altitude)f'
            }) + '\n')
            sys.stdout.write(json.dumps({
                'msg': 'tak',
                'uid': data.get('id'),
                'lat': '%(latitude)f',
                'lon': '%(longitude)f',
                'alt': '%(altitude)f',
                'time': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%fZ'),
                'remarks': 'model=' + data.get('model')
            }) + '\n')
            sys.stdout.flush()
    except Exception as e:
        print(e)
        client_socket.close()
        p.terminate()

def getArguments():
    frequency = FREQUENCY
    gain = GAIN
    notes = NOTES

    return (
        ['frequency', 'gain', 'notes'],
        [frequency, gain, notes]
    )

if __name__ == '__main__':
    # get default values
    (frequency, gain, notes) = getArguments()[1]

    # handle input
    nargs = len(sys.argv)
    frequency = float(sys.argv[1]) if nargs > 1 else frequency
    gain = float(sys.argv[2]) if nargs > 2 else gain
    notes = sys.argv[3] if nargs > 3 else notes

    print(frequency)
    print(gain)
    print(notes)

    # run
    main(frequency, gain)