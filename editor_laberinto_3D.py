import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.widgets import Button, Slider

# Configuración inicial
ANCHO = 15
LARGO = 15
ALTO = 5

# Inicializar laberinto 3D (Z, Y, X)
# 0: camino, 1: muro
laberinto = np.zeros((ALTO, LARGO, ANCHO), dtype=int)

# Suelo y paredes exteriores básicas
laberinto[:, 0, :] = 1
laberinto[:, -1, :] = 1
laberinto[:, :, 0] = 1
laberinto[:, :, -1] = 1

# Puntos fijos
inicio = (0, 1, 1)
objetivo = (ALTO - 1, LARGO - 2, ANCHO - 2)

# Colores: 0=blanco, 1=negro, 2=inicio(verde), 3=meta(amarillo)
cmap = ListedColormap(["white", "black", "green", "yellow"])

# Estado actual
piso_actual = 0

# Crear figura
fig, ax = plt.subplots(figsize=(10, 10))
plt.subplots_adjust(bottom=0.25)

def obtener_capa_visual(z):
    capa = laberinto[z].copy()
    if z == inicio[0]:
        capa[inicio[1], inicio[2]] = 2
    if z == objetivo[0]:
        capa[objetivo[1], objetivo[2]] = 3
    return capa

img = ax.imshow(obtener_capa_visual(piso_actual), cmap=cmap, origin='lower', extent=[0, ANCHO, 0, LARGO])

# Rejilla
for i in range(ANCHO + 1):
    ax.axvline(i, color='gray', linewidth=0.5, alpha=0.3)
for j in range(LARGO + 1):
    ax.axhline(j, color='gray', linewidth=0.5, alpha=0.3)

ax.set_title(f"EDITOR 3D - PISO {piso_actual}")

# Slider para pisos
ax_slider = plt.axes([0.2, 0.1, 0.6, 0.03])
slider_piso = Slider(ax_slider, 'Nivel Z', 0, ALTO - 1, valinit=0, valstep=1)

def actualizar_piso(val):
    global piso_actual
    piso_actual = int(slider_piso.val)
    img.set_data(obtener_capa_visual(piso_actual))
    ax.set_title(f"EDITOR 3D - PISO {piso_actual}")
    fig.canvas.draw()

slider_piso.on_changed(actualizar_piso)

# Botón Guardar
ax_save = plt.axes([0.4, 0.02, 0.2, 0.05])
btn_save = Button(ax_save, "GUARDAR (S)")

def guardar(event=None):
    np.save("laberinto_3d.npy", laberinto)
    print(f"✅ Laberinto 3D guardado en 'laberinto_3d.npy'")
    plt.suptitle("¡GUARDADO CON ÉXITO!", color="green", fontweight="bold")
    fig.canvas.draw()

btn_save.on_clicked(guardar)

# Eventos
def al_clic(event):
    if event.inaxes != ax: return
    x, y = int(event.xdata), int(event.ydata)
    if 0 <= x < ANCHO and 0 <= y < LARGO:
        if (piso_actual, y, x) == inicio or (piso_actual, y, x) == objetivo:
            return
        laberinto[piso_actual, y, x] = 1 if laberinto[piso_actual, y, x] == 0 else 0
        img.set_data(obtener_capa_visual(piso_actual))
        fig.canvas.draw()

def al_tecla(event):
    if event.key == 's':
        guardar()

fig.canvas.mpl_connect('button_press_event', al_clic)
fig.canvas.mpl_connect('key_press_event', al_tecla)

plt.show()
