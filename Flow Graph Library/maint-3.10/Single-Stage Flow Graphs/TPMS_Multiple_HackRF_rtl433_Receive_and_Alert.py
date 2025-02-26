#!/usr/bin/env python3
"""TPMS Capture
Capture TPMS using rtl_433 and RTL2832U
For FISSURE database identification, add the following row to the `attacks` table.
"protocol","attack_name","modulation_type","hardware","attack_type","filename","category_name","version"
"TPMS","Receive","FSK","RTL2832U","Python3 Script","TPMS_HackRF_Receive.py","Sniffing/Snooping","maint-3.10"
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

FREQUENCY = 315e6  # or 433920000 or 433e6 
GAIN = 76
SAMP_RATE = 1e6 #250000 #1000000
NOTES = 'Use rtl_433 to capture TPMS messages'

def main(frequency: float=FREQUENCY, gain: float=GAIN):
    # launch tpms receiver
    args = 'rtl_433 -d driver=hackrf -M level -t "antenna=TX/RX" -s {} -f {} -g {} -Y minsnr=1.0 -F syslog:127.0.0.1:1514'.format(SAMP_RATE, frequency, gain)
    p = Process(target=subprocess.run, args=(args,), kwargs={'shell': True})
    p.start()
    time.sleep(1) # let rtl_433 start

    # create message parser
    try:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.bind(('localhost', 1514))
        except OSError as e:
            if 'Errno 98' in str(e): # address already in use
                subprocess.run(['fuser', '-k', '1514/udp']) # kill as user
                try:
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    client_socket.bind(('localhost', 1514))
                except OSError as e:
                    if 'Errno 98' in str(e): # address already in use
                        subprocess.run(['sudo', 'fuser', '-k', '1514/udp']) # kill as sudo
                        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        client_socket.bind(('localhost', 1514))
                    else:
                        raise OSError(e)
            else:
                raise OSError(e)
        while True:
            time.sleep(0.1)
            data = client_socket.recvfrom(512)
            data = data[0].decode('utf-8')
            data = json.loads(data[data.index('rtl_433 - - - {') + 14:])
            #print('DATA:' + str(data) + "\n")
            #sys.stdout.write(data.get('type') + ', ID=' + data.get('id') + ', snr=' + data.get('snr') + ', model=' + data.get('model'))
            if 'id' in data.keys():
                id = data.pop('id')
                if 'pressure_PSI' in data.keys():
                    sys.stdout.write(json.dumps({
                        'msg': 'alert',
                        'text': f"TPMS id={id} PSI={data.get('pressure_PSI')}",
                    }) + '\n')
                    sys.stdout.flush()
            else:
                id = ''
            if 'time' in data.keys():
                _ = data.pop('time')
            sys.stdout.write(json.dumps({
                'msg': 'tak',
                'uid': id,
                'lat': '%(latitude)f',
                'lon': '%(longitude)f',
                'alt': '%(altitude)f',
                'time': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                'remarks': json.dumps(data, separators=(',', ':'))
            }) + '\n')
            sys.stdout.flush()
    finally:
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

    # run
    main(frequency, gain)