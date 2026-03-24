import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.widgets import Button, Slider

# Configuración inicial
ANCHO = 15
LARGO = 15
ALTO = 5

# Intentar cargar laberinto existente
try:
    laberinto = np.load("laberinto_3d.npy")
    ALTO, LARGO, ANCHO = laberinto.shape
    print(f"✅ Cargado laberinto de {ANCHO}x{LARGO}x{ALTO}")
except:
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

# --- FUNCIONES ---

def obtener_capa_visual(z):
    capa = laberinto[z].copy()
    if z == inicio[0]:
        capa[inicio[1], inicio[2]] = 2
    if z == objetivo[0]:
        capa[objetivo[1], objetivo[2]] = 3
    return capa

def actualizar_piso(val):
    global piso_actual
    piso_actual = int(slider_piso.val)
    img.set_data(obtener_capa_visual(piso_actual))
    ax.set_title(f"EDITOR 3D - PISO {piso_actual}")
    fig.canvas.draw()

def guardar(event=None):
    np.save("laberinto_3d.npy", laberinto)
    print(f"✅ Laberinto 3D guardado ({laberinto.shape})")
    plt.suptitle("¡GUARDADO CON ÉXITO!", color="green", fontweight="bold")
    fig.canvas.draw()

def agregar_capa(event):
    global laberinto, ALTO
    nueva_capa = np.zeros((1, LARGO, ANCHO), dtype=int)
    # Copiar bordes para la nueva capa
    nueva_capa[0, 0, :] = 1
    nueva_capa[0, -1, :] = 1
    nueva_capa[0, :, 0] = 1
    nueva_capa[0, :, -1] = 1
    laberinto = np.concatenate((laberinto, nueva_capa), axis=0)
    ALTO = laberinto.shape[0]
    actualizar_slider_ui()
    print(f"➕ Capa añadida. Total: {ALTO}")

def eliminar_capa(event):
    global laberinto, ALTO, piso_actual
    if ALTO > 1:
        laberinto = laberinto[:-1]
        ALTO = laberinto.shape[0]
        if piso_actual >= ALTO:
            piso_actual = ALTO - 1
            slider_piso.set_val(piso_actual)
        actualizar_slider_ui()
        print(f"➖ Capa eliminada. Total: {ALTO}")

def actualizar_slider_ui():
    slider_piso.valmax = ALTO - 1
    slider_piso.ax.set_xlim(0, ALTO - 1)
    # Actualizar la meta si queda fuera
    global objetivo
    objetivo = (ALTO - 1, LARGO - 2, ANCHO - 2)
    actualizar_piso(piso_actual)
    fig.canvas.draw()

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

img = ax.imshow(obtener_capa_visual(piso_actual), cmap=cmap, origin='lower', extent=[0, ANCHO, 0, LARGO])

# Rejilla
for i in range(ANCHO + 1):
    ax.axvline(i, color='gray', linewidth=0.5, alpha=0.3)
for j in range(LARGO + 1):
    ax.axhline(j, color='gray', linewidth=0.5, alpha=0.3)

ax.set_title(f"EDITOR 3D - PISO {piso_actual}")

# --- INTERFAZ Y EVENTOS ---

# Slider para pisos
ax_slider = plt.axes([0.2, 0.1, 0.6, 0.03])
slider_piso = Slider(ax_slider, 'Nivel Z', 0, ALTO - 1, valinit=0, valstep=1)
slider_piso.on_changed(actualizar_piso)

# Botones de Capas
ax_plus = plt.axes([0.1, 0.02, 0.1, 0.05])
btn_plus = Button(ax_plus, "+ CAPA")
btn_plus.on_clicked(agregar_capa)

ax_minus = plt.axes([0.22, 0.02, 0.1, 0.05])
btn_minus = Button(ax_minus, "- CAPA")
btn_minus.on_clicked(eliminar_capa)

ax_save = plt.axes([0.7, 0.02, 0.2, 0.05])
btn_save = Button(ax_save, "GUARDAR (S)")
btn_save.on_clicked(guardar)

# Conectar eventos de teclado y ratón
fig.canvas.mpl_connect('button_press_event', al_clic)
fig.canvas.mpl_connect('key_press_event', al_tecla)

plt.show()
