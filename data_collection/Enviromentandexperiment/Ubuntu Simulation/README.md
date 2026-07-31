# LIDAR Plugin for Gazebo Simulation

Configuration of the enviroment to run the experiment (2026/03)

## Project Overview

This project consists of:
- **C++ Gazebo Plugin**: Captures LiDAR scan data from a simulated Hokuyo sensor in Gazebo
- **Python Visualization**: Real-time visualization of LiDAR point clouds
- **CSV Export**: Conversion of LiDAR scans to CSV format for data analysis

## Prerequisites

- **Ubuntu** Ubuntu 22.04.5 LTS
- **Gazebo** Gazebo multi-robot simulator, version 11.10.2
- **CMake** (3.0 or later)
- **C++ compiler** (g++, C++11 or later)
- **Python** Python 3.10.12


## Installation & Setup

### 1. Install Gazebo

```bash
# Add Gazebo repository
sudo apt-get update
sudo apt-get install -y lsb-release gnupg curl

# Import Gazebo GPG key
curl https://repo.gazebosim.org/gazebo.gpg | sudo tee /etc/apt/trusted.gpg.d/gazebo.gpg > /dev/null

# Add repository 
echo "deb http://repo.gazebosim.org/gazebo ubuntu-$(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-latest.list

# Install Gazebo
sudo apt-get update
sudo apt-get install -y gazebo gazebo-dev gazebo-plugin-base

# Verify installation
gazebo --version
```

### 2. Install Dependencies

```bash
# Install build tools
sudo apt-get install -y build-essential cmake git

# Install Python dependencies
sudo apt-get install -y python3 python3-pip
pip3 install numpy matplotlib scipy
```

### 3. Build the LIDAR Plugin

```bash
# Navigate to the project directory
cd ~/gazebo_worlds/lidar_plugin

# Create and enter build directory
mkdir -p build
cd build

# Configure and build
cmake ..
make

# Verify the shared library was created
ls -la liblidar_plugin.so
```

### 4. Configure Environment

Add the plugin to your Gazebo path by adding this to your `~/.bashrc`:

```bash
export GAZEBO_PLUGIN_PATH=~/gazebo_worlds/lidar_plugin/build:$GAZEBO_PLUGIN_PATH
```

Then reload:

```bash
source ~/.bashrc
```

## Running the Experiment

The experiment runs in **3 separate terminals** for parallel execution:

### Terminal 1: Start Gazebo Server, example (phase3_res200deg)

```bash
export GAZEBO_PLUGIN_PATH=~/gazebo_worlds/lidar_plugin/build:$GAZEBO_PLUGIN_PATH
gzserver --verbose ~/gazebo_worlds/phase3_res200deg.world
```

This terminal:
- Initializes the Gazebo physics engine
- Loads the simulated world (`phase3_res200deg.world`)
- Activates the LIDAR plugin
- Begins writing scan data to `/tmp/lidar_scan.txt`

**Output example:**
```
[LidarPlugin] Listo! Escribiendo en: /tmp/lidar_scan.txt
[LidarPlugin] Scan #50 — 1024 puntos
[LidarPlugin] Scan #100 — 1024 puntos
```

### Terminal 2: Launch 3D Visualization Client

```bash
gzclient
```

This terminal:
- Opens the Gazebo GUI (3D viewer)
- Displays the simulated environment
- Shows the robot and LiDAR sensor in real-time
- Allows interaction with the simulation (camera control, pause/play)

### Terminal 3: Process and Visualize Data

```bash
# Option A: Real-time visualization
python3 ~/gazebo_worlds/ver_lidar.py

# Option B: Export to CSV (run after data collection)
python3 ~/gazebo_worlds/lidar_to_csv.py

# Or run both sequentially
python3 ~/gazebo_worlds/ver_lidar.py
python3 ~/gazebo_worlds/lidar_to_csv.py
```

## Project Files Description

### C++ Source Files

#### `lidar_plugin.cpp`
The core Gazebo sensor plugin that:
- Extends `SensorPlugin` class
- Hooks into the Hokuyo RaySensor in the simulation
- **Publishes** scan data via Gazebo transport layer to `/gazebo/phase3_res200deg/lidar_estatico/link/hokuyo/scan`
- **Writes** raw scan data to `/tmp/lidar_scan.txt` for file-based access
- Extracts and processes:
  - Range measurements (distance to objects)
  - Scan angles (min/max angle, angle resolution)
  - Sensor pose (position and orientation)
  - Intensity data (reflectivity)

**Key Methods:**
- `Load()`: Plugin initialization when Gazebo loads the world
- `OnUpdate()`: Called every sensor update cycle (~1-100Hz depending on simulation)
- `GZ_REGISTER_SENSOR_PLUGIN()`: Macro that registers the plugin with Gazebo

**Output Format** (written to `/tmp/lidar_scan.txt`):
```
angle_min: -3.14159
angle_max: 3.14159
count: 1024
0.5
0.45
0.52
... (1024 range values)
```

#### `CMakeLists.txt`
CMake build configuration that:
- Defines project name and minimum CMake version
- Finds and links Gazebo libraries
- Compiles `lidar_plugin.cpp` into a shared library (`liblidar_plugin.so`)
- Sets up include paths and library directories

### Python Scripts

#### `ver_lidar.py`
Real-time 2D/3D visualization script that:
- Monitors `/tmp/lidar_scan.txt` for new scan data
- Converts polar coordinates (angle, range) to Cartesian (x, y)
- Plots the point cloud in real-time using matplotlib
- Refreshes the display for each new scan
- **Use case**: Visual inspection of LiDAR data quality and sensor behavior

#### `lidar_to_csv.py`
Data export and archival script that:
- Reads the most recent scan from `/tmp/lidar_scan.txt`
- Converts range and angle data to Cartesian coordinates
- Exports as CSV file with columns: `angle, range, x, y, timestamp`
- Saves to timestamped file: `lidar_scan_[TIMESTAMP].csv`
- **Use case**: Data analysis, machine learning, mapping algorithms

### Build Files

#### `liblidar_plugin.so`
Compiled shared library that:
- Gazebo dynamically loads at runtime
- Contains the compiled `LidarPublisher` class
- Must be in `GAZEBO_PLUGIN_PATH` to be found

#### `CMakeCache.txt`
Stores CMake configuration from the previous build. Can be deleted to force a clean rebuild.

#### `Makefile`
Generated by CMake; contains build rules and commands executed by `make`.

#### `cmake_install.cmake`
Generated by CMake; handles installation rules (used by `make install`).

#### `TargetDirectories.txt`
Lists build artifact directories used by CMake for intermediate files.

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ Gazebo Simulation                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐                                           │
│  │ Hokuyo Sensor    │                                           │
│  │ (RaySensor)      │                                           │
│  └────────┬─────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────────┐                                       │
│  │ LidarPublisher Plugin│                                       │
│  │  (lidar_plugin.cpp)  │                                       │
│  └──┬────────────────┬──┘                                       │
│     │                │                                          │
│     ▼                ▼                                          │
│  Transport        File I/O                                      │
│  Publish          Write to                                      │
│                   /tmp/lidar_scan.txt                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
           │
           │ (Gazebo Message Protocol)
           │
    ┌──────▼──────────────────────────────────────────────────┐
    │ Python Data Processing                                  │
    ├─────────────────────────────────────────────────────────┤
    │                                                         │
    │  ┌─────────────────────────────────────────────────┐    │
    │  │ ver_lidar.py - Real-time Visualization          │    │
    │  │ • Reads /tmp/lidar_scan.txt                     │    │
    │  │ • Converts polar → Cartesian coordinates        │    │
    │  │ • Displays 2D/3D point cloud in matplotlib      │    │
    │  └─────────────────────────────────────────────────┘    │
    │                                                         │
    │  ┌─────────────────────────────────────────────────┐    │
    │  │ lidar_to_csv.py - Data Export                   │    │
    │  │ • Reads /tmp/lidar_scan.txt                     │    │
    │  │ • Generates CSV: angle, range, x, y, timestamp  │    │
    │  │ • Saves to lidar_scan_[TIMESTAMP].csv           │    │
    │  └─────────────────────────────────────────────────┘    │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Plugin Not Found Error
```
Error: Unable to load plugin [liblidar_plugin.so]
```

**Solution:**
```bash
# Verify plugin path
echo $GAZEBO_PLUGIN_PATH

# Rebuild plugin
cd ~/gazebo_worlds/lidar_plugin/build
cmake ..
make

# Ensure export is set
export GAZEBO_PLUGIN_PATH=~/gazebo_worlds/lidar_plugin/build:$GAZEBO_PLUGIN_PATH
```

### RaySensor Not Detected
```
[LidarPlugin] No es RaySensor
```

**Solution:**
- Verify the world file (`phase3_res200deg.world`) contains a proper `<sensor type="ray">` element
- Check the sensor name in the SDF matches what the plugin expects
- Ensure the plugin is attached to the correct link in the robot model

### No Data in `/tmp/lidar_scan.txt`
```bash
# Check if file exists and has content
cat /tmp/lidar_scan.txt
ls -la /tmp/lidar_scan.txt

# Check Gazebo server is running
ps aux | grep gzserver
```

### Python Scripts Not Detecting Data
```bash
# Verify data file path
tail -f /tmp/lidar_scan.txt

# Install missing Python packages
pip3 install numpy matplotlib scipy

# Run with verbose output
python3 -v ~/gazebo_worlds/ver_lidar.py
```


