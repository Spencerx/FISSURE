import fissure.utils
from .constants import MessageFields, MessageTypes
import meshtastic
from meshtastic.serial_interface import SerialInterface
import json
import asyncio
from typing import Any, Dict, List, Optional, Set
import logging
from pubsub import pub
import time

POLL_TIMEOUT = 5  # Adjust as needed
ACK_TIMEOUT = 3  # Time to wait for an ACK

class FissureMeshtasticNode:
    """Handles communication via Meshtastic, integrating with existing ZMQ infrastructure."""

    def __init__(self, serial_port: str, name: str, context: object):
        """Initialize connection to Meshtastic device."""
        self.parent_component = name.split("::")[0] if "::" in name else name
        self.name = name.split("::")[1] if "::" in name else name
        self.logger = fissure.utils.get_logger(source=self.parent_component)

        self.loop = asyncio.get_event_loop()
        self.interface = SerialInterface(serial_port)
        self.message_queue = asyncio.Queue()  # Queue for received messages
        self.context = context  # Object containing the callback methods
        self.running = True  # Flag to control async processing
        
        pub.subscribe(self._handle_message, "meshtastic.receive.text")

        loop = asyncio.get_event_loop()
        self.process_task = loop.create_task(self.process_messages())

    async def send_msg(self, msg_code: str, sensor_id: str, payload: Optional[str] = None):
        message = f"{sensor_id},{msg_code},{payload if payload else ''}"
        await asyncio.get_running_loop().run_in_executor(None, self.interface.sendText, message)

    async def recv_msg(self) -> Optional[Dict]:
        try:
            msgrcvd = await asyncio.wait_for(self.message_queue.get(), timeout=POLL_TIMEOUT)
            return msgrcvd
        except asyncio.TimeoutError:
            return None

    async def run_callback(self, context: object, parsed_command: Dict) -> Any:
        cb_name = parsed_command["callback"]
        try:
            cb = context.callbacks.get(cb_name)
        except AttributeError:
            cb = context.get(cb_name)
        if cb is None:
            raise Exception(f"method {cb_name} not implemented in context {context}")

        params = parsed_command.get("Parameters")
        if params is None:
            return await cb(context)
        elif len(params) == 0:
            return await cb(context, *params)
        else:
            if type(params) is dict:
                return await cb(context, **params)
            elif type(params) is list:
                return await cb(context, *params)
            elif type(params) is str:
                return await cb(context, *(params.split()))

    async def process_messages(self):
        while self.running:
            msg = await self.recv_msg()
            if msg:
                await self.run_callback(self.context, msg)
            await asyncio.sleep(0.1)

    async def _enqueue_message(self, message):
        await self.message_queue.put(message)

    def _handle_message(self, packet, interface=None):
        sender = packet.get("fromId", "Unknown Sender")
        raw_text = packet.get("decoded", {}).get("text", "")
        if raw_text:
            try:
                parsed_data = json.loads(raw_text)
                self.logger.info(f"📩 Received from {sender}: {parsed_data}")
                asyncio.run_coroutine_threadsafe(self._enqueue_message(parsed_data), self.loop)
            except json.JSONDecodeError:
                self.logger.warning(f"⚠️ Message from {sender} is not valid JSON: {raw_text}")

    async def disconnect(self):
        self.logger.info(f"Disconnecting Meshtastic node [{self.name}]...")
        self.running = False
        if hasattr(self, "process_task") and self.process_task:
            self.process_task.cancel()
            try:
                await self.process_task
            except asyncio.CancelledError:
                pass
        if self.interface:
            self.interface.close()
            self.interface = None
            self.logger.info("Meshtastic serial connection closed.")

    async def get_gps_position(self, timeout: int = 10) -> Optional[Dict[str, float]]:
        try:
            start_time = asyncio.get_running_loop().time()
            while asyncio.get_running_loop().time() - start_time < timeout:
                node_info = self.interface.getMyNodeInfo()
                if node_info and "position" in node_info:
                    position = node_info["position"]
                    if "latitudeI" in position and "longitudeI" in position:
                        latitude = round(position["latitudeI"] / 1e7, 6)
                        longitude = round(position["longitudeI"] / 1e7, 6)
                        altitude = position.get("altitude", 0.0)
                        return {"latitude": latitude, "longitude": longitude, "altitude": altitude}
                await asyncio.sleep(1)
            print("GPS data not available within timeout.")
            return None
        except Exception as e:
            print(f"Error accessing Meshtastic GPS: {e}")
            return None
