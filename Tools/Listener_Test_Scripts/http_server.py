from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
import random
import time

PORT = 8080

# Simulated list of alerts
alerts = [
    {"sensor_node_id": 0, "alert_text": "Initial alert message"}
]

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        
        # Serve alerts as line-by-line JSON
        for alert in alerts:
            self.wfile.write((json.dumps(alert) + "\n").encode("utf-8"))
    
    def do_POST(self):
        # Add a new alert via a POST request
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            alert = json.loads(post_data.decode('utf-8'))
            alerts.append(alert)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Alert added\n')
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid JSON\n')

def random_alert_generator():
    """
    Generates random alerts and appends them to the alerts list.
    Runs in a background thread to simulate random alert events.
    """
    sensor_node_id = 1
    while True:
        # Random delay between 1 to 10 seconds
        time.sleep(random.uniform(1, 10))

        # Generate a random alert message
        alert_text = f"Random alert {random.randint(1000, 9999)}"
        new_alert = {"sensor_node_id": sensor_node_id, "alert_text": alert_text}
        
        # Add the alert to the list and print it to the console
        alerts.append(new_alert)
        print(f"Generated new alert: {new_alert}")


if __name__ == "__main__":
    # Start the random alert generator in a separate thread
    alert_thread = threading.Thread(target=random_alert_generator, daemon=True)
    alert_thread.start()

    # Start the HTTP server
    server = HTTPServer(("localhost", PORT), SimpleHTTPRequestHandler)
    print(f"Serving alerts at http://localhost:{PORT}")
    server.serve_forever()