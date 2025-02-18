#!/usr/bin/env python3
"""Wifi Scanner

Scan wifi channels using an 802.11x adapter capable of monitor mode.

For FISSURE database identification, add the following row to the `attacks` table.

"protocol","attack_name","modulation_type","hardware","attack_type","filename","category_name","version"
"802.11x","Scan","Default","802.11x Adapter","Python3 Script","wifi_rx_scan.py","Sniffing/Snooping","maint-3.10"
"""
import sys
import subprocess
import time
import csv
import numpy as np
import json
from datetime import datetime, timezone

DURATION = -1 # to run until interrupted
DWELL = 1 # 1 second per channel
NOTES = 'Scan Wifi channels'

def apply_change(dev:str,commands:list[list[str]]):
    subprocess.run(['sudo','ip','link','set',dev,'down'])
    for command in commands:
        subprocess.run(command)
    subprocess.run(['sudo','ip','link','set',dev,'up'])

def set_monitor_mode(dev:str):
    apply_change(dev,[
        ['sudo','iwconfig',dev,'mode','Monitor']
    ])

def set_freq(dev:str,freq:float):
    apply_change(dev,[
        ['sudo','iwconfig',dev,'freq',str(freq)]
    ])

def set_channel(dev:str,channel:int):
    apply_change(dev,[
        ['sudo','iwconfig',dev,'channel',str(channel)]
    ])

def get_channels(dev:str)->dict:
    output = subprocess.run(['sudo','iwlist','wlx00c0cab6704c','frequency'], capture_output=True)
    output = output.stdout.decode('utf-8')
    output = output.split('\n')
    channels = {}
    for line in output:
        if 'Current' in line:
            continue
        if 'Channel' in line:
            line = line[line.index('Channel')+7:]
            channel = int(line[:line.index(':')])
            frequency = float(line[line.index(':')+1:line.index('GHz')])
            channels[channel] = frequency
    return channels

def scan(dev:str, channels:list[int]=None, duration:int=DURATION, dwell:int=DWELL, power_limit:float=-np.inf):
    """Scan Wifi Channels

    Scan wifi channels using an 802.11x adapter capable of monitor mode.

    For FISSURE database identification, add the following row to the `attacks` table.

    "protocol","attack_name","modulation_type","hardware","attack_type","filename","category_name","version"
    "802.11x","Scan","Default","802.11x Adapter","Python3 Script","wifi_rx_scan.py","Sniffing/Snooping","maint-3.10"

    Parameters
    ----------
    dev : str
        Phy interface name
    channels : list[int], optional
        Channels to scan, by default None to use all channels available to phy
    duration : int, optional
        Duration of scan where -1 is infinite, by default DURATION
    dwell : int, optional
        Dwell time per channel, by default DWELL

    Returns
    -------
    dict
        Detected transmitters where keys are detected transmitter mac addresses and values are the observed values including `timestamp` as time of first observation
    """
    if channels is None:
        # get available channels
        channels = list(get_channels(dev).keys())

    # set monitor mode
    set_monitor_mode(dev)

    # create known transmitter address list
    transmitters = {}

    tend = np.inf if duration == -1 else time.time() + duration
    while True:
        newta = False
        for channel in channels:
            # set channel
            set_channel(dev, channel)

            if time.time() + dwell > tend:
                # stop scan
                return transmitters

            # capture
            output = subprocess.run(['sudo', 'tshark', '-i', dev, '-E', 'separator=,', '-a', 'duration:' + str(dwell), '-Tfields', '-e', 'frame.time_epoch', '-e', 'radiotap.channel.freq', '-e', 'wlan.ta', '-e', 'wlan.ra', '-e', 'radiotap.dbm_antsignal', '-e', 'wlan.ssid'], capture_output=True)
            output = output.stdout.decode('utf-8')
            reader = csv.reader(output.split('\n'),escapechar="\\")
            for row in reader:
                if len(row) == 6:
                    ta = row[2]
                    if len(ta) > 0 and not ta in transmitters.keys():
                        power = int(row[4].split(',')[0])
                        if power > power_limit:
                            newta = True
                            if row[5] == '<MISSING>':
                                ssid = '<MISSING>'
                            else:
                                ssid = ''
                                for i in range(0,len(row[5]),2):
                                    ssid += chr(int(row[5][i:i+2], 16))
                            transmitters[ta] = {
                                'frequency': int(row[1]),
                                'timestamp': float(row[0]),
                                'power': power,
                                'ssid': ssid
                            }
                            taobv = transmitters.get(ta)
                            sys.stdout.write(json.dumps({
                                'msg': 'alert',
                                'text': time.strftime('%Y-%m-%d %H:%M:%S') + ' New Wifi Device: ' + str(ta) + ' frequency=' + str(taobv.get('frequency')) + ' snr=' + str(taobv.get('power')) + ' latitude=%(latitude)f longitude=%(longitude)f altitude=%(altitude)f'
                            }) + '\n')
                            sys.stdout.write(json.dumps({
                                'msg': 'tak',
                                'uid': str(ta),
                                'lat': '%(latitude)f',
                                'lon': '%(longitude)f',
                                'alt': '%(altitude)f',
                                'time': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                                'remarks': 'ssid=' + ssid + ', freq=' + str(taobv.get('frequency')) + ' MHz'
                            }) + '\n')
                            sys.stdout.flush()
                        
        if not newta:
            sys.stdout.write(time.strftime("%Y-%m-%d %H:%M:%S") + ' - No new mac addresses detected in channel scan\n')
            sys.stdout.flush()

def getArguments():
    iface = None
    duration=DURATION
    dwell=DWELL
    power = -100
    channels = None
    notes = NOTES

    return (
        ['iface', 'duration', 'dwell', 'power', 'channels', 'notes'],
        [iface, duration, dwell, power, channels, notes]
    )

if __name__ == '__main__':
    # get default values
    (iface, duration, dwell, power, channels, notes) = getArguments()[1]

    # handle input
    nargs = len(sys.argv)
    iface = sys.argv[1] if nargs > 1 else iface
    duration = int(sys.argv[2]) if nargs > 2 else duration
    dwell = int(sys.argv[3]) if nargs > 3 else dwell
    power = int(sys.argv[4]) if nargs > 4 else power
    channels = sys.argv[5] if nargs > 5 else channels
    channels = None if channels in [None, 'None'] else [int(c) for c in channels.split(',')]

    # run
    scan(iface, channels, duration, dwell, power)