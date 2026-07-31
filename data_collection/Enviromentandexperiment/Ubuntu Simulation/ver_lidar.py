import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

def leer_scan():
    try:
        with open('/tmp/lidar_scan.txt', 'r') as f:
            lineas = f.readlines()
        angle_min = float(lineas[0].split(':')[1])
        angle_max = float(lineas[1].split(':')[1])
        ranges    = [float(l.strip()) for l in lineas[3:] if l.strip()]
        return angle_min, angle_max, ranges
    except:
        return None, None, []

fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xlim(-6, 6)
ax.set_ylim(-6, 6)
ax.set_aspect('equal')
ax.grid(True, alpha=0.3)
ax.set_facecolor('#1a1a2e')
fig.patch.set_facecolor('#1a1a2e')

scatter = ax.scatter([], [], s=5, c='cyan', zorder=3)
ax.plot(0, 0, 'y^', markersize=12, label='LIDAR')
ax.tick_params(colors='white')
ax.legend(facecolor='#1a1a2e', labelcolor='white')

def update(frame):
    angle_min, angle_max, ranges = leer_scan()
    if not ranges:
        return scatter,
    n = len(ranges)
    step = (angle_max - angle_min) / n
    angles = [angle_min + i * step for i in range(n)]
    xs = [r * math.cos(a) for r, a in zip(ranges, angles) if 0.1 < r < 11.9]
    ys = [r * math.sin(a) for r, a in zip(ranges, angles) if 0.1 < r < 11.9]
    scatter.set_offsets(np.c_[xs, ys])
    ax.set_title(f'Mapa LIDAR 2D — {len(xs)} puntos', color='white')
    return scatter,

ani = animation.FuncAnimation(fig, update, interval=200, blit=False)
plt.tight_layout()
plt.show()
