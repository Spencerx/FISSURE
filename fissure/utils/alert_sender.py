#!/usr/bin/env python3
"""Send alertReturn to HIPRFISR/Dashboard
"""
from multiprocessing import Pipe
from multiprocessing.connection import Connection
import asyncio
import subprocess
import fissure.comms
import json

def _alert_sender(cmd: str, c2: Connection, identifier: str, sensor_node_id: any, hiprfisr_socket: fissure.comms.Server):
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
    """
    # run command
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, bufsize=1, universal_newlines=True, shell=True)

    # TODO: initialize fields with fixed position until sensor node GPS is available
    fields = {
        "latitude": 40.712776,
        "longitude": -74.005974,
        "altitude": 10.5
    }

    # monitor for alerts
    stop = False
    while not stop and proc.poll() is None:
        for proc_text in proc.stdout:
            # replace any fields in text
            proc_text = proc_text % fields

            try:
                data = json.loads(proc_text)

                if not data is dict or not 'msg' in data.keys():
                    pass # not an accepted format

                if data.get('msg') == 'alert':
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

                elif data.get('msg') == 'tak':
                    PARAMETERS = {
                        "uid": data.get('uid'),
                        "lat": data.get('lat'),
                        "lon": data.get('lon'),
                        "alt": data.get('alt'),
                        "time": data.get('time'),
                        "remarks": data.get('remarks'),
                    }
                    msg = {
                        fissure.comms.MessageFields.IDENTIFIER: identifier,
                        fissure.comms.MessageFields.MESSAGE_NAME: "takPlot",
                        fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
                    }
                    asyncio.run(hiprfisr_socket.send_msg(fissure.comms.MessageTypes.COMMANDS, msg))

            except json.decoder.JSONDecodeError:
                # not a valid json string
                pass

            if c2.poll(): # check for messages on c2 comms
                msg = c2.recv() # get message
                if msg == 'QUIT':
                    stop = True # stop alert monitoring
                    break # break out of for loop
                # TODO: when GPS is available check for updates, e.g. "FIELD latitude=41.5"
    proc.wait() # wait for process to end

class alertSender(object):
    def __init__(self, cmd: str, identifier: str, sensor_node_id: any, hiprfisr_socket: fissure.comms.Server):
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
        """
        (self.conn1, conn2) = Pipe()
        _alert_sender(cmd, conn2, identifier, sensor_node_id, hiprfisr_socket)

    def stop(self):
        """Stop capture and wait for process to finished
        """
        self.conn1.send('QUIT')
