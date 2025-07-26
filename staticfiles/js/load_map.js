export default function load_map(containerId) {
    // Create MAP global namespace to store global variables
    window.MAP = window.MAP || {}; // || {} ensures that if the namespace already exists, it won't be overwritten
    window.MAP.markers = []; // Store markers globally
    
    // Define the map style
    const style = {
      version: 8,
      sources: {
        "raster-tiles": {
          type: "raster",
          tiles: ["/tiles/{z}/{x}/{y}.png"],
          minzoom: 7,
          maxzoom: 20,
          tileSize: 256
        }
      },
      layers: [{
        id: "os-maps-zxy",
        type: "raster",
        source: "raster-tiles"
      }]
    };
    // Initialize the map
    MAP.map = new maplibregl.Map({
      container: containerId,
      minZoom: 7,
      maxZoom: 20,
      style: style,
      center: [-3.2, 55.0], // UK center
      zoom: 7,
      maxBounds: [
            [ -10.76418, 49.528423 ],
            [ 1.9134116, 61.331151 ]
        ], // UK bounds
    });

    // add geolocation control to the map
    const geolocateControl = new maplibregl.GeolocateControl({
        positionOptions: {
            enableHighAccuracy: true
        },        
        showAccuracyCircle: false,
    });
    MAP.map.addControl(geolocateControl);
}