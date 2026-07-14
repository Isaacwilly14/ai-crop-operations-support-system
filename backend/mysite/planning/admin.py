from django.contrib import admin

from .models import (
    ImportBatch,
    ImportedStickingPlanRow,
    StickingPlanHeader,
    StickingPlanLine,
    AllocationProposal,
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


@admin.register(StickingPlanLine)
class StickingPlanLineAdmin(admin.ModelAdmin):

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
        week = obj.sticking_week.split("-")[0]

        return (
            f"{obj.greenhouse.greenhouse_code}"
            f"/{week}"
            f"/{obj.reference[-3:]}"
        )

    @admin.display(description="Variety")
    def variety_display(self, obj):
        return obj.variety.variety_code
@admin.register(AllocationProposal)
class AllocationProposalAdmin(admin.ModelAdmin):

    list_display = (
        "sticking_plan_line",
        "greenhouse",
        "proposed_capacity",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
    )

    ordering = (
        "-created_at",
    )