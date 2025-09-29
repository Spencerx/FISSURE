#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""TPMS transmitter
"""
import asyncio
import os
import sys
from typing import Any, Dict
import logging

from fissure.utils.plugins.operations import Operation, setup_decorator, run_decorator
from fissure.utils.plugins.operations import get_arguments as get_arguments_base

# add gr_flowgraphs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gr_flowgraphs.TPMS_FSK_USRPB210_Transmit import TPMS_FSK_USRPB210_Transmit

class TPMSTransmitter(Operation):
    """TPMS Transmitter
    """
    def __init__(self, dev: str = '', sensor_node_id: int | str = 0, logger: logging.Logger = logging.getLogger(__name__), alert_callback: callable = None, tak_cot_callback: callable = None) -> None:
        """
        Parameters
        ----------
        dev : str, optional
            The Ettus USRP serial number, by default '' will use the first available device found
        sensor_node_id : int | str, optional
            The ID of the sensor node, by default 0
        logger : logging.Logger, optional
            Logger instance, by default None
        alert_callback : Callable, optional
            Alert callback function, by default None
        tak_cot_callback : Callable, optional
            TAK CoT callback function, by default None
        """
        super().__init__(sensor_node_id=sensor_node_id, logger=logger, alert_callback=alert_callback, tak_cot_callback=tak_cot_callback)
        self.dev = dev

        # defined and prepare resources
        resources = get_resources(self.dev)
        super().prepare_resources(resources)

    @setup_decorator
    async def setup(self) -> bool:
        """Setup the operation

        Returns
        -------
        bool
            True if setup was successful, False otherwise
        """
        return True
    
    @run_decorator
    async def run(self) -> None:
        """Run the operation
        """
        tb = TPMS_FSK_USRPB210_Transmit()
        try:
            tb.start()
            self.logger.info("TPMS Transmitter started.")
            while not self._stop:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            self.logger.info("TPMS Transmitter stopping...")
        finally:
            tb.stop()
            tb.wait()
            self.logger.info("TPMS Transmitter stopped.")

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
        'usrp': {
            'type': 'sdr',
            'model': 'USRP B2x0',
            'serial': dev,
            'description': 'Ettus USRP B2x0.',
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
    return {}

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
    return get_arguments_base(TPMSTransmitter, logger)

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
    return TPMSTransmitter(*args, **kwargs)