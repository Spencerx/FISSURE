# from comms.FissureZMQNode import *
# from fissure.comms.constants import *
# from fissure_libutils import *
from typing import List

import binascii
import fissure.comms
import fissure.utils
import fissure.utils.library
from fissure.utils.common import PLUGIN_DIR
from fissure.utils import plugin
from fissure.utils import plugin_editor
import os
import time
import yaml
import asyncio
import socket
import shutil
from fissure.Listeners import (
    MeshtasticListener,
    FilesystemListener,
    ZMQSubscriberListener,
    WebsitePollerListener,
    SerialPortListener,
    TCPUDPListener,
    MQTTListener
)

""" HiprFisr Specific Callback Functions """

# DELAY_SHORT = 0.25  # seconds

async def recallInfoMeshtasticReturnLT(component: object, tab_index="", nickname="", location="", notes=""):
    """
    Returns the recalled sensor node settings to the Dashboard.
    """
    print("MADE IT TO HIPRFISR CALLBACKS")
    
    # Send the Message
    PARAMETERS = {
        "tab_index": tab_index,
        "nickname": nickname,
        "location": location,
        "notes": notes
    }
    msg = {
        fissure.comms.MessageFields.IDENTIFIER: component.identifier,
        fissure.comms.MessageFields.MESSAGE_NAME: "recallInfoMeshtasticReturnLT",
        fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
    }
    await component.dashboard_socket.send_msg(fissure.comms.MessageTypes.COMMANDS, msg)



async def recallHardwareMeshtasticReturnLT(component: object, tsi={}):
    """
    Returns the recalled sensor node settings to the Dashboard.
    """
    print("MADE IT TO HIPRFISR CALLBACKS")
    print(tsi)
    
    # Send the Message
    PARAMETERS = {"tsi": tsi}
    msg = {
        fissure.comms.MessageFields.IDENTIFIER: component.identifier,
        fissure.comms.MessageFields.MESSAGE_NAME: "recallHardwareMeshtasticReturnLT",
        fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
    }
    await component.dashboard_socket.send_msg(fissure.comms.MessageTypes.COMMANDS, msg)


async def recallInfoMeshtasticLT(component: object, tab_index=""):
    """
    Recalls information from the sensor node config file.
    """
    component.logger.info(f"Recalling settings for sensor node {tab_index}...")
    PARAMETERS = {"tab_index": tab_index}
    msg = {
        fissure.comms.MessageFields.SOURCE: component.identifierLT,
        fissure.comms.MessageFields.DESTINATION: tab_index,                
        fissure.comms.MessageFields.MESSAGE_NAME: "recallInfoMeshtasticLT",
        fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
    }
    await component.sensor_nodes[int(tab_index)].listener.send_msg(fissure.comms.MessageTypes.COMMANDS, msg)


async def recallHardwareMeshtasticLT(component: object, tab_index=""):
    """
    Recalls information from the sensor node config file.
    """
    component.logger.info(f"Recalling hardware settings for sensor node {tab_index}...")
    PARAMETERS = {"sensor_node_id": tab_index}
    msg = {
        fissure.comms.MessageFields.SOURCE: component.identifierLT,
        fissure.comms.MessageFields.DESTINATION: tab_index,                
        fissure.comms.MessageFields.MESSAGE_NAME: "recallHardwareMeshtasticLT",
        fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
    }
    await component.sensor_nodes[int(tab_index)].listener.send_msg(fissure.comms.MessageTypes.COMMANDS, msg)


async def recallStatusMeshtasticLT(component: object, tab_index=""):
    """
    Recalls information from the sensor node config file.
    """
    component.logger.info(f"Recalling settings for sensor node {tab_index}...")
    PARAMETERS = {"tab_index": tab_index}
    msg = {
        fissure.comms.MessageFields.SOURCE: component.identifierLT,
        fissure.comms.MessageFields.DESTINATION: tab_index,                
        fissure.comms.MessageFields.MESSAGE_NAME: "recallStatusMeshtasticLT",
        fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
    }
    await component.sensor_nodes[int(tab_index)].listener.send_msg(fissure.comms.MessageTypes.COMMANDS, msg)


async def recallStatusMeshtasticReturnLT(component: object, tab_index="", status=""):
    """
    Returns the recalled sensor node settings to the Dashboard.
    """
    print("MADE IT TO HIPRFISR CALLBACKS")
    
    # Send the Message
    PARAMETERS = {
        "tab_index": tab_index,
        "status": status,
    }
    msg = {
        fissure.comms.MessageFields.IDENTIFIER: component.identifier,
        fissure.comms.MessageFields.MESSAGE_NAME: "recallStatusMeshtasticReturnLT",
        fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
    }
    await component.dashboard_socket.send_msg(fissure.comms.MessageTypes.COMMANDS, msg)
