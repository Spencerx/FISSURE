#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import pytak
from datetime import datetime, timezone
from fissure.utils.common import extractFrequencyFromUID
from fissure.utils.library import classifyFrequencyFromTextDirect



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

    Expected input fields (all optional except msg_type and uid):

        msg_type    : "pin" | "event" | "track"
        uid         : CoT UID
        lat/lon/alt : floats
        time        : ISO 8601 string
        remarks     : text
        stale       : int (seconds)
        tak_icon    : CoT symbol type ("a-f-G-U-H", "b-m-p-w", etc.)
        callsign    : optional callsign override
        data        : dict for event messages
        how         : TAK "how" value (optional)
    """

    # -------------------------------------------------
    # Validate required fields
    # -------------------------------------------------
    if "msg_type" not in message:
        component.logger.error("TAK send() missing required field: msg_type")
        return
    if "uid" not in message:
        component.logger.error("TAK send() missing required field: uid")
        return

    mtype = message["msg_type"]
    uid   = message["uid"]

    # Common optional fields
    lat      = message.get("lat")
    lon      = message.get("lon")
    alt      = message.get("alt", 0)
    time     = message.get("time")
    stale    = message.get("stale")
    how      = message.get("how")
    remarks  = message.get("remarks", "")
    tak_icon = message.get("tak_icon")

    # =====================================================
    # 1. PIN (map-visible position marker)
    # =====================================================
    if mtype == "pin":

        # Callsign fallback for pins
        callsign = message.get("callsign", uid)

        # -------------------------------------
        # Apply frequency classification
        # -------------------------------------
        try:
            freq_hz = extractFrequencyFromUID(uid)
            if freq_hz:
                cls = classifyFrequencyFromTextDirect(freq_hz)
                if cls:
                    remarks = f"{remarks}\n{cls}" if remarks else cls
        except Exception as e:
            component.logger.error(f"[TAK] Frequency classification error: {e}")

        # Build base event
        msg, detail = _build_base_event(
            uid=uid,
            stale=stale if stale is not None else 999999999
        )

        msg.set("type", tak_icon or "a-f-G-U-H")
        if how:
            msg.set("how", how)

        ET.SubElement(detail, "contact", {"callsign": callsign})
        ET.SubElement(detail, "remarks").text = remarks

        _set_point_pin(msg, lat, lon, alt)

        return _send_to_tak(component, msg)

    # =====================================================
    # 2. EVENT (structured, non-pin)
    # =====================================================
    if mtype == "event":

        msg, detail = _build_base_event(
            uid=uid,
            stale=stale if stale is not None else 30
        )

        msg.set("type", tak_icon or "b-f-t-r")
        if how:
            msg.set("how", how)

        fiss = ET.SubElement(detail, "fissure")

        data = message.get("data", {})
        event_type = data.get("event_type", "generic")

        event_node = ET.SubElement(fiss, event_type)
        _serialize_payload(event_node, data, skip_keys={"event_type"})

        _set_point_suppressed(msg)
        return _send_to_tak(component, msg)

    # =====================================================
    # 3. TRACK (auto-tracking)
    # =====================================================
    if mtype == "track":

        prefix = component.settings.get("callsign_prefix", "NODE")
        node_meta = component.nodes.get(uid, {})

        nickname = (
            message.get("callsign")
            or node_meta.get("callsign")
            or node_meta.get("nickname")
        )

        if not nickname:
            callsign = f"{prefix}-{uid[:8]}"
        else:
            if nickname.lower().startswith(prefix.lower() + "-"):
                callsign = nickname
            else:
                callsign = f"{prefix}-{nickname}"

        msg, detail = _build_base_event(
            uid=uid,
            stale=stale if stale is not None else 60
        )

        msg.set("type", tak_icon or "b-m-p-w")
        if how:
            msg.set("how", how)

        ET.SubElement(detail, "contact", {"callsign": callsign})
        _set_point_pin(msg, lat, lon, alt)

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