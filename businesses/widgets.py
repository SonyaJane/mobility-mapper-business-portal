from django import forms
from django.conf import settings
from django.forms.widgets import TextInput


class MapLibrePointWidget(forms.TextInput):
    """A custom widget for rendering a point on a MapLibre map
    This widget does three things:
    Tells Django to load the MapLibre CSS/JS.
    Uses the custom HTML template maplibre_point_widget.html 
    Passes the selected point back via value_from_datadict
    """
    template_name = "businesses/widgets/maplibre_point_widget.html"

    class Media:
        css = {
            'all': [
                'https://unpkg.com/maplibre-gl@5.6.1/dist/maplibre-gl.css',
            ]
        }
        js = [
            'https://unpkg.com/maplibre-gl@5.6.1/dist/maplibre-gl.js',
        ]
        
    def format_value(self, value):
        if value is None:
            return ''
        return str(value)

    def value_from_datadict(self, data, files, name):
        return data.get(name)
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['OS_MAPS_API_KEY'] = settings.OS_MAPS_API_KEY
        return context