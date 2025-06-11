import pystray
from PIL import Image, ImageDraw
import threading
import psutil
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
import os
from dotenv import load_dotenv
import logging
import paho.mqtt.client as mqtt
import socket
import json
import uuid

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Home Assistant Computer Activity Monitor")

# Get CORS settings from environment
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to control the server
server_running = True

# MQTT Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
DEVICE_NAME = os.getenv('DEVICE_NAME', socket.gethostname())
DEVICE_ID = os.getenv('DEVICE_ID', str(uuid.uuid4()))

# MQTT Client setup
mqtt_client = mqtt.Client()
if MQTT_USERNAME and MQTT_PASSWORD:
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the MQTT broker"""
    if rc == 0:
        logger.info("Connected to MQTT broker")
        publish_discovery_config()
    else:
        logger.error(f"Failed to connect to MQTT broker with code: {rc}")

def publish_discovery_config():
    """Publish Home Assistant discovery configuration"""
    base_topic = f"homeassistant/sensor/{DEVICE_ID}"
    
    # Status sensor configuration
    status_config = {
        "name": f"{DEVICE_NAME} Status",
        "unique_id": f"{DEVICE_ID}_status",
        "state_topic": f"{base_topic}/status",
        "device_class": "binary_sensor",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    # CPU sensor
    cpu_config = {
        "name": f"{DEVICE_NAME} CPU Usage",
        "unique_id": f"{DEVICE_ID}_cpu",
        "state_topic": f"{base_topic}/cpu",
        "unit_of_measurement": "%",
        "device_class": "sensor",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    # Memory sensor
    mem_config = {
        "name": f"{DEVICE_NAME} Memory (RAM) Usage",
        "unique_id": f"{DEVICE_ID}_memory",
        "state_topic": f"{base_topic}/memory",
        "unit_of_measurement": "%",
        "device_class": "sensor",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    # Disk sensor
    disk_config = {
        "name": f"{DEVICE_NAME} Disk Usage",
        "unique_id": f"{DEVICE_ID}_disk",
        "state_topic": f"{base_topic}/disk",
        "device_class": "sensor",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    # Uptime sensor
    uptime_config = {
        "name": f"{DEVICE_NAME} Uptime (Seconds)",
        "unique_id": f"{DEVICE_ID}_uptime",
        "state_topic": f"{base_topic}/uptime",
        "device_class": "sensor",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    # Formatted Uptime sensor
    formatted_uptime_config = {
        "name": f"{DEVICE_NAME} Uptime (Formatted)",
        "unique_id": f"{DEVICE_ID}_uptime_formatted",
        "state_topic": f"{base_topic}/uptime_formatted",
        "device_class": "sensor",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    # Publish configurations
    mqtt_client.publish(f"{base_topic}/status/config", json.dumps(status_config), retain=True)
    mqtt_client.publish(f"{base_topic}/cpu/config", json.dumps(cpu_config), retain=True)
    mqtt_client.publish(f"{base_topic}/memory/config", json.dumps(mem_config), retain=True)
    mqtt_client.publish(f"{base_topic}/disk/config", json.dumps(disk_config), retain=True)
    mqtt_client.publish(f"{base_topic}/uptime/config", json.dumps(uptime_config), retain=True)
    mqtt_client.publish(f"{base_topic}/uptime_formatted/config", json.dumps(formatted_uptime_config), retain=True)


def publish_system_info():
    """Publish system information to MQTT"""
    if not mqtt_client.is_connected():
        return
        
    base_topic = f"homeassistant/sensor/{DEVICE_ID}"
    system_info = get_system_info()
    
    # Publish status
    mqtt_client.publish(f"{base_topic}/status", "online")
    
    # Publish each metric individually
    mqtt_client.publish(f"{base_topic}/cpu", str(system_info["cpu_percent"]))
    mqtt_client.publish(f"{base_topic}/memory", str(system_info["memory_percent"]))
    mqtt_client.publish(f"{base_topic}/disk", str(system_info["disk_usage"]["percent"]))
    mqtt_client.publish(f"{base_topic}/uptime", str(system_info["uptime"]))

    # Publish formatted uptime (HH:MM:SS)
    formatted_uptime = time.strftime("%H:%M:%S", time.gmtime(system_info["uptime"]))
    mqtt_client.publish(f"{base_topic}/uptime_formatted", formatted_uptime)

def create_tray_icon():
    # Create a simple icon (a white circle on black background)
    icon_size = 64
    image = Image.new('RGB', (icon_size, icon_size), color='black')
    dc = ImageDraw.Draw(image)
    dc.ellipse([8, 8, icon_size-8, icon_size-8], fill='white')
    return image

def get_system_info():
    """Get basic system information"""
    data = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "uptime": time.time() - psutil.boot_time()
    }

    disk_usage = psutil.disk_usage('/');

    data["disk_usage"] = {
        "total": disk_usage.total,
        "used": disk_usage.used,
        "free": disk_usage.free,
        "percent": disk_usage.percent
    }

    # Figure out if the disk usage is in MB, GB, or TB
    if disk_usage.total > 1024 * 1024 * 1024:
        denominator = "GB"
    elif disk_usage.total > 1024 * 1024:
        denominator = "MB"
    else:
        denominator = "B"

    data["disk_usage"]["total"] = f"{disk_usage.total / (1024 * 1024 * 1024):.2f} {denominator}"
    data["disk_usage"]["used"] = f"{disk_usage.used / (1024 * 1024 * 1024):.2f} {denominator}"
    data["disk_usage"]["free"] = f"{disk_usage.free / (1024 * 1024 * 1024):.2f} {denominator}"
    data["disk_usage"]["percent"] = f"{disk_usage.percent:.2f}%"

    return data



@app.get("/")
async def root():
    """Root endpoint for health check"""
    logger.debug("Health check requested")

    data = {
        "status": "online",
        "timestamp": round(time.time(), 2),
        "time_in_hours_minutes_seconds" : time.strftime("%H:%M:%S", time.gmtime(time.time() - psutil.boot_time()))
    }
    return data

@app.get("/system")
async def system_info():
    """Get system information"""
    logger.debug("System info requested")
    return get_system_info()

def run_server():
    """Run the FastAPI server"""
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

def on_exit(icon):
    """Handle exit from system tray"""
    global server_running
    server_running = False
    logger.info("Shutting down application")
    if mqtt_client.is_connected():
        mqtt_client.publish(f"homeassistant/sensor/{DEVICE_ID}/status", "offline", retain=True)
        mqtt_client.disconnect()
    icon.stop()
    os._exit(0)

def mqtt_publish_loop():
    """Background thread for publishing MQTT updates"""
    while server_running:
        try:
            if not mqtt_client.is_connected():
                mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
                mqtt_client.loop_start()
            publish_system_info()
        except Exception as e:
            logger.error(f"Error in MQTT publish loop: {e}")
        time.sleep(30)  # Update every 30 seconds

def main():
    logger.info("Starting Home Assistant Desktop Monitor")
    
    # Set up MQTT client
    mqtt_client.on_connect = on_connect
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")
    
    # Start MQTT publish thread
    mqtt_thread = threading.Thread(target=mqtt_publish_loop)
    mqtt_thread.daemon = True
    mqtt_thread.start()
    
    # Start the API server in a separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    # Create and run the system tray icon
    icon = pystray.Icon("ha_desk")
    icon.icon = create_tray_icon()
    icon.title = "Home Assistant Desktop Monitor"
    icon.menu = pystray.Menu(
        pystray.MenuItem("Exit", on_exit)
    )
    
    # Run the icon
    icon.run()

if __name__ == "__main__":
    main()  