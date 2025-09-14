export default function load_map(containerId) {
    // Create MAP global namespace to store global variables
    window.MAP = window.MAP || {}; // || {} ensures that if the namespace already exists, it won't be overwritten
    window.MAP.markers = []; // Store markers globally
    
    // Define the map style with two raster sources: Maptiler (1-6) and OS (7-20)
    const style = {
      version: 8,
      sources: {
        "basemap": {
          type: "raster",
          tiles: [`https://api.maptiler.com/maps/streets-v2/256/{z}/{x}/{y}.png?key=cCcGqLo0AembUVq7bScM`],
          minzoom: 1,
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
          id: "basemap-zxy",
          type: "raster",
          source: "basemap",
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
     // Once the map has initialized and finished loading tiles, remove the loading overlay
     function hideMapLoading() {
       const loadingEl = document.getElementById('map-loading');
       if (loadingEl) {
         loadingEl.remove();
       }
     }
     // Remove overlay on initial style load and when the map becomes idle
     MAP.map.on('load', hideMapLoading);
     MAP.map.on('idle', hideMapLoading);

    // Add MapLibre attribution control with custom attribution
    MAP.map.addControl(new maplibregl.AttributionControl({
      compact: true,
      customAttribution: [
        "\u003ca href=\"https://www.maptiler.com/copyright/\" target=\"_blank\" rel=\"noopener\">OpenStreetMap contributors</a>",
        'Tiles © <a href="https://www.ordnancesurvey.co.uk/" target="_blank" rel="noopener">Ordnance Survey</a>'
      ]
    }), 'bottom-right');

    // Add navigation control (zoom +/- and compass)
    const navControl = new maplibregl.NavigationControl({
      visualizePitch: false
    });
    MAP.map.addControl(navControl, 'top-right');

    // Dynamic bounds: world for OSM tiles (<6), UK for OS tiles (>=6)
    const mapTilerBounds = [[-50, 10], [50, 80]];
    const osBounds = [[ -10.76418, 49.528423 ],[ 1.9134116, 61.331151 ]];
    // Set initial bounds
    MAP.map.setMaxBounds(MAP.map.getZoom() >= 6 ? osBounds : mapTilerBounds);
    MAP.map.on('zoomend', () => {
        if (MAP.map.getZoom() >= 6) {
            MAP.map.setMaxBounds(osBounds);
        } else {
            MAP.map.setMaxBounds(mapTilerBounds);
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

    let mapAttrb = document.querySelector('.maplibregl-ctrl-attrib');
    if (mapAttrb) {
        mapAttrb.classList.remove('maplibregl-compact-show');
    }
}