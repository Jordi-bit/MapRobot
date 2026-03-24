import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.widgets import TextBox, Button
import heapq

# Configuración inicial
ANCHO = 15
LARGO = 15
ALTO = 5

# Intentar cargar el laberinto 3D
try:
    laberinto = np.load("laberinto_3d.npy")
except:
    # Si no existe, crear uno vacío con suelo y paredes exteriores
    laberinto = np.zeros((ALTO, LARGO, ANCHO), dtype=int)
    # Suelo (z=0) es transitable (0), pero vamos a poner muros (1) alrededor
    laberinto[:, 0, :] = 1
    laberinto[:, -1, :] = 1
    laberinto[:, :, 0] = 1
    laberinto[:, :, -1] = 1
    # Asegurar que el interior del nivel 0 esté despejado
    laberinto[0, 1:-1, 1:-1] = 0

# Actualizar dimensiones según lo cargado
ALTO, LARGO, ANCHO = laberinto.shape

# Coordenadas: (z, y, x)
inicio = (0, 1, 1)
objetivo = (ALTO - 1, LARGO - 2, ANCHO - 2)

# Asegurar inicio y meta transitables
laberinto[inicio] = 0
laberinto[objetivo] = 0

# Estado del robot
rz, ry, rx = inicio
trazas = []
mostrar_muros_exteriores = False # Ocultos por defecto para mejor visión
opacidad_muros = 255 # Opacos por defecto ('ff')

# Colores para voxels: [vacio, muro, traza, robot, meta]
colors = np.full(laberinto.shape, None, dtype=object)

# Paleta de colores para niveles (Z)
colores_niveles = [
    '#FF9999', # Rojo suave
    '#99FF99', # Verde suave
    '#9999FF', # Azul suave
    '#FFFF99', # Amarillo suave
    '#FF99FF'  # Rosa suave
]

def actualizar_colores():
    colors[:] = None # Transparente por defecto
    
    # Renderizar muros con lógica de visibilidad
    for z in range(ALTO):
        color_base = colores_niveles[z % len(colores_niveles)]
        for y in range(LARGO):
            for x in range(ANCHO):
                if laberinto[z, y, x] == 1:
                    # Muros exteriores (si están activos)
                    if x == 0 or x == ANCHO-1 or y == 0 or y == LARGO-1:
                        if mostrar_muros_exteriores:
                            colors[z, y, x] = color_base + '22' # Alpha muy bajo
                    else:
                        # Muros interiores: Opacidad dinámica
                        alpha_hex = f"{opacidad_muros:02x}"
                        colors[z, y, x] = color_base + alpha_hex
    
    # Trazas: Blanco brillante (para que resalte sobre los niveles)
    for tz, ty, tx in trazas:
        colors[tz, ty, tx] = '#FFFFFFCC'
        
    # Meta: Dorado intenso
    colors[objetivo] = '#FFD700FF'
    
    # Robot: Rojo intenso (para máxima visibilidad)
    colors[rz, ry, rx] = '#FF0000FF'
    
    return colors

# Crear figura 3D
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
plt.subplots_adjust(bottom=0.2)

def dibujar_escena():
    # Guardar vista actual si ya existe el eje
    try:
        cur_elev = ax.elev
        cur_azim = ax.azim
        primera_vez = False
    except:
        primera_vez = True
        
    ax.clear()
    ax.set_xlabel('X (Ancho)')
    ax.set_ylabel('Y (Largo)')
    ax.set_zlabel('Z (Piso)')
    
    # Dibujar voxels: Solo aquellos que tienen un color asignado
    # Esto evita el ValueError al desativar muros exteriores
    facecolors = actualizar_colores()
    filled = np.vectorize(lambda x: x is not None)(facecolors)
    
    vox = ax.voxels(np.transpose(filled, (2, 1, 0)), 
                    facecolors=np.transpose(facecolors, (2, 1, 0)), 
                    edgecolor='#33333333', linewidth=0.2)
    
    # Ajustar vista
    if primera_vez:
        ax.view_init(elev=25, azim=-45)
    else:
        ax.view_init(elev=cur_elev, azim=cur_azim)
    
    # Asegurar proporción 1:1:1 para que los niveles no se vean estirados
    ax.set_box_aspect((ANCHO, LARGO, ALTO))
    
    ax.set_title(f"SIMULADOR ROBOT 3D - MEJORADO\nPosición actual: ({rx}, {ry}, {rz})", 
                 fontsize=12, fontweight='bold', color='darkblue')
    fig.canvas.draw()

# Función para mover
def mover_robot(dz, dy, dx, pasos=1, animar=True):
    global rz, ry, rx, trazas
    for _ in range(pasos):
        nz, ny, nx = rz + dz, ry + dy, rx + dx
        
        # Validar límites
        if not (0 <= nz < ALTO and 0 <= ny < LARGO and 0 <= nx < ANCHO):
            print("¡Fuera de límites!")
            return False
            
        # Validar muros
        if laberinto[nz, ny, nx] == 1:
            print("¡Choque con un muro!")
            return False
            
        # Mover y dejar traza
        trazas.append((rz, ry, rx))
        rz, ry, rx = nz, ny, nx
        
        if animar:
            dibujar_escena()
            # Usar una pausa más robusta que no choque con el event loop
            plt.pause(0.01)
            
        if (rz, ry, rx) == objetivo:
            print("¡META ALCANZADA!")
            return True
    
    if not animar:
        dibujar_escena()
    return True

# Procesar comandos
def procesar_comandos(texto):
    instrucciones = texto.lower().split(';')
    for inst in instrucciones:
        partes = inst.strip().split()
        if len(partes) < 2: continue
        cmd, num = partes[0], int(partes[1])
        
        if cmd in ['arriba', 'up']: mover_robot(1, 0, 0, num)
        elif cmd in ['abajo', 'down']: mover_robot(-1, 0, 0, num)
        elif cmd in ['norte', 'arriba_y', 'w']: mover_robot(0, 1, 0, num)
        elif cmd in ['sur', 'abajo_y', 's']: mover_robot(0, -1, 0, num)
        elif cmd in ['este', 'derecha', 'd']: mover_robot(0, 0, 1, num)
        elif cmd in ['oeste', 'izquierda', 'a']: mover_robot(0, 0, -1, num)
    textbox.set_val('')
    
def toggle_muros(event=None):
    global mostrar_muros_exteriores
    mostrar_muros_exteriores = not mostrar_muros_exteriores
    dibujar_escena()

def al_tecla(event):
    if event.key == 'm':
        toggle_muros()
    elif event.key == 'r':
        reiniciar_juego()

def ajustar_opacidad(cantidad):
    global opacidad_muros
    opacidad_muros = max(0, min(255, opacidad_muros + cantidad))
    dibujar_escena()

def reiniciar_juego(event=None):
    global rz, ry, rx, trazas
    rz, ry, rx = inicio
    trazas = []
    dibujar_escena()
    print("🔄 Laberinto reiniciado.")

# IA A* para 3D
def ia_camino():
    def h(p1, p2):
        return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1]) + abs(p1[2]-p2[2])
    
    vecinos = [
        (1,0,0,'arriba'), (-1,0,0,'abajo'),
        (0,1,0,'norte'), (0,-1,0,'sur'),
        (0,0,1,'este'), (0,0,-1,'oeste')
    ]
    
    cola = [(h((rz, ry, rx), objetivo), 0, (rz, ry, rx), [])]
    visitados = set()
    
    while cola:
        f, g, actual, camino = heapq.heappop(cola)
        if actual in visitados: continue
        visitados.add(actual)
        
        if actual == objetivo: return camino
        
        for dz, dy, dx, nombre in vecinos:
            nz, ny, nx = actual[0]+dz, actual[1]+dy, actual[2]+dx
            if (0 <= nz < ALTO and 0 <= ny < LARGO and 0 <= nx < ANCHO and 
                laberinto[nz, ny, nx] != 1):
                heapq.heappush(cola, (g + 1 + h((nz, ny, nx), objetivo), g + 1, (nz, ny, nx), camino + [(dz, dy, dx)]))
    return None

def ejecutar_ia(event):
    camino = ia_camino()
    if camino:
        for dz, dy, dx in camino:
            mover_robot(dz, dy, dx, 1, animar=True)
    else:
        print("No se encontró camino.")

# UI
ax_reiniciar = plt.axes([0.05, 0.05, 0.1, 0.05])
btn_reset = Button(ax_reiniciar, "REINICIAR (R)")
btn_reset.on_clicked(reiniciar_juego)

ax_box = plt.axes([0.2, 0.05, 0.4, 0.05])
textbox = TextBox(ax_box, "Comando: ", initial="")
textbox.on_submit(procesar_comandos)

ax_muros = plt.axes([0.62, 0.05, 0.08, 0.05])
btn_muros = Button(ax_muros, "MUROS (M)")
btn_muros.on_clicked(toggle_muros)

ax_mas = plt.axes([0.71, 0.05, 0.04, 0.05])
btn_mas = Button(ax_mas, "+")
btn_mas.on_clicked(lambda e: ajustar_opacidad(20))

ax_menos = plt.axes([0.76, 0.05, 0.04, 0.05])
btn_menos = Button(ax_menos, "-")
btn_menos.on_clicked(lambda e: ajustar_opacidad(-20))

ax_ia = plt.axes([0.82, 0.05, 0.1, 0.05])
btn_ia = Button(ax_ia, "IA (A*)")
btn_ia.on_clicked(ejecutar_ia)

fig.canvas.mpl_connect('key_press_event', al_tecla)

dibujar_escena()
plt.show()
