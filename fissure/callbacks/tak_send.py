import socket
import eventlet.green.ssl as ssl
import time
import argparse

# Instantiate the parser
parser = argparse.ArgumentParser()
parser.add_argument('uid', type=str)
parser.add_argument('lat', type=str)
parser.add_argument('lon', type=str)
parser.add_argument('alt', type=str)
parser.add_argument('time', type=str)  
parser.add_argument('remarks', type=str)
args = parser.parse_args()

# Client configuration
server_address = ('172.22.0.3', 8089)
certfile = '/var/lib/sss/takserver-docker-5.3-RELEASE-24/tak/certs/files/user-XPS-13-9360.pem'  # Path to your client certificate
keyfile = '/var/lib/sss/takserver-docker-5.3-RELEASE-24/tak/certs/files/user-XPS-13-9360_nopassword.key'  # Path to your client private key
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
