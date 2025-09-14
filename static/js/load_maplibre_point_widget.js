import load_map from "./load_map.js";

export default function load_maplibre_point_widget(containerId, widgetAttrsId) {
    document.addEventListener('DOMContentLoaded', async function () {
        // Load the map into the specified container
        load_map(containerId);

        let marker;
        let ukBoundary = null;

        // Load UK boundary GeoJSON
        await fetch('/static/geojson/uk-boundary.geojson')
            .then(res => res.json())
            .then(data => { ukBoundary = data; });

        // Determine the UK polygon from the boundary data
        let ukPolygon = null;
        if (ukBoundary.type === "FeatureCollection") {
            ukPolygon = ukBoundary.features[0]; // or combine features if there are multiple
        } else if (ukBoundary.type === "Feature") {
            ukPolygon = ukBoundary;
        } else {
            ukPolygon = ukBoundary; // already a Polygon/MultiPolygon
        }

        // If a location value already exists, show marker and make it draggable, and center map
        const initial = document.getElementById(widgetAttrsId).value;

        if (initial) {
        // Support both 'SRID=4326;POINT (lng lat)' and 'POINT(lng lat)' formats
        let match = initial.match(/POINT ?\(([-\d.]+) ([-\d.]+)\)/);
        if (!match) {
            match = initial.match(/SRID=\d+;POINT ?\(([-\d.]+) ([-\d.]+)\)/);
        }
        if (match) {
            const lng = parseFloat(match[1]);
            const lat = parseFloat(match[2]);
            setMarker([lng, lat], true);
        }
        }

        // move or create map marker
        function setMarker(coords, centerMap = true) {
            if (marker) { // If marker already exists, just update its position
                marker.setLngLat(coords);
            } else { // If no marker exists, create a new one
                marker = new maplibregl.Marker({ draggable: true })
                .setLngLat(coords)
                .addTo(MAP.map);
                marker.on('dragend', () => {
                    const lngLat = marker.getLngLat();
                    document.getElementById(widgetAttrsId).value = `POINT(${lngLat.lng} ${lngLat.lat})`;
                    // Smooth pan to new center
                    MAP.map.easeTo({ center: [lngLat.lng, lngLat.lat], duration: 1000 });
                });
            }

            // Update the hidden input with the POINT format
            document.getElementById(widgetAttrsId).value = `POINT(${coords[0]} ${coords[1]})`;
            if (centerMap) {
                // Smoothly pan to coords
                MAP.map.setZoom(19);                
                MAP.map.easeTo({ center: coords, duration: 1000 });
            }
        }

        MAP.map.on('click', function (e) {
            const lat = e.lngLat.lat
            const lng = e.lngLat.lng;
            // Use Turf.js to check if point is inside UK boundary
            if (ukPolygon && turf.booleanPointInPolygon([lng, lat], ukPolygon)) {
                setMarker([lng, lat], true);
            }
        });

        MAP.map.on('load', () => {
            MAP.map.resize();  // critical!
        });
    });
}