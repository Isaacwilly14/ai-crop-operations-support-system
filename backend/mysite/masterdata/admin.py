from django.contrib import admin
from .models import (
    Crop,
    CropSubGroup,
    GrowingGroup,
    Greenhouse,
    GreenhouseBed,
    Variety,
)


# ==========================
# Selecta Wagagai OSS Branding
# ==========================

admin.site.site_header = "Selecta Wagagai Production Smart Planning System"
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


# ==========================
# Growing Group Administration
# ==========================

@admin.register(GrowingGroup)
class GrowingGroupAdmin(admin.ModelAdmin):
    list_display = (
        "growing_group_code",
        "growing_group_name",
    )

    search_fields = (
        "growing_group_code",
        "growing_group_name",
    )

@admin.register(Greenhouse)
class GreenhouseAdmin(admin.ModelAdmin):
    list_display = (
        "greenhouse_code",
        "greenhouse_name",
    )

    search_fields = (
        "greenhouse_code",
        "greenhouse_name",
    )
@admin.register(GreenhouseBed)
class GreenhouseBedAdmin(admin.ModelAdmin):
    list_display = (
        "greenhouse",
        "side",
        "bed_no",
        "valve",
        "bay_no",
        "mother_plants",
        "control_valve",
    )

    list_filter = (
        "greenhouse",
        "side",
        "control_valve",
    )

    search_fields = (
        "bed_no",
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
        "growing_group",
    )

    search_fields = (
        "variety_code",
        "variety_name",
    )

    list_filter = (
        "subgroup",
        "growing_group",
    )