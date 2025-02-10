#!/usr/bin/env python3
"""Send alertReturn to HIPRFISR/Dashboard
"""
from multiprocessing import Pipe
from multiprocessing.connection import Connection
import asyncio
import subprocess
import fissure.comms

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

    # monitor for alerts
    stop = False
    while not stop and proc.poll() is None:
        for alert_text in proc.stdout:
            # TODO: Look for alert preamble

            PARAMETERS = {
                "sensor_node_id": sensor_node_id,
                "alert_text": alert_text
            }
            msg = {
                fissure.comms.MessageFields.IDENTIFIER: identifier,
                fissure.comms.MessageFields.MESSAGE_NAME: "alertReturn",
                fissure.comms.MessageFields.PARAMETERS: PARAMETERS,
            }
            asyncio.run(hiprfisr_socket.send_msg(fissure.comms.MessageTypes.COMMANDS, msg))

            if c2.poll(): # check for messages on c2 comms
                msg = c2.recv() # get message
                if msg == 'QUIT':
                    stop = True # stop alert monitoring
                    break # break out of for loop
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
