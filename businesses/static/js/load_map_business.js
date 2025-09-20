/**
 * load_map_business.js
 *
 * Exports a function to initialize and display a MapLibre map for a single business.
 * - Sets up a raster tile map style.
 * - Centers the map on the business location.
 * - Adds a marker at the business location.
 */

export default function load_map_business(containerId, business) {
    const style = {
      version: 8,
      sources: {
        "raster-tiles": {
          type: "raster",
          tiles: ["/tiles/{z}/{x}/{y}.png"],
          tileSize: 256,          
          minzoom: 8,
          maxzoom: 20,
        }
      },
      layers: [{
        id: "os-maps-zxy",
        type: "raster",
        source: "raster-tiles",
        minzoom: 8,
        maxzoom: 20
      }]
    };

    const map = new maplibregl.Map({
      container: containerId,
      style: style,
      center: [business.location.x, business.location.y],
      zoom: 14,
      minzoom: 8,
      maxZoom: 20
    });

    new maplibregl.Marker()
      .setLngLat([business.location.x, business.location.y])
      .addTo(map);
}