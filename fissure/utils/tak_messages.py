#!/usr/bin/env python3
import base64
import hashlib
import os
import pytak
import tempfile
from typing import Union, Tuple
import xml.etree.ElementTree as ET
import zipfile

from fissure.utils.artifacts import Artifact
from fissure.utils.common import extractFrequencyFromUID, get_fissure_config
from fissure.utils.library import classifyFrequencyFromTextDirect

# Optional cryptography imports for certificate handling
try:
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.hazmat.primitives.serialization import pkcs12
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


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

    # Normalize in case pytak returned a string or None
    if msg is None:
        # Create minimal CoT structure if pytak fails
        msg = ET.Element("event")
        msg.set("version", "2.0")
        msg.set("uid", uid)
        msg.set("time", "2025-01-01T00:00:00.000Z")
        msg.set("start", "2025-01-01T00:00:00.000Z") 
        msg.set("stale", f"2025-01-01T{stale:02d}:00:00.000Z")
    elif not isinstance(msg, ET.Element):
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


def _format_xml_pretty(element):
    """Format XML element with proper indentation like WinTAK."""
    import xml.dom.minidom
    
    rough_string = ET.tostring(element, encoding='UTF-8', xml_declaration=True)
    reparsed = xml.dom.minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding='UTF-8').decode('UTF-8')


def create_artifact_data_package(artifact: Union[Artifact, dict], file_data: bytes) -> Tuple[bytes, str]:
    """Create TAK-compatible data package for artifact with certificate signing."""
    
    if isinstance(artifact, dict):
        artifact = Artifact.from_dict(artifact)

    # Get TAK certificate path from config
    fissure_config = get_fissure_config()
    cert_path = fissure_config['tak'].get('webadmin_cert')
    
    # Generate a proper package name and subdirectory structure like WinTAK
    package_name = f"DP-{artifact.name[:20].upper()}"  # Max 20 chars, uppercase
    package_uid = artifact.id
    
    # Create subdirectory like WinTAK does (using first part of artifact ID)
    subdir = artifact.id.replace('-', '')[:32]  # Remove dashes, take first 32 chars
    
    # Create temporary ZIP file
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add the artifact file in subdirectory structure like WinTAK
            artifact_filename = os.path.basename(artifact.file_path)
            zip_entry_path = f"{subdir}/{artifact_filename}"
            zipf.writestr(zip_entry_path, file_data)

            # Create MANIFEST.xml with certificate info
            if cert_path and os.path.exists(cert_path):
                manifest_xml = _create_tak_manifest_with_certs(artifact, zip_entry_path, cert_path)
                print(f"\n=== SIGNED MANIFEST XML ===\n{manifest_xml}\n")
            else:
                # Fallback to unsigned manifest
                manifest = ET.Element("MissionPackageManifest", version="2")
                config = ET.SubElement(manifest, "Configuration")
                ET.SubElement(config, "Parameter", name="name", value=package_name)
                ET.SubElement(config, "Parameter", name="uid", value=package_uid)
                contents = ET.SubElement(manifest, "Contents")
                ET.SubElement(contents, "Content", 
                             zipEntry=zip_entry_path,
                             ignore="false")
                manifest_xml = _format_xml_pretty(manifest)
                print(f"\n=== UNSIGNED MANIFEST XML ===\n{manifest_xml}\n")
            
            zipf.writestr("MANIFEST.xml", manifest_xml.encode('UTF-8'))
        
        # Read the ZIP data
        with open(temp_zip.name, "rb") as f:
            zip_data = f.read()
            
        # Clean up temp file
        os.unlink(temp_zip.name)
    
    # Sign the data package if certificate is available
    if cert_path and os.path.exists(cert_path):
        print("=== SIGNING DATA PACKAGE WITH TAK CERTIFICATE ===")
        zip_data = _sign_data_package(zip_data, cert_path)
        print("=== DATA PACKAGE SIGNED ===")
    else:
        print("=== WARNING: No TAK certificate found, sending unsigned data package ===")
    
    return zip_data, artifact_filename


async def send_artifact_event(component: object, artifact: Union[Artifact, dict], artifact_data: bytes) -> None:
    """Send artifact event to TAK clients with certificate authentication."""
    if isinstance(artifact, dict):
        artifact = Artifact.from_dict(artifact)

    artifact_id = artifact.id
    tak_data, _ = create_artifact_data_package(artifact, artifact_data)
    
    # Calculate SHA256 checksum
    sha256_hash = hashlib.sha256(tak_data).hexdigest()

    # Get certificate info for authentication
    fissure_config = get_fissure_config()
    cert_path = fissure_config['tak'].get('webadmin_cert', '')

    # Build CoT message manually for fileshare - match WinTAK format
    msg, detail = _build_base_event(
        uid=f"FISSURE-DP-{artifact_id}",  # More descriptive UID
        stale=3600  # 1 hour stale time like WinTAK
    )

    # Set proper CoT type for data package
    msg.set("type", "b-f-t-d")  # File transfer data
    msg.set("how", "h-g-i-g-o")  # Generated by software
    msg.set("version", "2.0")  # Explicit version

    # Add authentication info if certificate is available
    if cert_path and os.path.exists(cert_path):
        # Add certificate-based authentication
        auth = ET.SubElement(detail, "authentication")
        auth.set("type", "certificate")
        auth.set("cert", "webadmin")

    # Add contact element like WinTAK does
    contact = ET.SubElement(detail, "contact")
    contact.set("callsign", f"FISSURE-{artifact.source_id[:8]}")

    # Create fileshare element directly under detail (TAK standard)
    fileshare = ET.SubElement(detail, "fileshare")
    
    # Add filename with proper .zip extension
    package_filename = f"DP-{artifact.name[:20].upper()}.zip"
    ET.SubElement(fileshare, "filename").text = package_filename
    ET.SubElement(fileshare, "sizeInBytes").text = str(len(tak_data))
    ET.SubElement(fileshare, "sha256").text = sha256_hash
    
    # Add sender information with certificate info
    ET.SubElement(fileshare, "senderUrl").text = "FISSURE"
    ET.SubElement(fileshare, "name").text = artifact.name
    
    # Add signature info if package is signed
    if cert_path and os.path.exists(cert_path):
        ET.SubElement(fileshare, "signed").text = "true"
        ET.SubElement(fileshare, "signature").text = "RSA-SHA256"
    
    # Base64 encoded data
    ET.SubElement(fileshare, "data").text = base64.b64encode(tak_data).decode('utf-8')

    # Set point coordinates (even data packages need location)
    point = msg.find("point")
    if point is None:
        point = ET.SubElement(msg, "point")
    point.set("lat", "0.0")
    point.set("lon", "0.0") 
    point.set("hae", "0.0")
    point.set("ce", "9999999.0")
    point.set("le", "9999999.0")

    # Log the final CoT message for debugging
    msg_xml = ET.tostring(msg, encoding="utf-8").decode("utf-8")
    print(f"\n=== TAK CoT MESSAGE (WITH CERTS) ===\n{msg_xml}\n======================\n")

    return _send_to_tak(component, msg)


async def send_artifact_event_with_mission_package(component: object, artifact: Union[Artifact, dict], artifact_data: bytes) -> None:
    """Send artifact as Mission Package CoT message - alternative format for better TAK compatibility."""
    if isinstance(artifact, dict):
        artifact = Artifact.from_dict(artifact)

    artifact_id = artifact.id
    tak_data, _ = create_artifact_data_package(artifact, artifact_data)
    sha256_hash = hashlib.sha256(tak_data).hexdigest()

    # Build CoT message as Mission Package instead of fileshare
    msg, detail = _build_base_event(
        uid=f"FISSURE-MP-{artifact_id}",  # Mission Package UID
        stale=7200  # 2 hour stale time
    )

    # Use Mission Package CoT type
    msg.set("type", "t-x-m-p")  # Mission Package type
    msg.set("how", "h-g-i-g-o")
    msg.set("version", "2.0")

    # Add mission package details
    mission = ET.SubElement(detail, "mission")
    mission.set("type", "CHANGE")
    mission.set("name", f"DP-{artifact.name[:20].upper()}")
    mission.set("uid", artifact_id)
    
    # Add the actual data package as attachment
    package = ET.SubElement(detail, "missionpackage")
    package.set("filename", f"DP-{artifact.name[:20].upper()}.zip")
    package.set("size", str(len(tak_data)))
    package.set("hash", sha256_hash)
    
    # Base64 encoded data
    data_elem = ET.SubElement(package, "data")
    data_elem.text = base64.b64encode(tak_data).decode('utf-8')

    # Add contact info
    contact = ET.SubElement(detail, "contact")
    contact.set("callsign", f"FISSURE-{artifact.source_id[:8]}")

    # Suppress point location for mission packages
    _set_point_suppressed(msg)

    # Log the message
    msg_xml = ET.tostring(msg, encoding="utf-8").decode("utf-8")
    print(f"\n=== TAK MISSION PACKAGE CoT ===\n{msg_xml}\n======================\n")

    return _send_to_tak(component, msg)


def _load_tak_certificate(cert_path: str, password: str = 'atakatak'):
    """Load TAK certificate from p12 file."""
    if not CRYPTO_AVAILABLE:
        print("Cryptography library not available - cannot load certificates")
        return None, None, None
    
    try:
        with open(cert_path, 'rb') as f:
            cert_data = f.read()
        
        private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
            cert_data, password.encode('utf-8')
        )
        
        return private_key, certificate, additional_certificates
    except Exception as e:
        print(f"Error loading certificate: {e}")
        return None, None, None


def _sign_data_package(zip_data: bytes, cert_path: str) -> bytes:
    """Sign TAK Data Package with certificate."""
    if not CRYPTO_AVAILABLE:
        print("Cryptography library not available - returning unsigned package")
        return zip_data
    
    try:
        private_key, certificate, _ = _load_tak_certificate(cert_path)
        
        if not private_key or not certificate:
            print("Certificate loading failed, returning unsigned package")
            return zip_data
        
        # Only sign if we have an RSA key
        if not isinstance(private_key, rsa.RSAPrivateKey):
            print("Certificate does not contain RSA key, returning unsigned package")
            return zip_data
            
        # Create signature
        signature = private_key.sign(
            zip_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # For TAK, we need to add the signature to the package
        # This is a simplified approach - real TAK signing is more complex
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
            # Copy original zip
            temp_zip.write(zip_data)
            temp_path = temp_zip.name
            
        # Add signature file to the zip
        with zipfile.ZipFile(temp_path, 'a') as zipf:
            zipf.writestr("META-INF/SIGNATURE.RSA", signature)
            
            # Add certificate
            cert_der = certificate.public_bytes(serialization.Encoding.DER)
            zipf.writestr("META-INF/CERT.RSA", cert_der)
            
        # Read back the signed zip
        with open(temp_path, 'rb') as f:
            signed_data = f.read()
            
        os.unlink(temp_path)
        return signed_data
        
    except Exception as e:
        print(f"Error signing data package: {e}")
        return zip_data  # Return unsigned on error


def _create_tak_manifest_with_certs(artifact: Union[Artifact, dict], zip_entry_path: str, cert_path: str) -> str:
    """Create TAK manifest with certificate information."""
    if isinstance(artifact, dict):
        artifact = Artifact.from_dict(artifact)
    
    # Load certificate for metadata
    _, certificate, _ = _load_tak_certificate(cert_path)
    
    package_name = f"DP-{artifact.name[:20].upper()}"
    package_uid = artifact.id
    
    manifest = ET.Element("MissionPackageManifest", version="2")
    
    # Configuration
    config = ET.SubElement(manifest, "Configuration")
    ET.SubElement(config, "Parameter", name="name", value=package_name)
    ET.SubElement(config, "Parameter", name="uid", value=package_uid)
    
    # Add certificate info if available
    if certificate:
        try:
            subject = certificate.subject.rfc4514_string()
            ET.SubElement(config, "Parameter", name="creator", value=subject)
            ET.SubElement(config, "Parameter", name="signed", value="true")
        except Exception as e:
            print(f"Error extracting certificate info: {e}")
    
    # Contents
    contents = ET.SubElement(manifest, "Contents")
    ET.SubElement(contents, "Content", 
                 zipEntry=zip_entry_path,
                 ignore="false")
    
    return _format_xml_pretty(manifest)