from django.contrib import admin
from .models import Business

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'tier', 'category', 'is_verified')
    list_filter = ('tier', 'category', 'is_verified')
    search_fields = ('name', 'owner__email')
