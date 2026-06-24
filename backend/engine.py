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
    Consolida de manera exacta las necesidades brutas de la lista de compras.
    Simula una estructura balanceada diaria con múltiples comidas según el periodo.
    """
    consolidado_insumos = {}
    
    # Clasificamos las recetas disponibles por su momento del día
    desayunos = [r for r in recetas_seleccionadas if r.get("tipo_comida") == "Desayuno-Once"]
    almuerzos = [r for r in recetas_seleccionadas if r.get("tipo_comida") == "Almuerzo"]
    cenas = [r for r in recetas_seleccionadas if r.get("tipo_comida") == "Cena"]

    for i in range(duracion_dias):
        menu_dia = []
        if desayunos: menu_dia.append(desayunos[i % len(desayunos)])
        if almuerzos: menu_dia.append(almuerzos[i % len(almuerzos)])
        if cenas: menu_dia.append(cenas[i % len(cenas)])

        for receta in menu_dia:
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
    Calcula el costo real buscando por subcadenas e implementando 
    formatos comerciales de inventariado mínimo en pesos chilenos.
    """
    ruta_json = os.path.join(os.path.dirname(__file__), 'data', 'precios_productos.json')
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            datos_precios = json.load(f)
    except Exception:
        return 35000

    productos_tienda = datos_precios.get(nombre_tienda, [])
    costo_total = 0.0

    for nombre_ingrediente, datos in requerimientos_consolidados.items():
        cantidad_necesaria = datos["cantidad"]
        unidad_receta = datos["unidad"]
        
        # Búsqueda flexible por subcadena para hacer match con los nombres del catálogo
        prod_precio = next((p for p in productos_tienda if nombre_ingrediente.lower() in p.get("nombre", "").lower()), None)
        
        # Fallback genérico por categoría si la subcadena falla
        if not prod_precio:
            prod_precio = next((p for p in productos_tienda if p.get("categoria") in nombre_ingrediente.lower()), None)
            
        if not prod_precio:
            continue
            
        precio_catalogo = float(prod_precio["precio"])
        
        # --- LOGICA DE TRADUCCIÓN A FORMATOS COMERCIALES ---
        if unidad_receta == "un":
            unidades_reales = math.ceil(cantidad_necesaria)
            if prod_precio.get("unidad_venta") == "kg":
                costo_total += precio_catalogo * (unidades_reales * 0.150)
            else:
                costo_total += precio_catalogo * unidades_reales
                
        elif unidad_receta == "kg":
            if cantidad_necesaria < 0.200:
                costo_total += precio_catalogo * 0.200
            else:
                costo_total += precio_catalogo * cantidad_necesaria
                
        elif unidad_receta == "ml":
            litros = max(0.250, cantidad_necesaria / 1000.0)
            costo_total += precio_catalogo * litros

    return int(costo_total)

def optimizar_canasta(objetivo, user_lat, user_lng, periodo="semana"):
    recetas_filtradas = cargar_recetas_por_objetivo(objetivo)
    duracion_dias = 7 if periodo == "semana" else 30
    
    requerimientos_periodo = calcular_requerimiento_materiales(recetas_filtradas, duracion_dias)
    
    # Construcción estructurada diaria multi-comida (Desayuno, Almuerzo y Cena)
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    desayunos = [r for r in recetas_filtradas if r.get("tipo_comida") == "Desayuno-Once"]
    almuerzos = [r for r in recetas_filtradas if r.get("tipo_comida") == "Almuerzo"]
    cenas = [r for r in recetas_filtradas if r.get("tipo_comida") == "Cena"]
    
    minuta_semanal = []
    for i, dia in enumerate(dias_semana):
        if i < duracion_dias:
            comidas_del_dia = []
            if desayunos:
                d = desayunos[i % len(desayunos)]
                comidas_del_dia.append({"tipo": "Desayuno-Once", "plato": d["nombre_receta"], "prep": d["preparacion"], "t": d["tiempo_estimado_minutos"]})
            if almuerzos:
                a = almuerzos[i % len(almuerzos)]
                comidas_del_dia.append({"tipo": "Almuerzo", "plato": a["nombre_receta"], "prep": a["preparacion"], "t": a["tiempo_estimado_minutos"]})
            if cenas:
                c = cenas[i % len(cenas)]
                comidas_del_dia.append({"tipo": "Cena", "plato": c["nombre_receta"], "prep": c["preparacion"], "t": c["tiempo_estimado_minutos"]})
                
            minuta_semanal.append({
                "dia": dia,
                "comidas": comidas_del_dia
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
            "costo_mensual_estimado": costo_estimado,
            "distancia_km": distancia
        }
        comparativa.append(item)
        
        if score < mejor_score:
            mejor_score = score
            recomendacion = item
            
    # Formateo dinámico del consolidado de materiales para el checklist de UI
    lista_compras_limpia = []
    for k, v in requerimientos_periodo.items():
        cant = v["cantidad"]
        if v["unidad"] == "un":
            cant = math.ceil(cant)
        elif v["unidad"] == "kg":
            cant = round(cant, 2)
        else:
            cant = round(cant, 1)
            
        lista_compras_limpia.append({
            "ingrediente": k,
            "cantidad": cant,
            "unidad": v["unidad"]
        })
            
    return {
        "minuta": minuta_semanal, 
        "comparativa": comparativa, 
        "recomendacion": recomendacion,
        "lista_compras": lista_compras_limpia
    }