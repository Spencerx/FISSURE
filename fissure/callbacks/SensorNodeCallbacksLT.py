import binascii
# import fissure.comms
import fissure.utils
import fissure.utils.hardware
from fissure.utils import plugin
import os
import shutil
import subprocess
import threading
import time
import yaml
from concurrent.futures import ThreadPoolExecutor
import asyncio
import zmq
from typing import List
import json
from fissure.comms import MessageFields, MessageTypes, Identifiers


async def recallInfoMeshtasticLT(component: object, tab_index=""):
    """
    Recall default settings from a local yaml file and send only essential fields to HIPRFISR.
    Handles low-throughput mode by sending 'nickname', 'location', and 'notes' together if under a certain size.
    If the total payload exceeds 200 bytes when including 'notes', 'notes' is excluded.
    """
    # Recall Default Settings Saved Locally
    component.logger.info("Recall Info LT")

    filename = os.path.join(fissure.utils.SENSOR_NODE_DIR, "Sensor_Node_Config", "default.yaml")
    with open(filename) as yaml_library_file:
        settings_dict = yaml.load(yaml_library_file, yaml.FullLoader)

    print(settings_dict)
    
    # Extract only the essential fields for low-throughput messaging
    essential_fields = {
        'tab_index': tab_index,
        'nickname': settings_dict.get('Sensor Node', {}).get('nickname', ''),
        'location': settings_dict.get('Sensor Node', {}).get('location', ''),
        'notes': settings_dict.get('Sensor Node', {}).get('notes', '')
    }

    # Prepare the payload including the 'notes' field initially
    payload = {
        'tab_index': essential_fields['tab_index'],
        'nickname': essential_fields['nickname'],
        'location': essential_fields['location'],
        'notes': essential_fields['notes']
    }

    # Estimate the size of the payload with 'notes' and avoid pre-encoding
    payload_size = len(str(payload).encode('utf-8'))

    if payload_size > 200:
        component.logger.warning(f"Payload size exceeds 200 bytes ({payload_size} bytes). Excluding 'notes' field.")
        payload.pop('notes', None)
    else:
        component.logger.info(f"Payload size within limits: {payload_size} bytes.")

    # Send the payload directly as a dictionary
    response_message = {
        MessageFields.SOURCE: component.identifier,
        MessageFields.DESTINATION: Identifiers.HIPRFISR_LT,
        MessageFields.MESSAGE_NAME: "recallInfoMeshtasticReturnLT",
        MessageFields.PARAMETERS: payload,
    }

    await component.hiprfisr_socket.send_msg("Commands", response_message)
    component.logger.info(f"Sent recallInfoMeshtasticReturnLT with payload: {payload}")


async def recallHardwareMeshtasticLT(component: object, sensor_node_id=""):
    """
    Recall default settings from a local yaml file and send only essential fields to HIPRFISR.
    Handles low-throughput mode by sending 'nickname', 'location', and 'notes' together if under a certain size.
    If the total payload exceeds 200 bytes when including 'notes', 'notes' is excluded.
    """
    # Recall Default Settings Saved Locally
    component.logger.info("Recall Settings LT")

    filename = os.path.join(fissure.utils.SENSOR_NODE_DIR, "Sensor_Node_Config", "default.yaml")
    with open(filename) as yaml_library_file:
        settings_dict = yaml.load(yaml_library_file, yaml.FullLoader)

    print(settings_dict)
    
    # Prepare the payload
    payload = {
        'tsi': settings_dict.get('Sensor Node', {}).get('tsi', ''),
        # 'pd': settings_dict.get('Sensor Node', {}).get('pd', ''),
        # 'attack': settings_dict.get('Sensor Node', {}).get('attack', ''),
        # 'iq': settings_dict.get('Sensor Node', {}).get('iq', ''),
        # 'archive': settings_dict.get('Sensor Node', {}).get('archive', '')
    }

    # Estimate the size of the payload with 'notes' and avoid pre-encoding
    payload_size = len(str(payload).encode('utf-8'))

    if payload_size > 200:
        component.logger.warning(f"Payload size exceeds 200 bytes ({payload_size} bytes).")
        # payload.pop('notes', None)
    else:
        component.logger.info(f"Payload size within limits: {payload_size} bytes.")

    # Send the payload directly as a dictionary
    response_message = {
        MessageFields.SOURCE: component.identifier,
        MessageFields.DESTINATION: Identifiers.HIPRFISR_LT,
        MessageFields.MESSAGE_NAME: "recallHardwareMeshtasticReturnLT",
        MessageFields.PARAMETERS: payload,
    }

    await component.hiprfisr_socket.send_msg("Commands", response_message)
    component.logger.info(f"Sent recallHardwareMeshtasticReturnLT with payload: {payload}")


async def recallStatusMeshtasticLT(component: object, tab_index=""):
    """
    Recalls sensor node status.
    """
    # Recall Default Settings Saved Locally
    component.logger.info("Recall Status LT")
    
    # Prepare the payload
    payload = {
        'tab_index': tab_index,
        'status': "test"
    }

    # Send the payload directly as a dictionary
    response_message = {
        MessageFields.SOURCE: component.identifier,
        MessageFields.DESTINATION: Identifiers.HIPRFISR_LT,
        MessageFields.MESSAGE_NAME: "recallStatusMeshtasticReturnLT",
        MessageFields.PARAMETERS: payload,
    }

    await component.hiprfisr_socket.send_msg("Commands", response_message)
    component.logger.info(f"Sent recallStatusMeshtasticReturnLT with payload: {payload}")
