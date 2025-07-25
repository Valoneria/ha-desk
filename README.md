# Home Assistant Desktop Monitor

A Python application that runs in the system tray and provides system information to Home Assistant installations on your network.

## Features

- Runs as a system tray application
- Monitors system resources (CPU, memory, disk usage)
- Automatic Home Assistant discovery via MQTT
- Configurable through environment variables
- **Automatic offline detection** - Home Assistant will show the device as offline when the computer is disconnected or the application is closed
- **Robust connection handling** - Automatically reconnects to MQTT broker if connection is lost

## Installation

1. Make sure you have Python 3.7+ installed (Python 3.10 recommended, will fail to install on Python 3.13)
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project directory (see Configuration section below)

## Configuration

Create a `.env` file in the project directory with the following options:

```env
# MQTT Configuration
MQTT_BROKER=your-mqtt-broker
MQTT_PORT=1883
MQTT_USERNAME=your-username
MQTT_PASSWORD=your-password
DEVICE_NAME=Your Computer Name
DEVICE_ID=optional-unique-id

# Logging
LOG_LEVEL=INFO

# Sensor Cleanup (optional)
CLEANUP_SENSORS_ON_START=true
```

### Configuration Options

- `MQTT_BROKER`: Your MQTT broker address (default: localhost)
- `MQTT_PORT`: MQTT broker port (default: 1883)
- `MQTT_USERNAME`: MQTT username (optional)
- `MQTT_PASSWORD`: MQTT password (optional)
- `DEVICE_NAME`: Name of your computer (default: hostname)
- `DEVICE_ID`: Unique identifier for the device (default: auto-generated UUID)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `CLEANUP_SENSORS_ON_START`: Automatically clean up old sensors on startup (default: true)

## Usage

1. Run the application:
   ```bash
   python ha_desk.py
   ```
2. The application will start and appear in your system tray
3. The device will automatically appear in Home Assistant if MQTT is configured

## Home Assistant Integration

The application uses MQTT discovery to automatically integrate with Home Assistant. Once running, it will create:

1. A device entry in Home Assistant with your computer's name
2. Two sensors:
   - Status sensor: Shows if your computer is online/offline
   - System Info sensor: Shows CPU usage percentage as the main value, with memory usage, disk usage, and uptime attached as additional attributes

### Prerequisites

1. MQTT broker must be configured in Home Assistant
2. MQTT integration must be enabled in Home Assistant
3. The MQTT broker must be accessible from your computer

### Automatic Discovery

No manual configuration is needed in Home Assistant. The device and sensors will appear automatically in:
- Home Assistant's device list
- The MQTT integration page
- Your dashboard (you can add the sensors to your dashboard)

### Sensor Details

#### Status Sensor
- Shows "online" when the application is running and connected to MQTT
- Shows "offline" when the application is closed or disconnected from MQTT
- Automatically detects network disconnections and computer shutdowns
- Updates every 30 seconds

#### System Info Sensor
- CPU usage
- Memory usage percentage
- Disk usage (total, used, free, percentage)
- System uptime
- Updates every 30 seconds

## Exiting the Application

Right-click the system tray icon and select "Exit" to close the application.

## Testing Availability

To test that the offline detection works correctly:

1. Start the application and verify it shows as "online" in Home Assistant
2. Close the application using the system tray "Exit" option
3. Check Home Assistant - the device should show as "offline" within a few seconds

You can also test network disconnection scenarios:
1. Start the application
2. Disconnect your computer from the network (disable WiFi/Ethernet)
3. Check Home Assistant - the device should show as "offline" after the MQTT connection timeout
4. Reconnect to the network
5. The application should automatically reconnect and show as "online" again

For advanced testing, you can use the included test script:
```bash
python test_availability.py
```

This script will connect to MQTT, publish online status, wait 10 seconds, then publish offline status and disconnect. This simulates the behavior of the main application.

## Sensor Cleanup

The application now automatically cleans up old sensors when it starts up. This prevents orphaned sensors from accumulating in Home Assistant when sensors are removed or changed.

### Automatic Cleanup

By default, the application will clean up old sensors on startup. You can disable this by setting:
```env
CLEANUP_SENSORS_ON_START=false
```

### Manual Cleanup

If you need to manually clean up sensors, you can use the standalone cleanup script:
```bash
python cleanup_sensors.py
```

This script will remove all sensors for your device from Home Assistant. You may need to restart Home Assistant or wait a few minutes for the changes to take effect.

### What Gets Cleaned Up

The cleanup process removes:
- Old sensor configurations
- Retained state messages
- Orphaned disk sensors
- Statistics sensors that are no longer used

## Downloading the Executable

If you don't want to build the executable yourself, you can download the latest pre-built version:

1. Go to the [Releases](https://github.com/Valoneria/ha-desk/releases) page
2. Download the latest `HAdesk.exe` from the assets
3. Create a `.env` file in the same directory (see Configuration section above)
4. Run `HAdesk.exe`

The pre-built executable:
- Includes all required dependencies
- Doesn't require Python installation
- Can be run on any Windows 10+ system
- Can be used to create shortcuts or run at startup

## Adding to Windows Startup

To make HAdesk start automatically when you log in to Windows:

1. Press `Windows + R` to open the Run dialog
2. Type `shell:startup` and press Enter
3. Create a shortcut to `HAdesk.exe` in the opened folder:
   - Right-click in the folder
   - Select New → Shortcut
   - Browse to your HAdesk.exe location
   - Name the shortcut "HAdesk"

Alternatively, you can use Task Scheduler for more control:
1. Open Task Scheduler (search for it in the Start menu)
2. Click "Create Basic Task"
3. Name it "HAdesk"
4. Set the trigger to "At log on"
5. Set the action to "Start a program"
6. Browse to your HAdesk.exe location
7. Complete the wizard

Note: Make sure your `.env` file is in the same directory as the executable for the startup to work properly.

## Building the Executable

To create a standalone executable of the application:

1. Switch to the build-tools branch:
   ```bash
   git checkout build-tools
   ```

2. Build the executable:
   ```bash
   python compiler.py
   ```

The build process will:
- Automatically create the application icon if it doesn't exist
- Generate version information
- Create a standalone executable

The executable will be created in the `build/dist` directory as `HAdesk.exe`. This executable can be:
- Run directly without Python installed
- Used to create shortcuts
- Distributed to other computers

Note: The build tools (`compiler.py` and `create_icon.py`) are available in the `build-tools` branch of this repository. This keeps the main branch clean while making the build tools easily accessible for developers. 


