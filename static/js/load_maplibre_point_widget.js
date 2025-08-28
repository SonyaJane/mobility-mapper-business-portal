import load_map from "./load_map.js";

export default function load_maplibre_point_widget(containerId, widgetAttrsId) {
    document.addEventListener('DOMContentLoaded', function () {

        // Load the map into the specified container
        load_map(containerId)
        
        let marker;
        
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
            console.log(e);
            const lat = e.lngLat.lat
            const lng = e.lngLat.lng;
            setMarker([lng, lat], true);
        });



        MAP.map.on('load', () => {
            MAP.map.resize();  // critical!
        });
    });
}