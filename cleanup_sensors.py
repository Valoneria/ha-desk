#!/usr/bin/env python3
"""
Standalone script to clean up old sensors from Home Assistant
"""
import paho.mqtt.client as mqtt
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MQTT Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
DEVICE_ID = os.getenv('DEVICE_ID', 'test_device')

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    if rc == 0:
        cleanup_sensors(client)
    else:
        print(f"Failed to connect to MQTT broker with code: {rc}")

def cleanup_sensors(client):
    """Clean up all sensors for the device"""
    base_topic = f"homeassistant/sensor/{DEVICE_ID}"
    binary_base_topic = f"homeassistant/binary_sensor/{DEVICE_ID}"
    
    # List of all possible sensor config topics
    cleanup_topics = [
        # Status sensor
        f"{binary_base_topic}/status/config",
        
        # CPU and Memory sensors (current values)
        f"{base_topic}/cpu_usage/config",
        f"{base_topic}/memory_ram_usage/config",
        
        # Statistics sensors
        f"{base_topic}/cpu_usage_min/config",
        f"{base_topic}/cpu_usage_max/config", 
        f"{base_topic}/cpu_usage_avg/config",
        f"{base_topic}/memory_ram_usage_min/config",
        f"{base_topic}/memory_ram_usage_max/config",
        f"{base_topic}/memory_ram_usage_avg/config",
        
        # Uptime sensors
        f"{base_topic}/uptime/config",
        f"{base_topic}/uptime_formatted/config",
        
        # Disk sensors (common patterns)
        f"{base_topic}/disk_c/config",
        f"{base_topic}/disk_d/config",
        f"{base_topic}/disk_e/config",
        f"{base_topic}/disk_f/config",
        f"{base_topic}/disk_g/config",
        f"{base_topic}/disk_h/config",
        f"{base_topic}/disk_root/config",
        f"{base_topic}/disk_home/config",
        f"{base_topic}/disk_boot/config",
    ]
    
    print("Cleaning up sensor configurations...")
    for topic in cleanup_topics:
        try:
            # Publish empty message to remove the sensor
            client.publish(topic, "", retain=True)
            print(f"Cleaned up: {topic}")
        except Exception as e:
            print(f"Error cleaning up {topic}: {e}")
    
    # Also clean up any state topics that might be retained
    state_cleanup_topics = [
        f"{binary_base_topic}/status",
        f"{binary_base_topic}/availability",
        f"{base_topic}/cpu_usage",
        f"{base_topic}/memory_ram_usage",
        f"{base_topic}/uptime",
        f"{base_topic}/uptime_formatted",
    ]
    
    print("Cleaning up state topics...")
    for topic in state_cleanup_topics:
        try:
            client.publish(topic, "", retain=True)
            print(f"Cleaned up state: {topic}")
        except Exception as e:
            print(f"Error cleaning up state topic {topic}: {e}")
    
    print("Sensor cleanup completed!")
    print("You may need to restart Home Assistant or wait a few minutes for changes to take effect.")

def main():
    # Create MQTT client
    client = mqtt.Client()
    
    # Set up authentication if provided
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    # Set up callbacks
    client.on_connect = on_connect
    
    try:
        # Connect to broker
        print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        # Wait for cleanup to complete
        time.sleep(5)
        
        # Disconnect
        client.disconnect()
        client.loop_stop()
        
        print("Cleanup script completed successfully.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 