import socket
import eventlet.green.ssl as ssl
import time
import argparse
import fissure.utils


# Instantiate the parser
parser = argparse.ArgumentParser()
parser.add_argument('uid', type=str)
parser.add_argument('lat', type=str)
parser.add_argument('lon', type=str)
parser.add_argument('alt', type=str)
parser.add_argument('time', type=str)  
parser.add_argument('remarks', type=str)
args = parser.parse_args()

# Get Tak server settings
settings: dict = fissure.utils.get_fissure_config()
tak_info = settings.get("tak")
s_addr = tak_info.get("ip_addr")
s_port = tak_info.get("port")
tak_cert = tak_info.get("cert")
tak_key = tak_info.get("key") 

# Client configuration
server_address = (s_addr, s_port)
certfile = tak_cert  # Path to your client certificate
keyfile = tak_key  # Path to your client private key
client_socket = socket.create_connection(server_address)
# Wrap the socket with SSL using the client certificate
# Connect to the server
_uid = args.uid
_time = args.time
lat = args.lat
lon = args.lon

_stale = "2029-08-09T18:18:06.521956Z" # some time in the future
tpms_pressure = args.remarks
sensor_id = args.uid
ssl_client_socket = ssl.wrap_socket(
    client_socket,
    keyfile=keyfile,
    certfile=certfile,
    server_side=False)
time.sleep(1)
cot_msg   = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
cot_msg  += "<event version=\"2.0\" type=\"a-f-G-U-H\" uid=\""+_uid+"\" how=\"m-g\" time=\""+_time+"\" start=\""+_time+"\" stale=\""+_stale+"\">"
cot_msg  += "<detail>"
cot_msg  += "<contact callsign=\""+sensor_id+"\"/>"
cot_msg  += "<remarks>\""+tpms_pressure+"\"</remarks>"
cot_msg  += "</detail>"
cot_msg  += "<point lat=\""+lat+"\" lon=\""+lon+"\" ce=\"0\" le=\"0\" hae=\"0\"/>"
cot_msg  += "</event>"
message = cot_msg.encode('utf-8')

# Send data securely
ssl_client_socket.sendall(message)

# Close the connection
ssl_client_socket.close()
