import zmq
import time

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:55555")

time.sleep(1)  # Give the subscriber time to connect

# Send a test message
print("Sending test message...")
socket.send_string("alerts {\"sensor_node_id\": 0, \"alert_text\": \"Hello from PUB!\"}")
print("Message sent!")
