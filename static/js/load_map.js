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
      center: [-4.350224, 54.272122], // UK center
      zoom: 4,
      // we'll manage bounds dynamically based on zoom
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

    // Add navigation control (zoom +/- and compass)
    const navControl = new maplibregl.NavigationControl({
      visualizePitch: false
    });
    MAP.map.addControl(navControl, 'top-right');

    // Dynamic bounds: world for OSM tiles (<6), UK for OS tiles (>=6)
    const osmBounds = [[-13, 44], [4, 63]];
    const osBounds = [[ -10.76418, 49.528423 ],[ 1.9134116, 61.331151 ]];
    // Set initial bounds
    MAP.map.setMaxBounds(MAP.map.getZoom() >= 6 ? osBounds : osmBounds);
    MAP.map.on('zoomend', () => {
        if (MAP.map.getZoom() >= 6) {
            MAP.map.setMaxBounds(osBounds);
        } else {
            MAP.map.setMaxBounds(osmBounds);
        }
    });

    // Add geolocation control to the map
    const geolocateControl = new maplibregl.GeolocateControl({
      positionOptions: {
        enableHighAccuracy: true
      },
      showAccuracyCircle: false,
    });
    MAP.map.addControl(geolocateControl);
}