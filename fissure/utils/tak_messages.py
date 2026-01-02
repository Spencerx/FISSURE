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
    """Create TAK-compatible data package for artifact - WinTAK format (simplified, no certificates)."""
    
    if isinstance(artifact, dict):
        artifact = Artifact.from_dict(artifact)

    # Generate a proper package name matching WinTAK conventions
    package_name = f"DP-{artifact.name[:20].upper().replace(' ', '_')}"
    package_uid = artifact.id
    
    # Create subdirectory like WinTAK does (use sanitized artifact ID)
    subdir = artifact.id.replace('-', '').replace('_', '')[:32]
    if not subdir:
        subdir = "artifacts"
    
    # Create temporary ZIP file
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add the artifact file in subdirectory structure like WinTAK
            artifact_filename = os.path.basename(artifact.file_path)
            # Ensure we have a valid filename
            if not artifact_filename:
                artifact_filename = f"{artifact.name}.bin"
            
            zip_entry_path = f"{subdir}/{artifact_filename}"
            zipf.writestr(zip_entry_path, file_data)

            # Create simple MANIFEST.xml matching WinTAK format exactly
            manifest = ET.Element("MissionPackageManifest", version="2")
            
            # Configuration - name first, then uid (order matters for WinTAK)
            config = ET.SubElement(manifest, "Configuration")
            ET.SubElement(config, "Parameter", name="name", value=package_name)
            ET.SubElement(config, "Parameter", name="uid", value=package_uid)
            
            # Contents section
            contents = ET.SubElement(manifest, "Contents")
            ET.SubElement(contents, "Content", 
                         zipEntry=zip_entry_path,
                         ignore="false")
            
            # Format XML to match WinTAK style (pretty print with proper indentation)
            manifest_xml = _format_xml_pretty(manifest)
            print(f"\n=== WINTAK-COMPATIBLE MANIFEST XML ===\n{manifest_xml}\n")
            
            # Save manifest in MANIFEST folder exactly like WinTAK
            zipf.writestr("MANIFEST/manifest.xml", manifest_xml.encode('UTF-8'))
        
        # Read the ZIP data
        with open(temp_zip.name, "rb") as f:
            zip_data = f.read()
            
        # Clean up temp file
        os.unlink(temp_zip.name)
    
    print("=== DATA PACKAGE CREATED (WINTAK-COMPATIBLE FORMAT) ===")
    print(f"Package Name: {package_name}")
    print(f"Package UID: {package_uid}")  
    print(f"Subdirectory: {subdir}")
    print(f"Artifact File: {artifact_filename}")
    print(f"ZIP Entry Path: {zip_entry_path}")
    print("======================================================")
    
    return zip_data, artifact_filename


async def send_artifact_event(component: object, artifact: Union[Artifact, dict], artifact_data: bytes) -> None:
    """Send artifact event to TAK clients with WinTAK-compatible data package format."""
    if isinstance(artifact, dict):
        artifact = Artifact.from_dict(artifact)

    artifact_id = artifact.id
    tak_data, _ = create_artifact_data_package(artifact, artifact_data)
    
    # Calculate SHA256 checksum
    sha256_hash = hashlib.sha256(tak_data).hexdigest()

    # Build CoT message manually for fileshare - match WinTAK format exactly
    msg, detail = _build_base_event(
        uid=f"FISSURE-DP-{artifact_id}",  # More descriptive UID
        stale=300  # 5 minute stale time (longer for file transfers)
    )

    # Set proper CoT type for data package - WinTAK uses b-f-t-r for file transfers
    msg.set("type", "b-f-t-r")  # File transfer request (like WinTAK)
    msg.set("version", "2.0")  # Version 2.0 like WinTAK
    
    # Set proper time attributes
    import datetime
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    msg.set("time", now)
    msg.set("start", now)
    stale_time = (datetime.datetime.utcnow() + datetime.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    msg.set("stale", stale_time)

    # Upload the data package to TAK server first
    package_filename = f"DP-{artifact.name[:20].upper().replace(' ', '_')}.zip"
    
    # TEMPORARY: Save package to Downloads for manual comparison/upload
    downloads_path = os.path.expanduser("~/Downloads")
    local_package_path = os.path.join(downloads_path, f"FISSURE_{package_filename}")
    try:
        with open(local_package_path, "wb") as f:
            f.write(tak_data)
        print(f"=== SAVED DATA PACKAGE TO: {local_package_path} ===")
        print("You can manually compare this with WinTAK packages or upload via WebTAK")
        component.logger.info(f"Data package saved locally: {local_package_path}")
    except Exception as e:
        component.logger.error(f"Could not save package locally: {e}")
    
    # Try to upload to TAK server
    sender_url = await upload_data_package_to_tak_server(tak_data, sha256_hash, package_filename, component)
    
    # Create fileshare element directly under detail (TAK standard)
    fileshare = ET.SubElement(detail, "fileshare")
    
    # Add attributes exactly like WinTAK format (order matters for some TAK clients)
    fileshare.set("filename", package_filename)
    fileshare.set("senderUrl", sender_url)  
    fileshare.set("sizeInBytes", str(len(tak_data)))
    fileshare.set("sha256", sha256_hash)
    fileshare.set("senderUid", f"FISSURE-{artifact.source_id}")
    fileshare.set("senderCallsign", f"FISSURE-{artifact.source_id[:8]}")
    fileshare.set("name", f"DP-{artifact.name[:20].upper().replace(' ', '_')}")

    # Add ackrequest element like WinTAK
    ackrequest = ET.SubElement(detail, "ackrequest")
    ackrequest.set("uid", f"ack-{artifact_id[:8]}")
    ackrequest.set("ackrequested", "true")
    ackrequest.set("tag", f"DP-{artifact.name[:20].upper().replace(' ', '_')}")

    '''# TEMPORARY TEST: Target specific user "LONE STAR" for artifact download
    dest = ET.SubElement(detail, "dest")
    dest.set("callsign", "LONE STAR")
    print(f"=== TARGETING ARTIFACT TO USER: LONE STAR ===")'''

    # Set point coordinates exactly like WinTAK (0,0 with high uncertainty)
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
    print("\n=== TAK CoT MESSAGE (WINTAK FORMAT) ===")
    print(msg_xml)
    print("======================\n")

    print("=== DATA PACKAGE DETAILS ===")
    print(f"SHA256: {sha256_hash}")
    print(f"Size: {len(tak_data)} bytes")
    print(f"Filename: {package_filename}")
    print(f"Download URL: {sender_url}")
    print("============================")

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


async def send_artifact_event_direct_embed(component: object, artifact: Union[Artifact, dict], artifact_data: bytes) -> None:
    """Send artifact event with data directly embedded in CoT message - fallback when TAK server upload fails."""
    if isinstance(artifact, dict):
        artifact = Artifact.from_dict(artifact)

    artifact_id = artifact.id
    tak_data, _ = create_artifact_data_package(artifact, artifact_data)
    
    # Calculate SHA256 checksum
    sha256_hash = hashlib.sha256(tak_data).hexdigest()

    # Build CoT message manually for fileshare - with embedded data
    msg, detail = _build_base_event(
        uid=f"FISSURE-DP-{artifact_id}",  # More descriptive UID
        stale=10  # 10 second stale time like WinTAK example
    )

    # Set proper CoT type for data package
    msg.set("type", "b-f-t-d")  # File transfer data (with embedded data)
    msg.set("version", "2")  # Version 2 like WinTAK
    
    # Create fileshare element directly under detail (TAK standard)
    fileshare = ET.SubElement(detail, "fileshare")
    
    # Add attributes for direct data transfer
    package_filename = f"DP-{artifact.name[:20].upper()}.zip"
    fileshare.set("filename", package_filename)
    fileshare.set("sizeInBytes", str(len(tak_data)))
    fileshare.set("sha256", sha256_hash)
    
    # Add sender information
    fileshare.set("senderUid", f"FISSURE-{artifact.source_id}")
    fileshare.set("senderCallsign", f"FISSURE-{artifact.source_id[:8]}")
    fileshare.set("name", f"DP-{artifact.name[:20].upper()}")

    # Embed the data directly in the CoT message
    data_element = ET.SubElement(fileshare, "data")
    data_element.text = base64.b64encode(tak_data).decode('utf-8')

    # Add ackrequest element like WinTAK
    ackrequest = ET.SubElement(detail, "ackrequest")
    ackrequest.set("uid", f"ack-{artifact_id[:8]}")
    ackrequest.set("ackrequested", "")
    ackrequest.set("tag", f"DP-{artifact.name[:20].upper()}")

    # Set point coordinates exactly like WinTAK
    point = msg.find("point")
    if point is None:
        point = ET.SubElement(msg, "point")
    point.set("lat", "0")
    point.set("lon", "0") 
    point.set("hae", "0")
    point.set("ce", "9999999")
    point.set("le", "9999999")

    # Log the final CoT message for debugging
    msg_xml = ET.tostring(msg, encoding="utf-8").decode("utf-8")
    print("\n=== TAK CoT MESSAGE (EMBEDDED DATA) ===")
    print(msg_xml[:1000] + "..." if len(msg_xml) > 1000 else msg_xml)  # Truncate for readability
    print("======================\n")

    print("=== DATA PACKAGE EMBEDDED IN COT MESSAGE ===")
    print(f"SHA256: {sha256_hash}")
    print(f"Size: {len(tak_data)} bytes")
    print(f"Filename: {package_filename}")
    print("===============================================")

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


async def upload_data_package_to_tak_server(tak_data: bytes, sha256_hash: str, filename: str, component) -> str:
    """Upload data package to TAK server sync endpoint with proper client certificate authentication."""
    try:
        import aiohttp
        import ssl
        import socket
        import tempfile
        
        # Get TAK server configuration
        fissure_config = get_fissure_config()
        tak_config = fissure_config.get('tak', {})
        
        tak_internal_ip = tak_config.get('ip_addr', 'localhost')
        api_port = '8443'  # Standard TAK server HTTPS API port
        p12_cert_path = tak_config.get('webadmin_cert', '')
        
        # Get external/host IP address for WinTAK clients to access
        external_ip = tak_config.get('external_ip')
        
        if not external_ip:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    external_ip = s.getsockname()[0]
            except Exception:
                external_ip = "169.254.152.101"
                component.logger.warning(f"Could not auto-detect external IP, using fallback: {external_ip}")
        
        component.logger.info(f"TAK server - Internal IP: {tak_internal_ip}:{api_port}, External IP: {external_ip}")
        
        # Download URL for clients
        download_url = f"https://{external_ip}:{api_port}/Marti/sync/content?hash={sha256_hash}"
        
        # Check if P12 certificate exists
        if not p12_cert_path or not os.path.exists(p12_cert_path):
            component.logger.error(f"Client certificate not found: {p12_cert_path}")
            component.logger.error("TAK server upload requires client certificate authentication")
            return download_url
        
        component.logger.info(f"Using client certificate: {p12_cert_path}")
        
        # Convert P12 certificate to PEM for aiohttp
        cert_pem_path = None
        key_pem_path = None
        
        try:
            # Import cryptography if available
            try:
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.primitives.serialization import pkcs12
                
                # Load P12 certificate
                with open(p12_cert_path, 'rb') as f:
                    p12_data = f.read()
                
                private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                    p12_data, b'atakatak'  # Standard TAK password
                )
                
                if private_key and certificate:
                    # Convert to PEM format
                    key_pem = private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    )
                    
                    cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
                    
                    # Save to temporary files
                    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.key') as key_file:
                        key_file.write(key_pem)
                        key_pem_path = key_file.name
                    
                    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.crt') as cert_file:
                        cert_file.write(cert_pem)
                        cert_pem_path = cert_file.name
                    
                    component.logger.info("✅ Successfully converted P12 to PEM format")
                else:
                    raise Exception("Could not extract key/certificate from P12 file")
                    
            except ImportError:
                component.logger.error("cryptography library not available - cannot convert P12 certificate")
                return download_url
            
            # Create SSL context with client certificate
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE  # Accept self-signed certs
            ssl_context.load_cert_chain(cert_pem_path, key_pem_path)
            
            component.logger.info("✅ SSL context created with client certificate")
            
            # Prepare upload data
            data = aiohttp.FormData()
            data.add_field('assetfile', tak_data, filename=filename, content_type='application/zip')
            
            # Headers
            headers = {
                'User-Agent': 'FISSURE-TAK-Client/1.0',
                'Accept': 'application/json, */*',
                'Connection': 'close'
            }
            
            # Try upload to TAK server
            upload_url = f"https://{tak_internal_ip}:{api_port}/Marti/sync/upload"
            component.logger.info(f"Uploading to: {upload_url}")
            
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=ssl_context),
                timeout=aiohttp.ClientTimeout(total=60)
            ) as session:
                
                component.logger.info(f"Uploading {len(tak_data)} bytes with client certificate...")
                
                async with session.post(upload_url, data=data, headers=headers) as response:
                    component.logger.info(f"Upload response status: {response.status}")
                    
                    # Read response for debugging
                    try:
                        response_text = await response.text()
                        if response_text:
                            component.logger.info(f"Upload response: {response_text[:300]}")
                    except Exception as e:
                        component.logger.warning(f"Could not read response body: {e}")
                    
                    if response.status in [200, 201, 202]:
                        component.logger.info("✅ Successfully uploaded data package to TAK server!")
                        return download_url
                    elif response.status == 409:
                        component.logger.info("✅ Data package already exists on TAK server")
                        return download_url
                    elif response.status == 401:
                        component.logger.error("❌ Authentication failed - check client certificate")
                        return download_url
                    elif response.status == 403:
                        component.logger.error("❌ Forbidden - check TAK server permissions")
                        return download_url
                    else:
                        component.logger.error(f"❌ Upload failed with HTTP {response.status}")
                        return download_url
            
        except Exception as e:
            component.logger.error(f"Certificate upload failed: {e}")
            return download_url
            
        finally:
            # Clean up temporary certificate files
            if cert_pem_path and os.path.exists(cert_pem_path):
                os.unlink(cert_pem_path)
            if key_pem_path and os.path.exists(key_pem_path):
                os.unlink(key_pem_path)
                    
    except ImportError:
        component.logger.warning("aiohttp not available - cannot upload to TAK server")
        fissure_config = get_fissure_config()
        tak_config = fissure_config.get('tak', {})
        external_ip = tak_config.get('external_ip', "169.254.152.101")
        download_url = f"https://{external_ip}:8443/Marti/sync/content?hash={sha256_hash}"
        return download_url
    except Exception as e:
        component.logger.error(f"Error in upload_data_package_to_tak_server: {e}")
        fissure_config = get_fissure_config()
        tak_config = fissure_config.get('tak', {})
        external_ip = tak_config.get('external_ip', "169.254.152.101")
        download_url = f"https://{external_ip}:8443/Marti/sync/content?hash={sha256_hash}"
        return download_url