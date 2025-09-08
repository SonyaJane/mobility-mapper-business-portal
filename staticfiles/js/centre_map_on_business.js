    // Center the map on the business marker and zoom in
    if (biz.location && MAP.map) {
        MAP.map.flyTo({ center: [biz.location.lng, biz.location.lat], zoom: 16 });
    }