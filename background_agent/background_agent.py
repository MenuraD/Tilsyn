import psutil
import time
import requests
from datetime import datetime
from pynput import keyboard
import threading

KEYWORDS = ["bully", "hate", "suicide", "kill"]  # Example keywords

class KeyLogger:
    def __init__(self):
        self.current_input = ""
        self.listener = None

    def on_press(self, key):
        try:
            char = key.char
        except AttributeError:
            return  # Skip non-character keys

        self.current_input += char
        # Check if any keyword is in the typed input
        for keyword in KEYWORDS:
            if keyword in self.current_input.lower():
                self.current_input = ""  # Reset to avoid duplicates
                send_to_dashboard(
                    "keyword_alert", 
                    {"keyword": keyword, "context": "Potential risk detected"}
                )
                break

    def start(self):
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

 
#Configuration
FLASK_SERVER = "http://127.0.0.1:5000"
REPORT_INTERVAL = 30
 
def get_active_applications():
  """Track foreground applications using psutil"""
  active_apps = []
  for proc in psutil.process_iter(['pid', 'name']):
    try:
      if proc.info['name'] not in active_apps:
        active_apps.append(proc.info['name'])
    except (psutil.NoSuchProcess, psutil.AccessDenied):
      continue
  return active_apps
 
def send_to_dashboard(activity_type, data):
  """Send data to Flask server"""
  try:
    requests.post(
      f"{FLASK_SERVER}/api/track-activity",
      json={
        "type": activity_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
      }
    )
  except requests.exceptions.RequestException as e:
    print(f"Failed to send data: {e}")
  
if __name__ == "__main__":
    key_logger = KeyLogger()
    key_logger_thread = threading.Thread(target=key_logger.start)
    key_logger_thread.daemon = True  # Terminate with main thread
    key_logger_thread.start()
    while True:
    #Track Applications
      apps = get_active_applications()
      if apps:
        send_to_dashboard("application_usage", {"applications": apps})
      time.sleep(REPORT_INTERVAL)


