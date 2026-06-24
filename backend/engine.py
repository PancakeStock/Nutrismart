"""
engine.py — Motor MRP y Costeo de Canasta — Nutrismart UAI Grupo 9
==================================================================
Arquitectura de capas:
  1. Carga de datos  (cargar_*)
  2. Explosión de materiales  (calcular_requerimiento_materiales)
  3. Conversión a formatos comerciales  (resolver_costo_ingrediente)
  4. Costeo por tienda  (calcular_costo_canasta)
  5. Optimización y ensamble final  (optimizar_canasta)

Tabla de conversión de unidades (UNIT_DISPATCH):
  Clave → (unidad_receta, unidad_venta)
  Valor → función lambda(cantidad_neta, precio_catalogo) → costo_CLP
"""

import os
import json
import math


# ---------------------------------------------------------------------------
# SUPERMERCADOS
# ---------------------------------------------------------------------------
SUPERMERCADOS_DB = [
    {"nombre": "Jumbo Paseo Los Dominicos",   "lat": -33.4111, "lng": -70.5218},
    {"nombre": "Lider Expres de Grecia",       "lat": -33.4764, "lng": -70.5482},
    {"nombre": "Unimarc Príncipe de Gales",    "lat": -33.4389, "lng": -70.5510},
]

# Pesos promedio en kg de productos vendidos "por unidad" en el retail CL.
# Se usan cuando la receta indica kg pero el catálogo vende por unidad.
PESO_PROMEDIO_UN = {
    "Coliflor Entera":      0.800,  # ~800g la unidad
    "Albahaca Fresca":      0.050,  # manojo ≈ 50g
    "Lechuga Entera":       0.350,  # lechuga mediana
    "Atún en Conserva al Agua": 0.170,  # lata estándar 170g
    "Jurel en Conserva":    0.170,  # lata estándar 170g
    "Cebollín Entero":      0.100,  # manojo ≈ 100g
}

# Peso promedio por unidad de productos vendidos por kg en el retail CL,
# cuando la receta indica cantidad en unidades.
PESO_UN_EN_KG = {
    "Cebolla Entera":   0.200,   # cebolla mediana ≈ 200g
    "Cebolla Morada":   0.200,
    "Tomate Entero":    0.180,   # tomate mediano ≈ 180g
    "Zanahoria Entera": 0.100,   # zanahoria mediana ≈ 100g
    "Palta Entera":     0.200,   # palta mediana ≈ 200g
    "Pimiento Entero":  0.180,   # pimiento mediano ≈ 180g
    "Ají Verde":        0.050,   # ají ≈ 50g
}

# Volumen estándar de envases vendidos "por unidad" cuando la receta
# indica ml pero el catálogo vende por unidad (no litro).
ML_POR_UN = {
    "Salsa de Tomate": 210.0,   # lata/tetra pequeña estándar CL ≈ 210ml
}

# ---------------------------------------------------------------------------
# TABLA DE DESPACHO DE CONVERSIONES
# Clave: (unidad_receta, unidad_venta)
# Valor: función(cantidad_neta, precio_catalogo, nombre_ingrediente) → costo
#
# Lógica de redondeo al empaque mínimo:
#   - Para artículos vendidos por unidad → math.ceil(unidades_necesarias)
#   - Para kg/litro → se compra exactamente lo necesario (a granel o porción)
#     redondeado hacia arriba al mínimo práctico de 200g/250ml
# ---------------------------------------------------------------------------

def _costo_kg_kg(cant, precio, nombre):
    """Receta en kg, catálogo en kg (granel). Mínimo 200g."""
    kg = max(0.200, cant)
    return precio * kg

def _costo_un_un(cant, precio, nombre):
    """Receta en unidades, catálogo en unidades. Siempre ceil."""
    return precio * math.ceil(cant)

def _costo_ml_litro(cant, precio, nombre):
    """Receta en ml, catálogo en precio/litro. Mínimo 250ml."""
    litros = max(0.250, cant / 1000.0)
    return precio * litros

def _costo_ml_un(cant, precio, nombre):
    """Receta en ml, catálogo vende por unidad (ej: lata de salsa tomate).
    Calculamos cuántas unidades caben para cubrir cant ml."""
    ml_por_envase = ML_POR_UN.get(nombre, 200.0)
    envases = max(1, math.ceil(cant / ml_por_envase))
    return precio * envases

def _costo_kg_un(cant, precio, nombre):
    """Receta en kg, catálogo vende por unidad (ej: coliflor, manojo albahaca).
    Usamos el peso promedio del ítem para saber cuántas unidades comprar."""
    peso_un = PESO_PROMEDIO_UN.get(nombre, 0.200)
    unidades = max(1, math.ceil(cant / peso_un))
    return precio * unidades

def _costo_un_kg(cant, precio, nombre):
    """Receta en unidades, catálogo vende por kg (ej: cebolla, tomate, palta).
    Convertimos unidades a kg usando pesos promedio."""
    peso_kg = PESO_UN_EN_KG.get(nombre, 0.150)
    kg_necesarios = max(0.200, cant * peso_kg)
    return precio * kg_necesarios

def _costo_un_litro(cant, precio, nombre):
    """Receta en unidades (inhabitual), catálogo en litros. Fallback seguro."""
    return precio * max(0.250, cant * 0.200)


UNIT_DISPATCH = {
    ("kg",  "kg"):    _costo_kg_kg,
    ("un",  "un"):    _costo_un_un,
    ("ml",  "litro"): _costo_ml_litro,
    ("ml",  "un"):    _costo_ml_un,
    ("kg",  "un"):    _costo_kg_un,
    ("un",  "kg"):    _costo_un_kg,
    ("un",  "litro"): _costo_un_litro,
    # Casos idénticos de forma alternativa
    ("ml",  "kg"):    lambda c, p, n: p * max(0.200, c / 1000.0),
}


# ---------------------------------------------------------------------------
# CARGA DE DATOS
# ---------------------------------------------------------------------------

def _data_path(filename):
    return os.path.join(os.path.dirname(__file__), "data", filename)


def cargar_recetas_por_objetivo(objetivo: str) -> list:
    try:
        with open(_data_path("recetas.json"), encoding="utf-8") as f:
            todas = json.load(f)
        return [r for r in todas if r.get("objetivo") == objetivo]
    except Exception as e:
        print(f"[ERROR] cargar_recetas_por_objetivo: {e}")
        return []


def cargar_precios() -> dict:
    try:
        with open(_data_path("precios_productos.json"), encoding="utf-8") as f:
            raw = f.read()
        # Saneamos la llave corrupta (carácter CJK erróneo) antes de parsear
        raw = raw.replace('"盤unidad_venta"', '"unidad_venta"')
        return json.loads(raw)
    except Exception as e:
        print(f"[ERROR] cargar_precios: {e}")
        return {}


# ---------------------------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------------------------

def calcular_haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    rl1, rlo1 = math.radians(lat1), math.radians(lon1)
    rl2, rlo2 = math.radians(lat2), math.radians(lon2)
    dlat, dlon = rl2 - rl1, rlo2 - rlo1
    a = math.sin(dlat / 2) ** 2 + math.cos(rl1) * math.cos(rl2) * math.sin(dlon / 2) ** 2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)


def _buscar_producto(nombre_ingrediente: str, productos_tienda: list) -> dict | None:
    """Búsqueda exacta primero, luego por subcadena insensible a mayúsculas."""
    nombre_lower = nombre_ingrediente.lower()
    # Paso 1: coincidencia exacta
    for p in productos_tienda:
        if p.get("nombre", "").lower() == nombre_lower:
            return p
    # Paso 2: subcadena
    for p in productos_tienda:
        if nombre_lower in p.get("nombre", "").lower():
            return p
    return None


# ---------------------------------------------------------------------------
# CAPA 2: EXPLOSIÓN DE MATERIALES (MRP)
# ---------------------------------------------------------------------------

def calcular_requerimiento_materiales(recetas: list, duracion_dias: int) -> dict:
    """
    Retorna un dict {nombre_ingrediente: {cantidad, unidad}} con las
    necesidades brutas acumuladas para el período completo.
    Se rota cíclicamente entre recetas disponibles por tipo de comida.
    """
    desayunos = [r for r in recetas if r.get("tipo_comida") == "Desayuno-Once"]
    almuerzos  = [r for r in recetas if r.get("tipo_comida") == "Almuerzo"]
    cenas      = [r for r in recetas if r.get("tipo_comida") == "Cena"]

    consolidado = {}

    for i in range(duracion_dias):
        menu_dia = []
        if desayunos: menu_dia.append(desayunos[i % len(desayunos)])
        if almuerzos: menu_dia.append(almuerzos[i % len(almuerzos)])
        if cenas:     menu_dia.append(cenas[i % len(cenas)])

        for receta in menu_dia:
            for ing in receta.get("ingredientes", []):
                nombre  = ing.get("nombre_comercial")
                cant    = float(ing.get("cantidad_numerica", 0))
                unidad  = ing.get("unidad_medida", "kg")

                if not nombre:
                    continue

                if nombre not in consolidado:
                    consolidado[nombre] = {"cantidad": 0.0, "unidad": unidad}
                consolidado[nombre]["cantidad"] += cant

    return consolidado


# ---------------------------------------------------------------------------
# CAPA 3: RESOLUCIÓN DE COSTO POR INGREDIENTE
# ---------------------------------------------------------------------------

def resolver_costo_ingrediente(
    nombre: str,
    cantidad_neta: float,
    unidad_receta: str,
    producto_catalogo: dict,
) -> float:
    """
    Aplica la tabla de despacho y retorna el costo en CLP para cubrir
    'cantidad_neta' unidades del ingrediente, redondeado al empaque mínimo.
    """
    precio     = float(producto_catalogo.get("precio", 0))
    unidad_cat = producto_catalogo.get("unidad_venta", "kg")

    clave = (unidad_receta, unidad_cat)
    fn = UNIT_DISPATCH.get(clave)

    if fn is None:
        # Fallback: si no hay conversión registrada, estimamos precio directo
        print(f"  [WARN] Combinación de unidades sin regla: {clave} para '{nombre}'")
        return precio * max(1, math.ceil(cantidad_neta))

    return fn(cantidad_neta, precio, nombre)


# ---------------------------------------------------------------------------
# CAPA 4: COSTEO TOTAL POR TIENDA
# ---------------------------------------------------------------------------

def calcular_costo_canasta(
    nombre_tienda: str,
    requerimientos: dict,
    precios_db: dict,
) -> tuple[int, list]:
    """
    Calcula el costo total de la canasta en una tienda específica.
    Retorna (costo_total_CLP, lista_compras_con_precio).
    """
    productos_tienda = precios_db.get(nombre_tienda, [])
    costo_total = 0.0
    desglose = []

    for nombre_ing, datos in requerimientos.items():
        cant   = datos["cantidad"]
        unidad = datos["unidad"]

        prod = _buscar_producto(nombre_ing, productos_tienda)
        if not prod:
            # Ingrediente no encontrado en esta tienda — se omite del costeo
            # (Podría hacerse fallback a precio promedio entre tiendas en v2)
            continue

        costo_item = resolver_costo_ingrediente(nombre_ing, cant, unidad, prod)
        costo_total += costo_item
        desglose.append({
            "ingrediente":     nombre_ing,
            "cantidad_neta":   cant,
            "unidad_receta":   unidad,
            "unidad_venta":    prod.get("unidad_venta"),
            "precio_catalogo": prod.get("precio"),
            "costo_estimado":  int(round(costo_item)),
        })

    return int(round(costo_total)), desglose


# ---------------------------------------------------------------------------
# CAPA 5: CONSTRUCCIÓN DE LISTA DE COMPRAS PARA EL FRONTEND
# ---------------------------------------------------------------------------
#
# EMPAQUES_MINIMOS_CL
# -------------------
# Define el empaque vendible mínimo real en el retail chileno para cada
# ingrediente, expresado en la misma unidad que usa el catálogo (unidad_venta).
#
# Estructura de cada entrada:
#   "Nombre Ingrediente": {
#       "empaque_min":  <float>   cantidad mínima del empaque,
#       "unidad":       <str>     unidad del empaque ("kg", "L", "un", "ml"),
#       "etiqueta":     <str>     texto legible para el usuario,
#   }
#
# Regla de uso:
#   cantidad_a_comprar = max(empaque_min, ceil(cant_neta / empaque_min) * empaque_min)
# ---------------------------------------------------------------------------

EMPAQUES_MINIMOS_CL = {
    # --- ACEITES Y LÍQUIDOS ---
    "Aceite Vegetal":           {"empaque_min": 0.900,  "unidad": "L",  "etiqueta": "botella 900 ml"},
    "Aceite de Oliva":          {"empaque_min": 0.500,  "unidad": "L",  "etiqueta": "botella 500 ml"},
    "Jugo de Limón":            {"empaque_min": 0.500,  "unidad": "L",  "etiqueta": "botella 500 ml"},
    "Vino Blanco":              {"empaque_min": 0.375,  "unidad": "L",  "etiqueta": "botella 375 ml"},
    "Leche Descremada":         {"empaque_min": 1.000,  "unidad": "L",  "etiqueta": "caja 1 litro"},
    "Leche Entera":             {"empaque_min": 1.000,  "unidad": "L",  "etiqueta": "caja 1 litro"},
    "Salsa de Tomate":          {"empaque_min": 1.000,  "unidad": "un", "etiqueta": "lata/tetra 210 ml"},

    # --- VERDURAS Y HORTALIZAS vendidas por kg ---
    "Palta Entera":             {"empaque_min": 0.200,  "unidad": "kg", "etiqueta": "unidad (~200 g)"},
    "Almendras":                {"empaque_min": 0.200,  "unidad": "kg", "etiqueta": "bolsa 200 g"},
    "Dientes de Dragón":        {"empaque_min": 0.100,  "unidad": "kg", "etiqueta": "bandeja 100 g"},
    "Champiñones Frescos":      {"empaque_min": 0.200,  "unidad": "kg", "etiqueta": "bandeja 200 g"},
    "Espinaca Fresca":          {"empaque_min": 0.200,  "unidad": "kg", "etiqueta": "bolsa 200 g"},
    "Espárragos Frescos":       {"empaque_min": 0.250,  "unidad": "kg", "etiqueta": "atado 250 g"},
    "Porotos Verdes Congelados":{"empaque_min": 0.400,  "unidad": "kg", "etiqueta": "bolsa 400 g"},
    "Frutos Rojos Congelados":  {"empaque_min": 0.300,  "unidad": "kg", "etiqueta": "bolsa 300 g"},
    "Frutillas Frescas":        {"empaque_min": 0.500,  "unidad": "kg", "etiqueta": "bandeja 500 g"},
    "Choclo en Grano":          {"empaque_min": 0.300,  "unidad": "kg", "etiqueta": "bolsa 300 g"},
    "Pan Integral":             {"empaque_min": 0.500,  "unidad": "kg", "etiqueta": "bolsa 500 g (molde)"},
    "Pan Marraqueta":           {"empaque_min": 0.200,  "unidad": "kg", "etiqueta": "2 unidades ≈ 200 g"},
    "Papa Entera":              {"empaque_min": 1.000,  "unidad": "kg", "etiqueta": "bolsa 1 kg"},
    "Harina de Trigo":          {"empaque_min": 1.000,  "unidad": "kg", "etiqueta": "bolsa 1 kg"},
    "Tomate Entero":            {"empaque_min": 0.500,  "unidad": "kg", "etiqueta": "bolsa ≈ 3 unidades"},
    "Cebolla Entera":           {"empaque_min": 0.500,  "unidad": "kg", "etiqueta": "bolsa malla 500 g"},
    "Cebolla Morada":           {"empaque_min": 0.500,  "unidad": "kg", "etiqueta": "bolsa malla 500 g"},
    "Zanahoria Entera":         {"empaque_min": 0.500,  "unidad": "kg", "etiqueta": "bolsa 500 g"},
    "Ají Verde":                {"empaque_min": 0.100,  "unidad": "kg", "etiqueta": "bolsita 100 g"},
    "Pimiento Entero":          {"empaque_min": 0.200,  "unidad": "kg", "etiqueta": "unidad ≈ 200 g"},
    "Ulte Cocido":              {"empaque_min": 0.200,  "unidad": "kg", "etiqueta": "bandeja 200 g"},
    "Lapas Frescas":            {"empaque_min": 0.500,  "unidad": "kg", "etiqueta": "bandeja 500 g"},
    "Choritos Congelados o Frescos": {"empaque_min": 0.500, "unidad": "kg", "etiqueta": "bolsa 500 g"},
    "Filete de Pescado Magro":  {"empaque_min": 0.400,  "unidad": "kg", "etiqueta": "bandeja ≈ 400 g"},
    "Salmón Fresco":            {"empaque_min": 0.300,  "unidad": "kg", "etiqueta": "filete ≈ 300 g"},
    "Pechuga de Pollo":         {"empaque_min": 0.500,  "unidad": "kg", "etiqueta": "bandeja ≈ 500 g"},
    "Gelatina sin Sabor":       {"empaque_min": 0.007,  "unidad": "kg", "etiqueta": "sobre 7 g"},
    "Yogurt Natural":           {"empaque_min": 0.150,  "unidad": "kg", "etiqueta": "pote 150 g"},
    "Queso Mantecoso":          {"empaque_min": 0.200,  "unidad": "kg", "etiqueta": "trozo 200 g"},
    "Queso Rallado":            {"empaque_min": 0.100,  "unidad": "kg", "etiqueta": "bolsa 100 g"},
    "Quesillo Fresco":          {"empaque_min": 0.200,  "unidad": "kg", "etiqueta": "pote 200 g"},

    # --- VENDIDOS POR UNIDAD (precio/un) ---
    "Huevo":                    {"empaque_min": 6.000,  "unidad": "un", "etiqueta": "cartón 6 unidades"},
    "Cebollín Entero":          {"empaque_min": 1.000,  "unidad": "un", "etiqueta": "manojo"},
    "Coliflor Entera":          {"empaque_min": 1.000,  "unidad": "un", "etiqueta": "unidad"},
    "Berenjena Entera":         {"empaque_min": 1.000,  "unidad": "un", "etiqueta": "unidad"},
    "Zapallito Italiano Entero":{"empaque_min": 1.000,  "unidad": "un", "etiqueta": "unidad"},
    "Ajo Entero":               {"empaque_min": 1.000,  "unidad": "un", "etiqueta": "cabeza"},
    "Lechuga Entera":           {"empaque_min": 1.000,  "unidad": "un", "etiqueta": "unidad"},
    "Melón Entero":             {"empaque_min": 1.000,  "unidad": "un", "etiqueta": "unidad"},
    "Albahaca Fresca":          {"empaque_min": 1.000,  "unidad": "un", "etiqueta": "manojo"},
    "Atún en Conserva al Agua": {"empaque_min": 1.000,  "unidad": "un", "etiqueta": "lata 170 g"},
    "Jurel en Conserva":        {"empaque_min": 1.000,  "unidad": "un", "etiqueta": "lata 170 g"},
    "Tortilla de Trigo":        {"empaque_min": 1.000,  "unidad": "un", "etiqueta": "paquete"},
    "Piña en Conserva o Fresca":{"empaque_min": 1.000,  "unidad": "un", "etiqueta": "lata/unidad"},
    "Salsa de Tomate":          {"empaque_min": 1.000,  "unidad": "un", "etiqueta": "lata/tetra 210 ml"},
}


def _formatear_cantidad_compra(nombre: str, cant_neta: float, unidad_receta: str) -> dict:
    """
    Convierte la cantidad neta de receta al empaque comercial mínimo
    real del retail chileno. Siempre redondea hacia ARRIBA al múltiplo
    del empaque mínimo necesario para cubrir la receta.

    Ejemplo: necesito 0.24 kg de pan integral → vendo en bolsas de 500g
             → resultado: 1 bolsa (500 g)
    """
    empaque = EMPAQUES_MINIMOS_CL.get(nombre)

    if empaque is None:
        # Fallback genérico si el ingrediente no está en la tabla
        if unidad_receta == "un":
            return {"ingrediente": nombre, "cantidad": math.ceil(cant_neta), "unidad": "un", "etiqueta": "unidades"}
        elif unidad_receta == "ml":
            if cant_neta < 500:
                return {"ingrediente": nombre, "cantidad": 500, "unidad": "ml", "etiqueta": "envase 500 ml"}
            return {"ingrediente": nombre, "cantidad": round(cant_neta / 1000, 2), "unidad": "L", "etiqueta": "envase"}
        else:
            return {"ingrediente": nombre, "cantidad": max(0.200, round(cant_neta, 3)), "unidad": "kg", "etiqueta": "a granel"}

    emp_min = empaque["empaque_min"]
    unidad  = empaque["unidad"]
    etiq    = empaque["etiqueta"]

    # Convertir cant_neta a la misma unidad del empaque antes de comparar
    if unidad_receta == "ml" and unidad == "L":
        # receta en ml, empaque en litros
        cant_en_unidad_empaque = cant_neta / 1000.0
    elif unidad_receta == "ml" and unidad == "un":
        # receta en ml, empaque vendido como unidad (lata, tetra)
        ml_por_envase = ML_POR_UN.get(nombre, 200.0)
        cant_en_unidad_empaque = cant_neta / ml_por_envase
    elif unidad_receta == "un" and unidad == "kg":
        # receta en unidades, empaque por kg (tomate, cebolla, etc.)
        peso_kg = PESO_UN_EN_KG.get(nombre, 0.150)
        cant_en_unidad_empaque = cant_neta * peso_kg
    elif unidad_receta == "kg" and unidad == "un":
        # receta en kg, empaque por unidad (coliflor, manojo albahaca)
        peso_un = PESO_PROMEDIO_UN.get(nombre, 0.200)
        cant_en_unidad_empaque = cant_neta / peso_un
    else:
        # unidades idénticas (kg/kg, un/un, L/L)
        cant_en_unidad_empaque = cant_neta

    # Cuántos empaques mínimos necesito para cubrir la cantidad neta
    n_empaques = max(1, math.ceil(cant_en_unidad_empaque / emp_min))
    cantidad_compra = n_empaques * emp_min

    # Redondear para presentación limpia
    if unidad in ("L", "kg"):
        cantidad_compra = round(cantidad_compra, 3)
    else:
        cantidad_compra = int(cantidad_compra)

    return {
        "ingrediente": nombre,
        "cantidad":    cantidad_compra,
        "unidad":      unidad,
        "etiqueta":    etiq,
    }


# ---------------------------------------------------------------------------
# PUNTO DE ENTRADA PRINCIPAL
# ---------------------------------------------------------------------------

def optimizar_canasta(
    objetivo: str,
    user_lat: float,
    user_lng: float,
    periodo: str = "semana",
) -> dict:

    duracion_dias = 7 if periodo == "semana" else 30
    dias_nombres  = ["Lunes", "Martes", "Miércoles", "Jueves",
                     "Viernes", "Sábado", "Domingo"]

    # --- Carga de datos ---
    recetas   = cargar_recetas_por_objetivo(objetivo)
    precios   = cargar_precios()

    if not recetas:
        return {"error": f"No se encontraron recetas para el objetivo '{objetivo}'"}

    # --- MRP: explosión de materiales para el período ---
    requerimientos = calcular_requerimiento_materiales(recetas, duracion_dias)

    # --- Minuta semanal estructurada ---
    desayunos = [r for r in recetas if r.get("tipo_comida") == "Desayuno-Once"]
    almuerzos  = [r for r in recetas if r.get("tipo_comida") == "Almuerzo"]
    cenas      = [r for r in recetas if r.get("tipo_comida") == "Cena"]

    minuta = []
    for i, dia in enumerate(dias_nombres[:duracion_dias]):
        comidas = []
        if desayunos:
            d = desayunos[i % len(desayunos)]
            comidas.append({"tipo": "Desayuno-Once", "plato": d["nombre_receta"],
                            "prep": d["preparacion"], "t": d["tiempo_estimado_minutos"]})
        if almuerzos:
            a = almuerzos[i % len(almuerzos)]
            comidas.append({"tipo": "Almuerzo", "plato": a["nombre_receta"],
                            "prep": a["preparacion"], "t": a["tiempo_estimado_minutos"]})
        if cenas:
            c = cenas[i % len(cenas)]
            comidas.append({"tipo": "Cena", "plato": c["nombre_receta"],
                            "prep": c["preparacion"], "t": c["tiempo_estimado_minutos"]})
        minuta.append({"dia": dia, "comidas": comidas})

    # --- Lista de compras para el frontend (formato comercial) ---
    lista_compras = [
        _formatear_cantidad_compra(nombre, datos["cantidad"], datos["unidad"])
        for nombre, datos in requerimientos.items()
    ]

    # --- Costeo y comparativa por supermercado ---
    ALPHA = 0.7    # peso del costo monetario
    BETA  = 3500   # penalización por km² de distancia

    comparativa = []
    mejor_score = float("inf")
    recomendacion = None

    for tienda in SUPERMERCADOS_DB:
        distancia = calcular_haversine(user_lat, user_lng, tienda["lat"], tienda["lng"])
        costo, _  = calcular_costo_canasta(tienda["nombre"], requerimientos, precios)
        score     = (ALPHA * costo) + (BETA * (distancia ** 2))

        item = {
            "supermercado":            tienda["nombre"],
            "costo_mensual_estimado":  costo,
            "distancia_km":            distancia,
        }
        comparativa.append(item)

        if score < mejor_score:
            mejor_score    = score
            recomendacion  = item

    return {
        "minuta":        minuta,
        "comparativa":   comparativa,
        "recomendacion": recomendacion,
        "lista_compras": lista_compras,
    }