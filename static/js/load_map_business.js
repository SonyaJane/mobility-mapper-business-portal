export default function load_map_business(containerId, business) {
    const style = {
      version: 8,
      sources: {
        "raster-tiles": {
          type: "raster",
          tiles: ["/tiles/{z}/{x}/{y}.png"],
          tileSize: 256
        }
      },
      layers: [{
        id: "os-maps-zxy",
        type: "raster",
        source: "raster-tiles"
      }]
    };

    const map = new maplibregl.Map({
      container: containerId,
      style: style,
      center: [business.location.x, business.location.y],
      zoom: 14
    });

    new maplibregl.Marker()
      .setLngLat([business.location.x, business.location.y])
      .addTo(map);
}