// frontend/src/geo.js

// Coordenadas iniciales (Fallback en Las Condes, Santiago por si denegan el permiso)
export let userCoords = { lat: -33.4126, lng: -70.6018 };

export function iniciarGeolocalizacion() {
  if ("geolocation" in navigator) {
    // highAccuracy: true obliga al dispositivo a usar el GPS real y no solo la IP (más precisión)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        userCoords.lat = pos.coords.latitude;
        userCoords.lng = pos.coords.longitude;
        console.log(
          "📍 Ubicación real capturada:",
          userCoords.lat,
          userCoords.lng,
        );
      },
      (err) => {
        console.warn(
          "⚠️ Permiso denegado o error de GPS. Usando fallback de Santiago.",
          err.message,
        );
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  } else {
    console.log("El navegador no soporta geolocalización.");
  }
}
