import psutil
import time
from collections import deque
from statistics import mean
import logging
import sys
import platform

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self, collection_interval=1, publish_interval=30):
        self.collection_interval = collection_interval
        self.publish_interval = publish_interval
        self.max_samples = publish_interval // collection_interval
        self.is_windows = platform.system().lower() == 'windows'
        
        # Initialize data collection queues
        self.cpu_samples = deque(maxlen=self.max_samples)
        self.memory_samples = deque(maxlen=self.max_samples)
        
        # Initialize the unified data structure
        self.system_data = {
            "status": "online",
            "timestamp": 0,
            "metrics": {
                "cpu": {"current": 0, "min": 0, "max": 0, "avg": 0},
                "memory": {"current": 0, "min": 0, "max": 0, "avg": 0},
                "disk": {}  # Will be populated with disk information
            },
            "uptime": {
                "seconds": 0,
                "formatted": "00:00:00"
            }
        }

    def get_windows_disk_info(self):
        """Get disk information specifically for Windows systems"""
        try:
            import win32api
            import win32file
            
            drives = []
            bitmask = win32api.GetLogicalDrives()
            for letter in range(65, 91):  # A-Z
                if bitmask & 1:
                    drive = f"{chr(letter)}:\\"
                    try:
                        # Get drive type
                        drive_type = win32file.GetDriveType(drive)
                        # Skip non-fixed drives (removable, network, etc.)
                        if drive_type == win32file.DRIVE_FIXED:
                            drives.append(drive)
                    except Exception as e:
                        logger.debug(f"Could not get drive type for {drive}: {e}")
                bitmask >>= 1
            for drive in drives:
                try:
                    # Get the disk free space
                    sectors_per_cluster, bytes_per_sector, free_clusters, total_clusters = win32file.GetDiskFreeSpace(drive)
                    
                    # Convert to float to handle large numbers
                    total_bytes = float(total_clusters) * float(sectors_per_cluster) * float(bytes_per_sector)
                    free_space = float(free_clusters) * float(sectors_per_cluster) * float(bytes_per_sector)
                    used_space = total_bytes - free_space
                    percent_used = (used_space / total_bytes) * 100 if total_bytes > 0 else 0

                    # Convert to GB for more compact representation
                    total_gb = round(total_bytes / (1024**3), 2)
                    used_gb = round(used_space / (1024**3), 2)
                    free_gb = round(free_space / (1024**3), 2)

                    # Create a unique key for each drive
                    drive_key = drive.replace(':', '').replace('\\', '')
                    self.system_data["metrics"]["disk"][f"disk_{drive_key}"] = {
                        "state": round(percent_used, 2),
                        "attributes": {
                            "partition": drive,
                            "name": "NTFS",
                            "device": drive,
                            "total_gb": total_gb,
                            "used_gb": used_gb,
                            "free_gb": free_gb
                        }
                    }
                except Exception as e:
                    logger.warning(f"Could not get usage for drive {drive}: {e}")
                    drive_key = drive.replace(':', '').replace('\\', '')
                    self.system_data["metrics"]["disk"][f"disk_{drive_key}"] = {
                        "state": 0,
                        "attributes": {
                            "partition": drive,
                            "name": "Unknown",
                            "device": drive,
                            "total_gb": 0,
                            "used_gb": 0,
                            "free_gb": 0,
                            "error": str(e)
                        }
                    }
        except ImportError:
            logger.error("win32api module not available. Falling back to psutil.")
            self._get_disk_info_fallback()
        except Exception as e:
            logger.error(f"Error getting Windows disk information: {e}")
            self._get_disk_info_fallback()

    def _get_disk_info_fallback(self):
        """Fallback method for getting disk information using psutil"""
        try:
            for partition in psutil.disk_partitions():
                if partition.fstype and partition.fstype.lower() not in ['cdrom', 'dvd']:
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        self.system_data["metrics"]["disk"][partition.mountpoint] = {
                            "partition": partition.mountpoint,
                            "name": partition.fstype,
                            "device": partition.device,
                            "current": usage.percent,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free
                        }
                    except Exception as e:
                        logger.warning(f"Could not get usage for {partition.mountpoint}: {e}")
        except Exception as e:
            logger.error(f"Error in fallback disk information collection: {e}")

    def get_system_info(self):
        """Get current system information"""
        uptime = round(time.time() - psutil.boot_time(), 2)
        
        # Get disk information based on platform
        if self.is_windows:
            self.get_windows_disk_info()
        else:
            self._get_disk_info_fallback()
        
        # Update the unified data structure
        self.system_data.update({
            "timestamp": round(time.time(), 2),
            "uptime": {
                "seconds": uptime,
                "formatted": time.strftime("%H:%M:%S", time.gmtime(uptime))
            }
        })
        
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "uptime": uptime
        }

    def collect_metrics(self):
        """Collect system metrics and update the unified data structure"""
        system_info = self.get_system_info()
        
        # Update samples
        self.cpu_samples.append(system_info["cpu_percent"])
        self.memory_samples.append(system_info["memory_percent"])
        
        # Update current values in the unified data structure
        self.system_data["metrics"]["cpu"]["current"] = system_info["cpu_percent"]
        self.system_data["metrics"]["memory"]["current"] = system_info["memory_percent"]
        
        logger.debug(f"Collected metrics - CPU: {system_info['cpu_percent']}%, Memory: {system_info['memory_percent']}%")
        return system_info

    def calculate_statistics(self):
        """Calculate statistics for all metrics and update the unified data structure"""
        # Ensure we have samples before calculating
        if not any([self.cpu_samples, self.memory_samples]):
            logger.warning("No samples available for statistics calculation")
            return self.system_data["metrics"]

        stats = {
            "cpu": {
                "current": float(self.cpu_samples[-1]) if self.cpu_samples else 0.0,
                "min": float(min(self.cpu_samples)) if self.cpu_samples else 0.0,
                "max": float(max(self.cpu_samples)) if self.cpu_samples else 0.0,
                "avg": float(round(mean(self.cpu_samples), 2)) if self.cpu_samples else 0.0
            },
            "memory": {
                "current": float(self.memory_samples[-1]) if self.memory_samples else 0.0,
                "min": float(min(self.memory_samples)) if self.memory_samples else 0.0,
                "max": float(max(self.memory_samples)) if self.memory_samples else 0.0,
                "avg": float(round(mean(self.memory_samples), 2)) if self.memory_samples else 0.0
            }
        }
        stats["disk"] = self.system_data["metrics"]["disk"]
        
        # Update statistics in the unified data structure
        self.system_data["metrics"] = stats
        
        logger.debug(f"Calculated statistics: {stats}")
        return stats

    def get_unified_data(self):
        """Get the complete unified data structure"""
        return self.system_data 