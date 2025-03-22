#!/usr/bin/env python3
"""Send alertReturn to HIPRFISR/Dashboard
"""
from multiprocessing import Pipe
from multiprocessing.connection import Connection
import asyncio
import subprocess
import fissure.comms
import json
import logging

def _alert_sender(cmd: str, c2: Connection, identifier: str, sensor_node_id: any, hiprfisr_socket: fissure.comms.Server, gps_position: dict, logger: logging.Logger, network_type: str):
    """Run Command and Capture stdout for Alerts

    Run command, capture stdout and send by to HIPRFISR as alertReturn command. Will stop capturing when `QUIT` is received on `c2`.

    Parameters
    ----------
    cmd : str
        System command to run
    c2 : Connection
        Pipe connection to command-and-control
    identifier : str
        Sensor node identifier
    sensor_node_id : any
        Sensor node ID
    hiprfisr_socket : fissure.comms.Server
        HIPRFISR socker
    gps_position : dict
        Dictionary with gps position
    logger : logging.Logger
        Sensor node logger
    """
    # Run command
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, bufsize=1, universal_newlines=True, shell=True)

    # Monitor for alerts
    stop = False
    while not stop and proc.poll() is None:
        for proc_text in proc.stdout:

            # Replace any gps fields in text
            proc_text = proc_text % gps_position

            try:
                data = json.loads(proc_text)

                if not data.__class__ is dict:
                    # Not within the scope of alert messaging; log as info
                    logger.info(str(data))

                elif not 'msg' in list(data.keys()):
                    # Not within the scope of alert messaging; log as info
                    logger.info(str(data))

                elif data.get('msg') == 'alert':
                    if network_type == "IP":
                        PARAMETERS = {
                            "sensor_node_id": sensor_node_id,
                            "alert_text": data.get('text')
                        }
                        msg = {
                            fissure.comms.MessageFields.IDENTIFIER: identifier,
                            fissure.comms.MessageFields.MESSAGE_NAME: "alertReturn",
                            fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
                        }
                        asyncio.run(hiprfisr_socket.send_msg(fissure.comms.MessageTypes.COMMANDS, msg))
                        
                    elif network_type == "Meshtastic":
                        PARAMETERS = {
                            "sensor_node_id": sensor_node_id,
                            "alert_text":  data.get('text')[:100] if data.get('text') else None                            
                        }
                        msg = {
                            fissure.comms.MessageFields.SOURCE: identifier,
                            fissure.comms.MessageFields.DESTINATION: fissure.comms.Identifiers.HIPRFISR_LT,
                            fissure.comms.MessageFields.MESSAGE_NAME: "alertReturnLT",
                            fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
                        }
                        asyncio.run(hiprfisr_socket.send_msg(fissure.comms.MessageTypes.COMMANDS, msg))

                elif data.get('msg') == 'tak':
                    if network_type == "IP":
                        PARAMETERS = {
                            "uid": data.get('uid'),
                            "lat": data.get('lat'),
                            "lon": data.get('lon'),
                            "alt": data.get('alt'),
                            "time": data.get('time'),
                            "remarks": data.get('remarks'),
                        }

                        if data.get('remarks') == "GPS UPDATE":
                            msg = {
                                fissure.comms.MessageFields.IDENTIFIER: identifier,
                                fissure.comms.MessageFields.MESSAGE_NAME: "takPlotGpsUpdate",
                                fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
                            }
                            asyncio.run(hiprfisr_socket.send_msg(fissure.comms.MessageTypes.COMMANDS, msg))                        

                        else:
                            msg = {
                                fissure.comms.MessageFields.IDENTIFIER: identifier,
                                fissure.comms.MessageFields.MESSAGE_NAME: "takPlot",
                                fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
                            }
                            asyncio.run(hiprfisr_socket.send_msg(fissure.comms.MessageTypes.COMMANDS, msg))
                        
                    elif network_type == "Meshtastic":
                        PARAMETERS = {
                            "msg": [
                                data.get('uid'),
                                data.get('lat'),
                                data.get('lon'),
                                data.get('alt'),
                                data.get('time'),
                                data.get('remarks')[:20] if data.get('remarks') else None
                            ]
                        }

                        if data.get('remarks') == "GPS UPDATE":
                            msg = {
                                fissure.comms.MessageFields.SOURCE: identifier,
                                fissure.comms.MessageFields.DESTINATION: fissure.comms.Identifiers.HIPRFISR_LT,
                                fissure.comms.MessageFields.MESSAGE_NAME: "takPlotGpsUpdateLT",
                                fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
                            }
                        else:
                            msg = {
                                fissure.comms.MessageFields.SOURCE: identifier,
                                fissure.comms.MessageFields.DESTINATION: fissure.comms.Identifiers.HIPRFISR_LT,
                                fissure.comms.MessageFields.MESSAGE_NAME: "takPlotLT",
                                fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
                            }
                        asyncio.run(hiprfisr_socket.send_msg(fissure.comms.MessageTypes.COMMANDS, msg))

                elif data.get('msg') == 'exploit':
                    if network_type == "IP":
                        PARAMETERS = {
                            "sensor_node_id": sensor_node_id,
                            "protocol": data.get('protocol'),
                            "modulation": data.get('modulation'),
                            "hardware": data.get('hardware'),
                            "type": data.get('type'),
                            "attack": data.get('attack'),
                            "variables": data.get('variables'),
                        }
                        msg = {
                            fissure.comms.MessageFields.IDENTIFIER: identifier,
                            fissure.comms.MessageFields.MESSAGE_NAME: "exploit",
                            fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
                        }
                        asyncio.run(hiprfisr_socket.send_msg(fissure.comms.MessageTypes.COMMANDS, msg))

                    elif network_type == "Meshtastic":
                        PARAMETERS = {
                            "msg": [
                                sensor_node_id,
                                data.get('protocol'),
                                data.get('modulation'),
                                data.get('hardware'),
                                data.get('type'),
                                data.get('attack'),
                                data.get('variables')
                                # data.get('variables')[:20] if data.get('variables') else None
                            ]
                        }
                        msg = {
                            fissure.comms.MessageFields.SOURCE: identifier,
                            fissure.comms.MessageFields.DESTINATION: fissure.comms.Identifiers.HIPRFISR_LT,
                            fissure.comms.MessageFields.MESSAGE_NAME: "exploitLT",
                            fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
                        }
                        asyncio.run(hiprfisr_socket.send_msg(fissure.comms.MessageTypes.COMMANDS, msg))

            except json.decoder.JSONDecodeError:
                # Not a valid json string
                logger.info(str(proc_text))

            if c2.poll(): # Check for messages on c2 comms
                msg = c2.recv()  # Get message
                if msg == 'QUIT':
                    stop = True  # Stop alert monitoring
                    break
    proc.wait()  # Wait for process to end

class alertSender(object):
    def __init__(self, cmd: str, identifier: str, sensor_node_id: any, hiprfisr_socket: fissure.comms.Server, gps_position: dict, logger: logging.Logger, network_type: str):
        """Run Command and Capture stdout for Alerts

        Run command, capture stdout and send by to HIPRFISR as alertReturn command

        Parameters
        ----------
        cmd : str
            System command to run
        identifier : str
            Sensor node identifier
        sensor_node_id : any
            Sensor node ID
        hiprfisr_socket : fissure.comms.Server
            HIPRFISR socker
        gps_position : dict
            Dictionary with gps position
        logger : logging.Logger
            Sensor node logger
        """
        (self.conn1, conn2) = Pipe()
        _alert_sender(cmd, conn2, identifier, sensor_node_id, hiprfisr_socket, gps_position, logger, network_type)

    def stop(self):
        """Stop capture and wait for process to finished
        """
        self.conn1.send('QUIT')
