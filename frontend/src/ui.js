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

  // 1. CORREGIDO: Renderizar la Minuta Completa (Múltiples comidas por bloque diario)
  const dietaContainer = document.getElementById("dieta-container");
  dietaContainer.innerHTML = "";

  if (data.minuta && data.minuta.length > 0) {
    data.minuta.forEach((diaData) => {
      let comidasHtml = "";
      diaData.comidas.forEach((c) => {
        comidasHtml += `
          <div class="mt-3 border-t border-slate-100 pt-2.5">
            <div class="flex justify-between items-center">
              <strong class="text-[11px] uppercase font-extrabold tracking-wide" style="color: #003b27;">${c.tipo}</strong>
              <span class="text-slate-400 text-xs font-semibold">⏱️ ${c.t} min</span>
            </div>
            <span class="text-slate-800 text-sm font-bold block mt-0.5">${c.plato}</span>
            <p class="text-slate-600 text-xs italic mt-1 bg-white p-2 rounded-lg border border-slate-200/60">${c.prep}</p>
          </div>
        `;
      });

      dietaContainer.innerHTML += `
        <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm mb-3">
            <span class="text-xs font-extrabold tracking-wider text-slate-400 uppercase block">${diaData.dia}</span>
            ${comidasHtml}
        </div>
      `;
    });
  }

  // 2. CORREGIDO: Renderizar Lista de Compras Real y Consolidada desde el Motor
  const listaContainer = document.getElementById("lista-compras-container");
  listaContainer.innerHTML = "";

  if (data.lista_compras && data.lista_compras.length > 0) {
    data.lista_compras.forEach((prod) => {
      const etiqueta = prod.etiqueta
        ? `<span class="text-[10px] text-slate-400 font-semibold uppercase tracking-wide mt-0.5 block">${prod.etiqueta}</span>`
        : "";
      listaContainer.innerHTML += `
        <label class="flex items-center gap-3 p-3 bg-slate-50 border border-slate-100 rounded-xl cursor-pointer hover:bg-slate-100 transition-all select-none">
          <input type="checkbox" class="w-4 h-4 rounded text-nutriDark focus:ring-nutriDark border-slate-300 flex-shrink-0">
          <div>
            <span class="text-xs text-slate-400 block uppercase font-bold tracking-tight">Comprar</span>
            <span class="text-sm font-bold text-slate-800">${prod.cantidad} ${prod.unidad} · ${prod.ingrediente}</span>
            ${etiqueta}
          </div>
        </label>
      `;
    });
  } else {
    listaContainer.innerHTML = `<p class="text-xs text-slate-400 p-2">No se encontraron ingredientes consolidados.</p>`;
  }

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
