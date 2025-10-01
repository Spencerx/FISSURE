#! /usr/bin/env python3
"""Plugin Operations Related Functionality
"""
import asyncio
import inspect
from inspect import signature, _empty
import logging
import os
import uuid
import re
import sys
from typing import Dict, Any

from fissure.Sensor_Node.utils.resources import Resource

_base_params = ['self', 'sensor_node_id', 'logger', 'alert_callback', 'tak_cot_callback']

def setup_decorator(func):
    async def wrapper(self, *args, **kwargs) -> bool:
        self.logger.info("Setting up operation environment...")

        # allocate resources
        self._resources = [] # track resources that were successfully allocated
        for res in self.resources:
            if not res.allocated:
                if not res.allocate():
                    self.logger.error(f"Failed to allocate resource: {res}")
                    self.logger.info("Operation environment setup failed.")
                    await self.teardown()
                    return False
                self._resources.append(res)
                self.logger.info(f"Allocated resource: {res}")

        # call the decorated setup function
        status = await func(self, *args, **kwargs)

        if not status:
            self.logger.info("Operation environment setup failed.")
            await self.teardown()
            return False
        
        # create flag to indicate successful setup
        self._setup_complete = True
        self.logger.info("Operation environment setup complete.")
        return True
    return wrapper

def run_decorator(func):
    async def wrapper(self, *args, **kwargs) -> None:
        if not self._setup_complete:
            self.logger.error("Operation environment not set up. Call setup() before run().")
            return
        self._running = True
        try:
            self.logger.info(f"Running operation {self.__class__.__name__}...")
            await func(self, *args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error during operation run: {e}")
        self.logger.info(f"Operation {self.__class__.__name__} run complete.")
        self._running = False
        return
    return wrapper

def stop_decorator(func):
    async def wrapper(self, *args, **kwargs) -> None:
        self.logger.info(f"Stopping {self.__class__.__name__}...")
        self._stop = True
        while self.running():
            await asyncio.sleep(0.1)
            self.logger.debug(f"Waiting for {self.__class__.__name__} to stop...")
        await func(self, *args, **kwargs)
        self.logger.info(f"{self.__class__.__name__} stopped.")
    return wrapper

def teardown_decorator(func):
    async def wrapper(self, *args, **kwargs) -> None:
        self.logger.info(f"Tearing down operation environment for {self.__class__.__name__}...")

        self._setup_complete = False

        await func(self, *args, **kwargs)

        if hasattr(self, '_resources'):
            self.logger.debug(f"Releasing {len(self._resources)} resources for {self.__class__.__name__}...")
            while len(self._resources) > 0:
                try:
                    res = self._resources.pop()
                    self.logger.debug(f"Releasing resource: {res}")
                    res.release()
                except Exception as e:
                    self.logger.error(f"Error releasing resource {res}: {e}")

        self.logger.info(f"Operation environment teardown complete for {self.__class__.__name__}.")
    return wrapper

async def send_alert(sensor_node_id: int | str, opid: str, message: str, logger=logging.getLogger(__name__)) -> None:
    """Placeholder for alert callback if none is provided.

    Parameters
    ----------
    sensor_node_id : int | str
        The sensor node ID
    opid : str
        The operation ID
    message : str
        The alert message.
    """
    logger.info(f"Alert {sensor_node_id}, {opid}: {message}")

async def send_tak_cot(sensor_node_id: int | str, opid: str, uid: str, remarks: str, lat: float | bool = True, lon: float | bool = True, alt: float | bool = True, time: float | bool = True, type: str="a-f-G-U-H", logger=logging.getLogger(__name__)) -> None:
    """Placeholder for TAK CoT callback if none is provided.

    Parameters
    ----------
    sensor_node_id : int | str
        The sensor node ID
    opid : str
        The operation ID
    uid : str
        The unique ID
    remarks : str
        The remarks
    lat : float | bool, optional
        The latitude, by default True
    lon : float | bool, optional
        The longitude, by default True
    alt : float | bool, optional
        The altitude, by default True
    time : float | bool, optional
        The time, by default True
    type : str, optional
        The type, by default "a-f-G-U-H"
    """
    logger.info(f"TAK CoT {sensor_node_id}, {opid}: uid={uid}, lat={lat}, lon={lon}, alt={alt}, time={time}, type={type}, remarks={remarks}")

class Operation(object):
    """Base class for plugin operations.
    """
    def __init__(self, sensor_node_id: int | str = 0, logger: logging.Logger = logging.getLogger(__name__), alert_callback: callable = None, tak_cot_callback: callable = None) -> None:
        """Initialize the Operation class.

        Parameters
        ----------
        sensor_node_id : int | str, optional
            The ID of the sensor node, by default 0
        logger : logging.Logger, optional
            Logger instance for logging, by default logging.getLogger(__name__)
        alert_callback : callable, optional
            Callback function for alerts, by default None
        tak_cot_callback : callable, optional
            Callback function for TAK CoT messages, by default None
        """
        # input parameters
        self.sensor_node_id = sensor_node_id
        self.logger = logger
        if alert_callback is None:
            alert_callback = send_alert
        if tak_cot_callback is None:
            tak_cot_callback = send_tak_cot
        self.alert_callback = alert_callback
        self.tak_cot_callback = tak_cot_callback

        # operation ID
        self.opid = str(uuid.uuid4())  # Generate a unique operation ID

        # status tracking
        self._setup_complete = False
        self._stop = False
        self._running = None # Use None to indicate that the operation has not started yet

        self.logger.debug(f"Initialized operation {self.__class__.__name__} with sensor_node_id={self.sensor_node_id}, opid={self.opid}")

    def __repr__(self):
        sig = inspect.signature(self.__init__)
        params = list(sig.parameters.keys())
        for p in _base_params:
            if p in params:
                params.remove(p)
        return f"{self.__class__.__name__}(sensor_node_id={self.sensor_node_id}" + ''.join([f", {p}={getattr(self, p)}" for p in params]) + ")"
    
    def prepare_resources(self, resources: Dict[str, Any]) -> None:
        """Prepare resources for the operation.

        This method can be overridden by subclasses to implement specific resource preparation logic.

        Parameters
        ----------
        resources : Dict[str, Any]
            A dictionary of resources to prepare.
        """
        self.logger.info(f"Resources defined: {resources}")
        self.resources = [
            Resource(
                pid=os.getpid(),
                op_uuid=self.opid,
                type=res_info.get('type'),
                model=res_info.get('model'),
                serial=res_info.get('serial'),
                logger=self.logger
            )
        for _, res_info in resources.items()]

    @setup_decorator
    async def setup(self) -> None:
        """
        Setup the environment to run the operation.

        Setup includes allocating resources for use by the operation. The developer can override this method to implement additional setup to prepare for running the operation.
        """
        return True

    @run_decorator
    async def run(self) -> None:
        """
        Run the operation.

        This method should be overridden by subclasses to implement the main functionality of the operation. If the operation includes loops,
        
        - the method should periodically check the `self._stop` flag to determine if it should exit gracefully
        - the method should call `await asyncio.sleep(0)` within loops to allow for cooperative multitasking
        """
        self.logger.error("The run() method must be implemented by the subclass.")

    def running(self) -> bool:
        """
        Check if operation is running.

        Returns
        -------
        bool
            True if the operation is running, False otherwise.
        """
        return self._running

    @stop_decorator
    async def stop(self) -> None:
        """
        Stop the operation.
        """
        return

    @teardown_decorator
    async def teardown(self) -> None:
        """
        Teardown the environment for the operation.
        """
        return

def get_arguments(Operation: Operation, logger: logging.Logger = logging.getLogger(__name__)) -> Dict[str, Any]:
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
    # Get the argument types of Operation.__init__ method
    sig = signature(Operation.__init__)
    input_types = {k: v.annotation for k, v in sig.parameters.items() if k != 'self'}

    # Get default values of Operation.__init__ parameters
    sig = signature(Operation.__init__)
    defaults = {}
    for name, param in sig.parameters.items():
        if name == 'self':
            continue
        if param.default is not _empty:
            defaults[name] = param.default
        else:
            defaults[name] = ''

    # Load the docstring
    docstring = Operation.__init__.__doc__
    params = {}
    if not docstring:
        logger.error("No docstring found.")
        sys.exit(0)

    # Find the Parameters section
    param_section = re.search(r'Parameters\s*-+\s*(.*?)(?=\n\S|\Z)', docstring, re.DOTALL)
    if not param_section:
        logger.error("No Parameters section found in docstring. Use numpy style docstring format.")
        sys.exit(0) 

    # Split by parameter blocks
    param_blocks = re.split(r'\n(?=\s*\w+\s*:\s*)', param_section.group(1))
    params = {}
    for block in param_blocks:
        # split the parameter lines
        lines = block.strip().split('\n')
        if not lines or ':' not in lines[0]:
            continue

        # First line: param : type, optional
        first = lines[0]
        name_type_optional = first.split(':', 1)
        name = name_type_optional[0].strip()
        if name in _base_params:
            continue
        type_optional = name_type_optional[1].strip().split(',', 1)
        if len(type_optional) == 1:
            required = True
        else:
            required = 'optional' not in type_optional[1].strip().lower()

        # get the description
        desc = ' '.join(line.strip() for line in lines[1:]).strip()

        # add to params
        params[name] = {
            'default': defaults.get(name, None),
            'type': input_types.get(name, str),
            'description': desc,
            'required': required
        }

    return params

def get_resources() -> Dict[str, Any]:
    """Get the resources required for the operation.

    This function should be implemented in the plugin operation module to specify the resources required for the operation.

    Returns
    -------
    Dict[str, Any]
        A dictionary specifying the resources required for the operation. The keys are resource names, and the values are dictionaries with key, value pairs (`type`, str), (`model`, str), (`serial`, str), (`description`, str), and (`required`, bool).
    """
    return {}

def get_interfaces() -> Dict[str, Any]:
    """Get the interfaces required for the operation.

    This function should be implemented in the plugin operation module to specify the interfaces required for the operation.

    Common interface types include:

    'alert': {
        'type': 'alert',
        'channel': 'fissure', # FISSURE zmq
        'direction': 'out',
        'description': 'Wifi AP detections.'
    }

    'tak': {
        'type': 'tak',
        'channel': 'fissure', # FISSURE zmq
        'direction': 'out',
        'description': 'Wifi AP detections in TAK CoT format.'
    }

    Returns
    -------
    Dict[str, Any]
        A dictionary specifying the interfaces required for the operation. The keys are interface names, and the values are dictionaries with key, value pairs (`type`, str), (`channel`, str), (`direction`, str), and (`description`, str).
    """
    return {}

def main(*args, **kwargs) -> object:
    """Create an instance of the operation class.

    This function must be implemented in the plugin operation module to create and return an instance of the operation class.

    The function contents consist of a single line that creates an instance of the operation class with the provided keyword arguments and returns it, e.g.:

        return Operation(**kwargs)

    Parameters
    ----------
    **kwargs : dict
        Keyword arguments to pass to the operation class constructor.

    Returns
    -------
    object
        An instance of the operation class.
    """
    kwargs["logger"].error("The main() function must be implemented in the plugin operation module to return an instance of the operation class.")
    return None