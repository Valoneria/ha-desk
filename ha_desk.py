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
from collections import deque
from statistics import mean

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

# Data collection settings
COLLECTION_INTERVAL = 1  # Collect data every second
PUBLISH_INTERVAL = 30    # Publish every 30 seconds
MAX_SAMPLES = PUBLISH_INTERVAL // COLLECTION_INTERVAL

# Data collection queues
cpu_samples = deque(maxlen=MAX_SAMPLES)
memory_samples = deque(maxlen=MAX_SAMPLES)
disk_samples = deque(maxlen=MAX_SAMPLES)

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
    binary_base_topic = f"homeassistant/binary_sensor/{DEVICE_ID}"
    
    # Status sensor configuration (as binary_sensor)
    status_config = {
        "name": f"{DEVICE_NAME} Status",
        "unique_id": f"{DEVICE_ID}_status",
        "state_topic": f"{binary_base_topic}/status",
        "device_class": "connectivity",
        "payload_on": "online",
        "payload_off": "offline",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    # CPU sensors
    cpu_config = {
        "name": f"{DEVICE_NAME} CPU Usage",
        "unique_id": f"{DEVICE_ID}_cpu",
        "state_topic": f"{base_topic}/cpu",
        "unit_of_measurement": "%",
        "device_class": "power",
        "state_class": "measurement",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    cpu_min_config = {
        "name": f"{DEVICE_NAME} CPU Usage (Min)",
        "unique_id": f"{DEVICE_ID}_cpu_min",
        "state_topic": f"{base_topic}/cpu_min",
        "unit_of_measurement": "%",
        "device_class": "power",
        "state_class": "measurement",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    cpu_max_config = {
        "name": f"{DEVICE_NAME} CPU Usage (Max)",
        "unique_id": f"{DEVICE_ID}_cpu_max",
        "state_topic": f"{base_topic}/cpu_max",
        "unit_of_measurement": "%",
        "device_class": "power",
        "state_class": "measurement",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    cpu_avg_config = {
        "name": f"{DEVICE_NAME} CPU Usage (Avg)",
        "unique_id": f"{DEVICE_ID}_cpu_avg",
        "state_topic": f"{base_topic}/cpu_avg",
        "unit_of_measurement": "%",
        "device_class": "power",
        "state_class": "measurement",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    # Memory sensors
    mem_config = {
        "name": f"{DEVICE_NAME} Memory (RAM) Usage",
        "unique_id": f"{DEVICE_ID}_memory",
        "state_topic": f"{base_topic}/memory",
        "unit_of_measurement": "%",
        "device_class": "power",
        "state_class": "measurement",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    mem_min_config = {
        "name": f"{DEVICE_NAME} Memory Usage (Min)",
        "unique_id": f"{DEVICE_ID}_memory_min",
        "state_topic": f"{base_topic}/memory_min",
        "unit_of_measurement": "%",
        "device_class": "power",
        "state_class": "measurement",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    mem_max_config = {
        "name": f"{DEVICE_NAME} Memory Usage (Max)",
        "unique_id": f"{DEVICE_ID}_memory_max",
        "state_topic": f"{base_topic}/memory_max",
        "unit_of_measurement": "%",
        "device_class": "power",
        "state_class": "measurement",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    mem_avg_config = {
        "name": f"{DEVICE_NAME} Memory Usage (Avg)",
        "unique_id": f"{DEVICE_ID}_memory_avg",
        "state_topic": f"{base_topic}/memory_avg",
        "unit_of_measurement": "%",
        "device_class": "power",
        "state_class": "measurement",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    # Disk sensors
    disk_config = {
        "name": f"{DEVICE_NAME} Disk Usage",
        "unique_id": f"{DEVICE_ID}_disk",
        "state_topic": f"{base_topic}/disk",
        "unit_of_measurement": "%",
        "device_class": "power",
        "state_class": "measurement",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    disk_min_config = {
        "name": f"{DEVICE_NAME} Disk Usage (Min)",
        "unique_id": f"{DEVICE_ID}_disk_min",
        "state_topic": f"{base_topic}/disk_min",
        "unit_of_measurement": "%",
        "device_class": "power",
        "state_class": "measurement",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    disk_max_config = {
        "name": f"{DEVICE_NAME} Disk Usage (Max)",
        "unique_id": f"{DEVICE_ID}_disk_max",
        "state_topic": f"{base_topic}/disk_max",
        "unit_of_measurement": "%",
        "device_class": "power",
        "state_class": "measurement",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    disk_avg_config = {
        "name": f"{DEVICE_NAME} Disk Usage (Avg)",
        "unique_id": f"{DEVICE_ID}_disk_avg",
        "state_topic": f"{base_topic}/disk_avg",
        "unit_of_measurement": "%",
        "device_class": "power",
        "state_class": "measurement",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    # Uptime sensors
    uptime_config = {
        "name": f"{DEVICE_NAME} Uptime (Seconds)",
        "unique_id": f"{DEVICE_ID}_uptime",
        "state_topic": f"{base_topic}/uptime",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    formatted_uptime_config = {
        "name": f"{DEVICE_NAME} Uptime (Formatted)",
        "unique_id": f"{DEVICE_ID}_uptime_formatted",
        "state_topic": f"{base_topic}/uptime_formatted",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }
    }
    
    # Publish configurations
    mqtt_client.publish(f"{binary_base_topic}/status/config", json.dumps(status_config), retain=True)
    
    # CPU sensors
    mqtt_client.publish(f"{base_topic}/cpu/config", json.dumps(cpu_config), retain=True)
    mqtt_client.publish(f"{base_topic}/cpu_min/config", json.dumps(cpu_min_config), retain=True)
    mqtt_client.publish(f"{base_topic}/cpu_max/config", json.dumps(cpu_max_config), retain=True)
    mqtt_client.publish(f"{base_topic}/cpu_avg/config", json.dumps(cpu_avg_config), retain=True)
    
    # Memory sensors
    mqtt_client.publish(f"{base_topic}/memory/config", json.dumps(mem_config), retain=True)
    mqtt_client.publish(f"{base_topic}/memory_min/config", json.dumps(mem_min_config), retain=True)
    mqtt_client.publish(f"{base_topic}/memory_max/config", json.dumps(mem_max_config), retain=True)
    mqtt_client.publish(f"{base_topic}/memory_avg/config", json.dumps(mem_avg_config), retain=True)
    
    # Disk sensors
    mqtt_client.publish(f"{base_topic}/disk/config", json.dumps(disk_config), retain=True)
    mqtt_client.publish(f"{base_topic}/disk_min/config", json.dumps(disk_min_config), retain=True)
    mqtt_client.publish(f"{base_topic}/disk_max/config", json.dumps(disk_max_config), retain=True)
    mqtt_client.publish(f"{base_topic}/disk_avg/config", json.dumps(disk_avg_config), retain=True)
    
    # Uptime sensors
    mqtt_client.publish(f"{base_topic}/uptime/config", json.dumps(uptime_config), retain=True)
    mqtt_client.publish(f"{base_topic}/uptime_formatted/config", json.dumps(formatted_uptime_config), retain=True)

def get_system_info():
    """Get current system information"""
    disk_usage = psutil.disk_usage('/')
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": disk_usage,
        "uptime": round(time.time() - psutil.boot_time(), 2)
    }

def collect_metrics():
    """Collect system metrics"""
    system_info = get_system_info()
    cpu_samples.append(system_info["cpu_percent"])
    memory_samples.append(system_info["memory_percent"])
    disk_samples.append(system_info["disk_usage"].percent)
    return system_info

def publish_system_info():
    """Publish system information to MQTT"""
    if not mqtt_client.is_connected():
        return
        
    base_topic = f"homeassistant/sensor/{DEVICE_ID}"
    binary_base_topic = f"homeassistant/binary_sensor/{DEVICE_ID}"
    system_info = get_system_info()
    
    # Publish status with retain=True
    mqtt_client.publish(f"{binary_base_topic}/status", "online", retain=True)
    
    # Calculate statistics for the period
    cpu_stats = {
        "current": system_info["cpu_percent"],
        "min": min(cpu_samples),
        "max": max(cpu_samples),
        "avg": round(mean(cpu_samples), 2)
    }
    
    memory_stats = {
        "current": system_info["memory_percent"],
        "min": min(memory_samples),
        "max": max(memory_samples),
        "avg": round(mean(memory_samples), 2)
    }
    
    disk_stats = {
        "current": system_info["disk_usage"].percent,
        "min": min(disk_samples),
        "max": max(disk_samples),
        "avg": round(mean(disk_samples), 2)
    }
    
    # Publish current values
    mqtt_client.publish(f"{base_topic}/cpu", str(cpu_stats["current"]))
    mqtt_client.publish(f"{base_topic}/memory", str(memory_stats["current"]))
    mqtt_client.publish(f"{base_topic}/disk", str(disk_stats["current"]))
    
    # Publish CPU statistics
    mqtt_client.publish(f"{base_topic}/cpu_min", str(cpu_stats["min"]))
    mqtt_client.publish(f"{base_topic}/cpu_max", str(cpu_stats["max"]))
    mqtt_client.publish(f"{base_topic}/cpu_avg", str(cpu_stats["avg"]))
    
    # Publish Memory statistics
    mqtt_client.publish(f"{base_topic}/memory_min", str(memory_stats["min"]))
    mqtt_client.publish(f"{base_topic}/memory_max", str(memory_stats["max"]))
    mqtt_client.publish(f"{base_topic}/memory_avg", str(memory_stats["avg"]))
    
    # Publish Disk statistics
    mqtt_client.publish(f"{base_topic}/disk_min", str(disk_stats["min"]))
    mqtt_client.publish(f"{base_topic}/disk_max", str(disk_stats["max"]))
    mqtt_client.publish(f"{base_topic}/disk_avg", str(disk_stats["avg"]))
    
    # Publish uptime values
    mqtt_client.publish(f"{base_topic}/uptime", str(system_info["uptime"]))
    formatted_uptime = time.strftime("%H:%M:%S", time.gmtime(system_info["uptime"]))
    mqtt_client.publish(f"{base_topic}/uptime_formatted", formatted_uptime)

def create_tray_icon():
    # Create a simple icon (a white circle on black background)
    icon_size = 64
    image = Image.new('RGB', (icon_size, icon_size), color='black')
    dc = ImageDraw.Draw(image)
    dc.ellipse([8, 8, icon_size-8, icon_size-8], fill='white')
    return image

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
        mqtt_client.publish(f"homeassistant/binary_sensor/{DEVICE_ID}/status", "offline", retain=True)
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
            
            # Collect metrics every second
            for _ in range(PUBLISH_INTERVAL):
                if not server_running:
                    break
                collect_metrics()
                time.sleep(COLLECTION_INTERVAL)
            
            # Publish aggregated data every 30 seconds
            if server_running:
                publish_system_info()
                
        except Exception as e:
            logger.error(f"Error in MQTT publish loop: {e}")
            time.sleep(5)  # Wait a bit before retrying

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