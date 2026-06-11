import math

# Coordenadas estáticas para la demo
SUPERMERCADOS_DB = [
    {"nombre": "Lider Cordillera", "lat": -33.5100, "lng": -70.5800, "factor_precio": 0.95},
    {"nombre": "Jumbo Bilbao", "lat": -33.4323, "lng": -70.5900, "factor_precio": 1.15},
    {"nombre": "Unimarc Los Leones", "lat": -33.4225, "lng": -70.6100, "factor_precio": 1.02}
]

def calcular_haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radio de la Tierra en km
    rad_lat1, rad_lon1 = math.radians(lat1), math.radians(lon1)
    rad_lat2, rad_lon2 = math.radians(lat2), math.radians(lon2)
    
    dlat = rad_lat2 - rad_lat1
    dlon = rad_lon2 - rad_lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def optimizar_canasta(objetivo, user_lat, user_lng):
    # Selección de minuta base
    if objetivo == "bajar_grasa":
        dieta = {
            "Desayuno": "Batido de Proteína (30g) + 50g de Avena Integral + 10g de Chía.",
            "Almuerzo": "200g de Pechuga de Pollo a la plancha + Ensalada verde mix libre.",
            "Merienda": "3 Huevos duros (solo 1 yema) + 1 Manzana verde.",
            "Cena": "150g de Merluza al horno + Brócoli al vapor."
        }
        costo_base = 110000
    else:
        dieta = {
            "Desayuno": "4 Huevos revueltos enteros + 2 Rebanadas de pan molde integral.",
            "Almuerzo": "250g de Carne molida de vacuno 5% + 150g de Arroz integral.",
            "Merienda": "Yogurt Griego natural + 40g de Nueces + 60g de Avena.",
            "Cena": "200g de Pechuga de Pollo + 200g de Puré de papas rústico."
        }
        costo_base = 145000

    comparativa = []
    mejor_score = float('inf')
    recomendacion = None
    
    ALPHA = 0.6
    BETA = 4000  # Penalización por distancia km^2
    
    for tienda in SUPERMERCADOS_DB:
        distancia = calcular_haversine(user_lat, user_lng, tienda["lat"], tienda["lng"])
        costo_estimado = int(costo_base * tienda["factor_precio"])
        
        # Fórmula Heurística
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