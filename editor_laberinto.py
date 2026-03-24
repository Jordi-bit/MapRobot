import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

# Tamaño del laberinto personalizado
ancho = 25   # columnas (X) - Reducido para mejor visibilidad en el juego
alto = 25    # filas (Y)

# Inicializar laberinto con caminos
laberinto = np.zeros((alto, ancho), dtype=int)

# Posiciones fijas de inicio y objetivo
inicio = (0, 0)  # (x, y)
objetivo = (ancho - 1, alto - 1)  # (x, y)
laberinto[inicio[1], inicio[0]] = 2
laberinto[objetivo[1], objetivo[0]] = 3

# Colores: 0 = blanco, 1 = negro, 2 = inicio (verde), 3 = objetivo (amarillo)
cmap = ListedColormap(["white", "black", "green", "yellow"])

# Crear figura
fig, ax = plt.subplots(figsize=(10, 10))
img = ax.imshow(laberinto, cmap=cmap, origin='lower', extent=[0, ancho, 0, alto])

# Dibujar rejilla
for i in range(ancho + 1):
    ax.axvline(i, color='gray', linewidth=0.5, alpha=0.5)
for j in range(alto + 1):
    ax.axhline(j, color='gray', linewidth=0.5, alpha=0.5)

# Etiquetas
ax.set_xticks(np.arange(ancho) + 0.5)
ax.set_yticks(np.arange(alto) + 0.5)
ax.set_xticklabels(np.arange(ancho))
ax.set_yticklabels(np.arange(alto))
ax.set_xlim(0, ancho)
ax.set_ylim(0, alto)
ax.tick_params(axis='both', which='both', length=0, labelsize=8)

# Título e instrucciones
plt.title("EDITOR DE LABERINTO\nClic: Poner/Quitar Muro | 's': Guardar", fontsize=14, color='darkblue')

# Clic para alternar entre camino y pared
def al_clic(event):
    if event.inaxes != ax:
        return
    x, y = int(event.xdata), int(event.ydata)
    if 0 <= x < ancho and 0 <= y < alto:
        if (x, y) == inicio or (x, y) == objetivo:
            return
        laberinto[y, x] = 1 if laberinto[y, x] == 0 else 0
        # Asegurar que inicio y objetivo no se borren
        laberinto[inicio[1], inicio[0]] = 2
        laberinto[objetivo[1], objetivo[0]] = 3
        img.set_data(laberinto)
        fig.canvas.draw()

# Guardar al presionar "s"
def al_tecla(event):
    if event.key == 's':
        # Guardar datos para el programa
        laberinto_guardar = laberinto.copy()
        # Convertir inicio/objetivo a camino para el archivo de datos si es necesario, 
        # o mantenerlos si el juego los espera. El juego AI.py los sobreescribe.
        np.savetxt("laberinto_guardado.txt", laberinto_guardar, fmt='%d')
        
        # Guardar como imagen
        plt.savefig("laberinto.png", bbox_inches='tight')
        
        print("✅ Laberinto guardado como 'laberinto_guardado.txt' y 'laberinto.png'.")
        plt.suptitle("¡GUARDADO CON ÉXITO!", fontsize=16, color='green', fontweight='bold')
        fig.canvas.draw()

# Conectar eventos
fig.canvas.mpl_connect('button_press_event', al_clic)
fig.canvas.mpl_connect('key_press_event', al_tecla)

plt.tight_layout()
plt.show()
