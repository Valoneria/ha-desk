import pystray
from PIL import Image, ImageDraw
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import paho.mqtt.client as mqtt
import socket
import uuid

from modules.sensor_config import SensorConfig
from modules.data_collector import DataCollector
from modules.mqtt_publisher import MQTTPublisher

# Load environment variables
load_dotenv()

# Configure logging
log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Set up file handler with rotation
log_file = os.path.join(log_dir, 'ha_desk.log')
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=5*1024*1024,  # 5MB
    backupCount=3
)
file_handler.setFormatter(logging.Formatter(log_format))

# Set up console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(log_format))

# Configure root logger
logging.basicConfig(
    level=log_level,
    format=log_format,
    handlers=[file_handler, console_handler]
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

if(os.getenv('DEV_MODE', 'false') == 'true'):
    #Dev interval
    PUBLISH_INTERVAL = 3

# Initialize components
mqtt_client = mqtt.Client()
if MQTT_USERNAME and MQTT_PASSWORD:
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

data_collector = DataCollector(COLLECTION_INTERVAL, PUBLISH_INTERVAL)
mqtt_publisher = MQTTPublisher(mqtt_client, DEVICE_ID)
sensor_config = SensorConfig(DEVICE_NAME, DEVICE_ID)

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the MQTT broker"""
    if rc == 0:
        logger.info("Connected to MQTT broker")
        sensor_config.publish_configs(mqtt_client)
    else:
        logger.error(f"Failed to connect to MQTT broker with code: {rc}")

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
    return data_collector.get_unified_data()

@app.get("/system")
async def system_info():
    """Get system information"""
    logger.debug("System info requested")
    return data_collector.get_unified_data()

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
    mqtt_publisher.publish_offline_status()
    if mqtt_client.is_connected():
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
                data_collector.collect_metrics()
                time.sleep(COLLECTION_INTERVAL)
            
            # Publish aggregated data every 30 seconds
            if server_running:
                data_collector.calculate_statistics()
                unified_data = data_collector.get_unified_data()
                mqtt_publisher.publish_system_info(
                    {"uptime": unified_data["uptime"]["seconds"]},
                    unified_data["metrics"]
                )
                
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