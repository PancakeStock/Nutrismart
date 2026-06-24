import os
import json
import math

# Coordenadas reales de sucursales cercanas a la UAI Peñalolén
SUPERMERCADOS_DB = [
    {"nombre": "Jumbo Paseo Los Dominicos", "lat": -33.4111, "lng": -70.5218},
    {"nombre": "Lider Expres de Grecia", "lat": -33.4764, "lng": -70.5482},
    {"nombre": "Unimarc Príncipe de Gales", "lat": -33.4389, "lng": -70.5510}
]

def calcular_haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    rad_lat1, rad_lon1 = math.radians(lat1), math.radians(lon1)
    rad_lat2, rad_lon2 = math.radians(lat2), math.radians(lon2)
    dlat = rad_lat2 - rad_lat1
    dlon = rad_lon2 - rad_lon1
    a = math.sin(dlat / 2)**2 + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def cargar_recetas_por_objetivo(objetivo):
    """Carga dinámicamente el JSON extraído y filtrado por el INTA"""
    ruta_recetas = os.path.join(os.path.dirname(__file__), 'data', 'recetas.json')
    try:
        with open(ruta_recetas, 'r', encoding='utf-8') as f:
            todas_las_recetas = json.load(f)
        return [r for r in todas_las_recetas if r.get("objetivo") == objetivo]
    except Exception as e:
        print(f"Error cargando recetas.json: {e}")
        return []

def calcular_requerimiento_materiales(recetas, duracion_dias=7):
    """Suma los ingredientes diarios de las recetas y los escala por la cantidad de días"""
    totales_insumos = {"proteina": 0, "carbohidrato": 0, "huevos_unidades": 0}
    
    for receta in recetas:
        for ing in receta.get("ingredientes", []):
            macro = ing.get("categoria_macro")
            cantidad = float(ing.get("cantidad_numerica", 0))
            if macro in totales_insumos:
                totales_insumos[macro] += cantidad
                
    # Retornamos el consumo total neto acumulado para el periodo elegido (semana o mes)
    return {
        "proteina": totales_insumos["proteina"] * duracion_dias,
        "carbohidrato": totales_insumos["carbohidrato"] * duracion_dias,
        "huevos_unidades": totales_insumos["huevos_unidades"] * duracion_dias
    }

def calcular_costo_canasta_real(nombre_tienda, requerimientos):
    """
    Toma el requerimiento neto (en gramos y unidades) y calcula el costo proporcional 
    basándose en el precio de empaque por kilo/unidad base del JSON de precios.
    """
    ruta_json = os.path.join(os.path.dirname(__file__), 'data', 'precios_productos.json')
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            datos_precios = json.load(f)
    except Exception:
        return 45000 # Fallback básico preventivo ante eventos catastróficos

    productos_tienda = datos_precios.get(nombre_tienda, [])
    costo_total = 0.0

    for cat, cantidad_necesaria in requerimientos.items():
        # Encontrar el producto correspondiente a la categoría macro
        prod = next((p for p in productos_tienda if p.get("categoria") == cat), None)
        if not prod:
            continue
            
        precio_comercial_base = float(prod["precio"])
        
        # --- EXPLOSIÓN Y CONVERSIÓN DE MATERIALES (MRP) ---
        if cat in ["proteina", "carbohidrato"]:
            # Convertimos gramos de consumo neto acumulado a Kilogramos de compra
            cantidad_en_kilos = cantidad_necesaria / 1000.0
            costo_total += precio_comercial_base * cantidad_en_kilos
        elif cat == "huevos_unidades":
            # Los huevos ya vienen en unidades físicas unitarias
            costo_total += precio_comercial_base * cantidad_necesaria

    return int(costo_total)

def optimizar_canasta(objetivo, user_lat, user_lng, periodo="semana"):
    recetas_filtradas = cargar_recetas_por_objetivo(objetivo)
    
    # Determinamos la duración del plan solicitado por la interfaz
    duracion_dias = 7 if periodo == "semana" else 30
    
    # 1. Obtener la demanda acumulada (MRP)
    requerimientos_periodo = calcular_requerimiento_materiales(recetas_filtradas, duracion_dias)
    
    # 2. Formatear la minuta detallada con los tiempos de cocción de los libros
    dieta = {}
    for r in recetas_filtradas:
        comida_tipo = r.get("tipo_comida", "Almuerzo")
        dieta[comida_tipo] = f"⏱️ {r.get('tiempo_estimado_minutos')} min | {r.get('nombre_receta')}: {r.get('preparacion')}"

    comparativa = []
    mejor_score = float('inf')
    recomendacion = None
    
    ALPHA = 0.7   
    BETA = 3500   

    for tienda in SUPERMERCADOS_DB:
        distancia = calcular_haversine(user_lat, user_lng, tienda["lat"], tienda["lng"])
        
        # 3. Aplicar regla proporcional contra los precios estandarizados
        costo_estimado = calcular_costo_canasta_real(tienda["nombre"], requerimientos_periodo)
        
        score = (ALPHA * costo_estimado) + (BETA * (distancia ** 2))
        
        item = {
            "supermercado": tienda["nombre"],
            "costo_mensual_estimado": costo_estimado, # Mantenemos la llave para compatibilidad UI anterior
            "distancia_km": distancia
        }
        comparativa.append(item)
        
        if score < mejor_score:
            mejor_score = score
            recomendacion = item
            
    return {"dieta": dieta, "comparativa": comparativa, "recomendacion": recomendacion}