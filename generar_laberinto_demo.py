import numpy as np

# Configuración coincidente con los scripts
ANCHO = 15
LARGO = 15
ALTO = 5

# Crear laberinto vacío con bordes
laberinto = np.zeros((ALTO, LARGO, ANCHO), dtype=int)
laberinto[:, 0, :] = 1
laberinto[:, -1, :] = 1
laberinto[:, :, 0] = 1
laberinto[:, :, -1] = 1

# Crear un camino que suba niveles
# Nivel 0: (1,1) -> (5,5)
for i in range(1, 6):
    laberinto[0, i, 1] = 0
    laberinto[0, 5, i] = 0

# Hueco para subir al nivel 1 en (5,5)
laberinto[1, 5, 5] = 0

# Nivel 1: (5,5) -> (10,10)
for i in range(5, 11):
    laberinto[1, i, 5] = 0
    laberinto[1, 10, i] = 0

# Huecos sucesivos
laberinto[2, 10, 10] = 0
laberinto[3, 10, 10] = 0
laberinto[4, 10, 10] = 0

# Meta en el último nivel
# objetivo = (ALTO - 1, LARGO - 2, ANCHO - 2) -> (4, 13, 13)
for i in range(10, 14):
    laberinto[4, i, 10] = 0
    laberinto[4, 13, i] = 0

np.save("laberinto_3d.npy", laberinto)
print("✅ Laberinto de demostración 3D generado en 'laberinto_3d.npy'")
