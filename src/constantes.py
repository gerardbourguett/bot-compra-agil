"""
Constantes del sistema Compra Ágil
Incluye mapeos de estados y lista de regiones oficiales.
"""

ESTADOS_LICITACION = {
    2: "Publicada",
    3: "Cerrada",
    4: "OC Emitida",
    5: "Cancelada",
    6: "Desierta"
}

# Ordenadas geográficamente de norte a sur (aproximado)
REGIONES = [
    {"id": 15, "nombre": "Arica y Parinacota", "codigo": 15},
    {"id": 1, "nombre": "Tarapacá", "codigo": 1},
    {"id": 2, "nombre": "Antofagasta", "codigo": 2},
    {"id": 3, "nombre": "Atacama", "codigo": 3},
    {"id": 4, "nombre": "Coquimbo", "codigo": 4},
    {"id": 5, "nombre": "Valparaíso", "codigo": 5},
    {"id": 13, "nombre": "Metropolitana", "codigo": 13},
    {"id": 6, "nombre": "O'Higgins", "codigo": 6},
    {"id": 7, "nombre": "Maule", "codigo": 7},
    {"id": 16, "nombre": "Ñuble", "codigo": 16},
    {"id": 8, "nombre": "Biobío", "codigo": 8},
    {"id": 9, "nombre": "Araucanía", "codigo": 9},
    {"id": 14, "nombre": "Los Ríos", "codigo": 14},
    {"id": 10, "nombre": "Los Lagos", "codigo": 10},
    {"id": 11, "nombre": "Aysén", "codigo": 11},
    {"id": 12, "nombre": "Magallanes", "codigo": 12}
]

def obtener_nombre_estado(id_estado):
    """Devuelve el nombre del estado dado su ID"""
    return ESTADOS_LICITACION.get(id_estado, "Desconocido")

def obtener_nombres_regiones():
    """Devuelve solo la lista de nombres de regiones"""
    return [r["nombre"] for r in REGIONES]
