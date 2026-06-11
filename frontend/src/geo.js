export let userCoords = { lat: -33.4126, lng: -70.6018 };

export function iniciarGeolocalizacion() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        userCoords.lat = pos.coords.latitude;
        userCoords.lng = pos.coords.longitude;
        console.log("Ubicación capturada con éxito:", userCoords);
      },
      (err) =>
        console.log(
          "Permiso de ubicación denegado, usando fallback de Santiago.",
        ),
    );
  }
}
