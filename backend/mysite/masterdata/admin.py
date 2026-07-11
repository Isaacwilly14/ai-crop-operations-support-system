from django.contrib import admin
from .models import (
    Crop,
    CropSubGroup,
    GrowingGroup,
    Greenhouse,
    GreenhouseBed,
    Variety,
    ProductionAllocation,
)


# ==========================================================
# Selecta Wagagai OSS Branding
# ==========================================================

admin.site.site_header = "Selecta Wagagai Production Smart Planning System"
admin.site.site_title = "Selecta Wagagai OSS"
admin.site.index_title = "Operations Support System"


# ==========================================================
# Crop Administration
# ==========================================================

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


# ==========================================================
# Crop Sub Group Administration
# ==========================================================

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


# ==========================================================
# Growing Group Administration
# ==========================================================

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


# ==========================================================
# Greenhouse Administration
# ==========================================================

@admin.register(Greenhouse)
class GreenhouseAdmin(admin.ModelAdmin):
    list_display = (
        "greenhouse_code",
        "greenhouse_name",
        "total_capacity",
        "occupied_capacity",
        "available_capacity",
        "utilization_percentage",
        "occupied_beds",
        "available_beds",
        "active_varieties",
    )

    search_fields = (
        "greenhouse_code",
        "greenhouse_name",
    )


# ==========================================================
# Greenhouse Bed Administration
# ==========================================================

@admin.register(GreenhouseBed)
class GreenhouseBedAdmin(admin.ModelAdmin):
    list_display = (
        "greenhouse",
        "side",
        "bed_no",
        "mother_plants",
        "occupied_capacity",
        "available_capacity",
        "utilization_percentage",
        "occupancy_details",
        "is_empty",
        "is_full",
    )

    list_filter = (
        "greenhouse",
        "side",
        "control_valve",
    )

    search_fields = (
        "bed_no",
    )

    ordering = (
        "greenhouse",
        "side",
        "bed_no",
    )
# ==========================================================
# Variety Administration
# ==========================================================

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


# ==========================================================
# Production Allocation Administration
# ==========================================================

@admin.register(ProductionAllocation)
class ProductionAllocationAdmin(admin.ModelAdmin):

    list_display = (
        "allocation_reference",
        "variety",
        "greenhouse_bed",
        "quantity",
        "start_date",
        "end_date",
        "status",
        "manual_override",
    )

    list_filter = (
        "status",
        "variety",
        "greenhouse_bed",
    )

    search_fields = (
        "allocation_reference",
        "notes",
    )

    actions = (
        "mark_in_production",
        "mark_out_of_production",
    )

    @admin.action(
        description="Mark selected allocations as In Production"
    )
    def mark_in_production(self, request, queryset):
        queryset.update(
            status="IN_PRODUCTION"
        )

    @admin.action(
        description="Mark selected allocations as Out Of Production"
    )
    def mark_out_of_production(self, request, queryset):
        queryset.update(
            status="OUT_OF_PRODUCTION"
        )