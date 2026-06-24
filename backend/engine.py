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

def calcular_requerimiento_materiales(recetas_seleccionadas, duracion_dias=7):
    """
    Consolida de manera exacta las necesidades brutas de la lista de compras 
    agrupadas por ingrediente específico, escalándolas por los días del período.
    """
    consolidado_insumos = {}
    
    # Suponiendo que repetimos el set de recetas seleccionadas cíclicamente para cubrir los días
    num_recetas = len(recetas_seleccionadas)
    if num_recetas == 0:
        return {}
        
    for i in range(duracion_dias):
        # Rotación de menús simulada para la composición de la canasta
        receta = recetas_seleccionadas[i % num_recetas]
        for ing in receta.get("ingredientes", []):
            nombre = ing.get("nombre_comercial")
            cantidad = float(ing.get("cantidad_numerica", 0))
            unidad = ing.get("unidad_medida", "kg")
            
            if nombre not in consolidado_insumos:
                consolidado_insumos[nombre] = {"cantidad": 0.0, "unidad": unidad}
            
            consolidado_insumos[nombre]["cantidad"] += cantidad
            
    return consolidado_insumos

def calcular_requerimiento_materiales(recetas_seleccionadas, duracion_dias=7):
    """
    Consolida de manera exacta las necesidades brutas de la lista de compras 
    agrupadas por ingrediente específico, escalándolas por los días del período.
    """
    consolidado_insumos = {}
    
    # Suponiendo que repetimos el set de recetas seleccionadas cíclicamente para cubrir los días
    num_recetas = len(recetas_seleccionadas)
    if num_recetas == 0:
        return {}
        
    for i in range(duracion_dias):
        # Rotación de menús simulada para la composición de la canasta
        receta = recetas_seleccionadas[i % num_recetas]
        for ing in receta.get("ingredientes", []):
            nombre = ing.get("nombre_comercial")
            cantidad = float(ing.get("cantidad_numerica", 0))
            unidad = ing.get("unidad_medida", "kg")
            
            if nombre not in consolidado_insumos:
                consolidado_insumos[nombre] = {"cantidad": 0.0, "unidad": unidad}
            
            consolidado_insumos[nombre]["cantidad"] += cantidad
            
    return consolidado_insumos

def calcular_costo_canasta_real(nombre_tienda, requerimientos_consolidados):
    """
    Toma los requerimientos por producto y calcula el costo proporcional 
    exacto basándose en las unidades de medida reales del catálogo de precios.
    """
    ruta_json = os.path.join(os.path.dirname(__file__), 'data', 'precios_productos.json')
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            datos_precios = json.load(f)
    except Exception:
        return 35000 # Fallback robusto en pesos chilenos

    productos_tienda = datos_precios.get(nombre_tienda, [])
    costo_total = 0.0

    for nombre_ingrediente, datos in requerimientos_consolidados.items():
        cantidad_necesaria = datos["cantidad"]
        unidad_receta = datos["unidad"]
        
        # Búsqueda difusa o exacta en la matriz de precios del supermercado
        prod_precio = next((p for p in productos_tienda if p.get("nombre") == nombre_ingrediente), None)
        
        # Si no está exacto, buscamos por categoría coincidente
        if not prod_precio:
            prod_precio = next((p for p in productos_tienda if p.get("categoria") in nombre_ingrediente.lower()), None)
            
        if not prod_precio:
            continue # Si no hay precio, no se suma (o se asume un costo base mínimo)
            
        precio_catalogo = float(prod_precio["precio"])
        
        # --- LÓGICA DE TRADUCCIÓN DE UNIDADES ---
        if unidad_receta == "kg":
            # Ya está en kg en tu JSON, multiplicación directa por el precio por kilo
            costo_total += precio_catalogo * cantidad_necesaria
        elif unidad_receta == "ml":
            # El aceite/salsas suelen tasarse por Litro (1000 ml) en el catálogo de precios
            costo_total += (precio_catalogo * (cantidad_necesaria / 1000.0))
        elif unidad_receta == "un":
            # Si el precio del JSON es por unidad (ej: un huevo) se multiplica directo. 
            # Si el precio es por kilo (ej: cebollas), asumimos un peso promedio por unidad (0.15 kg)
            if prod_precio.get("unidad_venta") == "kg":
                peso_estimado_kg = cantidad_necesaria * 0.150 
                costo_total += precio_catalogo * peso_estimado_kg
            else:
                costo_total += precio_catalogo * cantidad_necesaria

    return int(costo_total)

def optimizar_canasta(objetivo, user_lat, user_lng, periodo="semana"):
    recetas_filtradas = cargar_recetas_por_objetivo(objetivo)
    duracion_dias = 7 if periodo == "semana" else 30
    
    # 1. Obtener la demanda acumulada exacta usando la nueva función reestructurada
    requerimientos_periodo = calcular_requerimiento_materiales(recetas_filtradas, duracion_dias)
    
    # 2. Construcción dinámica del plan semanal (Lunes a Domingo) para la interfaz de Junaeb/INTA
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    minuta_semanal = []
    
    for idx, dia in enumerate(dias_semana):
        if idx < duracion_dias:
            # Selecciona una receta de manera rotativa para simular la minuta variada
            receta_dia = recetas_filtradas[idx % len(recetas_filtradas)] if recetas_filtradas else {}
            minuta_semanal.append({
                "dia": dia,
                "plato": receta_dia.get("nombre_receta", "Guiso Saludable INTA"),
                "tipo": receta_dia.get("tipo_comida", "Almuerzo"),
                "tiempo": f"⏱️ {receta_dia.get('tiempo_estimado_minutos')} min",
                "preparacion": receta_dia.get("preparacion", "")
            })

    comparativa = []
    mejor_score = float('inf')
    recomendacion = None
    
    ALPHA = 0.7   
    BETA = 3500   

    for tienda in SUPERMERCADOS_DB:
        distancia = calcular_haversine(user_lat, user_lng, tienda["lat"], tienda["lng"])
        costo_estimado = calcular_costo_canasta_real(tienda["nombre"], requerimientos_periodo)
        
        score = (ALPHA * costo_estimado) + (BETA * (distancia ** 2))
        
        item = {
            "supermercado": tienda["nombre"],
            "costo_mensual_estimado": costo_estimado, # Mantenemos key por compatibilidad con api.js
            "distancia_km": distancia
        }
        comparativa.append(item)
        
        if score < mejor_score:
            mejor_score = score
            recomendacion = item
            
    # Adjuntamos también la lista de compras consolidada limpia para el Checklist del frontend
    lista_compras_limpia = [
        {"ingrediente": k, "cantidad": round(v["cantidad"], 3), "unidad": v["unidad"]}
        for k, v in requerimientos_periodo.items()
    ]
            
    return {
        "minuta": minuta_semanal, 
        "comparativa": comparativa, 
        "recomendacion": recomendacion,
        "lista_compras": lista_compras_limpia
    }