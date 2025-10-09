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

from fissure.utils.plugins.operations import Operation, setup_decorator, run_decorator
from fissure.utils.plugins.operations import get_arguments as get_arguments_base

# add wifi_lib to path and import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from wifi_lib.query_iface import verify_interface, get_channels
from wifi_lib.configure_iface import set_monitor_mode, set_channel
from wifi_lib.oui import OUILookup, get_vendor_common_name

class WifiScanAP(Operation):
    """WiFi AP Scanner
    """
    def __init__(self, dev: str, duration: float = -1, dwell: float = 1, power: float = -100, channels: List[int] | None = None, sensor_node_id: int | str = 0, logger: logging.Logger = logging.getLogger(__name__), alert_callback: callable = None, tak_cot_callback: callable = None) -> None:
        """
        Initialize the Wifi AP Scanner.

        Parameters
        ----------
        dev : str
            Network interface to use for scanning (e.g., 'wlan0').
        duration : float, optional
            Duration of the scan in seconds. Default is -1 for indefinite scanning.
        dwell : float, optional
            Time to spend on each channel in seconds. Default is 1.
        power : float, optional
            Minimum signal strength (in dBm) to consider a device. Default is -100.
        channels : List[int] | None, optional
            List of channels to scan. If None, all available channels will be scanned.
        sensor_node_id : int | str, optional
            The ID of the sensor node, by default 0
        logger : logging.Logger, optional
            Logger instance for logging, by default None
        alert_callback : callable, optional
            Callback function for alerts, by default None
        tak_cot_callback : callable, optional
            Callback function for TAK CoT messages, by default None
        """
        # templated common init
        super().__init__(sensor_node_id=sensor_node_id, logger=logger, alert_callback=alert_callback, tak_cot_callback=tak_cot_callback)

        # developer defined init
        self.dev = dev
        self.duration = float(duration)
        self.dwell = float(dwell)
        self.power = float(power)
        if channels is None or channels == 'None':
            # get available channels
            self.channels = list(get_channels(dev).keys())
        else:
            self.channels = channels

        # verify interface is valid
        verify_interface(self.dev, raise_error=True, logger=self.logger)

        # defined and prepare resources
        resources = get_resources(self.dev)
        super().prepare_resources(resources)

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

    @setup_decorator
    async def setup(self) -> bool:
        """
        Setup the environment to run the operation.

        Returns
        -------
        bool
            True if setup is successful, False otherwise.
        """
        # set monitor mode
        configured = set_monitor_mode(self.dev, raise_error=True, logger=self.logger)
        if not configured:
            self.logger.debug(f"Failed to set monitor mode on interface {self.dev}.")
            self.logger.error("Operation environment setup failed.")
            await self.teardown()
            return False

        # create flag to indicate successful setup
        self._setup_complete = True
        self.logger.info("Operation environment setup complete.")
        return True

    @run_decorator
    async def run(self) -> None:
        """
        Run the operation.
        """
        # run end time
        tend = np.inf if self.duration == -1 else time.time() + self.duration
        while not self._stop:
            for channel in self.channels:
                # yield event loop and check for stop conditions
                await asyncio.sleep(0)
                if self._stop:
                    self.logger.info(f"Stop signal received. Stopping {self.__class__.__name__} channel scan...")
                    break
                if time.time() + self.dwell > tend:
                    # stop scan
                    self.logger.debug("Scan duration reached. Stopping scan...")
                    await self.stop()
                    return

                # set channel
                channel_set = set_channel(self.dev, channel)
                if not channel_set:
                    self.logger.error(f"Failed to set channel {channel} on interface {self.dev}.")
                    return

                # capture
                output = subprocess.run(self.cmd, capture_output=True)
                output = output.stdout.decode('utf-8')
                reader = csv.reader(output.split('\n'),escapechar="\\")
                self._curr_ap = []
                for row in reader:
                    # yield event loop and check for stop conditions
                    await asyncio.sleep(0)
                    if self._stop:
                        self.logger.info(f"Stop signal received. Stopping {self.__class__.__name__} channel scan...")
                        break

                    if len(row) == self.nfields: # populated line
                        # check power
                        power = row[self.fields.get('dbm_antsignal')]
                        power = self.power - 1 if len(power)==0 else int(power.split(',')[0])
                        if power < self.power:
                            continue

                        # get ssid
                        ssid_raw = row[self.fields.get('ssid')]
                        if ssid_raw == '<MISSING>' or ssid_raw == '' or ssid_raw is None:
                            # no ssid
                            ssid = '<MISSING>'
                        else:
                            ssid = ''
                            for i in range(0,len(ssid_raw),2):
                                ssid += chr(int(ssid_raw[i:i+2], 16))

                        # report AP if beacon or association request
                        type_subtype = int(row[self.fields.get('type_subtype')], 16)
                        freq = float(row[self.fields.get('freq')])
                        if type_subtype == 8: # beacon
                            mac_sa = row[self.fields.get('sa')]
                            await self.add_ap(ssid, mac_sa, freq, power)
                        elif type_subtype == 0: # association request
                            mac_da = row[self.fields.get('da')]
                            await self.add_ap(ssid, mac_da, freq, power)

    async def add_ap(self, ssid: str, mac: str, freq: float, power: float) -> None:
        """
        Add the AP to the AP table if not already present and report.

        Parameters
        ----------
        ssid : str
            SSID of the access point.
        mac : str
            MAC address of the access point.
        freq : float
            Frequency of the access point.
        power : float
            Signal power of the access point.
        """
        if mac not in self._curr_ap:
            self._curr_ap.append(mac)
            vendor = self.oui_lookup.match(mac)

            # get vendor plain text
            vendor_plain = get_vendor_common_name(vendor)

            # add to AP table
            self.aps[mac] = {
                'vendor': vendor,
                'vendor_plain': vendor_plain,
                'ssid': ssid,
                'stations': {}
            }

            # send alert
            await self.alert_callback(self.sensor_node_id, self.opid, f'Wifi AP vendor "{vendor}" Detected: SSID={ssid} MAC={mac} FREQ={freq}MHz POWER={power}dBm', logger=self.logger)

            # send tak cot
            await self.tak_cot_callback(self.sensor_node_id, self.opid, uid=ssid, remarks=f'Wifi AP vendor "{vendor}" Detected: SSID={ssid} MAC={mac} FREQ={freq}MHz POWER={power}dBm', lat=True, lon=True, alt=True, time=True, type='a-h-G-E-S', logger=self.logger)

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

def get_arguments(logger: logging.Logger = logging.getLogger(__name__)) -> Dict[str, Any]:
    """Get the arguments required to initialize the operation.

    Parameters
    ----------
    Operation : Operation
        The operation class to inspect.
    logger : logging.Logger, optional
        Logger instance for logging, by default logging.getLogger(__name__)

    Returns
    -------
    Dict[str, Any]
        A dictionary specifying the arguments required to initialize the operation. The keys are argument names, and the values are dictionaries with key, value pairs with keys `default`, `type`, `description`, and `required`. All values are cast to strings to facilitate JSON serialization.
    """
    return get_arguments_base(WifiScanAP, logger)

def main(*args, **kwargs) -> object:
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
    return WifiScanAP(*args, **kwargs)

if __name__ == "__main__":
    """Run the plugin script as a standalone program for testing purposes.
    """
    import traceback

    # set up logging
    logger = logging.getLogger(__file__.split('/')[-1])
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    # create operation instance
    # adjust parameters as needed for testing
    logger.debug("Initializing...")
    op = main(
        dev='wlx00c0cab5f8c9',
        duration=-1,
        dwell=1,
        power=-100,
        channels=None,
        logger=logger
    )
    logger.debug("Running...")

    # run operation
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(op.setup())
        logger.debug("Setup complete.")
        loop.run_until_complete(op.run())
    except Exception as e:
        loop.run_until_complete(op.stop())
        logger.error(f"Error occurred: {e}")
        logger.debug(traceback.format_exc())
    finally:
        loop.run_until_complete(op.teardown())