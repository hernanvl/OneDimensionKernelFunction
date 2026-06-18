import os
import random
import math

# ============================================
# CONFIGURATION
# ============================================

NUM_WORLDS = 100
OUTPUT_DIR = "generated_worlds_single_sensor"

ROOM_MIN = 4.0
ROOM_MAX = 10.0

OBST_MIN = 3
OBST_MAX = 15

MIN_DIST = 0.60          # obstacle–obstacle
SENSOR_MIN_DIST = 0.80   # sensor–obstacle

# ============================================
# SENSOR RESOLUTION OPTIONS
# ============================================

# angle_step : samples
RES_OPTIONS = {
    0.5: 720,
    1.5: 240,
    2.0: 180,
    3.0: 120,
    4.0: 90
}

# ============================================
# UTILS
# ============================================

def dist(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def random_position(room_x, room_y):
    return (
        random.uniform(-room_x + 0.5, room_x - 0.5),
        random.uniform(-room_y + 0.5, room_y - 0.5)
    )

def generate_non_overlapping_positions(n, room_x, room_y, forbidden, min_dist):
    positions = []
    attempts = 0

    while len(positions) < n:
        attempts += 1
        if attempts > 8000:
            raise RuntimeError("Could not generate valid positions")

        x, y = random_position(room_x, room_y)

        # Check forbidden (sensor)
        if any(dist((x, y), f) < min_dist for f in forbidden):
            continue

        # Check other obstacles
        if any(dist((x, y), p) < min_dist for p in positions):
            continue

        positions.append((x, y))

    return positions

# ============================================
# SDF TEMPLATES
# ============================================

OBSTACLE_RECT = """
    <model name="obstacle_{i}">
      <static>true</static>
      <pose>{x} {y} 0.5 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>{sx} {sy} 1.0</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>{sx} {sy} 1.0</size></box></geometry>
        </visual>
      </link>
    </model>
"""

OBSTACLE_CIRC = """
    <model name="obstacle_{i}">
      <static>true</static>
      <pose>{x} {y} 0.5 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry><cylinder><radius>{r}</radius><length>1.0</length></cylinder></geometry>
        </collision>
        <visual name="visual">
          <geometry><cylinder><radius>{r}</radius><length>1.0</length></cylinder></geometry>
        </visual>
      </link>
    </model>
"""

SENSOR_TEMPLATE = """
    <model name="lidar_sensor">
      <static>true</static>
      <pose>{x} {y} 0.4 0 0 0</pose>
      <link name="link">
        <sensor name="lidar" type="ray">
          <pose>0 0 0 0 0 0</pose>
          <visualize>true</visualize>
          <always_on>true</always_on>
          <update_rate>10</update_rate>
          <ray>
            <scan><horizontal>
              <samples>{samples}</samples>
              <resolution>1</resolution>
              <min_angle>-3.14159</min_angle>
              <max_angle>3.14159</max_angle>
            </horizontal></scan>
            <range><min>0.15</min><max>20.0</max><resolution>0.01</resolution></range>
          </ray>
          <plugin name="lidar_plugin" filename="liblidar_plugin.so"/>
        </sensor>
      </link>
    </model>
"""

WORLD_TEMPLATE = """<?xml version="1.0"?>
<sdf version="1.6">
  <world name="env_{id}">

    <include><uri>model://ground_plane</uri></include>
    <include><uri>model://sun</uri></include>

    <!-- WALLS -->
    <model name="wall_north"><static>true</static><pose>0 {ry} 1 0 0 0</pose>
      <link name="link"><collision name="collision">
        <geometry><box><size>{sx} 0.2 2</size></box></geometry>
      </collision><visual name="visual">
        <geometry><box><size>{sx} 0.2 2</size></box></geometry>
      </visual></link>
    </model>

    <model name="wall_south"><static>true</static><pose>0 -{ry} 1 0 0 0</pose>
      <link name="link"><collision name="collision">
        <geometry><box><size>{sx} 0.2 2</size></box></geometry>
      </collision><visual name="visual">
        <geometry><box><size>{sx} 0.2 2</size></box></geometry>
      </visual></link>
    </model>

    <model name="wall_east"><static>true</static><pose>{rx} 0 1 0 0 1.57</pose>
      <link name="link"><collision name="collision">
        <geometry><box><size>{sy} 0.2 2</size></box></geometry>
      </collision><visual name="visual">
        <geometry><box><size>{sy} 0.2 2</size></box></geometry>
      </visual></link>
    </model>

    <model name="wall_west"><static>true</static><pose>-{rx} 0 1 0 0 1.57</pose>
      <link name="link"><collision name="collision">
        <geometry><box><size>{sy} 0.2 2</size></box></geometry>
      </collision><visual name="visual">
        <geometry><box><size>{sy} 0.2 2</size></box></geometry>
      </visual></link>
    </model>

    <!-- SENSOR -->
    {sensor}

    <!-- OBSTACLES -->
    {obstacles}

  </world>
</sdf>
"""

# ============================================
# GENERATION LOOP
# ============================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

for wid in range(NUM_WORLDS):
    print(f"Generating world {wid}...")

    # Random room size
    room_x = random.uniform(ROOM_MIN, ROOM_MAX)
    room_y = random.uniform(ROOM_MIN, ROOM_MAX)

    # One sensor position
    sensor_pos = random_position(room_x, room_y)

    # Random sensor resolution
    angle_step = random.choice(list(RES_OPTIONS.keys()))
    samples = RES_OPTIONS[angle_step]

    # Obstacles
    num_obstacles = random.randint(OBST_MIN, OBST_MAX)
    obstacles = generate_non_overlapping_positions(
        num_obstacles,
        room_x,
        room_y,
        forbidden=[sensor_pos],
        min_dist=MIN_DIST
    )

    # Build obstacles XML
    obstacles_xml = ""
    for i, (x, y) in enumerate(obstacles):
        if random.random() < 0.5:
            sx = round(random.uniform(0.4, 1.5), 2)
            sy = round(random.uniform(0.4, 1.5), 2)
            obstacles_xml += OBSTACLE_RECT.format(i=i, x=x, y=y, sx=sx, sy=sy)
        else:
            r = round(random.uniform(0.3, 1.0), 2)
            obstacles_xml += OBSTACLE_CIRC.format(i=i, x=x, y=y, r=r)

    # Sensor XML
    sensor_xml = SENSOR_TEMPLATE.format(
        x=sensor_pos[0],
        y=sensor_pos[1],
        samples=samples
    )

    # Final world
    world_xml = WORLD_TEMPLATE.format(
        id=wid,
        rx=room_x,
        ry=room_y,
        sx=room_x * 2,
        sy=room_y * 2,
        sensor=sensor_xml,
        obstacles=obstacles_xml
    )

    # File name includes parameters
    filename = (
        f"env_{wid:03d}"
        f"_res{angle_step}deg"
        f"_{samples}samp"
        f"_o{num_obstacles}"
        f"_r{round(room_x,1)}x{round(room_y,1)}"
        ".world"
    )

    with open(f"{OUTPUT_DIR}/{filename}", "w") as f:
        f.write(world_xml)

print("Done. Worlds generated.")
