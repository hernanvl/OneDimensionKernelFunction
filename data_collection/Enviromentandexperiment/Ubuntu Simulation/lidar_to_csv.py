import math, time, csv

def leer_scan():
    with open('/tmp/lidar_scan.txt', 'r') as f:
        lineas = f.readlines()
    angle_min = float(lineas[0].split(':')[1])
    angle_max = float(lineas[1].split(':')[1])
    ranges    = [float(l.strip()) for l in lineas[3:] if l.strip()]
    return angle_min, angle_max, ranges

angle_min, angle_max, ranges = leer_scan()
n = len(ranges)
step = (angle_max - angle_min) / n
timestamp = int(time.time())

output = "/home/hernan/gazebo_worlds/lidar_scan.csv"

with open(output, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["timestamp", "quality", "angle_deg", "distance_mm"])
    for i, r in enumerate(ranges):
        angle_deg    = round(math.degrees(angle_min + i * step) % 360, 6)
        distance_mm  = round(r * 1000, 2)
        writer.writerow([timestamp, 15, angle_deg, distance_mm])

print(f"✅ Guardado: {output} — {n} filas")
