#! /usr/bin/env python3
"""Example Plugin Script
This script serves as an example of how to create a plugin script for FISSURE. The script can directly implement functionality or wrap existing code.
"""
import asyncio
import os
from typing import List, Dict, Any
import uuid

from fissure.Sensor_Node.utils.resources import Resource

# Optional: Define default values for arguments
EXAMPLE_ARG = "default_value"
EXAMPLE_ARG2 = 42
EXAMPLE_ARG3 = [1, 2, 3]

class PluginExample(object):
    """
    Example plugin script class

    This class can be modified to implement specific functionality for the plugin.
    """
    def __init__(self, example_arg: str = EXAMPLE_ARG, example_arg2: int = EXAMPLE_ARG2, example_arg3: List[int] = EXAMPLE_ARG3) -> None:
        """
        Initialize the plugin with given keyword arguments.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments for the plugin script.
        """
        self.opid = str(uuid.uuid4())  # Generate a unique operation ID
        self.example_arg = example_arg
        self.example_arg2 = example_arg2
        self.example_arg3 = example_arg3
        self._stop = False
        self.running = False

    async def run(self) -> None:
        """
        Run the plugin functionality.

        This method must be modified to implement specific functionality for the plugin.
        """
        # Allocate resources if needed
        self.resource = [
            Resource.request_resource(
                pid=os.getpid(),
                op_uuid=self.opid,
                type='example',
                model='example_model',
                serial='example_serial'
            )
        ]

        self.running = True
        counter = 0
        while not self._stop:
            # Plugin logic goes here
            print(f"{counter:<2} Example Plugin is running...")
            print("\texample_arg:", self.example_arg)
            print("\texample_arg2:", self.example_arg2)
            print("\texample_arg3:", self.example_arg3)
            await asyncio.sleep(1)  # Simulate work being done
            counter += 1
        self.running = False

    async def stop(self) -> None:
        """
        Stop the plugin functionality.

        This method must be modified to implement specific stop functionality for the plugin.
        """
        print("Stopping Example Plugin.")
        self._stop = True

        # Release resources
        if hasattr(self, 'resource'):
            for res in self.resource:
                res.release()

def main(**kwargs) -> object:
    """
    Main function to run the example plugin script.

    This function can be called when the plugin script is executed.

    Parameters
    ----------
    **kwargs : dict
        Keyword arguments for variables in the plugin script.

    Returns
    -------
    object
        An instance of the PluginExample class with the provided arguments.
    """
    print(f"Initializing Example Plugin with arguments: {kwargs}")
    example_plugin = PluginExample(**kwargs)
    return example_plugin

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
        'example_arg': {
            'default': EXAMPLE_ARG,
            'type': str,
            'help': 'This is an example argument for the plugin script.',
            'required': True,
            'choices': ['option1', 'option2', 'default_value'],
        },
        'example_arg2': {
            'default': EXAMPLE_ARG2,
            'type': int,
            'help': 'This is another example argument for the plugin script.',
            'required': False,
        },
        'example_arg3': {
            'default': EXAMPLE_ARG3,
            'type': List[int],
            'help': 'This is a list argument for the plugin script. Using Typing for type hinting.',
            'required': False,
            'nargs': '*', # use regex quanitifiers, e.g. '*', '+', '?', or dict {'min': 1, 'max': 3}
        },
    }

def get_resources() -> Dict[str, Any]:
    """
    Get the resources required by the plugin script.

    This function should be modified to return specific resources required by the plugin script. If no resrources are needed, it can return an empty dictionary.

    Returns
    -------
    Dict[str, Any]
        A dictionary containing the resources for the plugin script.
    """
    # Example resources, modify as needed
    return {
        'example_sdr': {
            'type': 'example',
            'model': 'example_model',
            'serial': 'example_serial',
            'description': 'This is an example resource for the plugin script with a specific model and serial number.',
            'required': True
        }
    }