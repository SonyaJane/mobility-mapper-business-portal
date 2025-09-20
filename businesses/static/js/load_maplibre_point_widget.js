/**
 * load_maplibre_point_widget.js
 *
 * Exports a function to initialise a MapLibre map widget for selecting a geographic point.
 * - Loads the map into the specified container.
 * - Loads UK boundary GeoJSON and restricts marker placement to within the UK.
 * - Allows users to set or move a draggable marker by clicking on the map.
 * - Updates a hidden input with the selected POINT (longitude latitude) value.
 * - If an initial value exists, centers the map and places a marker at that location.
 * - Smoothly pans and zooms the map when a marker is set or moved.
 * - Ensures the map resizes correctly when loaded.
 */

import load_map from "./load_map.js";

/**
 * Initializes a MapLibre map widget for selecting a geographic point.
 * Loads the map, restricts marker placement to the UK, and updates the hidden input with the selected point.
 */
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

        // Determine the UK polygons from the boundary data
        let ukPolygons = [];
        if (ukBoundary.type === "FeatureCollection") {
            ukPolygons = ukBoundary.features;
        } else if (ukBoundary.type === "Feature") {
            ukPolygons = [ukBoundary];
        } else {
            ukPolygons = [ukBoundary]; // already a Polygon/MultiPolygon
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

        /**
         * Moves or creates the map marker at the given coordinates.
         * Updates the hidden input and optionally centers the map.
         */
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
            const lat = e.lngLat.lat;
            const lng = e.lngLat.lng;
            // Check if point is inside any UK polygon
            const insideUK = ukPolygons.some(feature =>
                turf.booleanPointInPolygon([lng, lat], feature)
            );
            if (insideUK) {
                setMarker([lng, lat], true);
            }
        });

        MAP.map.on('load', () => {
            MAP.map.resize();
        });
    });
}