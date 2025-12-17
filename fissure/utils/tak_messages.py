#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import pytak
from datetime import datetime, timezone

# ---------------------------------------------------------
# Base COT builder
# ---------------------------------------------------------

def _build_base_event(uid: str, stale: int):
    """
    Creates base CoT event using pytak.gen_cot_xml().
    Returns (msg, detail).
    NOTE: pytak.gen_cot_xml() in your version does NOT accept "type",
          so CoT type must be set manually afterward.
    """
    msg = pytak.gen_cot_xml(uid=uid, stale=stale)

    # Normalize in case pytak returned a string
    if not isinstance(msg, ET.Element):
        msg = ET.fromstring(msg)

    detail = msg.find("detail")
    if detail is None:
        detail = ET.SubElement(msg, "detail")

    return msg, detail


# ---------------------------------------------------------
# Point helpers
# ---------------------------------------------------------

def _set_point_pin(msg, lat, lon, alt):
    """Map-visible pin."""
    pt = msg.find("point")
    if pt is None:
        pt = ET.SubElement(msg, "point")

    pt.set("lat", str(lat))
    pt.set("lon", str(lon))
    pt.set("hae", str(alt))
    pt.set("ce", "0")
    pt.set("le", "0")

def _set_point_suppressed(msg):
    """Event NOT visible on map."""
    pt = msg.find("point")
    if pt is None:
        pt = ET.SubElement(msg, "point")

    pt.set("lat", "0")
    pt.set("lon", "0")
    pt.set("hae", "0")
    pt.set("ce", "9999999")
    pt.set("le", "9999999")


# ---------------------------------------------------------
# Transmission helper
# ---------------------------------------------------------

def _send_to_tak(component, msg):
    """Serialize XML and send to TAK via pytak queue."""
    if not hasattr(component, "clitool") or component.clitool is None:
        component.logger.warning("TAK disabled or clitool not initialized. CoT message not sent.")
        return
    
    msg_bytes = ET.tostring(msg, encoding="utf-8")
    component.logger.debug("Sending TAK message:\n" + msg_bytes.decode("utf-8"))
    component.logger.info("Sending TAK message:\n" + msg_bytes.decode("utf-8"))
    component.clitool.tx_queue.put_nowait(msg_bytes)


# ---------------------------------------------------------
# Main entrypoint: send()
# ---------------------------------------------------------

async def send(component, message: dict):
    """
    Unified TAK message sender.

    message["type"] = "pin" | "event" | "track"
    message["uid"]  = CoT UID
    Other fields vary by type.
    """

    mtype = message["type"]

    # =====================================================
    # 1. PIN (map-visible position marker)
    # =====================================================
    if mtype == "pin":
        msg, detail = _build_base_event(
            uid=message["uid"],
            stale=message.get("stale", 999999999)
        )

        # Manually set CoT type (since pytak.gen_cot_xml cannot accept type=)
        msg.set("type", message.get("cot_type", "a-f-G-U-H"))
        # msg.set("how", message.get("how", "m-g"))

        # contact & remarks
        ET.SubElement(detail, "contact", {"callsign": message["callsign"]})
        ET.SubElement(detail, "remarks").text = message.get("remarks", "")

        # point visible on map
        _set_point_pin(msg, message["lat"], message["lon"], message.get("alt", 0))

        return _send_to_tak(component, msg)

    # =====================================================
    # 2. EVENT (structured, non-pin, multi-purpose)
    # =====================================================
    if mtype == "event":

        msg, detail = _build_base_event(
            uid=message["uid"],
            stale=message.get("stale", 30)
        )

        # Always use a non-pin, non-icon CoT type for FISSURE events.
        msg.set("type", message.get("cot_type", "b-f-t-r"))

        # Create <fissure> root
        fiss = ET.SubElement(detail, "fissure")

        data = message.get("data", {})
        event_type = data.get("event_type", "generic")

        # Create <plugin_list>, <detection>, <targets>, etc.
        event_node = ET.SubElement(fiss, event_type)

        # Serialize everything under this event
        _serialize_payload(event_node, data, skip_keys={"event_type"})

        # Suppress map pin
        _set_point_suppressed(msg)

        return _send_to_tak(component, msg)

    # =====================================================
    # 3. TRACK (auto-tracking, NO history needed)
    # =====================================================
    if mtype == "track":
        msg, detail = _build_base_event(
            uid=message["uid"],
            stale=message.get("stale", 60)
        )

        # Set CoT type for moving unit
        msg.set("type", message.get("cot_type", "b-m-p-w"))

        # Add callsign if provided
        if "callsign" in message:
            ET.SubElement(detail, "contact", {"callsign": message["callsign"]})

        # Current position pin (TAK will automatically build tracks over time)
        _set_point_pin(
            msg,
            message["lat"],
            message["lon"],
            message.get("alt", 0)
        )

        return _send_to_tak(component, msg)

    # =====================================================
    # UNKNOWN MESSAGE TYPE
    # =====================================================
    component.logger.error(f"Unknown TAK message type: {mtype}")


def _serialize_payload(parent, data, skip_keys=None):
    """
    Recursively serialize Python dict/lists/scalars into XML.

    parent     = XML node to attach elements to
    data       = python value (dict, list, scalar)
    skip_keys  = keys you do not want to serialize (e.g., event_type)
    """

    if skip_keys is None:
        skip_keys = set()

    if isinstance(data, dict):
        for key, value in data.items():

            if key in skip_keys:
                continue

            # LIST → multiple child nodes
            if isinstance(value, list):
                # Example: "plugins" → <plugin name="...">
                singular = key[:-1] if key.endswith("s") else key
                for item in value:
                    child = ET.SubElement(parent, singular)
                    _serialize_payload(child, item)
                continue

            # DICT → nested structure
            if isinstance(value, dict):
                child = ET.SubElement(parent, key)
                _serialize_payload(child, value)
                continue

            # SCALAR → simple text node
            child = ET.SubElement(parent, key)
            child.text = str(value)
        return

    # LIST OF NON-DICT ITEMS
    if isinstance(data, list):
        for item in data:
            child = ET.SubElement(parent, "item")
            _serialize_payload(child, item)
        return

    # SCALAR VALUE (fallback)
    parent.text = str(data)