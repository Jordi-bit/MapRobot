# Robot Laberinto AI 🤖🧩

Este proyecto es un simulador interactivo de laberinto donde puedes diseñar tus propios niveles y ver cómo un robot los resuelve utilizando inteligencia artificial (algoritmo A*).

## ✨ Características

- **Editor de Laberintos**: Interfaz gráfica para dibujar muros y caminos de forma intuitiva.
- **Simulador de Robot**: Control manual mediante comandos de texto (ej. `derecha 5; arriba 2`).
- **Inteligencia Artificial**: Resolución automática de rutas óptimas mediante el algoritmo A*.
- **Guardado Visual**: Genera automáticamente una imagen `.png` de tu diseño.
- **Interfaz en Español**: Pensado para facilitar el aprendizaje y la experimentación.

## 🚀 Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/TU_USUARIO/ROBOT-V1.0.git
   ```
2. Instala las librerías necesarias:
   ```bash
   pip install numpy matplotlib
   ```

## 🎮 Cómo usarlo

### 1. Diseñar el laberinto
Ejecuta el editor para crear tu mapa:
```bash
python editor_laberinto.py
```
- **Clic Izquierdo**: Poner/Quitar muro.
- **Tecla 'S'**: Guardar diseño (genera `laberinto_guardado.txt` y `laberinto.png`).

### 2. Ejecutar el simulador
Prueba tu laberinto con el robot:
```bash
python juego_laberinto_AI.py
```
- **Cuadro de texto**: Escribe comandos como `derecha 3; arriba 2` y pulsa Enter.
- **Tecla 'Z'**: Activa la IA para buscar la salida más rápida.
- **Tecla 'N' (o botón Reintentar)**: Reinicia el robot al punto de origen.

## 🛠️ Requisitos
- Python 3.x
- Matplotlib
- NumPy

## 📝 Créditos
Desarrollado como un proyecto educativo de robótica y algoritmos de búsqueda.
