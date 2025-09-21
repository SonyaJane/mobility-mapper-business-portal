/**
 * load_map.js
 *
 * Exports a function to initialise and display a MapLibre map for the accessible business search page.
 * - Sets up a hybrid raster tile map style using Maptiler (zoom 0-7) and Ordnance Survey tiles (zoom 8-20).
 * - Initialises the map centered on the UK with custom attribution and navigation controls.
 * - Dynamically manages map bounds based on zoom level (world for OSM, UK for OS).
 * - Adds geolocation and custom attribution controls.
 * - Removes the loading overlay once the map is ready.
 * - Stores the map and markers in a global MAP namespace for use by other scripts.
 */

export default function load_map(containerId) {
    // Create MAP global namespace to store global variables
    window.MAP = window.MAP || {}; // || {} ensures that if the namespace already exists, it won't be overwritten
    window.MAP.markers = []; // Store markers globally
    
    // Define the map style with two raster sources: Maptiler (1-6) and OS (7-20)
    const style = {
      version: 8,
      sources: {
        "maptiler": {
          type: "raster",
          tiles: [`https://api.maptiler.com/maps/streets-v2/256/{z}/{x}/{y}.png?key=cCcGqLo0AembUVq7bScM`],
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
          id: "maptiler-zxy",
          type: "raster",
          source: "maptiler",
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
    // Initialise the map with custom attribution
    MAP.map = new maplibregl.Map({
      container: containerId,
      minZoom: 0,
      maxZoom: 20,
      style: style,
      center: [-4.350224, 54.272122], // UK center
      zoom: 4,
      // manage bounds dynamically based on zoom
      attributionControl: false // disable default, we'll add our own
    });
     // Once the map has initialised and finished loading tiles, remove the loading overlay
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
    const mapTilerBounds = [[-13, 44], [4, 63]];
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