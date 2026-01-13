#!/usr/bin/env python3
import asyncio
import xml.etree.ElementTree as ET
import pytak
from configparser import ConfigParser
import logging
import json

from fissure.utils.common import get_fissure_config
from fissure.callbacks import HiprFisrCallbacks

def load_config() -> ConfigParser:
    """
    Prepare TAK Configuration

    Returns
    -------
    ConfigParser
        Configuration parser object with TAK settings.
    """
    # load fissure config
    fissure_config = get_fissure_config()
    tak_config = fissure_config['tak']
    url = f"tls://{tak_config.get('ip_addr')}:{tak_config.get('port', '8089')}"

    # prepare config parser
    config = ConfigParser()
    config["mycottool"] = {"COT_URL": url}
    config = config["mycottool"]
    config["COT_URL"] = url
    config["PYTAK_TLS_CLIENT_CAFILE"] = tak_config.get('cert')
    config["PYTAK_TLS_CLIENT_CERT"] = tak_config.get('webadmin_cert')
    config["PYTAK_TLS_CLIENT_KEY"] = tak_config.get('key')
    config["PYTAK_TLS_DONT_VERIFY"] = str(1)
    config["PYTAK_TLS_CLIENT_PASSWORD"] = 'atakatak'
    return config

def gen_cot() -> str:
    """
    Generate CoT Event
    
    This is a simple example of generating a CoT Event.

    Returns
    -------
    str
        CoT Event as XML string.
    """
    root = ET.Element("event")
    root.set("version", "2.0")
    root.set("type", "a-f-G")  # insert your type of marker
    root.set("uid", "example")
    root.set("how", "h-g-i-g-o")
    root.set("time", pytak.cot_time())
    root.set("start", pytak.cot_time())
    root.set(
        "stale", pytak.cot_time(60)
    )  # time difference in seconds from 'start' when stale initiates
    detail = ET.SubElement(root, "detail")
    remarks = ET.SubElement(detail, "remarks")
    remarks.text = "Testing Testing2"
    contact = ET.SubElement(detail, "contact")
    callsign = ET.SubElement(contact, "callsign")
    callsign.text = "example"
    pt_attr = {
        "lat": "40.781789",  # set your lat (this loc points to Central Park NY)
        "lon": "-73.968698",  # set your long (this loc points to Central Park NY)
        "hae": "0",
        "ce": "0",
        "le": "0",
    }
    ET.SubElement(root, "point", attrib=pt_attr)
    print(ET.tostring(root))
    return ET.tostring(root)

class TakSender(pytak.QueueWorker):
    """
    TAK Sender Class
    """
    def __init__(self, queue: asyncio.queues.Queue, config: ConfigParser, cot: str, logger: logging.Logger = logging.getLogger()):
        """Initialize TAK Sender.

        Parameters
        ----------
        queue : asyncio.queues.Queue
            The queue to send data to.
        config : ConfigParser
            Configuration parser object with TAK settings.
        cot : str
            CoT Event as XML string.
        logger : logging.Logger, optional
            Logger instance, by default logging.getLogger()
        """
        super().__init__(queue, config)
        self._logger = logger
        self.cot = cot

    async def run(self):
        await self.put_queue(self.cot)

class TakReceiver(pytak.QueueWorker):
    """
    TAK Receiver Class

    Overload handle_data to process received CoT Events.
    """
    def __init__(self, queue: asyncio.queues.Queue, config: ConfigParser, hipfisr: object = None, logger: logging.Logger = logging.getLogger()):
        """Initialize TAK Receiver.

        Parameters
        ----------
        queue : asyncio.queues.Queue
            The queue to receive data from.
        config : ConfigParser
            Configuration parser object with TAK settings.
        hipfisr : object, optional
            HIPRFISR instance, by default None
        logger : logging.Logger, optional
            Logger instance, by default logging.getLogger()
        """
        super().__init__(queue, config)
        self._logger = logger
        self.hipfisr = hipfisr

    # async def handle_data(self, data: str) -> None:
    #     """
    #     Handle data from the receive queue

    #     Parameters
    #     ----------
    #     data : str
    #         Data received from TAK server
    #     """
    #     data_decode = data.decode()
    #     self._logger.debug("TAK Msg Received:\n%s\n", data_decode)
    #     # print("TAK Msg Received:\n%s\n", data_decode)
    #     try:
    #         root = ET.fromstring(data_decode)
    #         uid = root.get("uid", "unknown")
    #         remarks = root.find(".//detail/remarks")
    #         if remarks is not None and remarks.text:
    #             # Plugin Names
    #             if remarks.text == "FTN Requested: Plugin Names":
    #                 self._logger.info(f"FTN Plugin Names Requested for UID: {uid}")
    #                 await HiprFisrCallbacks.sendPluginNamesTak(self.hipfisr, uid, sensor_node_id=0)
                
    #             # List of Plugin Actions
    #             elif remarks.text.startswith("FTN Requested: Plugin Actions:"):
    #                 plugin_name = remarks.text.split("FTN Requested: Plugin Actions:")[-1].strip()
    #                 self._logger.info(f"FTN Plugin Action Names Requested: {plugin_name} for UID: {uid}")
    #                 await HiprFisrCallbacks.sendPluginActionNamesTak(self.hipfisr, uid, plugin_name, sensor_node_id=0)

    #             # Execute Plugin Action
    #             elif remarks.text.startswith("FTN Requested: Plugin Action:"):
    #                 remaining = remarks.text.split("FTN Requested: Plugin Action:")[-1].strip()
    #                 plugin_name, action_name = remaining.split(":", 1)
    #                 plugin_name = plugin_name.strip()
    #                 action_name = action_name.strip()
    #                 self._logger.info(f"FTN Plugin Action Requested: {action_name} for UID: {uid}")
    #                 await HiprFisrCallbacks.sendPluginActionTak(self.hipfisr, uid, sensor_node_id=0, plugin_name=plugin_name, action_name=action_name, parameters={})

    #             # Stop Plugin Action
    #             elif remarks.text.startswith("FTN Requested: Plugin Action Stop"):
    #                 self._logger.info(f"FTN Plugin Stop Requested for UID: {uid}")
    #                 await HiprFisrCallbacks.stop_all_plugin_operations(self.hipfisr, uid, sensor_node_id=0)
    #     except ET.ParseError as e:
    #         self._logger.error("XML Parse Error: %s", e)



    async def handle_data(self, data: bytes) -> None:
        """
        Handle data from the receive queue.

        Expects WinTAK->FISSURE requests in:
        <event ... uid="{request_uid}" type="t-x-fissure">
            <detail>
                <fissure>
                    <request>plugin_action</request>
                    <request_id>fissure-req-...</request_id>
                    <node_uid>...</node_uid>
                    <requester_uid>...</requester_uid>              (optional)
                    <requester_callsign>...</requester_callsign>    (optional)
                    <plugin_name>...</plugin_name>
                    <action_name>...</action_name>
                    <parameters_json>{...}</parameters_json>        (optional; JSON object)
                </fissure>
            </detail>
        </event>
        """
        try:
            data_decode = data.decode("utf-8", errors="replace")
        except Exception:
            data_decode = str(data)

        self._logger.info("TAK Msg Received:\n%s\n", data_decode)

        try:
            root = ET.fromstring(data_decode)
            
            # Deleting after testing Artifact Download
#            uid = root.get("uid", "unknown")
#            remarks = root.find(".//detail/remarks")
#            if remarks is not None and remarks.text:
#                if remarks.text == "FTN Requested: Plugin Names":
#                    self._logger.info(f"FTN Plugin Names Requested for UID: {uid}")
#                    await HiprFisrCallbacks.sendPluginNamesTak(self.hipfisr, uid, sensor_node_id=0)
#                elif remarks.text.startswith("FTN Requested: Plugin Actions:"):
#                    plugin_name = remarks.text.split("FTN Requested: Plugin Actions:")[-1].strip()
#                    self._logger.info(f"FTN Plugin Action Names Requested: {plugin_name} for UID: {uid}")
#                    await HiprFisrCallbacks.sendPluginActionNamesTak(self.hipfisr, uid, plugin_name, sensor_node_id=0)
#                elif remarks.text.startswith("FTN Requested: Plugin Action:"):
#                    remaining = remarks.text.split("FTN Requested: Plugin Action:")[-1].strip()
#                    plugin_name, action_name = remaining.split(":", 1)
#                    plugin_name = plugin_name.strip()
#                    action_name = action_name.strip()
#                    self._logger.info(f"FTN Plugin Action Requested: {action_name} for UID: {uid}")
#                    await HiprFisrCallbacks.sendPluginActionTak(self.hipfisr, uid, sensor_node_id=0, plugin_name=plugin_name, action_name=action_name, parameters={})
#                elif remarks.text.startswith("FTN Requested: Plugin Action Stop"):
#                    self._logger.info(f"FTN Plugin Stop Requested for UID: {uid}")
#                    await HiprFisrCallbacks.stop_all_plugin_operations(self.hipfisr, uid, sensor_node_id=0)
#                elif remarks.text.startswith("FTN Requested: Artifact Download:"):
#                    artid = remarks.text.split("FTN Requested: Artifact Download:")[-1].strip()
#                    self._logger.info(f"FTN Artifact Download Requested for artifact id: {artid}")
#                    await HiprFisrCallbacks.transferArtifactRequest(self.hipfisr, artid, 'tak', None)

            # Event metadata
            event_uid = root.get("uid", "unknown")
            event_type = root.get("type", "unknown")

            detail = root.find(".//detail")
            if detail is None:
                return

            fissure = detail.find("fissure")
            if fissure is None:
                return

            request = (fissure.findtext("request") or "").strip().lower()
            if not request:
                return

            # Correlation ID
            request_id = (fissure.findtext("request_id") or "").strip() or event_uid

            # Required target node
            node_uid = (fissure.findtext("node_uid") or "").strip()

            # Optional requester identity
            requester_uid = (fissure.findtext("requester_uid") or "").strip()
            requester_callsign = (fissure.findtext("requester_callsign") or "").strip()

            if not node_uid:
                self._logger.warning(
                    "FISSURE request missing node_uid (request=%s, request_id=%s, event_uid=%s, event_type=%s, requester_uid=%s)",
                    request, request_id, event_uid, event_type, requester_uid or "none"
                )
                return

            plugin_name = (fissure.findtext("plugin_name") or "").strip()
            action_name = (fissure.findtext("action_name") or "").strip()

            # -----------------------------
            # parameters_json (ONLY)
            # -----------------------------
            parameters = {}

            params_json = fissure.findtext("parameters_json")
            if params_json:
                try:
                    parsed = json.loads(params_json)
                    if not isinstance(parsed, dict):
                        raise ValueError("parameters_json must decode to a JSON object")
                    parameters = parsed
                except Exception as e:
                    self._logger.warning(
                        "Invalid parameters_json (node_uid=%s, request_id=%s): %s",
                        node_uid, request_id, str(e)
                    )
                    return

            self._logger.info(
                "FISSURE RX request=%s node_uid=%s request_id=%s event_uid=%s requester_uid=%s callsign=%s parameters=%s",
                request,
                node_uid,
                request_id,
                event_uid,
                requester_uid or "none",
                requester_callsign or "none",
                list(parameters.keys()) if parameters else "none",
            )

            # -----------------------------
            # Dispatch
            # -----------------------------
            # Query
            if request in ("plugin_names", "plugins", "get_plugin_names"):
                await HiprFisrCallbacks.sendPluginNamesTak(
                    self.hipfisr,
                    node_uid,
                    sensor_node_id=0
                )

            # Load Plugin
            elif request in ("plugin_actions", "get_plugin_actions"):
                if not plugin_name:
                    self._logger.warning(
                        "plugin_actions requested but plugin_name missing (node_uid=%s, request_id=%s)",
                        node_uid, request_id
                    )
                    return

                await HiprFisrCallbacks.sendPluginActionNamesTak(
                    self.hipfisr,
                    node_uid,
                    plugin_name,
                    sensor_node_id=0
                )

            # Execute Action
            elif request in ("plugin_action", "execute_plugin_action", "run_plugin_action"):
                if not plugin_name or not action_name:
                    self._logger.warning(
                        "plugin_action missing plugin_name/action_name (node_uid=%s, request_id=%s, plugin=%s, action=%s)",
                        node_uid,
                        request_id,
                        plugin_name or "missing",
                        action_name or "missing"
                    )
                    return

                await HiprFisrCallbacks.sendPluginActionTak(
                    self.hipfisr,
                    node_uid,
                    sensor_node_id=0,
                    plugin_name=plugin_name,
                    action_name=action_name,
                    parameters=parameters,
                )

            # Stop Action
            elif request in ("plugin_action_stop", "stop_plugin_action", "stop_all"):
                await HiprFisrCallbacks.stop_all_plugin_operations(
                    self.hipfisr,
                    node_uid,
                    sensor_node_id=0
                )
            
            # Artifact Download
            elif request in ("artifact_download", "get_artifact", "download_artifact"):
                artifact_id = parameters.get("artifact_id")

                if not artifact_id:
                    self._logger.warning(
                        "artifact_download requested but artifact_id missing (node_uid=%s, request_id=%s)",
                        node_uid, request_id
                    )
                    return

                self._logger.info(
                    "Artifact download requested (artifact_id=%s, node_uid=%s, request_id=%s)",
                    artifact_id, node_uid, request_id
                )

                # Match the original behavior: request transfer to TAK, with no inline data
                await HiprFisrCallbacks.transferArtifactRequest(self.hipfisr, artifact_id, "tak", None)



            else:
                self._logger.debug(
                    "Ignoring unknown request '%s' (node_uid=%s, request_id=%s)",
                    request, node_uid, request_id
                )

        except ET.ParseError as e:
            self._logger.error("XML Parse Error: %s", e)
        except Exception as e:
            self._logger.exception("handle_data failed: %s", e)






    async def run(self) -> None:
        """
        Wait forever for CoT events from TAK server.
        Only exits on shutdown or None sentinel.
        """
        self._logger.debug("TAK Receiver started, waiting for data...")

        while True:
            try:
                data = await self.queue.get()  # blocks until a message arrives

                # pytak uses None as shutdown sentinel in some cases
                if data is None:
                    self._logger.debug("TAK receiver got shutdown signal.")
                    return

                await self.handle_data(data)

            except asyncio.CancelledError:
                # Task cancelled cleanly on shutdown
                return
            except Exception as e:
                self._logger.error(f"TAK receiver error: {e}")
                await asyncio.sleep(1)

async def main(rx: bool = True, tx: bool = False):
    """
    TAK server client main function

    Parameters
    ----------
    rx : bool, optional
        Enable receiving, by default True
    tx : bool, optional
        Enable transmitting, by default False
    """
    # load config
    config = load_config()

    # Initializes worker queues and tasks.
    clitool = pytak.CLITool(config)
    await clitool.setup()

    logger = logging.getLogger("TakReceiver")
    logger.setLevel(logging.INFO)
    while True:
        # add tasks
        tasks = []
        if rx:
            tasks.append(TakReceiver(clitool.rx_queue, config, logger=logger))
        if tx:
            tasks.append(TakSender(clitool.tx_queue, config, cot=gen_cot(), logger=logger))
        clitool.add_tasks(
            set(tasks)
        )

        # run task
        await clitool.run()

        # wait before restarting
        await asyncio.sleep(1.0)

if __name__ == "__main__":
    asyncio.run(main(True, True))