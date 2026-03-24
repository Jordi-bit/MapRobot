import matplotlib.pyplot as plt                    # Librería para gráficos 2D
from matplotlib.widgets import TextBox, Button      # Librería para TextBox y Button
import numpy as np                                 # Librería para trabajar con matrices y arrays
from matplotlib.colors import ListedColormap       # Librería para usar colores personalizados
import heapq

# Cargar el laberinto desde el archivo guardado por el editor
try:
    laberinto = np.loadtxt("laberinto_guardado.txt", dtype=int)
except:
    # Si no existe, crear uno vacío por defecto
    laberinto = np.zeros((25, 25), dtype=int)

alto, ancho = laberinto.shape
tamano_y, tamano_x = alto, ancho

# Coordenadas de inicio y objetivo
inicio = (0, 0)
objetivo = (ancho - 1, alto - 1)

# Asegurar que inicio y objetivo sean transitables en el dato
laberinto[inicio[1], inicio[0]] = 0
laberinto[objetivo[1], objetivo[0]] = 0

# Colores personalizados: 0=camino, 1=muro, 2=traza, 3=robot, 4=meta, 5=choque
cmap = ListedColormap([
    "white",      # 0 = camino (blanco)
    "black",      # 1 = muro (negro)
    "#90EE90",   # 2 = traza (verde claro)
    "#006400",   # 3 = robot (verde oscuro)
    "#FFD700",   # 4 = meta (dorado/amarillo)
    "#FF0000"    # 5 = choque (rojo)
])

# Estado del robot
x, y = inicio

# Dibujar elementos especiales sobre una copia para no ensuciar el archivo de datos original
def obtener_rejilla_visual():
    visual = laberinto.copy()
    visual[visual == 2] = 2 # Mantener trazas
    visual[objetivo[1], objetivo[0]] = 4
    visual[y, x] = 3
    return visual

# Crear figura
fig, ax = plt.subplots(figsize=(9, 9))
plt.subplots_adjust(top=0.85) # Dejar espacio para controles
img = ax.imshow(obtener_rejilla_visual(), cmap=cmap, origin='lower', 
                extent=[0, ancho, 0, alto], vmin=0, vmax=5, zorder=0)

# Dibujar rejilla
for i in range(ancho + 1):
    ax.axvline(i, color='gray', linewidth=0.5, alpha=0.3, zorder=1)
for j in range(alto + 1):
    ax.axhline(j, color='gray', linewidth=0.5, alpha=0.3, zorder=1)

# Ajustes de ejes
ax.set_xticks(np.arange(ancho) + 0.5)
ax.set_xticklabels(np.arange(ancho), fontsize=8)
ax.set_yticks(np.arange(alto) + 0.5)
ax.set_yticklabels(np.arange(alto), fontsize=8)

# Botón Reiniciar
ax_btn = plt.axes([0.81, 0.92, 0.15, 0.04])
btn_reset = Button(ax_btn, 'REINTENTAR', color='lightgray', hovercolor='orange')

# TextBox para comandos
axbox = plt.axes([0.15, 0.92, 0.5, 0.04])
textbox = TextBox(axbox, "Robot: ", initial="")

# Texto de ayuda
ayuda = fig.text(0.5, 0.89, "Escribe 'derecha 5; arriba 2' | 'z': IA | 'n' o botón: Reiniciar", 
                 fontsize=10, color='blue', ha='center')

# Variables de control de mensajes
mensaje_pantalla = None

def mostrar_mensaje(texto, color_fondo='moccasin', color_texto='red'):
    global mensaje_pantalla
    if mensaje_pantalla:
        mensaje_pantalla.remove()
    mensaje_pantalla = ax.text(ancho/2, alto/2, texto, fontsize=20, fontweight='bold',
                               color=color_texto, ha='center', va='center', zorder=10,
                               bbox=dict(facecolor=color_fondo, edgecolor='orange', boxstyle='round,pad=1'))
    fig.canvas.draw()

# Función para reiniciar
def reiniciar_todo(event=None):
    global x, y, laberinto, mensaje_pantalla
    try:
        laberinto = np.loadtxt("laberinto_guardado.txt", dtype=int)
    except:
        pass
    x, y = inicio
    if mensaje_pantalla:
        mensaje_pantalla.remove()
        mensaje_pantalla = None
    img.set_data(obtener_rejilla_visual())
    fig.canvas.draw()
    print("🔄 Reiniciado desde el origen.")

btn_reset.on_clicked(reiniciar_todo)

# Función para mover el robot
def mover_robot(direccion, pasos=1, animar=True):
    global x, y, mensaje_pantalla
    
    for _ in range(pasos):
        nx, ny = x, y
        if direccion in ['up', 'arriba']: ny += 1
        elif direccion in ['down', 'abajo']: ny -= 1
        elif direccion in ['left', 'izquierda']: nx -= 1
        elif direccion in ['right', 'derecha']: nx += 1
        
        # Validar límites
        if not (0 <= nx < ancho and 0 <= ny < alto):
            mostrar_mensaje("¡FUERA DE LÍMITES!\n¿REINTENTAR? (Pulsa 'n' o botón)")
            return False
            
        # Validar muros
        if laberinto[ny, nx] == 1:
            # Mostrar choque visualmente (opcionalmente mover el robot al muro y ponerlo rojo)
            x, y = nx, ny
            img.set_data(obtener_rejilla_visual())
            mostrar_mensaje("¡¡ MISIÓN FALLIDA !!\n¿REINTENTAR? (Pulsa 'n' o botón)")
            return False
            
        # Mover y dejar traza
        laberinto[y, x] = 2 # Traza en posición vieja
        x, y = nx, ny
        
        if animar:
            img.set_data(obtener_rejilla_visual())
            plt.pause(0.1)
            
        if (x, y) == objetivo:
            mostrar_mensaje("¡¡ MISIÓN CUMPLIDA !!\nFELICIDADES", 'lightyellow', 'blue')
            return True
            
    img.set_data(obtener_rejilla_visual())
    fig.canvas.draw()
    return True

# Procesar entrada de texto
def procesar_comandos(texto):
    if not texto: return
    # Limpiar mensajes previos
    global mensaje_pantalla
    if mensaje_pantalla:
        mensaje_pantalla.remove()
        mensaje_pantalla = None
        
    instrucciones = texto.lower().split(';')
    for inst in instrucciones:
        partes = inst.strip().split()
        if len(partes) == 2:
            dir, num = partes[0], partes[1]
            try:
                mover_robot(dir, int(num))
            except:
                continue
    textbox.set_val('')

# Algoritmo A* para la IA
def ia_buscar_camino():
    def heuristica(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    vecinos = [(-1,0, 'izquierda'), (1,0, 'derecha'), (0,-1, 'abajo'), (0,1, 'arriba')]
    cola = [(0 + heuristica(inicio, objetivo), 0, (x, y), [])]
    visitados = set()

    while cola:
        f, g, actual, camino = heapq.heappop(cola)
        if actual in visitados: continue
        visitados.add(actual)

        if actual == objetivo:
            return camino

        for dx, dy, nombre in vecinos:
            nx, ny = actual[0] + dx, actual[1] + dy
            if 0 <= nx < ancho and 0 <= ny < alto and laberinto[ny, nx] != 1:
                heapq.heappush(cola, (g + 1 + heuristica((nx, ny), objetivo), g + 1, (nx, ny), camino + [nombre]))
    return None

def ejecutar_ia(event):
    if event.key == 'z':
        camino = ia_buscar_camino()
        if camino:
            for paso in camino:
                if not mover_robot(paso, 1, animar=True):
                    break
        else:
            mostrar_mensaje("NO HAY CAMINO POSIBLE", 'mistyrose', 'red')

def teclado_eventos(event):
    if event.key == 'n':
        reiniciar_todo()
    elif event.key == 'z':
        ejecutar_ia(event)

# Conectar eventos
textbox.on_submit(procesar_comandos)
fig.canvas.mpl_connect('key_press_event', teclado_eventos)

plt.show()