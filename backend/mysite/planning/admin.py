from django.contrib import admin

from .models import (
    ImportBatch,
    ImportedStickingPlanRow,
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