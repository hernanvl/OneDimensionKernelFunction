import os
import math

# ============================================
# CONFIGURATION
# ============================================

OUTPUT_DIR = "movement_worlds"
NUM_POSES = 25                     # number of movement steps
START_X = -4.0
END_X = 4.0
Y_POS = 0.0
Z_POS = 0.4

# Obstacles (fixed)
OBSTACLES = [
    ("obs_0", -1.0,  0.8, "box", 1.0, 0.6),
    ("obs_1",  2.5, -1.2, "cyl", 0.5, None),
    ("obs_2",  3.5,  1.5, "box", 0.6, 0.6),
    ("obs_3", -3.5, -2.0, "cyl", 0.7, None)
]

# Room size
ROOM_X = 5.0
ROOM_Y = 3.0

# ============================================
# SDF TEMPLATES
# ============================================

OBSTACLE_BOX = """
    <model name="{name}">
      <static>true</static>
      <pose>{x} {y} 0.5 0 0 0</pose>
      <link name="link">
        <collision name="col">
          <geometry><box><size>{sx} {sy} 1.0</size></box></geometry>
        </collision>
        <visual name="vis">
          <geometry><box><size>{sx} {sy} 1.0</size></box></geometry>
        </visual>
      </link>
    </model>
"""

OBSTACLE_CYL = """
    <model name="{name}">
      <static>true</static>
      <pose>{x} {y} 0.5 0 0 0</pose>
      <link name="link">
        <collision name="col">
          <geometry><cylinder><radius>{r}</radius><length>1.0</length></cylinder></geometry>
        </collision>
        <visual name="vis">
          <geometry><cylinder><radius>{r}</radius><length>1.0</length></cylinder></geometry>
        </visual>
      </link>
    </model>
"""

SENSOR_TEMPLATE = """
    <model name="lidar_sensor">
      <static>true</static>
      <pose>{x} {y} {z} 0 0 {yaw}</pose>
      <link name="link">
        <sensor name="lidar" type="ray">
          <pose>0 0 0 0 0 0</pose>
          <visualize>true</visualize>
          <always_on>true</always_on>
          <update_rate>10</update_rate>
          <ray>
            <scan><horizontal>
              <samples>360</samples>
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
  <world name="movement_env_{id}">

    <include><uri>model://ground_plane</uri></include>
    <include><uri>model://sun</uri></include>

    <!-- WALLS -->
    <model name="wall_north"><static>true</static><pose>0 {ry} 1 0 0 0</pose>
      <link name="link"><collision name="col">
        <geometry><box><size>{sx} 0.2 2</size></box></geometry>
      </collision><visual name="vis">
        <geometry><box><size>{sx} 0.2 2</size></box></geometry>
      </visual></link>
    </model>

    <model name="wall_south"><static>true</static><pose>0 -{ry} 1 0 0 0</pose>
      <link name="link"><collision name="col">
        <geometry><box><size>{sx} 0.2 2</size></box></geometry>
      </collision><visual name="vis">
        <geometry><box><size>{sx} 0.2 2</size></box></geometry>
      </visual></link>
    </model>

    <model name="wall_east"><static>true</static><pose>{rx} 0 1 0 0 1.57</pose>
      <link name="link"><collision name="col">
        <geometry><box><size>{sy} 0.2 2</size></box></geometry>
      </collision><visual name="vis">
        <geometry><box><size>{sy} 0.2 2</size></box></geometry>
      </visual></link>
    </model>

    <model name="wall_west"><static>true</static><pose>-{rx} 0 1 0 0 1.57</pose>
      <link name="link"><collision name="col">
        <geometry><box><size>{sy} 0.2 2</size></box></geometry>
      </collision><visual name="vis">
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
# GENERATION
# ============================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Build obstacle XML once
obstacles_xml = ""
for name, x, y, typ, a, b in OBSTACLES:
    if typ == "box":
        obstacles_xml += OBSTACLE_BOX.format(name=name, x=x, y=y, sx=a, sy=b)
    else:
        obstacles_xml += OBSTACLE_CYL.format(name=name, x=x, y=y, r=a)

# Generate poses along straight line
for pid in range(NUM_POSES):
    alpha = pid / (NUM_POSES - 1)
    x = START_X + alpha * (END_X - START_X)
    y = Y_POS
    yaw = 0.0  # facing forward

    sensor_xml = SENSOR_TEMPLATE.format(x=x, y=y, z=Z_POS, yaw=yaw)

    world_xml = WORLD_TEMPLATE.format(
        id=pid,
        rx=ROOM_X,
        ry=ROOM_Y,
        sx=ROOM_X * 2,
        sy=ROOM_Y * 2,
        sensor=sensor_xml,
        obstacles=obstacles_xml
    )

    filename = f"movement_pose_{pid:03d}.world"
    with open(f"{OUTPUT_DIR}/{filename}", "w") as f:
        f.write(world_xml)

print("Done. Movement worlds generated.")
