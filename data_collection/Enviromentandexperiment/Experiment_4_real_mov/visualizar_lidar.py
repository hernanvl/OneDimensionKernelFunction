import subprocess
import re
import numpy as np
import matplotlib.pyplot as plt

ULTRA_SIMPLE = r"C:\Users\herna\Downloads\rplidar_sdk-master\rplidar_sdk-master\output\Win32\Debug\ultra_simple.exe"

proc = subprocess.Popen(
    [ULTRA_SIMPLE, "--channel", "--serial", "COM3", "115200"],
    stdout=subprocess.PIPE,
    text=True
)

pattern = re.compile(r"theta:\s*([\d\.]+)\s*Dist:\s*([\d\.]+)")

plt.ion()
fig, ax = plt.subplots()
ax.set_xlim(-6000, 6000)
ax.set_ylim(-6000, 6000)
ax.set_aspect("equal")

while True:
    xs = []
    ys = []

    # juntar 360 puntos
    for _ in range(360):
        line = proc.stdout.readline()
        match = pattern.search(line)
        if match:
            theta = float(match.group(1))
            dist = float(match.group(2))

            ang = np.deg2rad(theta)
            x = dist * np.cos(ang)
            y = dist * np.sin(ang)

            xs.append(x)
            ys.append(y)

    ax.clear()
    ax.set_xlim(-6000, 6000)
    ax.set_ylim(-6000, 6000)
    ax.set_aspect("equal")
    ax.scatter(xs, ys, s=5)
    plt.pause(0.001)
