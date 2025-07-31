export default function load_map(containerId) {
    // Create MAP global namespace to store global variables
    window.MAP = window.MAP || {}; // || {} ensures that if the namespace already exists, it won't be overwritten
    window.MAP.markers = []; // Store markers globally
    
    // Define the map style with two raster sources: OSM (0-6) and OS (7-20)
    const style = {
      version: 8,
      sources: {
        "osm-tiles": {
          type: "raster",
          tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
          minzoom: 0,
          maxzoom: 7,
          tileSize: 256
        },
        "os-tiles": {
          type: "raster",
          tiles: ["/tiles/{z}/{x}/{y}.png"],
          minzoom: 8,
          maxzoom: 20,
          tileSize: 256
        }
      },
      layers: [
        {
          id: "osm-zxy",
          type: "raster",
          source: "osm-tiles",
          minzoom: 0,
          maxzoom: 7
        },
        {
          id: "os-maps-zxy",
          type: "raster",
          source: "os-tiles",
          minzoom: 6,
          maxzoom: 20
        }
      ]
    };
    // Initialize the map with custom attribution
    MAP.map = new maplibregl.Map({
      container: containerId,
      minZoom: 0,
      maxZoom: 20,
      style: style,
      center: [-3.2, 55.0], // UK center
      zoom: 4,
      // maxBounds: [
      //   [ -10.76418, 49.528423 ],
      //   [ 1.9134116, 61.331151 ]
      // ], // UK bounds
      attributionControl: false // disable default, we'll add our own
    });

    // Add MapLibre attribution control with custom attribution
    MAP.map.addControl(new maplibregl.AttributionControl({
      compact: true,
      customAttribution: [
        'Map data © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a>',
        'Tiles © <a href="https://www.ordnancesurvey.co.uk/" target="_blank" rel="noopener">Ordnance Survey</a>'
      ]
    }), 'bottom-right');


    // Print current zoom level in the console whenever it changes
    MAP.map.on('zoom', function() {
        console.log('Current zoom level:', MAP.map.getZoom());
    });

    // Add navigation control (zoom +/- and compass)
    const navControl = new maplibregl.NavigationControl({
      visualizePitch: false
    });
    MAP.map.addControl(navControl, 'top-right');

    // Add geolocation control to the map
    const geolocateControl = new maplibregl.GeolocateControl({
      positionOptions: {
        enableHighAccuracy: true
      },
      showAccuracyCircle: false,
    });
    MAP.map.addControl(geolocateControl);
}