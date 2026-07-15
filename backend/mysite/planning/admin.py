from django.contrib import admin

from .models import BufferHistory
from .models import (
    ImportBatch,
    ImportedStickingPlanRow,
    StickingPlanHeader,
    StickingPlanLine,
)

admin.site.register(
    BufferHistory
)


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):

    list_display = (
        "batch_reference",
        "file_name",
        "status",
        "imported_at",
    )

    search_fields = (
        "batch_reference",
        "file_name",
    )

    ordering = (
        "-imported_at",
    )


@admin.register(ImportedStickingPlanRow)
class ImportedStickingPlanRowAdmin(admin.ModelAdmin):

    list_display = (
        "import_batch",
        "row_number",
        "variety_code",
        "greenhouse_code",
        "sticking_week",
        "planned_quantity",
        "validation_status",
    )

    list_filter = (
        "validation_status",
        "greenhouse_code",
    )

    search_fields = (
        "variety_code",
        "greenhouse_code",
    )

    ordering = (
        "row_number",
    )


@admin.register(StickingPlanHeader)
class StickingPlanHeaderAdmin(admin.ModelAdmin):

    list_display = (
        "reference",
        "season",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "reference",
        "season",
    )

    ordering = (
        "-created_at",
    )


# FIX: Changed decorator argument from 'StickingPlanLineAdmin' to 'StickingPlanLine'
@admin.register(StickingPlanLine)
class StickingPlanLineAdmin(admin.ModelAdmin):

    # PERFORMANCE BOOST: Fetches foreign key relations in 1 query instead of N+1
    list_select_related = (
        "header",
        "variety",
        "greenhouse",
    )

    list_display = (
        "short_reference",
        "header",
        "variety_display",
        "greenhouse",
        "sticking_week",
        "sticking_monday",
        "planting_week",
        "planting_monday",
        "production_end_week",
        "planned_quantity",
        "urc_needed",
        "available_capacity",
        "exceeds_capacity",
        "status",
        "greenhouse_capacity",
        "greenhouse_planned_quantity",
        "remaining_capacity",
        "overbooked_quantity",
        "greenhouse_overbooked",
    )

    list_filter = (
        "greenhouse",
        "status",
        "sticking_week",
    )

    search_fields = (
        "reference",
        "variety__variety_code",
        "variety__variety_name",
        "greenhouse__greenhouse_code",
    )

    ordering = (
        "-created_at",
    )

    @admin.display(description="Ref")
    def short_reference(self, obj):
        # Fallback guard in case sticking_week or reference are empty
        if not obj.sticking_week or not obj.reference:
            return f"{obj.greenhouse.greenhouse_code}/--/---"

        week = obj.sticking_week.split("-")[0]

        return (
            f"{obj.greenhouse.greenhouse_code}"
            f"/{week}"
            f"/{obj.reference[-3:]}"
        )

    @admin.display(description="Variety")
    def variety_display(self, obj):
        return obj.variety.variety_code

    @admin.display(description="Capacity")
    def greenhouse_capacity(self, obj):
        return obj.greenhouse_capacity

    @admin.display(description="Planned")
    def greenhouse_planned_quantity(self, obj):
        return obj.greenhouse_planned_quantity

    @admin.display(description="Remaining")
    def remaining_capacity(self, obj):
        return obj.remaining_capacity

    @admin.display(description="Overbooked Qty")
    def overbooked_quantity(self, obj):
        return obj.overbooked_quantity

    @admin.display(boolean=True, description="Overbooked?")
    def greenhouse_overbooked(self, obj):
        return obj.greenhouse_overbooked

    @admin.display(boolean=True, description="Exceeds Capacity?")
    def exceeds_capacity(self, obj):
        return obj.exceeds_capacity