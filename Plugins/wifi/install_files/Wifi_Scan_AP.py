#!/usr/bin/env python3
"""Wifi Access Point Scanner

Scan wifi channels using an 802.11x adapter capable of monitor mode. Report if an access point (AP) is found.

References:

- [1] https://community.cisco.com/t5/wireless-mobility-knowledge-base/802-11-frames-a-starter-guide-to-learn-wireless-sniffer-traces/ta-p/3110019
"""
import asyncio
import csv
import logging
import numpy as np
import os
import sys
import subprocess
import time
from typing import List, Dict, Any
import uuid

from fissure.Sensor_Node.utils.resources import Resource

# add wifi_lib to path and import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from wifi_lib.query_iface import verify_interface, get_channels
from wifi_lib.configure_iface import set_monitor_mode, set_channel
from wifi_lib.oui import OUILookup

# vendor plain text (reduced from variants)
# (search term, plain output)
VENDOR_PLAIN = [
    ('d-link', 'd-link'),
    ('tp-link', 'tp-link')
]

class WifiScanAP(object):
    """Find WiFi APs.
    """
    def __init__(self, dev: str = None, duration: float = -1, dwell: float = 1, power: float = -100, channels: List[int] | None = None, sensor_node_id: int | str = 0, logger: logging.Logger = None, alert_callback: callable = None, tak_cot_callback: callable = None) -> None:
        """
        Initialize the Wifi AP Scanner.

        Parameters
        ----------
        dev : str
            Network interface to use for scanning (e.g., 'wlan0').
        duration : float
            Duration of the scan in seconds. Use -1 for indefinite scanning.
        dwell : float
            Time to spend on each channel in seconds.
        power : float
            Minimum signal strength (in dBm) to consider a device.
        channels : List[int] | None
            List of channels to scan. If None, all available channels will be scanned.
        sensor_node_id : int | str
            Identifier for the sensor node.
        logger : logging.Logger
            Logger instance for logging messages.
        alert_callback : callable
            Callback function for sending alerts.
        tak_cot_callback : callable
            Callback function for sending TAK CoT messages.
        """
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        self.sensor_node_id = sensor_node_id
        self.alert_callback = alert_callback
        self.tak_cot_callback = tak_cot_callback
        self.opid = str(uuid.uuid4())  # Generate a unique operation ID
        self.dev = dev
        self.duration = float(duration)
        self.dwell = float(dwell)
        self.power = float(power)
        self._setup_complete = False
        self._stop = False
        self._running = None # Use None to indicate that the operation has not started yet

        if channels is None or channels == 'None':
            # get available channels
            self.channels = list(get_channels(dev).keys())
        else:
            self.channels = channels

        # get details from the interface
        if self.dev is None:
            self.logger.error("No network interface specified for Wifi Exploit Finder.")
            raise ValueError("Network interface must be specified.")
        
        # verify interface is valid
        verify_interface(self.dev, raise_error=True, logger=self.logger)

        # define resources
        self.logger.info("Defining resources for Wifi Exploit Finder...")
        pid = os.getpid()  # Get the current process ID
        self.logger.info(f"Process ID: {pid}")
        resources = get_resources(self.dev)
        self.logger.info(f"Resources defined: {resources}")
        self.resources = [
            Resource(
                pid=pid,
                op_uuid=self.opid,
                type=res_info.get('type'),
                model=res_info.get('model'),
                serial=res_info.get('serial'),
                logger=self.logger
            )
        for res_name, res_info in resources.items()]

        self.aps = {} # AP table

        # build tshark command
        self.fields_ordered = [
            'frame.time_epoch',
            'radiotap.channel.freq',
            'wlan.sa',
            'wlan.ta',
            'wlan.ra',
            'wlan.da',
            'radiotap.dbm_antsignal',
            'wlan.ssid',
            'wlan.fc.type_subtype'
        ]
        self.nfields = len(self.fields_ordered)
        self.fields = {field.split('.')[-1]: i for (i, field) in enumerate(self.fields_ordered)}
        self.cmd = ['sudo', 'tshark', '-i', dev, '-E', 'separator=,', '-E', 'occurrence=f', '-a', 'duration:' + str(dwell), '-Tfields']
        for field in self.fields_ordered:
            self.cmd += ['-e', field]

        # initialize oui lookup
        self.oui_lookup = OUILookup()

    def __repr__(self):
        return f"WifiScanAP(dev={self.dev}, duration={self.duration}, dwell={self.dwell}, power={self.power}, channels={self.channels})"

    async def setup(self) -> None:
        """
        Setup the environment for the operation.
        """
        self.logger.info("Setting up operation environment...")

        self._resources = [] # track resources that were successfully allocated
        for res in self.resources:
            if not res.allocated:
                if not res.allocate():
                    self.logger.error(f"Failed to allocate resource: {res}")
                    await self.teardown()
                    return False
                self._resources.append(res)
                self.logger.info(f"Allocated resource: {res}")
        self.logger.info("Operation environment setup complete.")

        # set monitor mode
        configured = set_monitor_mode(self.dev, raise_error=True, logger=self.logger)
        
        if not configured:
            self.logger.error(f"Failed to set monitor mode on interface {self.dev}.")
            await self.teardown()
            return False
        self.logger.info(f"Interface {self.dev} set to monitor mode.")

        # create flag to indicate successful setup
        self._setup_complete = True
        return True

    async def teardown(self) -> None:
        """
        Teardown the environment for the operation.
        """
        self.logger.info("Tearing down operation environment...")

        self._setup_complete = False

        if hasattr(self, '_resources'):
            self.logger.info(f"Releasing {len(self._resources)} resources for Wifi Exploit Finder...")
            while len(self._resources) > 0:
                res = self._resources.pop()
                self.logger.info(f"Releasing resource: {res}")
                res.release()

        self.logger.info("Operation environment teardown complete.")

    async def run(self) -> None:
        """
        Run the wifi exploit finder.
        """
        if not self._setup_complete:
            self.logger.error("Operation environment not set up. Call setup() before run().")
            return
        
        self.logger.info("Wifi Exploit Finder started.")
        self._running = True
        tend = np.inf if self.duration == -1 else time.time() + self.duration
        while not self._stop:
            for channel in self.channels:
                await asyncio.sleep(0.01) # yield to event loop
                if self._stop:
                    self.logger.info("Stop signal received. Stopping Wifi Exploit Finder channel scan...")
                    break

                # set channel
                channel_set = set_channel(self.dev, channel)

                if not channel_set:
                    self.logger.error(f"Failed to set channel {channel} on interface {self.dev}.")
                    continue

                if time.time() + self.dwell > tend:
                    # stop scan
                    return
                
                # capture
                output = subprocess.run(self.cmd, capture_output=True)
                output = output.stdout.decode('utf-8')
                reader = csv.reader(output.split('\n'),escapechar="\\")
                self._curr_ap = []
                for row in reader:
                    await asyncio.sleep(0.01) # yield to event loop
                    if len(row) == self.nfields: # populated line
                        power = row[self.fields.get('dbm_antsignal')]
                        power = self.power - 1 if len(power)==0 else int(power.split(',')[0])
                        if power < self.power:
                            continue

                        mac_sa = row[self.fields.get('sa')]
                        mac_da = row[self.fields.get('da')]
                        freq = float(row[self.fields.get('freq')])

                        type_subtype = int(row[self.fields.get('type_subtype')], 16)
                        if type_subtype == 8: # beacon
                            await self.add_ap(mac_sa, freq, row)

                        elif type_subtype == 0: # association request
                            await self.add_ap(mac_da, freq, row)

        self.logger.info("Wifi Exploit Finder stopped.")
        self._running = False

    def running(self) -> bool:
        """
        Check if the wifi exploit finder is running.

        Returns
        -------
        bool
            True if the wifi exploit finder is running, False otherwise.
        """
        return self._running

    async def stop(self) -> None:
        """
        Stop the wifi exploit finder.
        """
        self.logger.info("Stopping Wifi Exploit Finder...")
        self._stop = True
        while self._running:
            await asyncio.sleep(1)
            self.logger.info("Waiting for Wifi Exploit Finder to stop...")
        self.logger.info("Wifi Exploit Finder stopped.")

    async def add_ap(self, mac: str, freq: float, row: List[str]) -> None:
        """
        Add an access point if it matches the exploit criteria.

        Parameters
        ----------
        mac : str
            MAC address of the access point.
        freq : float
            Frequency of the access point.
        row : List[str]
            Row of data from tshark output.
        """
        if mac not in self._curr_ap:
            self._curr_ap.append(mac)
            vendor = self.oui_lookup.match(mac)
            
            # get ssid
            ssid_raw = row[self.fields.get('ssid')]
            if ssid_raw == '<MISSING>' or ssid_raw == '' or ssid_raw == None:
                # no ssid
                ssid = '<MISSING>'
            else:
                ssid = ''
                for i in range(0,len(ssid_raw),2):
                    ssid += chr(int(ssid_raw[i:i+2], 16))

            # get vendor plain text
            vendor_plain = None
            for vplain in VENDOR_PLAIN:
                if vendor is not None and vplain[0] in vendor.lower():
                    vendor_plain = vplain[1]

            # add to AP table
            self.aps[mac] = {
                'vendor': vendor,
                'vendor_plain': vendor_plain,
                'ssid': ssid,
                'stations': {}
            }

            await self.alert_callback(self.sensor_node_id, self.opid, f'{vendor_plain} Wifi AP Detected: SSID={ssid} MAC={mac}')

            await self.tak_cot_callback(self.sensor_node_id, self.opid, uid=ssid, remarks=f'Exploitable {vendor_plain} Wifi AP Detected', lat=True, lon=True, alt=True, time=True, type='a-h-G-E-S')

def get_arguments() -> dict:
    """
    Get the arguments for the plugin script.

    This function should be modified to return specific arguments required by the plugin script.

    Returns
    -------
    dict
        A dictionary containing the arguments for the plugin script.
    """
    return {
        'dev': {
            'default': None,
            'type': str,
            'description': 'Network interface to use for scanning (e.g., "wlan0").',
            'required': True,
        },
        'duration': {
            'default': -1,
            'type': int,
            'description': 'Duration of the scan in seconds. Use -1 for indefinite scanning.',
            'required': False,
        },
        'dwell': {
            'default': 1,
            'type': int,
            'description': 'Time to spend on each channel in seconds.',
            'required': False,
        },
        'power': {
            'default': -100,
            'type': float,
            'description': 'Minimum signal strength (in dBm) to consider a device.',
            'required': False,
        },
        'channels': {
            'default': None,
            'type': List[int],
            'description': 'List of channels to scan. If None, all available channels will be scanned.',
            'required': False,
            'nargs': '*', # use regex quanitifiers, e.g. '*', '+', '?', or dict {'min': 1, 'max': 3}
        }
    }

def get_resources(dev: str = '') -> Dict[str, Any]:
    """
    Get the resources required by the plugin script.

    Parameters
    ----------
    dev : str
        The network device name (e.g., 'wlan0').

    Returns
    -------
    Dict[str, Any]
        A dictionary containing the resources for the plugin script.
    """
    return {
        'wifi_interface': {
            'type': 'wifi_adapter',
            'model': '',
            'serial': dev,
            'description': 'A wifi adapter capable of operating in monitor mode.',
            'required': True
        }
    }

def get_interfaces() -> Dict[str, Any]:
    """
    Get the interfaces available for the plugin script.

    Returns
    -------
    Dict[str, Any]
        A dictionary containing the interfaces for the plugin script.
    """
    return {
        'alert': {
            'type': 'alert',
            'channel': 'fissure', # FISSURE zmq
            'direction': 'out',
            'description': 'Wifi AP detections.'
        },
        'tak': {
            'type': 'tak',
            'channel': 'fissure', # FISSURE zmq
            'direction': 'out',
            'description': 'Wifi AP detections in TAK CoT format.'
        }
    }

def main(**kwargs) -> object:
    """
    Main function to run the plugin script.

    Parameters
    ----------
    **kwargs : dict
        Keyword arguments for variables in WifiScanAP.

    Returns
    -------
    object
        An instance of the WifiScanAP class with the provided arguments.
    """
    operation = WifiScanAP(**kwargs)
    return operation