import os
import json
import math

SUPERMERCADOS_DB = [
    {"nombre": "Lider Cordillera", "lat": -33.5100, "lng": -70.5800},
    {"nombre": "Jumbo Bilbao", "lat": -33.4323, "lng": -70.5900},
    {"nombre": "Unimarc Los Leones", "lat": -33.4225, "lng": -70.6100}
]

# MATRIZ DE RECETAS (Extracción de libros de cocina con ingredientes diarios y preparación)
RECETAS_CONFIG = {
    "bajar_grasa": {
        "Desayuno": {
            "detalle": "Batido de Proteína con Avena Integral (Mezclar 30g de proteína con 50g de avena en licuadora con agua fría).",
            "ingredientes": {"proteina": 0.030, "carbohidrato": 0.050} # Unidades en kg
        },
        "Almuerzo": {
            "detalle": "Pechuga de Pollo a la plancha (Sellar 200g de pechuga en sartén caliente por 6 minutos por lado, servir con ensalada mix verde).",
            "ingredientes": {"proteina": 0.200}
        },
        "Merienda": {
            "detalle": "3 Huevos duros (Hervir en agua por 9 minutos, retirar la cáscara y consumir retirando dos de las yemas).",
            "ingredientes": {"huevos_unidades": 3}
        },
        "Cena": {
            "detalle": "Merluza al vapor con Brócoli (Cocinar 150g de filete junto a los árboles de brócoli en vaporera por 12 minutos con sal de mar).",
            "ingredientes": {"proteina": 0.150}
        }
    },
    "subir_masa": {
        "Desayuno": {
            "detalle": "Huevos Revueltos con Pan de Molde (Batir 4 huevos enteros, cocinar en sartén a fuego medio y acompañar con 2 rebanadas de pan tostado).",
            "ingredientes": {"huevos_unidades": 4, "carbohidrato": 0.080}
        },
        "Almuerzo": {
            "detalle": "Guiso de Vacuno con Arroz Integral (Sofreír 250g de carne molida, mezclar con 150g de arroz previamente grandeado).",
            "ingredientes": {"proteina": 0.250, "carbohidrato": 0.150}
        },
        "Merienda": {
            "detalle": "Bowl de Yogurt Griego Potenciado (Verter el yogurt natural en un tazón, sumar 40g de nueces picadas y 60g de avena integral).",
            "ingredientes": {"carbohidrato": 0.060}
        },
        "Cena": {
            "detalle": "Pollo Dorado con Puré Rústico (Asar 200g de pollo al horno, moler papas cocidas con su piel añadiendo un toque de leche de almendras).",
            "ingredientes": {"proteina": 0.200, "carbohidrato": 0.200}
        }
    }
}

def calcular_haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    rad_lat1, rad_lon1 = math.radians(lat1), math.radians(lon1)
    rad_lat2, rad_lon2 = math.radians(lat2), math.radians(lon2)
    dlat = rad_lat2 - rad_lat1
    dlon = rad_lon2 - rad_lon1
    a = math.sin(dlat / 2)**2 + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def calcular_requerimiento_mensual(objetivo):
    """Suma los gramajes diarios y calcula la necesidad neta para el mes completo"""
    comidas = RECETAS_CONFIG[objetivo]
    totales_diarios = {"proteina": 0, "carbohidrato": 0, "huevos_unidades": 0}
    
    for datos in comidas.values():
        for ing, cantidad in datos["ingredientes"].items():
            totales_diarios[ing] += cantidad
            
    # Retornamos los kilos o unidades requeridas multiplicando por 30 días
    return {
        "proteina": math.ceil(totales_diarios["proteina"] * 30),
        "carbohidrato": math.ceil(totales_diarios["carbohidrato"] * 30),
        "huevos_unidades": math.ceil(totales_diarios["huevos_unidades"] * 30)
    }

def calcular_costo_canasta_real(nombre_tienda, requerimientos):
    """Suma los costos reales de los productos necesarios basándose en el JSON"""
    ruta_json = os.path.join(os.path.dirname(__file__), 'data', 'precios_productos.json')
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            datos_precios = json.load(f)
    except Exception:
        return 120000 # Fallback preventivo

    productos_tienda = datos_precios.get(nombre_tienda, [])
    costo_total = 0

    for prod in productos_tienda:
        cat = prod.get("categoria")
        if cat in requerimientos:
            costo_total += prod["precio"] * requerimientos[cat]

    return int(costo_total)

def optimizar_canasta(objetivo, user_lat, user_lng):
    # 1. Obtener la demanda de insumos para el mes
    requerimientos_mes = calcular_requerimiento_mensual(objetivo)
    
    # 2. Formatear la minuta con sus instrucciones detalladas para el frontend
    dieta = {}
    for comida, datos in RECETAS_CONFIG[objetivo].items():
        dieta[comida] = datos["detalle"]

    comparativa = []
    mejor_score = float('inf')
    recomendacion = None
    
    ALPHA = 0.7   # Peso asignado a la economía
    BETA = 3500   # Penalización por lejanía geográfica

    for tienda in SUPERMERCADOS_DB:
        distancia = calcular_haversine(user_lat, user_lng, tienda["lat"], tienda["lng"])
        
        # 3. Calcular la cotización basándose en necesidades exactas de la receta
        costo_estimado = calcular_costo_canasta_real(tienda["nombre"], requerimientos_mes)
        
        # Heurística de selección
        score = (ALPHA * costo_estimado) + (BETA * (distancia ** 2))
        
        item = {
            "supermercado": tienda["nombre"],
            "costo_mensual_estimado": costo_estimado,
            "distancia_km": distancia
        }
        comparativa.append(item)
        
        if score < mejor_score:
            mejor_score = score
            recomendacion = item
            
    return {"dieta": dieta, "comparativa": comparativa, "recomendacion": recomendacion}