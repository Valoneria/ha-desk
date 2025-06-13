import json
import os

class SensorConfig:
    def __init__(self, device_name, device_id):
        self.device_name = device_name
        self.device_id = device_id
        self.base_topic = f"homeassistant/sensor/{device_id}"
        self.binary_base_topic = f"homeassistant/binary_sensor/{device_id}"
        
        self.device_info = {
            "identifiers": [device_id],
            "name": device_name,
            "model": "Computer Activity Monitor",
            "manufacturer": "Custom"
        }

    def get_status_config(self):
        return {
            "name": f"{self.device_name} Status",
            "unique_id": f"{self.device_id}_status",
            "state_topic": f"{self.binary_base_topic}/status",
            "device_class": "connectivity",
            "payload_on": "online",
            "payload_off": "offline",
            "device": self.device_info
        }

    def get_metric_config(self, metric_name, unit="%", device_class="power"):
        return {
            "name": f"{self.device_name} {metric_name}",
            "unique_id": f"{self.device_id}_{metric_name.lower().replace(' ', '_')}",
            "state_topic": f"{self.base_topic}/{metric_name.lower().replace(' ', '_')}",
            "unit_of_measurement": unit,
            "device_class": device_class,
            "state_class": "measurement",
            "device": self.device_info
        }

    def get_statistic_config(self, metric_name, stat_type, unit="%", device_class="power"):
        return {
            "name": f"{self.device_name} {metric_name} ({stat_type.title()})",
            "unique_id": f"{self.device_id}_{metric_name.lower().replace(' ', '_')}_{stat_type}",
            "state_topic": f"{self.base_topic}/{metric_name.lower().replace(' ', '_')}_{stat_type}",
            "unit_of_measurement": unit,
            "device_class": device_class,
            "state_class": "measurement",
            "device": self.device_info
        }

    def get_disk_config(self, mountpoint, fstype, device):
        """Get configuration for a disk sensor"""
        return {
            "name": f"{self.device_name} Disk {mountpoint} ({fstype})",
            "unique_id": f"{self.device_id}_disk_{mountpoint.replace('/', '_').replace(':', '')}",
            "state_topic": f"{self.base_topic}/disk_{mountpoint.replace('/', '_').replace(':', '')}",
            "unit_of_measurement": "%",
            "device_class": "power",
            "state_class": "measurement",
            "device": self.device_info
        }

    def publish_configs(self, mqtt_client):
        """Publish all sensor configurations to MQTT"""
        # Status sensor
        mqtt_client.publish(
            f"{self.binary_base_topic}/status/config",
            json.dumps(self.get_status_config()),
            retain=True
        )

        # CPU sensors
        metrics = ["CPU Usage", "Memory (RAM) Usage"]
        for metric in metrics:
            # Current value sensor
            mqtt_client.publish(
                f"{self.base_topic}/{metric.lower().replace(' ', '_').replace('(', '').replace(')', '')}/config",
                json.dumps(self.get_metric_config(metric)),
                retain=True
            )
            
            # Statistics sensors
            for stat in ["min", "max", "avg"]:
                mqtt_client.publish(
                    f"{self.base_topic}/{metric.lower().replace(' ', '_').replace('(', '').replace(')', '')}_{stat}/config",
                    json.dumps(self.get_statistic_config(metric, stat)),
                    retain=True
                )

        # Uptime sensors
        uptime_config = {
            "name": f"{self.device_name} Uptime (Seconds)",
            "unique_id": f"{self.device_id}_uptime",
            "state_topic": f"{self.base_topic}/uptime",
            "device": self.device_info
        }
        
        formatted_uptime_config = {
            "name": f"{self.device_name} Uptime (Formatted)",
            "unique_id": f"{self.device_id}_uptime_formatted",
            "state_topic": f"{self.base_topic}/uptime_formatted",
            "device": self.device_info
        }

        mqtt_client.publish(f"{self.base_topic}/uptime/config", json.dumps(uptime_config), retain=True)
        mqtt_client.publish(f"{self.base_topic}/uptime_formatted/config", json.dumps(formatted_uptime_config), retain=True) 