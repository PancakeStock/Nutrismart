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

export function renderizarResultados(data) {
  document.getElementById("no-data").classList.add("hidden");
  document.getElementById("results").classList.remove("hidden");

  // 1. Minuta Semanal
  const dietaContainer = document.getElementById("dieta-container");
  dietaContainer.innerHTML = "";
  Object.entries(data.dieta).forEach(([comida, detalle]) => {
    dietaContainer.innerHTML += `
      <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
          <strong class="text-xs uppercase block font-extrabold tracking-wide" style="color: #003b27;">${comida}</strong>
          <span class="text-slate-700 text-sm font-semibold">${detalle}</span>
      </div>
    `;
  });

  // 2. Tabla Comparativa
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

  // 3. Tarjeta destacada del ganador
  document.getElementById("ganador-text").innerHTML = `
    Conviene comprar en <strong style="color: #003b27;">${data.recomendacion.supermercado}</strong>.
    El gasto mensual proporcional será de <strong>$${data.recomendacion.costo_mensual_estimado.toLocaleString("es-CL")}</strong>
    estando a solo <strong>${data.recomendacion.distancia_km} km</strong> de tu ubicación.
  `;
}
