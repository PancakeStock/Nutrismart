import { userCoords, iniciarGeolocalizacion } from "./geo.js";
import { actualizarEstadoConexion, renderizarResultados } from "./ui.js";

const API_URL = "https://nutrismart-backend-chqy.onrender.com";

iniciarGeolocalizacion();

fetch(`${API_URL}/api/health`)
  .then((res) => res.json())
  .then(() => actualizarEstadoConexion("online"))
  .catch(() => actualizarEstadoConexion("error"));

document.getElementById("diet-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const objetivo = document.getElementById("objetivo").value;
  const periodo = document.getElementById("periodo").value;
  const btn = e.target.querySelector("button");

  btn.innerText = "Calculando Ingeniería de Precios...";
  btn.disabled = true;

  try {
    const response = await fetch(`${API_URL}/api/planificar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        objetivo: objetivo,
        periodo: periodo,
        lat: userCoords.lat,
        lng: userCoords.lng,
      }),
    });

    const data = await response.json();
    renderizarResultados(data, periodo);
  } catch (err) {
    alert("Hubo un problema al conectar con el motor matemático en Render.");
  } finally {
    btn.innerText = "Optimizar Presupuesto";
    btn.disabled = false;
  }
});
