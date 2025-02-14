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
MAX_CHUNK_SIZE = 100  # Safe max payload size per message
CHUNK_RETRY_LIMIT = 3  # Max retries per chunk
ACK_TIMEOUT = 3  # Time to wait for an ACK


class FissureMeshtasticNode:
    """Handles communication via Meshtastic, integrating with existing ZMQ infrastructure."""

    def __init__(self, serial_port: str, name: str, context: object):
        """Initialize connection to Meshtastic device."""
        # Initialize Logging
        self.parent_component = name.split("::")[0] if "::" in name else name
        self.name = name.split("::")[1] if "::" in name else name
        self.logger = fissure.utils.get_logger(source=self.parent_component)

        self.loop = asyncio.get_event_loop()
        self.interface = SerialInterface(serial_port)
        self.message_queue = asyncio.Queue()  # Queue for received messages
        self.context = context  # Object containing the callback methods
        self.running = True  # Flag to control async processing
        self.chunk_buffer = {}
        
        # Subscribe to Meshtastic message events via PubSub
        pub.subscribe(self._handle_message, "meshtastic.receive.text")

        # self.task = asyncio.create_task(self.process_messages())  # Start processing
        loop = asyncio.get_event_loop()
        self.process_task = loop.create_task(self.process_messages())


    async def send_msg(self, msg_type: str, msg: Dict, target_ids: Optional[List[str]] = None, **kwargs):
        """
        Send a command over Meshtastic, with chunking and ACKs.
        """
        print("IN THE SEND MSG!")
        print(msg)

        msg[MessageFields.TYPE] = msg_type
        encoded_msg = json.dumps(msg)
        chunks = [encoded_msg[i:i + MAX_CHUNK_SIZE] for i in range(0, len(encoded_msg), MAX_CHUNK_SIZE)]
        message_id = int(time.time())  # Unique ID for tracking chunks

        loop = asyncio.get_running_loop()
        self.pending_acks = set()  # Track chunks waiting for acknowledgment

        for index, chunk in enumerate(chunks):
            chunk_msg = {
                "Identifier": msg.get("Identifier", "unknown"),
                "MessageID": message_id,
                "ChunkIndex": index,
                "TotalChunks": len(chunks),
                "Payload": chunk
            }

            self.pending_acks.add(index)  # Track chunk waiting for ACK
            retry_count = 0

            while retry_count < CHUNK_RETRY_LIMIT:
                await loop.run_in_executor(None, self.interface.sendText, json.dumps(chunk_msg))
                await asyncio.sleep(0.5)  # Small delay to avoid collisions

                # Wait for acknowledgment
                start_time = time.time()
                while time.time() - start_time < ACK_TIMEOUT:
                    if index not in self.pending_acks:  # Chunk was acknowledged
                        break
                    await asyncio.sleep(0.1)

                if index not in self.pending_acks:
                    break  # Move to next chunk
                else:
                    retry_count += 1
                    self.logger.warning(f"⚠️ Retrying chunk {index}/{len(chunks)} (Attempt {retry_count})")

            if retry_count == CHUNK_RETRY_LIMIT:
                self.logger.error(f"❌ Chunk {index} failed after {CHUNK_RETRY_LIMIT} retries!")

        print("AFTER the send")
        self.logger.info(f"[{self.name}] sent message in {len(chunks)} chunks.")

        # Ignore Message Parameters in Logging
        if msg_type == "Commands":
            if msg["MessageName"] in fissure.utils.BANNED_MESSAGE_NAMES:
                log_message = msg.copy()
                log_message.pop("Parameters", None)
            else:
                log_message = msg
            if self.logger.isEnabledFor(logging.INFO):
                self.logger.info(f"[{self.name}] sent message: {msg['MessageName']}" + (f" to {target_ids}" if target_ids else ""))
            self.logger.debug(f"[{self.name}] sent message: {log_message}" + (f" to {target_ids}" if target_ids else ""))
        else:
            if self.logger.isEnabledFor(logging.INFO):
                self.logger.info(f"[{self.name}] sent message: {msg['MessageName']}" + (f" to {target_ids}" if target_ids else ""))
            self.logger.debug(f"[{self.name}] sent message: {msg}" + (f" to {target_ids}" if target_ids else ""))        


    def send_heartbeat(self, msg: Dict, target_ids: Optional[List[str]] = None, **kwargs):
        """Send a heartbeat over Meshtastic."""
        self.interface.sendText(json.dumps(msg))


    async def recv_msg(self) -> Optional[Dict]:
        """Asynchronously retrieve an incoming message from the queue, with logging and filtering."""
        try:
            print("receiving...")
            msgrcvd = await asyncio.wait_for(self.message_queue.get(), timeout=POLL_TIMEOUT)
            if msgrcvd is None:
                return None

            # Determine Sender ID (if available)
            sender_id = msgrcvd.get(MessageFields.SENDER_ID)
            sender_id_no_uuid = sender_id.split('-')[0] if sender_id else None

            print("IN THE RECEIVE!")
            print(msgrcvd)
            print(sender_id)
            print(sender_id_no_uuid)
            print(msgrcvd.get(MessageFields.TYPE))

            # Handle Command Messages
            if msgrcvd.get(MessageFields.TYPE) == MessageTypes.COMMANDS:
                cb = msgrcvd.get(MessageFields.MESSAGE_NAME)
                msgrcvd["callback"] = cb  # Ensure callback field exists
                
                # Ignore Parameters in Logging for Certain Messages
                if cb in fissure.utils.BANNED_MESSAGE_NAMES:
                    log_message = msgrcvd.copy()
                    log_message.pop("Parameters", None)
                else:
                    log_message = msgrcvd

                # Log messages at INFO level
                if self.logger.isEnabledFor(logging.INFO):
                    if sender_id_no_uuid:
                        self.logger.info(f"[{self.name}] received message: {cb} from [{sender_id_no_uuid}]")
                    else:
                        self.logger.info(f"[{self.name}] received message: {cb}")

                # Log full message details at DEBUG level
                if sender_id:
                    self.logger.debug(f"[{self.name}] received message: {log_message} from [{sender_id}]")
                else:
                    self.logger.debug(f"[{self.name}] received message: {log_message}")

            # Handle Other Message Types
            else:
                if sender_id_no_uuid:
                    self.logger.debug(f"[{self.name}] received message: {msgrcvd} from [{sender_id_no_uuid}]")
                else:
                    self.logger.debug(f"[{self.name}] received message: {msgrcvd}")

            return msgrcvd  # Return the processed message

        except asyncio.TimeoutError:
            return None  # No message received within timeout


    async def run_callback(self, context: object, parsed_command: Dict) -> Any:
        """
        Process and execute the callback with the provided parameters

        :param context: context to find the callback method
        :type context: object | Dict
        :param parsed_command: command containing the callback function to execute and (optional) parameters
        :type parsed_command: Dict
        :raises Exception: if the callback is not implemented in the provided context
        :return: result of the executed callback
        :rtype: any
        """
        print("In the callback!")
        print(parsed_command)
        cb_name = parsed_command["callback"]
        try:
            cb = context.callbacks.get(cb_name)
        except AttributeError:  # pragma: no cover
            cb = context.get(cb_name)
        if cb is None:  # pragma: no cover
            raise Exception(f"method {cb_name} not implemented in context {context}")

        params = parsed_command.get("Parameters")

        # Ignore Message Parameters in Logging
        if cb_name in fissure.utils.BANNED_MESSAGE_NAMES:
            self.logger.debug(f"executing callback: {cb_name}")
        else:
            self.logger.debug(f"executing callback: {cb_name} with parameters: {params}")

        # Process parameters and execute callback functon
        if params is None:
            # No Parameters
            return await cb(context)
        elif len(params) == 0:
            # Empty Parameters
            return await cb(context, *params)
        else:
            if type(params) is dict:  # Dictionary Params
                return await cb(context, **params)
            elif type(params) is list:  # List Params
                return await cb(context, *params)
            elif type(params) is str:  # Space Separated String Params
                return await cb(context, *(params.split()))
            else:  # pragma: no cover
                self.warning.logger(
                    f"[{self.name}] received callback ({cb_name}) with unrecognized parameters: {params}"
                )


    async def process_messages(self):
        """Continuously processes messages from the queue using `run_callback`."""
        while self.running:
            msg = await self.recv_msg()
            if msg:
                await self.run_callback(self.context, msg)

            await asyncio.sleep(0.1)


    async def _enqueue_message(self, message):
        """Places received messages into the async queue."""
        await self.message_queue.put(message)


    def _handle_message(self, packet, interface=None):
        """Handles incoming messages and sends ACKs for chunked messages."""
        sender = packet.get("fromId", "Unknown Sender")
        raw_text = packet.get("decoded", {}).get("text", "")

        if raw_text:
            try:
                parsed_data = json.loads(raw_text)

                if "ChunkIndex" in parsed_data:
                    # This is a chunked message
                    identifier = parsed_data["Identifier"]
                    message_id = parsed_data["MessageID"]
                    chunk_index = parsed_data["ChunkIndex"]
                    total_chunks = parsed_data["TotalChunks"]
                    payload = parsed_data["Payload"]

                    if identifier not in self.chunk_buffer:
                        self.chunk_buffer[identifier] = {}

                    self.chunk_buffer[identifier][chunk_index] = payload

                    # Send an acknowledgment (ACK) back
                    ack_msg = {
                        "Identifier": identifier,
                        "MessageID": message_id,
                        "ChunkIndex": chunk_index,
                        "ACK": True
                    }
                    self.interface.sendText(json.dumps(ack_msg))

                    # If all chunks are received, reassemble the message
                    if len(self.chunk_buffer[identifier]) == total_chunks:
                        full_msg = "".join(self.chunk_buffer[identifier][i] for i in range(total_chunks))
                        del self.chunk_buffer[identifier]  # Clear buffer
                        
                        parsed_data = json.loads(full_msg)  # Reconstruct original message
                        self.logger.info(f"📩 Reassembled full message from {sender}: {parsed_data}")

                        # Pass full message for processing
                        asyncio.run_coroutine_threadsafe(self._enqueue_message(parsed_data), self.loop)

                elif "ACK" in parsed_data:
                    # This is an acknowledgment
                    chunk_index = parsed_data["ChunkIndex"]
                    if chunk_index in self.pending_acks:
                        self.pending_acks.remove(chunk_index)

                else:
                    # Normal message handling
                    self.logger.info(f"📩 Received from {sender}: {parsed_data}")
                    asyncio.run_coroutine_threadsafe(self._enqueue_message(parsed_data), self.loop)

            except json.JSONDecodeError:
                self.logger.warning(f"⚠️ Message from {sender} is not valid JSON: {raw_text}")


    async def disconnect(self):
        """Disconnect from the serial interface and stop processing messages."""
        self.logger.info(f"Disconnecting Meshtastic node [{self.name}]...")
        
        # Stop message processing
        self.running = False
        
        # Cancel processing task if it exists
        if hasattr(self, "process_task") and self.process_task:
            self.process_task.cancel()
            try:
                await self.process_task
            except asyncio.CancelledError:
                pass  # Task successfully canceled

        # Close the Meshtastic Serial connection
        try:
            if self.interface:
                self.interface.close()
                self.interface = None  # Remove reference
                self.logger.info("Meshtastic serial connection closed.")
            else:
                self.logger.warning("No valid Meshtastic serial interface found during disconnect.")
        except Exception as e:
            self.logger.warning(f"Error closing Meshtastic serial interface: {e}")


    async def get_gps_position(self, timeout: int = 10) -> Optional[Dict[str, float]]:
        """
        Fetch GPS coordinates from the Meshtastic device.

        Args:
            timeout (int): Maximum time in seconds to wait for GPS data.

        Returns:
            dict: A dictionary containing latitude, longitude, and altitude if successful, or None if failed.
        """
        try:
            start_time = asyncio.get_running_loop().time()

            while asyncio.get_running_loop().time() - start_time < timeout:
                node_info = self.interface.getMyNodeInfo()

                if node_info and "position" in node_info:
                    position = node_info["position"]
                    if node_info and "position" in node_info:
                        position = node_info["position"]

                        # Prefer `latitudeI` and `longitudeI` (more precise), fallback to float values if needed
                        if "latitudeI" in position and "longitudeI" in position:
                            latitude = round(position["latitudeI"] / 1e7, 6)
                            longitude = round(position["longitudeI"] / 1e7, 6)
                        elif "latitude" in position and "longitude" in position:
                            latitude = round(position["latitude"], 6)
                            longitude = round(position["longitude"], 6)
                        else:
                            latitude = None
                            longitude = None

                        altitude = position.get("altitude", 0.0)  # Altitude is optional

                        if latitude is not None and longitude is not None and latitude != 0 and longitude != 0:
                            return {
                                "latitude": latitude,
                                "longitude": longitude,
                                "altitude": altitude
                            }

                await asyncio.sleep(1)  # Retry if GPS is unavailable

            print("GPS data not available within timeout.")
            return None

        except Exception as e:
            print(f"Error accessing Meshtastic GPS: {e}")
            return None
