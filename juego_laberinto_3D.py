import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.widgets import TextBox, Button, Slider
import matplotlib.patches as patches
import heapq
import os
import json
from datetime import datetime
from tello_controller import TelloController
import tkinter as tk
from tkinter import filedialog

# Initialize tkinter root (hidden)
root = tk.Tk()
root.withdraw()

# --- CONFIGURACIÓN Y ESTADO ---
# Colores del tema oscuro (estilo editor_laberinto_3d)
C_BG = '#0d1117'
C_SIDEBAR = '#161b22'
C_CATEGORY = '#1c2333'
C_CATEGORY_ALT = '#21262d'
C_BORDER = '#30363d'
C_TEXT = '#e6edf3'
C_TEXT_MUTED = '#8b949e'
C_TEXT_DIM = '#6e7681'
C_ACCENT = '#58a6ff'
C_GREEN = '#3fb950'
C_RED = '#f85149'
C_YELLOW = '#d29922'
C_PURPLE = '#bc8cff'
C_BTN_BG = '#21262d'
C_BTN_HOVER = '#30363d'
C_BTN_ACTIVE = '#1f6feb'


plt.style.use('dark_background')
plt.rcParams['text.color'] = C_TEXT
fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor(C_BG)

SX, SW = 0.0, 0.18  # Sidebar x position and width

# Sidebar background
sidebar_bg = patches.Rectangle(
    (SX, 0), SW, 1.0,
    fill=True, facecolor=C_SIDEBAR, edgecolor='none',
    transform=fig.transFigure, zorder=-10
)
fig.patches.append(sidebar_bg)

sidebar_border = patches.Rectangle(
    (SW, 0), 0.003, 1.0,
    fill=True, facecolor=C_BORDER, edgecolor='none',
    transform=fig.transFigure, zorder=-9
)
fig.patches.append(sidebar_border)

ax = fig.add_axes([0.205, 0.03, 0.68, 0.86], projection='3d')

# Desactivar atajos de teclado por defecto de Matplotlib que interfieren
plt.rcParams['keymap.quit'] = [] # Evitar que 'q' cierre la ventana
plt.rcParams['keymap.save'] = [] # Evitar que 's' abra el diálogo de guardado
laberinto = None # Se cargará en recargar_laberinto
colors = None    # Se creará en recargar_laberinto
btn_niveles = [] # Botones de pisos
ax_niveles = []  # Ejes de los botones de pisos
# Variables Globales (Estado)
resolucion_cm = 25
ESC_FACTOR = 100.0 / resolucion_cm
ANCHO_m, LARGO_m, ALTO_m = 1.0, 1.0, 1.0
ALTO, LARGO, ANCHO = 4, 4, 4
inicio = [0, 0, 0] # Nivel, Y, X
objetivos = [[0, 1, 1]]  # Lista de metas
objetivo = [0, 1, 1]  # Meta actual (primera de la lista)
meta_indice_actual = 0  # Índice de la meta actual
modo_tour = False  # Si True, el dron visita todas las metas en orden
posicion_origen = None  # Se guarda cuando el dron sale por primera vez
DRONE_SIZE = [0.05, 0.20, 0.20] # Z, Y, X en metros
velocidad_movimiento = 0.2     # Metros por pulsación 
rz, ry, rx = 0.0, 0.0, 0.0
trazas = []
mapa_descubierto = None
mostrar_todo_el_mapa = False # Toggle para ver el mapa completo sin explorar
cancelar_operacion = False
mostrar_trazas = True # Estado de visibilidad de trazas
opacidad_muros = 255
niveles_visibles = []
reset_vista = False
alt_seguridad_cm = 20 # Nueva variable: Altura de seguridad por defecto (cm)
TELLO_HOVER_CM = 80  # Altura a la que el Tello se estabiliza tras el takeoff (cm, aprox. hardware)

modo_exploracion = False # Nuevo: Modo niebla de guerra
modo_ia_expandido = False # Estado del menú IA
modo_niveles_expandido = False # Estado del menú de niveles
modo_camara_expandido = False # Estado del menú de cámara
tello_active = False     # Estado de conexión con drone real
modo_simulacion = True   # Si True, el dron opera en modo simulación (no conecta al hardware)
tello = TelloController()
tello.force_simulation = modo_simulacion  # Sincronizar el modo inicial
# resolucion_cm = 100      # Default (ya declarado arriba)
# ESC_FACTOR = 1.0         # Celdas por metro (100 / res) (ya declarado arriba)
archivo_actual = "laberinto_3d.npy"

# Paleta de colores para niveles (Z)
colores_niveles = ['#FF9999', '#99FF99', '#9999FF', '#FFFF99', '#FF99FF']

def escanear_entorno(radio_m=1.0):
    global mapa_descubierto
    if mapa_descubierto is None: return
    # Revelar un área alrededor del robot (Simula sensores del drone)
    # Convertir metros a índices (coherente con A*)
    radio_celdas = int(radio_m * ESC_FACTOR)
    iz = int(rz * ESC_FACTOR)
    iy = int(ry * ESC_FACTOR)
    ix = int(rx * ESC_FACTOR)
    
    z_min, z_max = max(0, iz-1), min(ALTO, iz+2)
    y_min, y_max = max(0, iy-radio_celdas), min(LARGO, iy+radio_celdas+1)
    x_min, x_max = max(0, ix-radio_celdas), min(ANCHO, ix+radio_celdas+1)
    mapa_descubierto[z_min:z_max, y_min:y_max, x_min:x_max] = True

def cargar_metadata(ruta_npy):
    global objetivo, objetivos, inicio, resolucion_cm, ANCHO_m, LARGO_m, ALTO_m, ALTO, LARGO, ANCHO
    ruta_json = ruta_npy.replace(".npy", ".json")
    if os.path.exists(ruta_json):
        try:
            with open(ruta_json, 'r') as f:
                data = json.load(f)
                # Cargar múltiples metas
                objetivos_data = data.get("objetivo", [[ALTO - 1, LARGO - 1, ANCHO - 1]])
                if isinstance(objetivos_data[0], int):
                    objetivos = [objetivos_data]
                else:
                    objetivos = objetivos_data
                objetivo = objetivos[0]  # Usar primera meta como objetivo principal
                inicio = data.get("inicio", [0, 0, 0])
                resolucion_cm = data.get("resolucion_cm", 25)
                # Actualizar metros
                ANCHO_m = ANCHO * (resolucion_cm / 100.0)
                LARGO_m = LARGO * (resolucion_cm / 100.0)
                ALTO_m = ALTO * (resolucion_cm / 100.0)
                print(f"🏠 Inicio: {inicio} | 🎯 Metas: {len(objetivos)} | Res: {resolucion_cm}cm")
        except Exception as e:
            print(f"Error al cargar metadata: {e}")

def recargar_laberinto():
    global laberinto, ALTO, LARGO, ANCHO, objetivo, inicio, niveles_visibles, colors
    global rz, ry, rx, trazas, ESC_FACTOR, mapa_descubierto, ANCHO_m, LARGO_m, ALTO_m
    try:
        laberinto = np.load(archivo_actual)
        ALTO, LARGO, ANCHO = laberinto.shape
        
        # Cargar Objetivo, Inicio y Resolución desde metadata
        cargar_metadata(archivo_actual)
            
        ESC_FACTOR = 100.0 / resolucion_cm
        # Posicionar dron en el centro del cubo de inicio (coordenadas de celda a metros)
        rz = (inicio[0] + 0.1) / ESC_FACTOR # Un poco elevado del suelo
        ry = (inicio[1] + 0.5) / ESC_FACTOR
        rx = (inicio[2] + 0.5) / ESC_FACTOR
        
        # Solo inicializar si es la primera vez o si ha cambiado el tamaño
        if len(niveles_visibles) != ALTO:
            niveles_visibles = [True] * ALTO
        
        # Asegurarse de que el objetivo sea transitable
        laberinto[tuple(objetivo)] = 0
        # Asegurarse de que el inicio sea transitable
        laberinto[tuple(map(int, inicio))] = 0
        
        colors = np.full(laberinto.shape, None, dtype=object)
        
        # Inicializar posición y mapa descubierto
        trazas = []
        mapa_descubierto = np.zeros(laberinto.shape, dtype=bool)
        escanear_entorno() # Descubrir punto inicial
        
        print(f"✅ Laberinto cargado: {ANCHO}x{LARGO}x{ALTO}")
        return True
    except Exception as e:
        print(f"❌ Error al cargar: {e}")
        # Garantizar que las variables críticas existan aunque falle la carga
        laberinto = np.zeros((ALTO, LARGO, ANCHO), dtype=int)
        mapa_descubierto = np.zeros_like(laberinto, dtype=bool)
        colors = np.full(laberinto.shape, None, dtype=object)
        return False

# Inicializar datos
recargar_laberinto()

# --- LÓGICA DE RENDERIZADO ---

def actualizar_colores():
    global colors
    if colors is None or colors.shape != laberinto.shape: 
        colors = np.full(laberinto.shape, None, dtype=object)
    colors.fill(None)

       # Definir colores por nivel (visibilidad 1-based para el usuario)
    for z in range(ALTO):
        if niveles_visibles[z]:
            color_base = colores_niveles[z % len(colores_niveles)]
            alpha_hex = f"{opacidad_muros:02x}"
            
            # Solo iterar si hay algo que mostrar
            for y in range(LARGO):
                for x in range(ANCHO):
                    is_discovered = mapa_descubierto[z, y, x] if mapa_descubierto is not None else False
                    
                    if laberinto[z, y, x] == 1: # Es un muro
                        if mostrar_todo_el_mapa or (modo_exploracion and is_discovered):
                            colors[z, y, x] = color_base + alpha_hex
    
    # Mostrar todas las metas
    for i, obj in enumerate(objetivos):
        if len(obj) >= 3 and niveles_visibles[obj[0]]:
            if i == meta_indice_actual:
                colors[obj[0], obj[1], obj[2]] = '#FF8C00FF'  # Naranja para la meta seleccionada
            else:
                colors[obj[0], obj[1], obj[2]] = '#FFD700FF'  # Oro para las demás metas
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
    
    # Coordenadas en metros para el renderizado
    x_grid, y_grid, z_grid = np.indices((ANCHO+1, LARGO+1, ALTO+1)) / ESC_FACTOR

    ax.voxels(x_grid, y_grid, z_grid, 
               filled=np.transpose(filled, (2, 1, 0)), 
               facecolors=np.transpose(facecolors, (2, 1, 0)), 
               edgecolor='#33333333', linewidth=0.2)
    
    if primera_vez or reset_vista:
        ax.view_init(elev=25, azim=-45)
        reset_vista = False
    else:
        ax.view_init(elev=cur_elev, azim=cur_azim)
    
    # Enforzar límites explícitos en METROS
    ANCHO_m, LARGO_m, ALTO_m = ANCHO/ESC_FACTOR, LARGO/ESC_FACTOR, ALTO/ESC_FACTOR
    # Forzar ticks exactos según resolución para evitar confusión de "5 cuadros"
    step = resolucion_cm / 100.0
    ax.set_xticks(np.arange(0, ANCHO_m + 0.01, step))
    ax.set_yticks(np.arange(0, LARGO_m + 0.01, step))
    ax.set_zticks(np.arange(0, ALTO_m + 0.01, step))
    ax.set_box_aspect((ANCHO_m, LARGO_m, ALTO_m))
    
    # Ajustar límites exactos
    ax.set_xlim(0, ANCHO_m)
    ax.set_ylim(0, LARGO_m)
    ax.set_zlim(0, ALTO_m)
    
    # 2. El Robot (Drone) - Dibujado como un cubo centrado en su posición (rx, ry, rz)
    dz, dy, dx = DRONE_SIZE
    v = np.array([
        [rx-dx/2, ry-dy/2, rz], [rx+dx/2, ry-dy/2, rz], [rx+dx/2, ry+dy/2, rz], [rx-dx/2, ry+dy/2, rz],
        [rx-dx/2, ry-dy/2, rz+dz], [rx+dx/2, ry-dy/2, rz+dz], [rx+dx/2, ry+dy/2, rz+dz], [rx-dx/2, ry+dy/2, rz+dz]
    ])
    verts = [[v[0],v[1],v[2],v[3]], [v[4],v[5],v[6],v[7]], [v[0],v[1],v[5],v[4]], [v[2],v[3],v[7],v[6]], [v[1],v[2],v[6],v[5]], [v[4],v[7],v[3],v[0]]]
    ax.add_collection3d(Poly3DCollection(verts, facecolors='white', edgecolors='black', alpha=1.0))
    
    # 2.5 Traza de alta precisión (Proporcional al dron y al mismo nivel)
    if mostrar_trazas and len(trazas) > 1:
        pts = np.array(trazas)
        # Dibujar la traza justo a ras del dron (con un mínimo offset de 0.01 para evitar z-fighting)
        # Usamos un linewidth más grueso para que sea proporcional al ancho del dron (20cm)
        ax.plot3D(pts[:, 2], pts[:, 1], pts[:, 0] + 0.01, color='lime', alpha=0.7, linewidth=6, zorder=10)
        # Una línea central más brillante para definir el camino
        ax.plot3D(pts[:, 2], pts[:, 1], pts[:, 0] + 0.02, color='white', alpha=0.9, linewidth=1, zorder=11)

    lvl_actual = int(rz * ESC_FACTOR) + 1
    if 'texto_info' in globals():
        texto_info.set_text(f"NIVEL {lvl_actual} | Alt: {rz:.2f}m | Pos: ({rx:.2f}, {ry:.2f})")
    # Color de etiquetas de ejes en Dark Mode
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.zaxis.label.set_color('white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.tick_params(axis='z', colors='white')
    
    # Compass overlay (N/S/E/W) rotated -45° to align with 3D view base
    ax.text2D(0.039, 0.911, "N", transform=ax.transAxes, fontsize=10, weight='bold', color='red', ha='center', va='center')
    ax.text2D(0.081, 0.869, "S", transform=ax.transAxes, fontsize=8, color='white', ha='center', va='center')
    ax.text2D(0.039, 0.869, "W", transform=ax.transAxes, fontsize=8, color='white', ha='center', va='center')
    ax.text2D(0.081, 0.911, "E", transform=ax.transAxes, fontsize=8, color='white', ha='center', va='center')
    ax.text2D(0.060, 0.890, "X", transform=ax.transAxes, fontsize=6, color='gray', ha='center', va='center')
    
    fig.canvas.draw()
    actualizar_barra_altitud()

# --- BARRA DE ALTITUD ---
ax_alt = fig.add_axes([0.905, 0.15, 0.015, 0.65]) # Barra de altitud
bar_rect = None

def actualizar_barra_altitud():
    global bar_rect
    ax_alt.clear()
    ALTO_m = ALTO / ESC_FACTOR
    ax_alt.set_ylim(0, ALTO_m)
    # Marcas de niveles 1..N
    yticks = [(i + 0.5) / ESC_FACTOR for i in range(ALTO)]
    ax_alt.set_yticks(yticks)
    ax_alt.set_yticklabels([str(i+1) for i in range(ALTO)], fontsize=8)
    
    # Ticks precisos: Metros (Labels), Decímetros (Ticks mayores), 5cm (Ticks menores)
    ax_alt.yaxis.set_major_locator(MultipleLocator(1))
    ax_alt.yaxis.set_minor_locator(MultipleLocator(0.1))
    
    ax_alt.yaxis.tick_right()
    ax_alt.tick_params(colors='white', labelsize=7, which='both')
    
    # Dibujar fondo de la barra
    ax_alt.add_patch(plt.Rectangle((0, 0), 1, ALTO, color='#333333', alpha=0.3))
    
    # Dibujar indicador de altura actual (línea de precisión)
    ax_alt.axhline(y=rz, color='#00ffff', linewidth=2, alpha=0.9)
    ax_alt.axhline(y=rz, color='#00ffff', linewidth=4, alpha=0.3) # Resplandor
    
    ax_alt.set_title("ALT", fontsize=8, color='white')
    
    # Marcas de límites
    ax_alt.axhline(1, color='cyan', linestyle='--', linewidth=1, alpha=0.5)
    
# --- ACCIONES DEL ROBOT ---

def check_collision(z, y, x):
    """Verifica si el centro del dron colisiona con algún muro (coherente con A*)."""
    iz = int(z * ESC_FACTOR)
    iy = int(y * ESC_FACTOR)
    ix = int(x * ESC_FACTOR)
    # Fuera de límites = colisión
    if not (0 <= iz < ALTO and 0 <= iy < LARGO and 0 <= ix < ANCHO):
        return True
    # Colisión con muro
    if laberinto[iz, iy, ix] == 1:
        return True
    return False

def mover_robot(dz_req, dy_req, dx_req, pasos=1, animar=True):
    global rz, ry, rx, trazas
    # Normalizar movimiento según velocidad actual (si no es IA)
    step_z = dz_req * velocidad_movimiento
    step_y = dy_req * velocidad_movimiento
    step_x = dx_req * velocidad_movimiento
    
    for _ in range(pasos):
        nz, ny, nx = rz + step_z, ry + step_y, rx + step_x
        
        altura_segura_m = slider_alt.val / 100.0 if 'slider_alt' in globals() else 0.5
        
        # Auto-elevar si se intenta volar horizontalmente por debajo de la altura de seguridad
        if step_z == 0 and rz < (altura_segura_m - 0.001):
            subir_a = altura_segura_m
            while rz < subir_a - 0.001:
                nz = min(rz + velocidad_movimiento, subir_a)
                if check_collision(nz, ry, rx): break
                trazas.append((rz, ry, rx))
                rz = nz
                escanear_entorno()
                if animar:
                    dibujar_escena()
                    fig.canvas.flush_events()
            nz = rz
            print(f"↕ Auto-elevado a {rz:.2f}m para movimiento horizontal.")
             
        # Límite de suelo
        if nz < 0.0:
            nz = 0.0

        if check_collision(nz, ny, nx):
            print(f"🚫 Colisión en celda ({int(nz*ESC_FACTOR)}, {int(ny*ESC_FACTOR)}, {int(nx*ESC_FACTOR)}) - hay un muro")
            return False
        
        trazas.append((rz, ry, rx))
        rz, ry, rx = nz, ny, nx
        escanear_entorno()
        if animar:
            dibujar_escena()
            fig.canvas.flush_events() 
            
        if tello_active:
            if rz == 1 and nz == 0:
                print("🛬 Detectada intención de aterrizaje. Aterrizando Tello...")
                tello.aterrizar()
            else:
                dir_map = {
                    (1,0,0): "up", (-1,0,0): "down",
                    (0,1,0): "forward", (0,-1,0): "back",
                    (0,0,1): "right", (0,0,-1): "left"
                }
                cmd = dir_map.get((dz_req, dy_req, dx_req))
                if cmd: 
                    dist_cm = int(30 * (velocidad_movimiento / 0.2))
                    tello.mover(cmd, max(20, dist_cm))

    if not animar: dibujar_escena()
    return True

def mover_robot_a_celda(z, y, x, animar=True):
    """Mueve al robot exactamente al centro de la celda destino en metros."""
    global rz, ry, rx, trazas
    
    tz = (z + 0.1) / ESC_FACTOR
    ty = (y + 0.5) / ESC_FACTOR
    tx = (x + 0.5) / ESC_FACTOR
    
    if check_collision(tz, ty, tx): return False
    
    dist = np.sqrt((tz-rz)**2 + (ty-ry)**2 + (tx-rx)**2)
    if dist < 0.001: return True
    
    pasos = int(np.ceil(dist / velocidad_movimiento))
    sdz, sdy, sdx = (tz-rz)/pasos, (ty-ry)/pasos, (tx-rx)/pasos
    
    for i in range(pasos):
        if cancelar_operacion: return False
        
        if i == pasos - 1:
            nz, ny, nx = tz, ty, tx
        else:
            nz, ny, nx = rz + sdz, ry + sdy, rx + sdx
        
        if check_collision(nz, ny, nx):
            print(f"🚫 Colisión en celda ({int(nz*ESC_FACTOR)}, {int(ny*ESC_FACTOR)}, {int(nx*ESC_FACTOR)}) durante la ruta")
            return False
        
        trazas.append((rz, ry, rx))
        rz, ry, rx = nz, ny, nx
        escanear_entorno()
        if animar:
            dibujar_escena()
            fig.canvas.flush_events()
            plt.pause(0.01)
            
    return True

# --- YA NO USAMOS ESTA VERSIÓN AQUÍ ABAJO, LA MOVI ARRIBA ---

# --- INTERFAZ ---

def _get_celda_actual():
    return int(rz * ESC_FACTOR), int(ry * ESC_FACTOR), int(rx * ESC_FACTOR)

def procesar_comandos(texto):
    texto = texto.lower().replace(',', ';').replace('luego', ';').replace(' y ', '; ')
    for inst in texto.split(';'):
        partes = inst.strip().split()
        if len(partes) < 2: continue
        cmd = partes[0]
        try:
            num = int(partes[1].strip(',.;:'))
        except ValueError:
            continue
        if cmd in ['arriba', 'up']:
            cz, cy, cx = _get_celda_actual()
            for _ in range(num):
                if not mover_robot_a_celda(cz + 1, cy, cx): break
                cz, cy, cx = _get_celda_actual()
        elif cmd in ['abajo', 'down']:
            cz, cy, cx = _get_celda_actual()
            for _ in range(num):
                if not mover_robot_a_celda(max(0, cz - 1), cy, cx): break
                cz, cy, cx = _get_celda_actual()
        elif cmd in ['norte', 'w']:
            cz, cy, cx = _get_celda_actual()
            for _ in range(num):
                prev = (cz, cy, cx)
                _key_mover_a_celda(cz, cy + 1, cx)
                cz, cy, cx = _get_celda_actual()
                if (cz, cy, cx) == prev: break
        elif cmd in ['sur', 's']:
            cz, cy, cx = _get_celda_actual()
            for _ in range(num):
                prev = (cz, cy, cx)
                _key_mover_a_celda(cz, cy - 1, cx)
                cz, cy, cx = _get_celda_actual()
                if (cz, cy, cx) == prev: break
        elif cmd in ['este', 'd']:
            cz, cy, cx = _get_celda_actual()
            for _ in range(num):
                prev = (cz, cy, cx)
                _key_mover_a_celda(cz, cy, cx + 1)
                cz, cy, cx = _get_celda_actual()
                if (cz, cy, cx) == prev: break
        elif cmd in ['oeste', 'a']:
            cz, cy, cx = _get_celda_actual()
            for _ in range(num):
                prev = (cz, cy, cx)
                _key_mover_a_celda(cz, cy, cx - 1)
                cz, cy, cx = _get_celda_actual()
                if (cz, cy, cx) == prev: break
        else:
            print(f"⚠️ Comando no reconocido: '{cmd}'")
    textbox.set_val('')

def _key_mover_a_celda(_, y, x):
    altura_segura_m = slider_alt.val / 100.0 if 'slider_alt' in globals() else 0.5
    if rz < (altura_segura_m - 0.001):
        cz = int(rz * ESC_FACTOR)
        cy = int(ry * ESC_FACTOR)
        cx = int(rx * ESC_FACTOR)
        alt_v = max(1, int(altura_segura_m * ESC_FACTOR))
        if alt_v > cz:
            mover_robot_a_celda(alt_v, cy, cx)
    cz = int(rz * ESC_FACTOR)
    mover_robot_a_celda(cz, y, x)

def on_key(event):
    if event.inaxes == textbox.ax:
        return
    key = event.key.lower()
    if key in ('w', 's', 'd', 'a'):
        cz = int(rz * ESC_FACTOR)
        cy = int(ry * ESC_FACTOR)
        cx = int(rx * ESC_FACTOR)
        if key == 'w': _key_mover_a_celda(cz, cy + 1, cx)
        elif key == 's': _key_mover_a_celda(cz, cy - 1, cx)
        elif key == 'd': _key_mover_a_celda(cz, cy, cx + 1)
        elif key == 'a': _key_mover_a_celda(cz, cy, cx - 1)
    elif key == 'q':
        cz, cy, cx = _get_celda_actual()
        mover_robot_a_celda(cz + 1, cy, cx)
    elif key == 'e':
        cz, cy, cx = _get_celda_actual()
        mover_robot_a_celda(max(0, cz - 1), cy, cx)
    elif key == 'r': retornar_a_inicio()
    elif key == 'c': toggle_camara()

def toggle_trazas(event=None):
    global mostrar_trazas
    mostrar_trazas = not mostrar_trazas
    dibujar_escena()

def aplicar_tema():
    global sidebar_bg, sidebar_border
    
    fig.patch.set_facecolor(C_BG)
    sidebar_bg.set_facecolor(C_SIDEBAR)
    sidebar_border.set_facecolor(C_BORDER)
    if 'topbar_bg' in globals() and topbar_bg is not None:
        topbar_bg.set_facecolor(C_SIDEBAR)
    
    ax.set_facecolor(C_BG)
    
    if 'text_vel' in globals():
        text_vel.set_color(C_TEXT)
    for p in [ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane]:
        p.set_facecolor(C_CATEGORY)
        p.set_alpha(0.8)
    
    ax.grid(color=C_TEXT, alpha=0.1)
    ax.xaxis.label.set_color(C_TEXT)
    ax.yaxis.label.set_color(C_TEXT)
    ax.zaxis.label.set_color(C_TEXT)
    ax.tick_params(colors=C_TEXT)
    
    botones = [btn_reset, btn_tr, btn_mas, btn_menos, btn_ia,
               btn_auto, btn_ret, btn_map, btn_tello, btn_sim, btn_vista, btn_exp, btn_vel_p, btn_vel_m,
               btn_cam_toggle, btn_cam_mode, btn_cam_action, btn_menu_ia, btn_borrar_tr,
               btn_menu_niveles, btn_menu_camara, btn_meta, btn_ir_meta, btn_tour]
    for b in botones:
        if b == btn_vista and mostrar_todo_el_mapa:
            b.color = C_YELLOW
            b.ax.set_facecolor(C_YELLOW)
        elif b == btn_exp and modo_exploracion:
            b.color = C_ACCENT
            b.ax.set_facecolor(C_ACCENT)
        elif b == btn_tello and tello_active:
            b.color = 'orange'
            b.ax.set_facecolor('orange')
        elif b == btn_sim:
            if modo_simulacion:
                b.color = C_ACCENT
                b.ax.set_facecolor(C_ACCENT)
                b.label.set_text("SIM")
            else:
                b.color = C_RED
                b.ax.set_facecolor(C_RED)
                b.label.set_text("REAL")
        elif b == btn_cam_action and tello.recording:
            b.color = C_RED
            b.ax.set_facecolor(C_RED)
        elif b == btn_cam_toggle and tello.stream_on:
            b.color = C_ACCENT
            b.ax.set_facecolor(C_ACCENT)
        else:
            b.color = C_BTN_BG
            b.ax.set_facecolor(C_BTN_BG)
        
        b.hovercolor = C_BTN_HOVER
        b.label.set_color(C_TEXT)
    if 'slider_alt' in globals():
        slider_alt.label.set_color(C_TEXT)
        slider_alt.valtext.set_color(C_TEXT)
        slider_alt.poly.set_facecolor(C_BTN_HOVER)
        slider_alt.ax.set_facecolor(C_BTN_BG)

    # CMD: fondo gris claro con texto oscuro
    textbox.ax.set_facecolor('#d4d4d4')
    for p in textbox.ax.patches:
        p.set_facecolor('#d4d4d4')
    for t in textbox.ax.texts:
        t.set_color('#1a1a1a')
    if hasattr(textbox, '_textcolor'):
        textbox._textcolor = '#1a1a1a'
    
    actualizar_botones_niveles()



def ajustar_opacidad(cantidad):
    global opacidad_muros
    opacidad_muros = max(0, min(255, opacidad_muros + cantidad))
    dibujar_escena()

def toggle_exploracion(event=None):
    global modo_exploracion
    modo_exploracion = not modo_exploracion
    c = 'cyan' if modo_exploracion else ('#2a2a2a')
    btn_exp.color = c
    btn_exp.ax.set_facecolor(c)
    dibujar_escena()

def toggle_menu_niveles(event=None):
    global modo_niveles_expandido
    modo_niveles_expandido = not modo_niveles_expandido
    btn_menu_niveles.label.set_text("NIVELES Z ▲" if modo_niveles_expandido else "NIVELES Z ▼")
    actualizar_botones_niveles()
    fig.canvas.draw_idle()

def toggle_menu_camara(event=None):
    global modo_camara_expandido
    modo_camara_expandido = not modo_camara_expandido
    btn_menu_camara.label.set_text("CÁMARA ▲" if modo_camara_expandido else "CÁMARA ▼")
    actualizar_visibilidad_camara()

def actualizar_visibilidad_camara():
    if not 'axes_camara' in globals(): return
    for ax_c in axes_camara:
        ax_c.set_visible(modo_camara_expandido)
    fig.canvas.draw()

def actualizar_botones_niveles():
    global btn_niveles, ax_niveles
    if 'ax_niveles' in globals():
        for axes in ax_niveles: axes.remove()
    btn_niveles, ax_niveles = [], []
    
    # En la sidebar, debajo del encabezado NIVELES Z (y=0.390)
    start_y = 0.350
    for i in range(ALTO):
        pos_y = start_y - (i * 0.04)
        ax_z = fig.add_axes([SX + 0.025, pos_y, SW - 0.05, 0.035]) 
        ax_z.set_visible(modo_niveles_expandido)
        
        if niveles_visibles[i]:
            c = C_GREEN
        else:
            c = '#4d1b1b'
        
        b = Button(ax_z, f"Z{i}", color=c)
        b.label.set_fontsize(7)
        b.hovercolor = C_BTN_HOVER
        b.ax.set_facecolor(c)
        b.label.set_color(C_TEXT)
        b.on_clicked(lambda e, z=i: toggle_nivel(z))
        btn_niveles.append(b)
        ax_niveles.append(ax_z)

def reiniciar_juego(event=None):
    global reset_vista, cancelar_operacion, tello_active, trazas
    cancelar_operacion = True
    
    # Desconectar el dron si está conectado
    if tello_active:
        try:
            tello.aterrizar()
        except:
            pass
        tello.desconectar()
        tello_active = False
        c = '#2a2a2a'
        btn_tello.color = c
        btn_tello.ax.set_facecolor(c)
    
    # Limpiar trazas
    trazas = []
    
    # Recargar laberinto y reiniciar posición
    if recargar_laberinto():
        reset_vista = True
        actualizar_botones_niveles()
        actualizar_barra_altitud()
        actualizar_estado_camara()
        dibujar_escena()
    
    # Resetear posición de origen
    posicion_origen = None
    
    # Resetear modo tour
    global modo_tour
    modo_tour = False
    if 'btn_tour' in globals():
        btn_tour.color = '#2a2a2a'
        btn_tour.ax.set_facecolor('#2a2a2a')
    
    cancelar_operacion = False

def borrar_trazas(event=None):
    """Borra las trazas del mapa."""
    global trazas
    trazas = []
    print("🗑️ Trazas borradas.")
    dibujar_escena()

def toggle_nivel(z):
    niveles_visibles[z] = not niveles_visibles[z]
    if niveles_visibles[z]:
        c = '#1b4d1b'
    else:
        c = '#4d1b1b'
    btn_niveles[z].color = c
    btn_niveles[z].ax.set_facecolor(c)
    dibujar_escena()

def toggle_vista_completa(event):
    global mostrar_todo_el_mapa
    mostrar_todo_el_mapa = not mostrar_todo_el_mapa
    c = 'yellow' if mostrar_todo_el_mapa else ('#2a2a2a')
    btn_vista.color = c
    btn_vista.ax.set_facecolor(c)
    print(f"👁️ Vista de mapa completo: {'ACTIVADA' if mostrar_todo_el_mapa else 'EXPLORACIÓN'}")
    dibujar_escena()

def toggle_modo_tour(event):
    global modo_tour
    modo_tour = not modo_tour
    c = 'cyan' if modo_tour else ('#2a2a2a')
    btn_tour.color = c
    btn_tour.ax.set_facecolor(c)
    print(f"🔄 Modo TOUR: {'ACTIVADO' if modo_tour else 'DESACTIVADO'}")
    dibujar_escena()

def seleccionar_meta(event):
    global objetivo, meta_indice_actual
    if len(objetivos) == 0:
        print("❌ No hay metas definidas.")
        return
    meta_indice_actual = (meta_indice_actual + 1) % len(objetivos)
    objetivo = objetivos[meta_indice_actual]
    print(f"🎯 Meta seleccionada: {meta_indice_actual+1}/{len(objetivos)} -> {objetivo}")
    dibujar_escena()

def toggle_cam_mode(event=None):
    global btn_cam_mode, btn_cam_action
    is_video = tello.toggle_mode()
    btn_cam_mode.label.set_text("MODO: VIDEO" if is_video else "MODO: FOTO")
    # No cambiar el texto de btn_cam_action, dejarlo como GRAVAR
    dibujar_escena()

def ejecutar_accion_cam(event=None):
    global btn_cam_action
    if tello.is_video_mode:
        is_recording = tello.toggle_recording()
        # El texto se mantiene como GRAVAR
        btn_cam_action.color = 'red' if is_recording else ('#2a2a2a')
        btn_cam_action.ax.set_facecolor(btn_cam_action.color)
    else:
        tello.take_photo()
    fig.canvas.draw_idle()

def toggle_camara(event=None):
    if not tello_active:
        print("⚠️ Conecta el dron (TELLO) primero.")
        return
    if tello.stream_on:
        tello.detener_video()
    else:
        tello.iniciar_video()
    # Auto-expandir cuando encendemos
    if tello.stream_on and not modo_camara_expandido:
        toggle_menu_camara()
    actualizar_estado_camara()

def actualizar_estado_camara():
    if not 'btn_cam_toggle' in globals(): return
    if tello.stream_on:
        btn_cam_toggle.label.set_text("CÁMARA: ON")
        btn_cam_toggle.color = 'cyan'
        btn_cam_toggle.ax.set_facecolor('cyan')
    else:
        btn_cam_toggle.label.set_text("CÁMARA: OFF")
        c = '#2a2a2a'
        btn_cam_toggle.color = c
        btn_cam_toggle.ax.set_facecolor(c)
    fig.canvas.draw_idle()

def toggle_menu_ia(event=None):
    global modo_ia_expandido
    modo_ia_expandido = not modo_ia_expandido
    btn_menu_ia.label.set_text("MENÚ IA ▲" if modo_ia_expandido else "MENÚ IA ▼")
    actualizar_estado_sidebar()
    fig.canvas.draw_idle()

def actualizar_estado_sidebar():
    if not 'axes_sidebar' in globals(): return
    for ax_sb in axes_sidebar:
        ax_sb.set_visible(modo_ia_expandido)
    fig.canvas.draw()

def ejecutar_ia(event):
    global tello_active, posicion_origen, objetivo, meta_indice_actual, modo_tour
    
    print(f"🚀 EJECUTAR IA - Posición actual: ({rz:.2f}, {ry:.2f}, {rx:.2f}), tello_active={tello_active}")
    
    # Guardar posición de origen cuando el dron sale por primera vez
    if posicion_origen is None:
        posicion_origen = (rz, ry, rx)
        print(f"📍 Posición de origen guardada: ({rz:.2f}, {ry:.2f}, {rx:.2f})")
    
    # Activar visualmente el botón Tello como "en vuelo" y encender la cámara
    if not tello_active:
        print("🔌 Intentando conectar con Tello...")
        if tello.conectar():
            tello_active = True
            btn_tello.color = 'orange'
            btn_tello.ax.set_facecolor('orange')
            tello.despegar()
            tello.iniciar_video()
            actualizar_estado_camara()
            print("✅ Tello conectado y despegado")
        else:
            print("⚠️ No hay dron real, operando en MODO SIMULACIÓN")
            tello_active = False
    
    # Calcular altura segura
    altura_segura_m = slider_alt.val / 100.0 if 'slider_alt' in globals() else 0.5
    altura_segura_v = min(ALTO-1, max(1, int(altura_segura_m * ESC_FACTOR)))

    # Determinar qué metas visitar
    metas_a_visitar = []
    if modo_tour:
        # Modo tour: visitar todas las metas en orden
        metas_a_visitar = objetivos
        meta_indice_actual = 0
    else:
        # Modo normal: solo la meta actual
        metas_a_visitar = [objetivo]
    
    # 1. Primero subir a la altura segura SIN buscar ruta todavía
    cur_z_v = int(rz * ESC_FACTOR)
    print(f"📏 Altura actual: {rz:.2f}m (celda {cur_z_v}), altura segura: {altura_segura_v}")
    if cur_z_v < altura_segura_v:
        print(f"🛫 Elevando a nivel seguro: {altura_segura_v} (z={altura_segura_m}m)")
        if tello_active:
            # Subir o bajar la diferencia con respecto al hover natural del takeoff (aprox 80cm)
            extra_cm = int((altura_segura_m * 100) - TELLO_HOVER_CM)
            if extra_cm > 20:
                tello.mover("up", extra_cm)
            elif extra_cm < -20:
                tello.mover("down", abs(extra_cm))
        else:
            print("⚠️ Modo simulación (sin dron)")
        iy0 = max(0, min(LARGO-1, int(ry * ESC_FACTOR)))
        ix0 = max(0, min(ANCHO-1, int(rx * ESC_FACTOR)))
        print(f"📍 Elevando desde celda ({cur_z_v}, {iy0}, {ix0}) -> ({altura_segura_v}, {iy0}, {ix0})")
        if not mover_robot_a_celda(altura_segura_v, iy0, ix0):
            print("❌ Error al elevar el dron.")
            return
    else:
        print(f"✈️ Dron ya en altura segura (z={cur_z_v}), iniciando navegación...")

    # Procesar cada meta
    for idx, meta_actual in enumerate(metas_a_visitar):
        if cancelar_operacion: break
        
        if modo_tour:
            objetivo = meta_actual
            print(f"🎯 Visitando meta {idx+1}/{len(metas_a_visitar)}: {meta_actual}")
        
        # El objetivo de vuelo es la celda justo SOBRE el destino, a la altura segura
        destino_vuelo = (max(altura_segura_v, meta_actual[0]), meta_actual[1], meta_actual[2])
        start_pos = (int(rz * ESC_FACTOR), int(ry * ESC_FACTOR), int(rx * ESC_FACTOR))
        print(f"🤖 IA buscando ruta de {start_pos} a {destino_vuelo}...")
        
        def h(p): return abs(p[0]-destino_vuelo[0]) + abs(p[1]-destino_vuelo[1]) + abs(p[2]-destino_vuelo[2])
        cola = [(h(start_pos), 0, start_pos, [])]
        visitados = set()
        camino_encontrado = None
        
        while cola:
            f, g, actual, camino = heapq.heappop(cola)
            if actual in visitados: continue
            visitados.add(actual)
            if actual == destino_vuelo:
                camino_encontrado = camino
                break
            for dz, dy, dx in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
                nz, ny, nx = actual[0]+dz, actual[1]+dy, actual[2]+dx
                if (altura_segura_v <= nz < ALTO and 0 <= ny < LARGO and 0 <= nx < ANCHO and laberinto[nz, ny, nx] != 1):
                    heapq.heappush(cola, (g + 1 + h((nz, ny, nx)), g + 1, (nz, ny, nx), camino + [(dz, dy, dx)]))
        
        if camino_encontrado:
            print(f"✅ Ruta encontrada! Pasos: {len(camino_encontrado)}")
            for dz, dy, dx in camino_encontrado:
                if cancelar_operacion: break
                if tello_active:
                    dir_map = {(1,0,0): "up", (-1,0,0): "down", (0,1,0): "forward", (0,-1,0): "back", (0,0,1): "right", (0,0,-1): "left"}
                    cmd = dir_map.get((dz, dy, dx))
                    if cmd: tello.mover(cmd, max(20, int(100.0 / ESC_FACTOR)))

                nz, ny, nx = start_pos[0]+dz, start_pos[1]+dy, start_pos[2]+dx
                if not mover_robot_a_celda(nz, ny, nx):
                    print(f"🛑 Movimiento interrumpido en ({nz}, {ny}, {nx})")
                    break
                start_pos = (nz, ny, nx)
            
            if modo_tour and idx < len(metas_a_visitar) - 1:
                print(f"✅ Meta {idx+1} alcanzada. Yendo a la siguiente...")
        else:
            print(f"❌ No se encontró ruta a meta {idx+1}")
    
    if modo_tour:
        print("🏁 Tour completado!")
    
    # Descender a la celda meta (aterriza SOBRE el muro si hay, no lo atraviesa)
    meta_aterrizaje = (meta_actual[0], meta_actual[1], meta_actual[2])
    print(f"🛬 Descendiendo a celda meta {meta_aterrizaje}...")
    if not mover_robot_a_celda(*meta_aterrizaje):
        print(f"⚠️ No se pudo descender a la meta, quedando en ({int(rz*ESC_FACTOR)}, {int(ry*ESC_FACTOR)}, {int(rx*ESC_FACTOR)})")
    tello.aterrizar()
    tello.stream_on = False
    tello_active = False
    c = '#2a2a2a'
    btn_tello.color = c
    btn_tello.ax.set_facecolor(c)
    dibujar_escena()

def ejecutar_auto_scan(event=None):
    """Algoritmo de 'Frontier Exploration' para mapear el entorno solo."""
    print("🤖 Iniciando Auto-Escaneo...")
    global rz, ry, rx, cancelar_operacion
    cancelar_operacion = False
    
    while not cancelar_operacion:
        # 1. Encontrar fronteras: puntos conocidos que lindan con desconocidos
        fronteras = []
        for z in range(1, ALTO): # REGLA DE SEGURIDAD: No buscar fronteras en el suelo
            if not niveles_visibles[z]: continue
            for y in range(LARGO):
                for x in range(ANCHO):
                    # Solo visitamos si es transitable (0) y ya descubierto
                    if laberinto[z, y, x] == 0 and mapa_descubierto[z, y, x]:
                        # Mirar vecinos para ver si hay algo sin descubrir
                        algun_desconocido = False
                        for dz, dy, dx in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
                            nz, ny, nx = z+dz, y+dy, x+dx
                            if (0 <= nz < ALTO and 0 <= ny < LARGO and 0 <= nx < ANCHO and 
                                not mapa_descubierto[nz, ny, nx]):
                                algun_desconocido = True
                                break
                        if algun_desconocido:
                            fronteras.append((z, y, x))
        
        if not fronteras: 
            print("🏁 No hay más fronteras. Escaneo completado.")
            break
            
        # 2. Ir a la frontera más cercana
        curr_pos = (int(rz * ESC_FACTOR), int(ry * ESC_FACTOR), int(rx * ESC_FACTOR))
        print(f"🗺️ {len(fronteras)} fronteras detectadas. Buscando ruta desde {curr_pos}...")
        def dist(p): return abs(p[0]-curr_pos[0]) + abs(p[1]-curr_pos[1]) + abs(p[2]-curr_pos[2])
        frontera_destino = min(fronteras, key=dist)
        
        # 3. Planificar ruta a la frontera (A* usando SOLO lo que conocemos)
        cola = [(0, curr_pos, [])]
        visitados = set()
        encontrado = False
        while cola:
            g, actual, camino = heapq.heappop(cola)
            if actual in visitados: continue
            visitados.add(actual)
            if actual == frontera_destino:
                # Mover 1 celda = (1/ESC_FACTOR) metros
                dist_m = 1.0 / ESC_FACTOR
                pasos = int(dist_m / velocidad_movimiento)
                
                # Asegurar altura antes de mover horizontalmente
                altura_segura_m = slider_alt.val / 100.0 if 'slider_alt' in globals() else 0.5
                if rz < altura_segura_m: 
                    subir_m = altura_segura_m - rz
                    pasos_up = int(subir_m / velocidad_movimiento)
                    mover_robot(1, 0, 0, max(1, pasos_up))
                
                for dz, dy, dx in camino: 
                    if cancelar_operacion: break
                    if not mover_robot(dz, dy, dx, max(1, pasos)): break
                encontrado = True
                break
            for dz, dy, dx in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
                nz, ny, nx = actual[0]+dz, actual[1]+dy, actual[2]+dx
                if (0 <= nz < ALTO and 0 <= ny < LARGO and 0 <= nx < ANCHO and 
                    laberinto[nz, ny, nx] == 0 and mapa_descubierto[nz, ny, nx]):
                    heapq.heappush(cola, (g + 1, (nz, ny, nx), camino + [(dz, dy, dx)]))
        
        if not encontrado: break # No hay ruta a ninguna frontera
        plt.pause(0.05) # Pausa para ver el progreso
    
    # Al finalizar, guardar automáticamente
    guardar_mapa_escaneado()

def guardar_mapa_escaneado():
    """Guarda el progreso del mapa en una nueva carpeta."""
    if not os.path.exists("mapas_escaneados"):
        os.makedirs("mapas_escaneados")
    
    # Crear una versión del laberinto donde solo lo descubierto es visible
    # Lo no descubierto se guarda como muro (1) para seguridad
    mapa_final = np.ones(laberinto.shape, dtype=int)
    mapa_final[mapa_descubierto] = laberinto[mapa_descubierto]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"mapas_escaneados/escaneo_{timestamp}.npy"
    np.save(nombre_archivo, mapa_final)
    print(f"💾 Mapa guardado en: {nombre_archivo}")

def toggle_sim_mode(event=None):
    global modo_simulacion
    if tello_active:
        print("⚠️ Desconecta el Tello primero para cambiar de modo.")
        return
        
    modo_simulacion = not modo_simulacion
    tello.force_simulation = modo_simulacion
    
    if modo_simulacion:
        btn_sim.color = C_ACCENT
        btn_sim.ax.set_facecolor(C_ACCENT)
        btn_sim.label.set_text("SIM")
        print("🔄 Modo cambiado a: SIMULACIÓN")
    else:
        btn_sim.color = C_RED
        btn_sim.ax.set_facecolor(C_RED)
        btn_sim.label.set_text("REAL")
        print("🔄 Modo cambiado a: DRON REAL")
    
    fig.canvas.draw_idle()

def toggle_tello(event=None):
    global tello_active, posicion_origen
    if not tello_active:
        # Guardar posición de origen cuando el dron sale por primera vez
        if posicion_origen is None:
            posicion_origen = (rz, ry, rx)
            print(f"📍 Posición de origen guardada: ({rz:.2f}, {ry:.2f}, {rx:.2f})")
        
        if tello.conectar():
            tello_active = True
            btn_tello.color = 'orange'
            btn_tello.ax.set_facecolor('orange')
            tello.despegar()
            # El Tello sube ~TELLO_HOVER_CM por hardware tras el takeoff.
            # Solo enviamos move_up adicional si la altura segura supera ese valor.
            altura_segura_m = slider_alt.val / 100.0 if 'slider_alt' in globals() else 0.2
            altura_segura_v = max(1, int(altura_segura_m * ESC_FACTOR))
            iy0 = max(0, min(LARGO-1, int(ry * ESC_FACTOR)))
            ix0 = max(0, min(ANCHO-1, int(rx * ESC_FACTOR)))
            if int(rz * ESC_FACTOR) < altura_segura_v:
                extra_cm = int((altura_segura_m * 100) - TELLO_HOVER_CM)
                if extra_cm > 20:  # Subir si es más alto que 80cm
                    tello.mover("up", extra_cm)
                elif extra_cm < -20: # Bajar si es más bajo que 80cm
                    tello.mover("down", abs(extra_cm))
                mover_robot_a_celda(altura_segura_v, iy0, ix0, animar=True)  # Actualizar posición visual
            tello.iniciar_video()
            actualizar_estado_camara()
    else:
        print("🔌 Apagando Tello...")
        if rz > 0:
            retornar_a_inicio()
        tello.desconectar()
        tello_active = False
        c = '#2a2a2a'
        btn_tello.color = c
        btn_tello.ax.set_facecolor(c)
        dibujar_escena()

def retornar_a_inicio(event=None):
    """Retorna al inicio siguiendo las trazas o usando A* con posicion_origen."""
    global cancelar_operacion, tello_active, rz, ry, rx, posicion_origen
    cancelar_operacion = False
    
    # Si el dron está apagado, reconectar para el viaje de vuelta
    if not tello_active:
        if tello.conectar():
            tello_active = True
            btn_tello.color = 'orange'
            btn_tello.ax.set_facecolor('orange')
            tello.despegar()
            tello.iniciar_video()
        else:
            print("❌ No se pudo reconectar el dron para retornar.")
            return
    
    print("🏠 Retornando al origen...")
    
    # Obtener altura segura
    altura_segura_m = slider_alt.val / 100.0 if 'slider_alt' in globals() else 0.5
    altura_segura_v = max(1, int(altura_segura_m * ESC_FACTOR))
    
    # Usar A* para encontrar el camino más corto de retorno
    if posicion_origen is not None:
        print(f"📍 Calculando ruta más corta al inicio...")
        retornar_por_astar(altura_segura_v)
    else:
        print("⚠️ No hay posición de origen registrada. Buscando ruta alternativa...")
        retornar_por_astar(altura_segura_v)
    
    # Desconectar visualmente el dron
    if tello_active:
        print("🔌 Desconectando Tello tras retorno.")
        tello_active = False
        c = '#2a2a2a'
        btn_tello.color = c
        btn_tello.ax.set_facecolor(c)
        tello.stream_on = False
        dibujar_escena()

def retornar_por_astar(altura_segura_v):
    """Retorna al inicio usando A* para encontrar la ruta más corta."""
    global cancelar_operacion, rz, ry, rx, tello_active, posicion_origen
    
    print("🗺️ Buscando ruta más corta al inicio con A*...")
    
    if posicion_origen is None:
        print("❌ No hay posición de origen registrada.")
        return
    
    # Posición actual en celdas
    start_pos = (int(rz * ESC_FACTOR), int(ry * ESC_FACTOR), int(rx * ESC_FACTOR))
    
    # Subir a altura segura si es necesario
    cur_z_v = int(rz * ESC_FACTOR)
    if cur_z_v < altura_segura_v:
        print(f"🛫 Elevando a altura segura: {altura_segura_v}")
        iy0 = max(0, min(LARGO-1, int(ry * ESC_FACTOR)))
        ix0 = max(0, min(ANCHO-1, int(rx * ESC_FACTOR)))
        if not mover_robot_a_celda(altura_segura_v, iy0, ix0):
            print("❌ Error al elevar.")
            return
        start_pos = (altura_segura_v, iy0, ix0)
    
    # Destino: posición de origen (en altura segura)
    destino = (altura_segura_v, int(inicio[1]), int(inicio[2]))
    
    # Asegurar que el destino esté libre
    if laberinto[destino] == 1:
        print("⚠️ Celda de origen bloqueada, buscando alternativa...")
        destino = (altura_segura_v, 0, 0)
    
    print(f"🤖 IA retornando de {start_pos} a {destino}...")
    
    # A*
    def h(p): return abs(p[0]-destino[0]) + abs(p[1]-destino[1]) + abs(p[2]-destino[2])
    cola = [(h(start_pos), 0, start_pos, [])]
    visitados = set()
    camino_encontrado = None
    
    while cola:
        f, g, actual, camino = heapq.heappop(cola)
        if actual in visitados: continue
        visitados.add(actual)
        if actual == destino:
            camino_encontrado = camino
            break
        for dz, dy, dx in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
            nz, ny, nx = actual[0]+dz, actual[1]+dy, actual[2]+dx
            if (altura_segura_v <= nz < ALTO and 0 <= ny < LARGO and 0 <= nx < ANCHO and laberinto[nz, ny, nx] != 1):
                heapq.heappush(cola, (g + 1 + h((nz, ny, nx)), g + 1, (nz, ny, nx), camino + [(dz, dy, dx)]))
    
    if camino_encontrado is not None:
        print(f"✅ Ruta encontrada! Retornando por {len(camino_encontrado)} pasos...")
        for dz, dy, dx in camino_encontrado:
            if cancelar_operacion: break
            if tello_active:
                dir_map = {(1,0,0): "up", (-1,0,0): "down", (0,1,0): "forward", (0,-1,0): "back", (0,0,1): "right", (0,0,-1): "left"}
                cmd = dir_map.get((dz, dy, dx))
                if cmd: tello.mover(cmd, max(20, int(100.0 / ESC_FACTOR)))
            
            nz, ny, nx = start_pos[0]+dz, start_pos[1]+dy, start_pos[2]+dx
            if not mover_robot_a_celda(nz, ny, nx):
                print(f"🛑 Movimiento interrumpido en ({nz}, {ny}, {nx})")
                break
            start_pos = (nz, ny, nx)
        
        print("🛬 Aterrizando en el origen...")
        if tello_active:
            tello.aterrizar()
        mover_robot_a_celda(int(inicio[0]), int(inicio[1]), int(inicio[2]))
        print("🏁 Retorno completado.")
    else:
        print("❌ No se encontró ruta al origen.")

def abrir_otro_mapa(event):
    global archivo_actual
    # Abrir explorador para elegir archivo
    ruta = filedialog.askopenfilename(
        initialdir=".",
        title="Seleccionar Mapa",
        filetypes=(("Archivos Numpy", "*.npy"), ("Todos los archivos", "*.*"))
    )
    
    if not ruta:
        print("📂 Carga cancelada.")
        return
        
    archivo_actual = ruta
    print(f"📂 Cargando: {archivo_actual}")
    reiniciar_juego()

def ajustar_velocidad(delta):
    global velocidad_movimiento
    velocidad_movimiento = max(0.05, min(1.0, velocidad_movimiento + delta))
    print(f"⚡ Velocidad ajustada: {velocidad_movimiento:.2f} m/step")
    if 'text_vel' in globals():
        text_vel.set_text(f"{velocidad_movimiento:.2f} m/s")
    dibujar_escena()

# Conectar eventos de teclado
fig.canvas.mpl_connect('key_press_event', on_key)

# ─── SIDEBAR: HELPER FUNCTIONS ───
def make_btn(ax_pos, text, color=C_BTN_BG, hover=C_BTN_HOVER, tcolor=C_TEXT, fsize=7.5):
    b = Button(ax_pos, text, color=color, hovercolor=hover)
    b.label.set_color(tcolor)
    b.label.set_fontsize(fsize)
    b.label.set_fontweight('bold')
    return b

def section_box(y_top, h):
    fig.patches.append(patches.Rectangle(
        (SX + 0.01, y_top), SW - 0.02, h,
        fill=True, facecolor=C_CATEGORY, edgecolor=C_BORDER, linewidth=0.6,
        transform=fig.transFigure, zorder=-8
    ))

def section_title(y, text):
    fig.text(
        SX + 0.025, y, text,
        fontsize=7, fontweight='bold', color=C_TEXT_MUTED,
        transform=fig.transFigure
    )

# ─── SIDEBAR: TITLE ───
fig.text(SX + 0.025, 0.971, 'SIMULADOR 3D', fontsize=14, fontweight='bold',
         color=C_TEXT, transform=fig.transFigure)
fig.text(SX + 0.025, 0.956, 'LABERINTO', fontsize=9, fontweight='normal',
         color=C_TEXT_MUTED, transform=fig.transFigure)

fig.patches.append(patches.Rectangle(
    (SX + 0.02, 0.945), SW - 0.04, 0.004,
    fill=True, facecolor=C_BORDER, edgecolor='none',
    transform=fig.transFigure, zorder=-8
))

# ─── SIDEBAR: MENÚ IA ───
section_box(0.44, 0.50)
section_title(0.925, 'INTELIGENCIA')

y_ia = 0.885
ax_menu_ia = plt.axes([SX + 0.025, y_ia, SW - 0.05, 0.035])
btn_menu_ia = Button(ax_menu_ia, "MENÚ IA ▼")
btn_menu_ia.label.set_fontsize(7)
btn_menu_ia.on_clicked(toggle_menu_ia)

y_ia -= 0.04
ax_ia = plt.axes([SX + 0.025, y_ia, SW - 0.05, 0.035])
btn_ia = Button(ax_ia, "IA (A*)")
btn_ia.label.set_fontsize(7)
btn_ia.on_clicked(ejecutar_ia)

y_ia -= 0.04
ax_tour = plt.axes([SX + 0.025, y_ia, SW - 0.05, 0.035])
btn_tour = Button(ax_tour, "TOUR")
btn_tour.label.set_fontsize(7)
btn_tour.on_clicked(toggle_modo_tour)

y_ia -= 0.04
ax_meta = plt.axes([SX + 0.025, y_ia, SW - 0.05, 0.035])
btn_meta = Button(ax_meta, "META")
btn_meta.label.set_fontsize(7)
btn_meta.on_clicked(seleccionar_meta)

y_ia -= 0.04
ax_ir_meta = plt.axes([SX + 0.025, y_ia, SW - 0.05, 0.035])
btn_ir_meta = Button(ax_ir_meta, "IR META", color=C_GREEN)
btn_ir_meta.label.set_fontsize(7)
btn_ir_meta.on_clicked(ejecutar_ia)

y_ia -= 0.04
ax_exp = plt.axes([SX + 0.025, y_ia, SW - 0.05, 0.035])
btn_exp = Button(ax_exp, "EXPLORAR", color=C_BTN_BG)
btn_exp.label.set_fontsize(7)
btn_exp.on_clicked(toggle_exploracion)

y_ia -= 0.04
ax_auto = plt.axes([SX + 0.025, y_ia, SW - 0.05, 0.035])
btn_auto = Button(ax_auto, "AUTO-MAP")
btn_auto.label.set_fontsize(7)
btn_auto.on_clicked(ejecutar_auto_scan)

y_ia -= 0.04
ax_ret = plt.axes([SX + 0.025, y_ia, SW - 0.05, 0.035])
btn_ret = Button(ax_ret, "RETORNAR", color=C_RED)
btn_ret.label.set_fontsize(7)
btn_ret.on_clicked(retornar_a_inicio)

y_ia -= 0.04
ax_vista = plt.axes([SX + 0.025, y_ia, SW - 0.05, 0.035])
btn_vista = Button(ax_vista, 'MOSTRAR TODO')
btn_vista.label.set_fontsize(7)
btn_vista.on_clicked(toggle_vista_completa)

y_ia -= 0.04
ax_trazas = plt.axes([SX + 0.025, y_ia, SW - 0.05, 0.035])
btn_tr = Button(ax_trazas, "TRAZAS")
btn_tr.label.set_fontsize(7)
btn_tr.on_clicked(toggle_trazas)

y_ia -= 0.04
ax_borrar_tr = plt.axes([SX + 0.025, y_ia, SW - 0.05, 0.035])
btn_borrar_tr = Button(ax_borrar_tr, "BORRAR TRAZAS")
btn_borrar_tr.label.set_fontsize(7)
btn_borrar_tr.on_clicked(borrar_trazas)

y_ia -= 0.04
ax_mas = plt.axes([SX + 0.025 + (SW - 0.05)/2, y_ia, (SW - 0.05)/2, 0.035])
btn_mas = Button(ax_mas, "OPA+")
btn_mas.label.set_fontsize(6)
btn_mas.on_clicked(lambda e: ajustar_opacidad(20))

ax_menos = plt.axes([SX + 0.025, y_ia, (SW - 0.05)/2, 0.035])
btn_menos = Button(ax_menos, "OPA-")
btn_menos.label.set_fontsize(6)
btn_menos.on_clicked(lambda e: ajustar_opacidad(-20))

axes_sidebar = [ax_ia, ax_tour, ax_meta, ax_ir_meta, ax_exp, ax_auto, ax_ret, ax_vista, ax_trazas, ax_borrar_tr, ax_mas, ax_menos]

# ─── SIDEBAR: NIVELES Z ───
section_box(0.21, 0.23)
section_title(0.425, 'NIVELES Z')

ax_menu_niveles = plt.axes([SX + 0.025, 0.390, SW - 0.05, 0.035])
btn_menu_niveles = Button(ax_menu_niveles, "NIVELES Z ▼")
btn_menu_niveles.label.set_fontsize(7)
btn_menu_niveles.on_clicked(toggle_menu_niveles)

# ─── SIDEBAR: CÁMARA ───
section_box(0.03, 0.18)
section_title(0.195, 'CÁMARA')

y_cam = 0.155
ax_menu_camara = plt.axes([SX + 0.025, y_cam, SW - 0.05, 0.035])
btn_menu_camara = Button(ax_menu_camara, "CÁMARA ▼")
btn_menu_camara.label.set_fontsize(7)
btn_menu_camara.on_clicked(toggle_menu_camara)

y_cam -= 0.04
ax_cam_toggle = plt.axes([SX + 0.025, y_cam, SW - 0.05, 0.035])
btn_cam_toggle = Button(ax_cam_toggle, "CAM: OFF")
btn_cam_toggle.label.set_fontsize(7)
btn_cam_toggle.on_clicked(toggle_camara)

y_cam -= 0.04
ax_cam_mode = plt.axes([SX + 0.025, y_cam, SW - 0.05, 0.035])
btn_cam_mode = Button(ax_cam_mode, "MODO: VID")
btn_cam_mode.label.set_fontsize(7)
btn_cam_mode.on_clicked(toggle_cam_mode)

y_cam -= 0.04
ax_cam_action = plt.axes([SX + 0.025, y_cam, SW - 0.05, 0.035])
btn_cam_action = Button(ax_cam_action, "GRAVAR")
btn_cam_action.label.set_fontsize(7)
btn_cam_action.on_clicked(ejecutar_accion_cam)

axes_camara = [ax_cam_toggle, ax_cam_mode, ax_cam_action]

# ─── TOP BAR BACKGROUND ───
MAIN_X0 = SX + SW
TOP_Y = 0.91
TOP_H = 0.08
topbar_bg = patches.Rectangle(
    (MAIN_X0, TOP_Y), 1.0 - MAIN_X0, TOP_H,
    fill=True, facecolor=C_SIDEBAR, edgecolor='none',
    transform=fig.transFigure, zorder=-10
)
fig.patches.append(topbar_bg)

fig.patches.append(patches.Rectangle(
    (MAIN_X0, TOP_Y), 1.0 - MAIN_X0, 0.003,
    fill=True, facecolor=C_BORDER, edgecolor='none',
    transform=fig.transFigure, zorder=-9
))

# ─── TOP BAR: CONTROLES ───
bx = MAIN_X0 + 0.01

ax_reiniciar = plt.axes([bx, TOP_Y + 0.015, 0.07, 0.038])
btn_reset = Button(ax_reiniciar, "REINICIAR")
btn_reset.label.set_fontsize(7)
btn_reset.on_clicked(reiniciar_juego)
bx += 0.095

cmd_x = bx
ax_box = plt.axes([cmd_x, TOP_Y + 0.015, 0.12, 0.038])
textbox = TextBox(ax_box, "Cmd: ", initial="")
textbox.ax.set_facecolor('#d4d4d4')
for p in textbox.ax.patches:
    p.set_facecolor('#d4d4d4')
textbox.text_disp.set_color('#1a1a1a')
textbox.text_disp.set_fontsize(9)
textbox.text_disp.set_fontweight('bold')
textbox.label.set_color('#1a1a1a')
textbox.label.set_fontsize(8)
def _fix_tb_color(txt):
    for t in textbox.ax.texts:
        t.set_color('#1a1a1a')
    if hasattr(textbox, '_textcolor'):
        textbox._textcolor = '#1a1a1a'
    if hasattr(textbox, 'text_disp'):
        textbox.text_disp.set_color('#1a1a1a')
textbox.on_text_change(_fix_tb_color)
textbox.on_submit(procesar_comandos)
fig.text(cmd_x + 0.06, TOP_Y + 0.070, "Control Manual (arriba-abajo-norte-sur-este-oeste)",
         ha='center', va='bottom', color=C_TEXT, fontsize=5.5)
bx += 0.135

ax_map = plt.axes([bx, TOP_Y + 0.015, 0.07, 0.038])
btn_map = Button(ax_map, "OTRO MAPA")
btn_map.label.set_fontsize(7)
btn_map.on_clicked(abrir_otro_mapa)
bx += 0.080

ax_tello = plt.axes([bx, TOP_Y + 0.015, 0.07, 0.038])
btn_tello = Button(ax_tello, "TELLO", color='#3d1515', hovercolor='#5a1f1f')
btn_tello.label.set_fontsize(7)
btn_tello.label.set_color(C_RED)
btn_tello.on_clicked(toggle_tello)
bx += 0.080

ax_sim = plt.axes([bx, TOP_Y + 0.015, 0.055, 0.038])
btn_sim = Button(ax_sim, "SIM", color=C_ACCENT, hovercolor=C_BTN_HOVER)
btn_sim.label.set_fontsize(7)
btn_sim.label.set_color('white')
btn_sim.label.set_fontweight('bold')
btn_sim.on_clicked(toggle_sim_mode)
bx += 0.065

ax_vel_m = plt.axes([bx, TOP_Y + 0.015, 0.035, 0.038])
btn_vel_m = Button(ax_vel_m, "-V")
btn_vel_m.label.set_fontsize(7)
btn_vel_m.on_clicked(lambda e: ajustar_velocidad(-0.05))

# Speed text centered between -V and +V
vel_m_end = bx + 0.035
vel_p_start = bx + 0.090
text_vel = fig.text((vel_m_end + vel_p_start) / 2, TOP_Y + 0.034,
                    f"{velocidad_movimiento:.2f} m/s",
                    ha='center', va='center', color=C_TEXT,
                    fontsize=8, weight='bold')

ax_vel_p = plt.axes([vel_p_start, TOP_Y + 0.015, 0.035, 0.038])
btn_vel_p = Button(ax_vel_p, "+V")
btn_vel_p.label.set_fontsize(7)
btn_vel_p.on_clicked(lambda e: ajustar_velocidad(0.05))
bx = vel_p_start + 0.045

# Info text (NIVEL / Alt / Pos) next to speed
info_x_start = bx + 0.01
texto_info = fig.text(info_x_start, TOP_Y + 0.034,
         f"NIVEL {int(rz * ESC_FACTOR) + 1} | Alt: {rz:.2f}m | Pos: ({rx:.2f}, {ry:.2f})",
         ha='left', va='center', color=C_TEXT, fontsize=7, weight='normal')

# ─── SLIDER DE ALTITUD DE SEGURIDAD ───
ax_slider_alt = plt.axes([0.94, 0.15, 0.015, 0.65])
slider_alt = Slider(
    ax=ax_slider_alt, label='Alt Seg (cm)\n', valmin=1, valmax=100,
    valinit=alt_seguridad_cm, valstep=1, orientation='vertical'
)
def actualizar_alt_seguridad(val):
    global alt_seguridad_cm
    alt_seguridad_cm = int(val)
slider_alt.on_changed(actualizar_alt_seguridad)

# Aplicar estado inicial
actualizar_estado_sidebar()
actualizar_botones_niveles()
actualizar_visibilidad_camara()
aplicar_tema()
dibujar_escena()
plt.show()
