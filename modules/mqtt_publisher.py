import time
import logging
import json

logger = logging.getLogger(__name__)

class MQTTPublisher:
    def __init__(self, mqtt_client, device_id):
        self.mqtt_client = mqtt_client
        self.device_id = device_id
        self.base_topic = f"homeassistant/sensor/{device_id}"
        self.binary_base_topic = f"homeassistant/binary_sensor/{device_id}"
        
        # Define metric configurations
        self.metrics = {
            "cpu": "CPU Usage",
            "memory": "Memory (RAM) Usage"
        }

    def publish_availability(self, status):
        """Publish availability status"""
        if self.mqtt_client.is_connected():
            self.mqtt_client.publish(f"{self.binary_base_topic}/availability", status, retain=True)

    def publish_system_info(self, system_info, statistics):
        """Publish system information to MQTT"""
        if not self.mqtt_client.is_connected():
            return

        try:
            # Publish status
            self.mqtt_client.publish(f"{self.binary_base_topic}/status", "online", retain=True)

            # Publish metrics and their statistics
            for metric_key, metric_name in self.metrics.items():
                metric_data = statistics[metric_key]
                metric_base = metric_name.lower().replace(' ', '_').replace('(', '').replace(')', '')
                
                # Publish configuration
                config = {
                    "name": metric_name,
                    "unique_id": f"{self.device_id}_{metric_base}",
                    "state_topic": f"{self.base_topic}/{metric_base}",
                    "unit_of_measurement": "%",
                    "device_class": "power",
                    "state_class": "measurement",
                    "device": {
                        "identifiers": [self.device_id],
                        "name": "Computer Activity Monitor",
                        "model": "Computer Activity Monitor",
                        "manufacturer": "Custom"
                    }
                }
                self.mqtt_client.publish(
                    f"{self.base_topic}/{metric_base}/config",
                    json.dumps(config),
                    retain=True
                )
                
                # Publish current value
                self.mqtt_client.publish(
                    f"{self.base_topic}/{metric_base}",
                    str(metric_data["current"])
                )
                
                # Publish statistics (min, max, avg)
                for stat_type in ["min", "max", "avg"]:
                    self.mqtt_client.publish(
                        f"{self.base_topic}/{metric_base}_{stat_type}",
                        str(metric_data[stat_type])
                    )

            # Publish disk information
            for drive_key, disk_data in statistics["disk"].items():
                try:
                    # Publish disk usage percentage
                    self.mqtt_client.publish(
                        f"{self.base_topic}/{drive_key}",
                        str(disk_data["state"])
                    )
                    
                    # Publish disk configuration
                    config = {
                        "name": f"Disk {disk_data['attributes']['partition']} {disk_data['attributes']['name']} (Storage usage)",
                        "unique_id": f"{self.device_id}_{drive_key}",
                        "state_topic": f"{self.base_topic}/{drive_key}",
                        "unit_of_measurement": "%",
                        "device_class": "power",
                        "state_class": "measurement",
                        "device": {
                            "identifiers": [self.device_id],
                            "name": "Computer Activity Monitor",
                            "model": "Computer Activity Monitor",
                            "manufacturer": "Custom"
                        }
                    }
                    self.mqtt_client.publish(
                        f"{self.base_topic}/{drive_key}/config",
                        json.dumps(config),
                        retain=True
                    )
                except Exception as e:
                    logger.error(f"Error publishing disk data for {drive_key}: {e}")

            # Publish uptime values
            self.mqtt_client.publish(f"{self.base_topic}/uptime", str(system_info["uptime"]))
            formatted_uptime = time.strftime("%H:%M:%S", time.gmtime(system_info["uptime"]))
            self.mqtt_client.publish(f"{self.base_topic}/uptime_formatted", formatted_uptime)
            
        except Exception as e:
            logger.error(f"Error in publish_system_info: {e}")

    def publish_offline_status(self):
        """Publish offline status when shutting down"""
        if self.mqtt_client.is_connected():
            self.mqtt_client.publish(f"{self.binary_base_topic}/availability", "offline", retain=True)
            self.mqtt_client.publish(f"{self.binary_base_topic}/status", "offline", retain=True) 