export const statusDot = document.getElementById("status-dot");
export const statusText = document.getElementById("status-text");

export function actualizarEstadoConexion(estado) {
  if (estado === "online") {
    statusDot.className = "w-2.5 h-2.5 rounded-full bg-emerald-500";
    statusText.innerText = "Online";
    statusText.className = "text-xs font-bold text-emerald-400";
  } else {
    statusDot.className = "w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping";
    statusText.innerText = "Error de Servidor";
    statusText.className = "text-xs font-bold text-rose-500";
  }
}

export function renderizarResultados(data, periodo = "semana") {
  document.getElementById("no-data").classList.add("hidden");
  document.getElementById("results").classList.remove("hidden");

  // 1. Minuta del libro con preparación paso a paso
  const dietaContainer = document.getElementById("dieta-container");
  dietaContainer.innerHTML = "";
  Object.entries(data.dieta).forEach(([comida, detalle]) => {
    dietaContainer.innerHTML += `
      <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
          <strong class="text-xs uppercase block font-extrabold tracking-wide" style="color: #003b27;">${comida}</strong>
          <span class="text-slate-700 text-sm font-medium block mt-1">${detalle}</span>
      </div>
    `;
  });

  // 2. NUEVO: Renderizar Lista de Compras Dinámica con Checklist
  const listaContainer = document.getElementById("lista-compras-container");
  listaContainer.innerHTML = "";

  // Como nuestro motor escala proporcionalmente, mapeamos un estimado referencial para el checklist del usuario.
  // En una versión avanzada esto lee un diccionario de insumos neto, aquí automatizamos para la demo académica.
  const factorMultiplicador = periodo === "semana" ? 1 : 4.2;
  const esBajarGrasa =
    data.dieta.Almuerzo.includes("Criolla") ||
    data.dieta.Almuerzo.includes("Mexicana");

  const checklistItems = esBajarGrasa
    ? [
        {
          item: "Filete Pescado / Pollo",
          cant: (1.2 * factorMultiplicador).toFixed(1) + " kg",
        },
        {
          item: "Mix Verduras (Tomate/Zapallito)",
          cant: (2.5 * factorMultiplicador).toFixed(1) + " kg",
        },
        {
          item: "Huevos de Selección",
          cant: Math.ceil(7 * factorMultiplicador) + " un",
        },
      ]
    : [
        {
          item: "Carne Vacuno / Pollo",
          cant: (1.8 * factorMultiplicador).toFixed(1) + " kg",
        },
        {
          item: "Carbohidratos (Papas/Pan/Arroz)",
          cant: (3.2 * factorMultiplicador).toFixed(1) + " kg",
        },
        {
          item: "Huevos de Selección",
          cant: Math.ceil(12 * factorMultiplicador) + " un",
        },
      ];

  checklistItems.forEach((prod) => {
    listaContainer.innerHTML += `
      <label class="flex items-center gap-3 p-3 bg-slate-50 border border-slate-100 rounded-xl cursor-pointer hover:bg-slate-100 transition-all select-none">
        <input type="checkbox" class="w-4 h-4 rounded text-nutriDark focus:ring-nutriDark border-slate-300">
        <div>
          <span class="text-xs text-slate-400 block uppercase font-bold tracking-tight">Comprar</span>
          <span class="text-sm font-bold text-slate-800">${prod.cant} de ${prod.item}</span>
        </div>
      </label>
    `;
  });

  // 3. Tabla Comparativa
  const tablaBody = document.getElementById("tabla-body");
  tablaBody.innerHTML = "";
  data.comparativa.forEach((item) => {
    const esGanador = item.supermercado === data.recomendacion.supermercado;
    tablaBody.innerHTML += `
      <tr class="${esGanador ? "bg-emerald-50/50 text-emerald-900 font-bold" : ""}">
          <td class="py-3 px-2 flex items-center gap-2">
              ${esGanador ? "✅" : "🏢"} ${item.supermercado}
          </td>
          <td class="py-3 text-right text-slate-900 font-bold px-2">
              $${item.costo_mensual_estimado.toLocaleString("es-CL")}
          </td>
          <td class="py-3 text-right text-slate-500 px-2">
              ${item.distancia_km} km
          </td>
      </tr>
    `;
  });

  // 4. Tarjeta destacada del ganador
  const textoPeriodo = periodo === "semana" ? "semanal" : "mensual";
  document.getElementById("ganador-text").innerHTML = `
    Conviene comprar en <strong style="color: #003b27;">${data.recomendacion.supermercado}</strong>.
    El gasto ${textoPeriodo} proporcional será de <strong>$${data.recomendacion.costo_mensual_estimado.toLocaleString("es-CL")}</strong>
    estando a solo <strong>${data.recomendacion.distancia_km} km</strong> de tu ubicación actual en Peñalolén.
  `;
}
