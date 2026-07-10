from django.contrib import admin
from .models import Crop, CropSubGroup, Variety


# ==========================
# Selecta Wagagai OSS Branding
# ==========================

admin.site.site_header = "Selecta Wagagai OSS System"
admin.site.site_title = "Selecta Wagagai OSS"
admin.site.index_title = "Operations Support System"


# ==========================
# Crop Administration
# ==========================

@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = (
        "crop_code",
        "crop_name",
    )

    search_fields = (
        "crop_code",
        "crop_name",
    )

    ordering = (
        "crop_name",
    )


# ==========================
# Crop Sub Group Administration
# ==========================

@admin.register(CropSubGroup)
class CropSubGroupAdmin(admin.ModelAdmin):
    list_display = (
        "subgroup_code",
        "subgroup_name",
        "crop",
    )

    search_fields = (
        "subgroup_code",
        "subgroup_name",
    )

    list_filter = (
        "crop",
    )

    ordering = (
        "subgroup_name",
    )


# ==========================
# Variety Administration
# ==========================

@admin.register(Variety)
class VarietyAdmin(admin.ModelAdmin):
    list_display = (
        "variety_code",
        "variety_name",
        "subgroup",
    )

    search_fields = (
        "variety_code",
        "variety_name",
    )

    list_filter = (
        "subgroup",
    )

    ordering = (
        "variety_name",
    )