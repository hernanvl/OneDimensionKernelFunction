import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os

# CONFIGURACIÓN
ARCHIVO_CSV = 'mov2.csv' 

def replay():
    if not os.path.exists(ARCHIVO_CSV):
        print(f"ERROR: No encuentro el archivo {ARCHIVO_CSV}")
        print(f"Asegúrate de que esté en: {os.getcwd()}")
        return

    print("Cargando datos...")
    df = pd.read_csv(ARCHIVO_CSV)
    
    # Agrupar por timestamp (cada vuelta del lidar)
    scans = [group for _, group in df.groupby('timestamp')]
    print(f"Total de vueltas (frames) a mostrar: {len(scans)}")

    fig = plt.figure(figsize=(20, 20))
    ax = fig.add_subplot(111, projection='polar')
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    
    scatter = ax.scatter([], [], s=5, c='red')
    ax.set_ylim(0, 4000) 

    def update(frame):
        current_scan = scans[frame]
        angles = np.radians(current_scan['angle_deg'])
        distances = current_scan['distance_mm']
        offsets = np.column_stack((angles, distances))
        scatter.set_offsets(offsets)
        return scatter,

    ani = animation.FuncAnimation(fig, update, frames=len(scans), interval=50, blit=True)
    plt.title(f"Reproduciendo: {ARCHIVO_CSV}")
    plt.show()

if __name__ == '__main__':
    replay()