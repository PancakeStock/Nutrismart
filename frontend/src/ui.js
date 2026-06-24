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

  // 1. CORREGIDO: Renderizar la Minuta Nutritiva (Lunes a Domingo)
  const dietaContainer = document.getElementById("dieta-container");
  dietaContainer.innerHTML = "";

  // Ahora leemos el arreglo ordenado enviado por el backend
  if (data.minuta && data.minuta.length > 0) {
    data.minuta.forEach((item) => {
      dietaContainer.innerHTML += `
        <div class="bg-slate-50 p-3 rounded-xl border border-slate-100 flex flex-col gap-1">
            <div class="flex justify-between items-center">
              <strong class="text-xs uppercase font-extrabold tracking-wide text-emerald-700">${item.dia} - ${item.tipo}</strong>
              <span class="text-xs text-slate-400 font-bold">${item.tiempo}</span>
            </div>
            <span class="text-slate-800 text-sm font-bold mt-0.5">${item.plato}</span>
            <p class="text-slate-600 text-xs italic mt-1 bg-white p-2 rounded-lg border border-slate-200/60">${item.preparacion}</p>
        </div>
      `;
    });
  }

  // 2. CORREGIDO: Renderizar Lista de Compras Dinámica y Real desde el Backend
  const listaContainer = document.getElementById("lista-compras-container");
  listaContainer.innerHTML = "";

  // Iteramos sobre la lista real que nos envía el motor unificado
  if (data.lista_compras && data.lista_compras.length > 0) {
    data.lista_compras.forEach((prod) => {
      listaContainer.innerHTML += `
        <label class="flex items-center gap-3 p-3 bg-slate-50 border border-slate-100 rounded-xl cursor-pointer hover:bg-slate-100 transition-all select-none">
          <input type="checkbox" class="w-4 h-4 rounded text-nutriDark focus:ring-nutriDark border-slate-300">
          <div>
            <span class="text-xs text-slate-400 block uppercase font-bold tracking-tight">Comprar</span>
            <span class="text-sm font-bold text-slate-800">${prod.cantidad} ${prod.unidad} de ${prod.ingrediente}</span>
          </div>
        </label>
      `;
    });
  } else {
    listaContainer.innerHTML = `<p class="text-xs text-slate-400 p-2">No se encontraron ingredientes para este plan.</p>`;
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
