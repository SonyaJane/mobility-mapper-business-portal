from django.contrib import admin
from .models import Business

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'tier', 'category', 'is_approved', 'verified_by_wheelers')
    list_filter = ('tier', 'category', 'is_approved', 'verified_by_wheelers')
    search_fields = ('name', 'owner__email')
