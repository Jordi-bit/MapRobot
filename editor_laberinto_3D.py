import sys
import io
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.widgets import Button, TextBox
import matplotlib.patches as patches
from mpl_toolkits.mplot3d import Axes3D
import os
import json
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

ANCHO_m = 15.0
LARGO_m = 15.0
ALTO_m = 5.0
resolucion_cm = 100

def calc_celdas(m, res):
    return max(3, int(round(m * (100.0 / res))))

ANCHO = calc_celdas(ANCHO_m, resolucion_cm)
LARGO = calc_celdas(LARGO_m, resolucion_cm)
ALTO = max(1, int(round(ALTO_m * (100.0 / resolucion_cm))))

try:
    laberinto = np.load("laberinto_3d.npy")
    ALTO, LARGO, ANCHO = laberinto.shape
    ANCHO_m = ANCHO * (resolucion_cm / 100.0)
    LARGO_m = LARGO * (resolucion_cm / 100.0)
    ALTO_m = ALTO * (resolucion_cm / 100.0)
    print(f"Cargado laberinto de {ANCHO}x{LARGO}x{ALTO} celdas")
except:
    laberinto = np.zeros((ALTO, LARGO, ANCHO), dtype=int)

inicio = [0, 1, 1]
objetivos = []
archivo_actual = "laberinto_3d.npy"

def cargar_metadata(ruta_npy):
    global objetivos, resolucion_cm, ANCHO_m, LARGO_m, ALTO_m
    ruta_json = ruta_npy.replace(".npy", ".json")
    if os.path.exists(ruta_json):
        try:
            with open(ruta_json, 'r') as f:
                data = json.load(f)
                objetivos = data.get("objetivo", [])
                if isinstance(objetivos[0], int):
                    objetivos = [objetivos]
                resolucion_cm = data.get("resolucion_cm", 100)
                ANCHO_m = ANCHO * (resolucion_cm / 100.0)
                LARGO_m = LARGO * (resolucion_cm / 100.0)
                ALTO_m = ALTO * (resolucion_cm / 100.0)
                print(f"Metas: {objetivos} | Res: {resolucion_cm}cm")
        except:
            pass

cargar_metadata(archivo_actual)

def obtener_cmap():
    colores_base = ["#D0D0D0", "black", "green", "yellow",
                    "orange", "cyan", "magenta", "lime", "pink", "teal",
                    "coral", "gold", "plum", "skyblue", "lightgreen"]
    n = max(4, 4 + len(objetivos))
    return ListedColormap(colores_base[:n])

cmap = obtener_cmap()
piso_actual = 0
modo_muros = True
modo_meta = False
modo_inicio = False
img = None
ax3d_embed = None

# --- COLOR PALETTE ---
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
C_INPUT_BG = '#0d1117'
C_GRID = '#21262d'

plt.style.use('dark_background')
fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor(C_BG)
ax = fig.add_axes([0.205, 0.03, 0.38, 0.86])
ax.set_facecolor(C_BG)
ax3d_embed = fig.add_axes([0.60, 0.03, 0.37, 0.86], projection='3d')
ax3d_embed.set_facecolor('#121212')

# --- LAYOUT CONSTANTS ---
SX = 0.0
SW = 0.18
SX1 = SX + SW
MAIN_L = 0.02
MAIN_R = 0.02
MAIN_B = 0.02
MAIN_T = 0.13
TOP_H = 0.08
TOP_Y = 1.0 - TOP_H - 0.01

# Sidebar background
fig.patches.append(patches.Rectangle(
    (SX, 0), SW, 1.0,
    fill=True, facecolor=C_SIDEBAR, edgecolor='none',
    transform=fig.transFigure, zorder=-10
))

fig.patches.append(patches.Rectangle(
    (SW, 0), 0.003, 1.0,
    fill=True, facecolor=C_BORDER, edgecolor='none',
    transform=fig.transFigure, zorder=-9
))

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

def sidebar_btn(y, text, **kw):
    return make_btn(
        plt.axes((SX + 0.025, y, SW - 0.05, 0.035)),
        text, **kw
    )

# ─── SIDEBAR: TITLE ───
fig.text(SX + 0.025, 0.971, 'EDITOR 3D', fontsize=14, fontweight='bold',
         color=C_TEXT, transform=fig.transFigure)
fig.text(SX + 0.025, 0.956, 'LABERINTO', fontsize=9, fontweight='normal',
         color=C_TEXT_MUTED, transform=fig.transFigure)

fig.patches.append(patches.Rectangle(
    (SX + 0.02, 0.945), SW - 0.04, 0.004,
    fill=True, facecolor=C_BORDER, edgecolor='none',
    transform=fig.transFigure, zorder=-8
))

# ─── SIDEBAR: ARCHIVO ───
section_box(0.73, 0.21)
section_title(0.925, 'ARCHIVO')
b_nuevo = sidebar_btn(0.885, 'NUEVO MAPA', color=C_BTN_BG, hover=C_BTN_HOVER, tcolor=C_PURPLE)
b_cargar = sidebar_btn(0.843, 'CARGAR MAPA', color=C_BTN_BG, hover=C_BTN_HOVER, tcolor=C_ACCENT)
b_guardar = sidebar_btn(0.801, 'GUARDAR MAPA', color=C_BTN_BG, hover=C_BTN_HOVER, tcolor=C_GREEN)

TOOL_BUTTONS = []

# ─── SIDEBAR: HERRAMIENTAS ───
section_box(0.43, 0.30)
section_title(0.715, 'HERRAMIENTAS')
b_muros = sidebar_btn(0.675, 'DIBUJAR MUROS', color=C_BTN_BG, hover=C_BTN_HOVER, tcolor=C_TEXT)
b_meta = sidebar_btn(0.633, 'SITUAR META', color=C_BTN_BG, hover=C_BTN_HOVER, tcolor=C_YELLOW)
b_inicio = sidebar_btn(0.591, 'SITUAR INICIO', color=C_BTN_BG, hover=C_BTN_HOVER, tcolor=C_GREEN)
TOOL_BUTTONS[:] = [b_muros, b_meta, b_inicio]
b_borrar_metas = sidebar_btn(0.549, 'BORRAR METAS', color='#3d1515', hover='#5a1f1f', tcolor=C_RED)

# ─── SIDEBAR: CAPAS ───
section_box(0.31, 0.12)
section_title(0.415, 'CAPAS')
b_capa_add = sidebar_btn(0.365, '+ AÑADIR CAPA', color=C_BTN_BG, hover=C_BTN_HOVER, tcolor=C_GREEN)
b_capa_del = sidebar_btn(0.323, '- ELIMINAR CAPA', color='#3d1515', hover='#5a1f1f', tcolor=C_RED)

# ─── SIDEBAR: PISO ───
section_box(0.17, 0.14)
section_title(0.295, 'PISO')

ax_txt_piso = plt.axes((SX + 0.065, 0.200, SW - 0.13, 0.032))
txt_piso = TextBox(ax_txt_piso, '', initial=str(piso_actual), textalignment='center')
txt_piso.set_active(False)
txt_piso.text_disp.set_color(C_TEXT)
txt_piso.text_disp.set_fontsize(9)
txt_piso.text_disp.set_fontweight('bold')
txt_piso.text_disp.set_horizontalalignment('center')
txt_piso.ax.set_facecolor(C_INPUT_BG)
txt_piso.ax.tick_params(colors=C_TEXT)

fig.text(SX + 0.042, 0.280, 'Bajar', fontsize=6, color=C_TEXT_DIM,
         ha='center', transform=fig.transFigure)
b_piso_m = make_btn(
    plt.axes((SX + 0.025, 0.240, 0.035, 0.035)),
    '\u25C0', color=C_BTN_BG, hover=C_BTN_HOVER, tcolor=C_TEXT, fsize=9
)
fig.text(SX + 0.137, 0.280, 'Subir', fontsize=6, color=C_TEXT_DIM,
         ha='center', transform=fig.transFigure)
b_piso_p = make_btn(
    plt.axes((SX + 0.120, 0.240, 0.035, 0.035)),
    '\u25B6', color=C_BTN_BG, hover=C_BTN_HOVER, tcolor=C_TEXT, fsize=9
)

# ─── SIDEBAR: STATUS ───
section_box(0.03, 0.14)
section_title(0.155, 'ESTADO')
fig.text(SX + 0.025, 0.125, f'Capas: {ALTO}', fontsize=7, color=C_TEXT_DIM,
         transform=fig.transFigure)
fig.text(SX + 0.025, 0.108, f'Celdas: {ANCHO}x{LARGO}', fontsize=7, color=C_TEXT_DIM,
         transform=fig.transFigure)
fig.text(SX + 0.025, 0.091, f'Metas: {len(objetivos)}', fontsize=7, color=C_TEXT_DIM,
         transform=fig.transFigure)
status_text = fig.text(
    SX + 0.025, 0.050, 'Listo',
    fontsize=7, color=C_TEXT_MUTED, transform=fig.transFigure
)

# ─── TOP BAR: DIMENSIONES ───
fig.patches.append(patches.Rectangle(
    (MAIN_X0 := SX + SW, TOP_Y), 1.0 - MAIN_X0, TOP_H,
    fill=True, facecolor=C_SIDEBAR, edgecolor='none',
    transform=fig.transFigure, zorder=-10
))

fig.text(MAIN_X0 + 0.01, TOP_Y + 0.060, 'DIMENSIONES DEL MAPA',
         fontsize=8, fontweight='bold', color=C_TEXT_MUTED,
         transform=fig.transFigure)

def dim_textbox(x, label, initial, w=0.05):
    ax_b = plt.axes((x, TOP_Y + 0.015, w, 0.038))
    tb = TextBox(ax_b, label, initial=str(initial), textalignment='center')
    tb.ax.set_facecolor(C_INPUT_BG)
    tb.text_disp.set_color('black')
    tb.text_disp.set_fontsize(14)
    tb.text_disp.set_horizontalalignment('center')
    tb.label.set_color(C_TEXT)
    tb.label.set_fontsize(12)
    return tb

box_ancho = dim_textbox(MAIN_X0 + 0.065, 'X (m)', f'{ANCHO_m:.1f}', 0.06)
box_largo = dim_textbox(MAIN_X0 + 0.200, 'Y (m)', f'{LARGO_m:.1f}', 0.06)
box_alto = dim_textbox(MAIN_X0 + 0.335, 'Z (m)', f'{ALTO_m:.1f}', 0.06)
box_res  = dim_textbox(MAIN_X0 + 0.530, 'cm / Superficie cubo', str(resolucion_cm), 0.05)

def set_status(msg):
    status_text.set_text(msg)
    fig.canvas.draw_idle()

# ─── FUNCTIONS ───

def obtener_capa_visual(z):
    capa = laberinto[z].copy()
    if z == inicio[0]:
        capa[int(inicio[1]), int(inicio[2])] = 2
    for i, obj in enumerate(objetivos):
        if len(obj) >= 3 and obj[0] == z:
            capa[int(obj[1]), int(obj[2])] = 3 + i
    return capa

def dibujar_rejilla():
    global img, piso_actual, cmap
    ax.clear()
    cmap = obtener_cmap()
    n_colors = cmap.N
    max_val = n_colors - 1
    img = ax.imshow(
        obtener_capa_visual(piso_actual),
        cmap=cmap, origin='lower',
        extent=(0, ANCHO_m, 0, LARGO_m),
        vmin=0, vmax=max_val
    )

    for i, obj in enumerate(objetivos):
        if len(obj) >= 3 and obj[0] == piso_actual:
            xm = (obj[2] + 0.5) * (resolucion_cm / 100.0)
            ym = (obj[1] + 0.5) * (resolucion_cm / 100.0)
            ax.text(xm, ym, f'M{i+1}', fontsize=11, fontweight='bold',
                    ha='center', va='center', color='black')

    for i in range(ANCHO + 1):
        ax.axvline(i * (resolucion_cm / 100.0), color=C_GRID, linewidth=0.5, alpha=0.3)
    for j in range(LARGO + 1):
        ax.axhline(j * (resolucion_cm / 100.0), color=C_GRID, linewidth=0.5, alpha=0.3)

    ax.set_xlabel('X (metros)', color=C_TEXT_MUTED, fontsize=9)
    ax.set_ylabel('Y (metros)', color=C_TEXT_MUTED, fontsize=9)
    ax.tick_params(colors=C_TEXT_MUTED, labelsize=7)
    ax.spines['bottom'].set_color(C_BORDER)
    ax.spines['left'].set_color(C_BORDER)
    ax.spines['top'].set_color(C_BORDER)
    ax.spines['right'].set_color(C_BORDER)

    modo_txt = 'SITUAR META' if modo_meta else ('SITUAR INICIO' if modo_inicio else ('DIBUJAR MUROS' if modo_muros else '---'))
    ax.set_title(f'Nivel {piso_actual}/{ALTO}  |  Alt: {piso_actual * resolucion_cm / 100.0:.2f}m  |  Modo: {modo_txt}',
                 fontsize=9, fontweight='bold', color=C_TEXT_MUTED, pad=6)

    ax.set_xticks(np.arange(0, ANCHO_m + 0.01, resolucion_cm / 100.0))
    ax.set_yticks(np.arange(0, LARGO_m + 0.01, resolucion_cm / 100.0))
    ax.set_facecolor('#1a1a2e')

    if 'txt_piso' in globals() and txt_piso is not None:
        txt_piso.set_val(str(piso_actual))

    fig.canvas.draw_idle()
    _actualizar_vista_3d()

def guardar(event=None):
    global archivo_actual
    ruta = filedialog.asksaveasfilename(
        initialdir='.', title='Guardar Mapa',
        defaultextension='.npy',
        filetypes=(('Archivos Numpy', '*.npy'), ('Todos', '*.*'))
    )
    if not ruta:
        set_status('Guardado cancelado.')
        return
    archivo_actual = ruta
    datos_a_guardar = np.clip(laberinto, 0, 1)
    np.save(archivo_actual, datos_a_guardar)
    ruta_json = archivo_actual.replace('.npy', '.json')
    with open(ruta_json, 'w') as f:
        json.dump({
            'inicio': list(map(int, inicio)),
            'objetivo': [list(map(int, obj)) for obj in objetivos],
            'resolucion_cm': resolucion_cm
        }, f)
    set_status(f'Guardado: {os.path.basename(archivo_actual)} ({len(objetivos)} metas)')

def agregar_capa(event):
    global laberinto, ALTO, piso_actual
    nueva_capa = np.zeros((1, LARGO, ANCHO), dtype=int)
    laberinto = np.concatenate((laberinto, nueva_capa), axis=0)
    ALTO = laberinto.shape[0]
    piso_actual = ALTO - 1
    dibujar_rejilla()
    set_status(f'Nivel anadido. Total: {ALTO}')

def eliminar_capa(event):
    global laberinto, ALTO, piso_actual
    if ALTO > 1:
        laberinto = laberinto[:-1]
        ALTO = laberinto.shape[0]
        if piso_actual >= ALTO:
            piso_actual = ALTO - 1
        dibujar_rejilla()
        set_status(f'Nivel eliminado. Total: {ALTO}')

def al_clic(event):
    global objetivos, inicio, modo_muros, modo_meta, modo_inicio
    if event.inaxes != ax:
        return
    x = int(event.xdata / (resolucion_cm / 100.0))
    y = int(event.ydata / (resolucion_cm / 100.0))
    if not (0 <= x < ANCHO and 0 <= y < LARGO):
        return
    if modo_inicio:
        inicio = [piso_actual, y, x]
        set_status(f'Inicio establecido en nivel {piso_actual}: ({x}, {y})')
    elif modo_meta:
        nuevos_objetivos = [
            o for o in objetivos
            if len(o) < 3 or o[0] != piso_actual or o[1] != y or o[2] != x
        ]
        nuevos_objetivos.append([piso_actual, y, x])
        objetivos = nuevos_objetivos
        set_status(f'Meta anadida en ({x}, {y}) nivel {piso_actual}. Total: {len(objetivos)}')
    elif modo_muros:
        laberinto[piso_actual, y, x] = 1 if laberinto[piso_actual, y, x] == 0 else 0
        acc = 'Muro' if laberinto[piso_actual, y, x] == 1 else 'Vacio'
        set_status(f'{acc} en ({x}, {y}) nivel {piso_actual}')
    else:
        return
    dibujar_rejilla()

def _btn_pulsado(btn):
    btn.color = C_BTN_ACTIVE
    btn.ax.set_facecolor(C_BTN_ACTIVE)
    for spine in btn.ax.spines.values():
        spine.set_color(C_ACCENT)
        spine.set_linewidth(1.8)

def _btn_normal(btn):
    btn.color = C_BTN_BG
    btn.ax.set_facecolor(C_BTN_BG)
    for spine in btn.ax.spines.values():
        spine.set_color(C_BORDER)
        spine.set_linewidth(0.6)

def _reset_tool_buttons():
    for btn in TOOL_BUTTONS:
        _btn_normal(btn)

def _set_active_tool(btn):
    _reset_tool_buttons()
    _btn_pulsado(btn)

def toggle_modo_meta(event):
    global modo_muros, modo_meta, modo_inicio
    if modo_meta:
        modo_meta = False
        _reset_tool_buttons()
        set_status('Modo meta desactivado')
    else:
        modo_muros = False
        modo_meta = True
        modo_inicio = False
        _set_active_tool(b_meta)
        set_status('Modo meta activado')
    dibujar_rejilla()

def toggle_modo_inicio(event):
    global modo_muros, modo_inicio, modo_meta
    if modo_inicio:
        modo_inicio = False
        _reset_tool_buttons()
        set_status('Modo inicio desactivado')
    else:
        modo_muros = False
        modo_inicio = True
        modo_meta = False
        _set_active_tool(b_inicio)
        set_status('Modo inicio activado')
    dibujar_rejilla()

def toggle_modo_muros(event):
    global modo_muros, modo_meta, modo_inicio
    if modo_muros:
        modo_muros = False
        modo_meta = False
        modo_inicio = False
        _reset_tool_buttons()
        set_status('Modo dibujo de muros desactivado')
    else:
        modo_muros = True
        modo_meta = False
        modo_inicio = False
        _set_active_tool(b_muros)
        set_status('Modo dibujo de muros activado')
    dibujar_rejilla()

def borrar_metas(event=None):
    global objetivos
    objetivos = []
    set_status('Todas las metas borradas.')
    dibujar_rejilla()

def cargar_mapa(event):
    global laberinto, ALTO, LARGO, ANCHO, archivo_actual, piso_actual
    ruta = filedialog.askopenfilename(
        initialdir='.', title='Cargar Mapa',
        filetypes=(('Archivos Numpy', '*.npy'), ('Todos', '*.*'))
    )
    if not ruta:
        set_status('Carga cancelada.')
        return
    archivo_actual = ruta
    laberinto = np.load(archivo_actual)
    ALTO, LARGO, ANCHO = laberinto.shape
    piso_actual = 0
    cargar_metadata(archivo_actual)
    try:
        box_ancho.set_val(f'{ANCHO_m:.1f}')
        box_largo.set_val(f'{LARGO_m:.1f}')
        box_alto.set_val(f'{ALTO_m:.1f}')
        box_res.set_val(str(resolucion_cm))
    except NameError:
        pass
    set_status(f'Cargado: {os.path.basename(archivo_actual)}')
    dibujar_rejilla()

def cambiar_piso(delta):
    global piso_actual
    piso_actual = max(0, min(ALTO - 1, piso_actual + delta))
    dibujar_rejilla()
    set_status(f'Nivel {piso_actual} / {ALTO}')

def nuevo_mapa(event):
    global laberinto, ANCHO, LARGO, ALTO, ANCHO_m, LARGO_m, ALTO_m
    global resolucion_cm, piso_actual, inicio, objetivos, archivo_actual
    try:
        wm = float(box_ancho.text)
        lm = float(box_largo.text)
        hm = float(box_alto.text)
        res = int(box_res.text)
    except ValueError:
        set_status('Error: valores numericos invalidos.')
        return
    resolucion_cm = max(5, res)
    ANCHO_m, LARGO_m, ALTO_m = max(0.25, wm), max(0.25, lm), max(0.25, hm)
    ANCHO = calc_celdas(ANCHO_m, resolucion_cm)
    LARGO = calc_celdas(LARGO_m, resolucion_cm)
    ALTO = 1
    laberinto = np.zeros((ALTO, LARGO, ANCHO), dtype=int)
    piso_actual = 0
    inicio = [0, 0, 0]
    objetivos = []
    archivo_actual = 'nuevo_laberinto_custom.npy'
    set_status(f'Nuevo mapa: {ANCHO_m}x{LARGO_m}x{ALTO_m}m @ {resolucion_cm}cm')
    dibujar_rejilla()

def _actualizar_vista_3d():
    global ax3d_embed
    if ax3d_embed is None:
        return
    try:
        ax3d_embed.clear()
        ESC = 100.0 / resolucion_cm
        colors = np.full(laberinto.shape, None, dtype=object)
        paleta = ['#FF9999', '#99FF99', '#9999FF', '#FFFF99', '#FF99FF']

        for z in range(ALTO):
            c = paleta[z % len(paleta)]
            for y in range(LARGO):
                for x in range(ANCHO):
                    if laberinto[z, y, x] == 1:
                        colors[z, y, x] = c + 'CC'

        if 0 <= inicio[0] < ALTO and 0 <= inicio[1] < LARGO and 0 <= inicio[2] < ANCHO:
            colors[inicio[0], inicio[1], inicio[2]] = '#00FF00FF'

        for i, obj in enumerate(objetivos):
            if len(obj) >= 3 and 0 <= obj[0] < ALTO and 0 <= obj[1] < LARGO and 0 <= obj[2] < ANCHO:
                colors[obj[0], obj[1], obj[2]] = '#FF8C00FF' if i == 0 else '#FFD700FF'

        filled = np.vectorize(lambda x: x is not None)(colors)
        xg, yg, zg = np.indices((ANCHO + 1, LARGO + 1, ALTO + 1)) / ESC

        ax3d_embed.voxels(xg, yg, zg,
                    filled=np.transpose(filled, (2, 1, 0)),
                    facecolors=np.transpose(colors, (2, 1, 0)),
                    edgecolor='#33333333', linewidth=0.2)

        ax3d_embed.view_init(elev=25, azim=-45)
        step = resolucion_cm / 100.0
        ancho_m = ANCHO / ESC
        largo_m = LARGO / ESC
        alto_m = ALTO / ESC

        ax3d_embed.set_xticks(np.arange(0, ancho_m + 0.01, step))
        ax3d_embed.set_yticks(np.arange(0, largo_m + 0.01, step))
        ax3d_embed.set_zticks(np.arange(0, alto_m + 0.01, step))
        ax3d_embed.set_box_aspect((ancho_m, largo_m, alto_m))
        ax3d_embed.set_xlim(0, ancho_m)
        ax3d_embed.set_ylim(0, largo_m)
        ax3d_embed.set_zlim(0, alto_m)

        for axis in [ax3d_embed.xaxis, ax3d_embed.yaxis, ax3d_embed.zaxis]:
            axis.label.set_color('white')
        ax3d_embed.tick_params(colors='white')
        ax3d_embed.set_xlabel('X')
        ax3d_embed.set_ylabel('Y')
        ax3d_embed.set_zlabel('Z')

        fig.canvas.draw_idle()
    except Exception as e:
        set_status(f'Error 3D: {e}')

def al_tecla(event):
    if event.key == 's':
        guardar()

# ─── WIRE BUTTONS ───
b_nuevo.on_clicked(nuevo_mapa)
b_cargar.on_clicked(cargar_mapa)
b_guardar.on_clicked(guardar)
b_muros.on_clicked(toggle_modo_muros)
b_meta.on_clicked(toggle_modo_meta)
b_inicio.on_clicked(toggle_modo_inicio)
b_borrar_metas.on_clicked(borrar_metas)
b_capa_add.on_clicked(agregar_capa)
b_capa_del.on_clicked(eliminar_capa)
b_piso_m.on_clicked(lambda e: cambiar_piso(-1))
b_piso_p.on_clicked(lambda e: cambiar_piso(1))

fig.canvas.mpl_connect('button_press_event', al_clic)
fig.canvas.mpl_connect('key_press_event', al_tecla)

dibujar_rejilla()

# Set default mode to muros
_set_active_tool(b_muros)

plt.show()
