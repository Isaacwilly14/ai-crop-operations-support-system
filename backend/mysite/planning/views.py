from django.shortcuts import (
    render,
    get_object_or_404,
)

import pandas as pd

from masterdata.models import (
    Variety,
    Greenhouse,
)

from .models import (
    ImportBatch,
    ImportedStickingPlanRow,
    StickingPlanHeader,
    StickingPlanLine,
)


def upload_sticking_plan(request):

    message = None

    if request.method == "POST":

        uploaded_file = request.FILES.get("file")

        if uploaded_file:

            batch = ImportBatch.objects.create(
                batch_reference=(
                    f"IMP-{ImportBatch.objects.count() + 1:03d}"
                ),
                file_name=uploaded_file.name,
                uploaded_file=uploaded_file,
            )

            try:

                df = pd.read_excel(
                    batch.uploaded_file.path
                )

                imported_rows = 0
                valid_rows = 0
                invalid_rows = 0

                for index, row in df.iterrows():

                    imported_row = (
                        ImportedStickingPlanRow.objects.create(
                            import_batch=batch,
                            row_number=index + 1,
                            variety_code=str(
                                row.get(
                                    "VarietyCode",
                                    ""
                                )
                            ).strip(),
                            variety_name=str(
                                row.get(
                                    "VarietyName",
                                    ""
                                )
                            ).strip(),
                            greenhouse_code=str(
                                row.get(
                                    "Greenhouse",
                                    ""
                                )
                            ).strip(),
                            sticking_week=str(
                                row.get(
                                    "StickingWeek",
                                    ""
                                )
                            ).strip(),
                            production_end_week=str(
                                row.get(
                                    "EndWeek",
                                    ""
                                )
                            ).strip(),
                            planned_quantity=int(
                                row.get(
                                    "Quantity",
                                    0
                                ) or 0
                            ),
                            urc_per_bag=int(
                                row.get(
                                    "URCPerBag",
                                    0
                                ) or 0
                            ),
                        )
                    )

                    imported_row.validate_row()

                    if (
                        imported_row.validation_status
                        == "VALID"
                    ):
                        valid_rows += 1
                    else:
                        invalid_rows += 1

                    imported_rows += 1

                message = (
                    f"Batch {batch.batch_reference} created. "
                    f"{imported_rows} rows imported. "
                    f"Valid: {valid_rows}. "
                    f"Invalid: {invalid_rows}."
                )

            except Exception as e:

                message = (
                    f"Import failed: {e}"
                )

    return render(
        request,
        "planning/upload_sticking_plan.html",
        {
            "message": message
        }
    )


def validation_errors(request):

    invalid_rows = (
        ImportedStickingPlanRow.objects.filter(
            validation_status="INVALID"
        )
        .order_by(
            "row_number"
        )
    )

    return render(
        request,
        "planning/validation_errors.html",
        {
            "invalid_rows": invalid_rows
        }
    )


def approve_batch(request, batch_id):

    batch = get_object_or_404(
        ImportBatch,
        id=batch_id
    )

    valid_rows = (
        ImportedStickingPlanRow.objects.filter(
            import_batch=batch,
            validation_status="VALID"
        )
    )

    header = StickingPlanHeader.objects.create(
        season="Imported Plan"
    )

    created_lines = 0

    for row in valid_rows:

        try:

            variety = Variety.objects.get(
                variety_code=row.variety_code
            )

            greenhouse = Greenhouse.objects.get(
                greenhouse_code=row.greenhouse_code
            )

            StickingPlanLine.objects.create(
                header=header,
                variety=variety,
                greenhouse=greenhouse,
                sticking_week=row.sticking_week,
                production_end_week=row.production_end_week,
                planned_quantity=row.planned_quantity,
                urc_per_bag=row.urc_per_bag,
            )

            created_lines += 1

        except Exception:
            continue

    batch.status = "IMPORTED"
    batch.save()

    return render(
        request,
        "planning/batch_approved.html",
        {
            "batch": batch,
            "header": header,
            "created_lines": created_lines,
        }
    )