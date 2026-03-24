import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.widgets import TextBox, Button
import heapq

# --- CONFIGURACIÓN Y ESTADO ---
ANCHO, LARGO, ALTO = 15, 15, 5
inicio = (0, 1, 1)
objetivo = (ALTO - 1, LARGO - 2, ANCHO - 2)

rz, ry, rx = inicio
trazas = []
mostrar_muros_exteriores = False
opacidad_muros = 255
niveles_visibles = []
reset_vista = False

# Paleta de colores para niveles (Z)
colores_niveles = ['#FF9999', '#99FF99', '#9999FF', '#FFFF99', '#FF99FF']

def recargar_laberinto():
    global laberinto, ALTO, LARGO, ANCHO, objetivo, niveles_visibles, colors
    try:
        laberinto = np.load("laberinto_3d.npy")
        ALTO, LARGO, ANCHO = laberinto.shape
        objetivo = (ALTO - 1, LARGO - 2, ANCHO - 2)
        # Solo inicializar si es la primera vez o si ha cambiado el tamaño
        if len(niveles_visibles) != ALTO:
            niveles_visibles = [True] * ALTO
        laberinto[objetivo] = 0
        colors = np.full(laberinto.shape, None, dtype=object)
        print(f"✅ Laberinto cargado: {ANCHO}x{LARGO}x{ALTO}")
        return True
    except Exception as e:
        print(f"❌ Error al cargar: {e}")
        return False

# Inicializar datos
recargar_laberinto()

# --- LÓGICA DE RENDERIZADO ---

def actualizar_colores():
    colors[:] = None
    for z in range(ALTO):
        if not niveles_visibles[z]: continue
        color_base = colores_niveles[z % len(colores_niveles)]
        for y in range(LARGO):
            for x in range(ANCHO):
                if laberinto[z, y, x] == 1:
                    if x == 0 or x == ANCHO-1 or y == 0 or y == LARGO-1:
                        if mostrar_muros_exteriores:
                            colors[z, y, x] = color_base + '22'
                    else:
                        alpha_hex = f"{opacidad_muros:02x}"
                        colors[z, y, x] = color_base + alpha_hex
    
    for tz, ty, tx in trazas:
        if niveles_visibles[tz]: colors[tz, ty, tx] = '#FFFFFFCC'
    if niveles_visibles[objetivo[0]]: colors[objetivo] = '#FFD700FF'
    if niveles_visibles[rz]: colors[rz, ry, rx] = '#FF0000FF'
    return colors

def dibujar_escena():
    global reset_vista
    try:
        cur_elev, cur_azim = ax.elev, ax.azim
        primera_vez = False
    except:
        primera_vez = True
        
    ax.clear()
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    
    facecolors = actualizar_colores()
    filled = np.vectorize(lambda x: x is not None)(facecolors)
    
    ax.voxels(np.transpose(filled, (2, 1, 0)), 
               facecolors=np.transpose(facecolors, (2, 1, 0)), 
               edgecolor='#33333333', linewidth=0.2)
    
    if primera_vez or reset_vista:
        ax.view_init(elev=25, azim=-45)
        reset_vista = False
    else:
        ax.view_init(elev=cur_elev, azim=cur_azim)
    
    # FORZAR PROPORCIONES 1:1:1
    # Para que cada unidad de datos ocupe el mismo espacio visual
    ax.set_xlim(0, ANCHO)
    ax.set_ylim(0, LARGO)
    ax.set_zlim(0, ALTO)
    ax.set_box_aspect((ANCHO, LARGO, ALTO))
    
    ax.set_title(f"SIMULADOR 3D - Nivel {rz}\nPos: ({rx}, {ry}, {rz})", fontsize=10)
    fig.canvas.draw()

# --- ACCIONES DEL ROBOT ---

def mover_robot(dz, dy, dx, pasos=1, animar=True):
    global rz, ry, rx, trazas
    for _ in range(pasos):
        nz, ny, nx = rz + dz, ry + dy, rx + dx
        if not (0 <= nz < ALTO and 0 <= ny < LARGO and 0 <= nx < ANCHO): return False
        if laberinto[nz, ny, nx] == 1: return False
        trazas.append((rz, ry, rx))
        rz, ry, rx = nz, ny, nx
        if animar:
            dibujar_escena()
            plt.pause(0.01)
        if (rz, ry, rx) == objetivo:
            print("¡META!")
            return True
    if not animar: dibujar_escena()
    return True

# --- INTERFAZ ---

def procesar_comandos(texto):
    for inst in texto.lower().split(';'):
        partes = inst.strip().split()
        if len(partes) < 2: continue
        cmd, num = partes[0], int(partes[1])
        if cmd in ['arriba', 'up']: mover_robot(1, 0, 0, num)
        elif cmd in ['abajo', 'down']: mover_robot(-1, 0, 0, num)
        elif cmd in ['norte', 'w']: mover_robot(0, 1, 0, num)
        elif cmd in ['sur', 's']: mover_robot(0, -1, 0, num)
        elif cmd in ['este', 'd']: mover_robot(0, 0, 1, num)
        elif cmd in ['oeste', 'a']: mover_robot(0, 0, -1, num)
    textbox.set_val('')

def toggle_muros(event=None):
    global mostrar_muros_exteriores
    mostrar_muros_exteriores = not mostrar_muros_exteriores
    dibujar_escena()

def ajustar_opacidad(cantidad):
    global opacidad_muros
    opacidad_muros = max(0, min(255, opacidad_muros + cantidad))
    dibujar_escena()

def actualizar_botones_niveles():
    global btn_niveles, ax_niveles
    if 'ax_niveles' in globals():
        for axes in ax_niveles: axes.remove()
    btn_niveles, ax_niveles = [], []
    for i in range(ALTO):
        ax_z = fig.add_axes([0.05 + (i * 0.06), 0.12, 0.05, 0.04])
        b = Button(ax_z, f"Z{i}", color='lightgreen')
        b.on_clicked(lambda e, z=i: toggle_nivel(z))
        btn_niveles.append(b)
        ax_niveles.append(ax_z)

def reiniciar_juego(event=None):
    global rz, ry, rx, trazas, reset_vista, niveles_visibles
    if recargar_laberinto():
        rz, ry, rx = inicio
        trazas = []
        reset_vista = True
        actualizar_botones_niveles()
        dibujar_escena()

def toggle_nivel(z):
    niveles_visibles[z] = not niveles_visibles[z]
    btn_niveles[z].color = 'lightgreen' if niveles_visibles[z] else 'mistyrose'
    dibujar_escena()

def ejecutar_ia(event):
    def h(p): return abs(p[0]-objetivo[0]) + abs(p[1]-objetivo[1]) + abs(p[2]-objetivo[2])
    cola = [(h((rz, ry, rx)), 0, (rz, ry, rx), [])]
    visitados = set()
    while cola:
        f, g, actual, camino = heapq.heappop(cola)
        if actual in visitados: continue
        visitados.add(actual)
        if actual == objetivo:
            for dz, dy, dx in camino: mover_robot(dz, dy, dx, 1)
            return
        for dz, dy, dx in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
            nz, ny, nx = actual[0]+dz, actual[1]+dy, actual[2]+dx
            if (0 <= nz < ALTO and 0 <= ny < LARGO and 0 <= nx < ANCHO and laberinto[nz, ny, nx] != 1):
                heapq.heappush(cola, (g + 1 + h((nz, ny, nx)), g + 1, (nz, ny, nx), camino + [(dz, dy, dx)]))

# --- INICIALIZACIÓN ---
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
plt.subplots_adjust(bottom=0.2)

ax_reiniciar = plt.axes([0.05, 0.05, 0.1, 0.05])
btn_reset = Button(ax_reiniciar, "REINICIAR")
btn_reset.on_clicked(reiniciar_juego)

ax_box = plt.axes([0.2, 0.05, 0.4, 0.05])
textbox = TextBox(ax_box, "Cmd: ", initial="")
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

fig.canvas.mpl_connect('key_press_event', lambda e: toggle_muros() if e.key == 'm' else None)

actualizar_botones_niveles()
dibujar_escena()
plt.show()
