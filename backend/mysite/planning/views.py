from django.db import models

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
    AllocationProposal,
    BedAllocation,
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


def batch_list(request):

    batches = (
        ImportBatch.objects.all()
        .order_by("-imported_at")
    )

    return render(
        request,
        "planning/batch_list.html",
        {
            "batches": batches
        }
    )

def dashboard(request):

    total_batches = (
        ImportBatch.objects.count()
    )

    total_rows = (
        ImportedStickingPlanRow.objects.count()
    )

    valid_rows = (
        ImportedStickingPlanRow.objects.filter(
            validation_status="VALID"
        ).count()
    )

    invalid_rows = (
        ImportedStickingPlanRow.objects.filter(
            validation_status="INVALID"
        ).count()
    )

    sticking_plans = (
        StickingPlanLine.objects.count()
    )

    greenhouse_status = []

    for greenhouse in Greenhouse.objects.all():

        planned_quantity = (
            StickingPlanLine.objects.filter(
                greenhouse=greenhouse
            )
            .aggregate(
                total=models.Sum(
                    "planned_quantity"
                )
            )["total"]
            or 0
        )

        capacity = greenhouse.total_capacity

        remaining = (
            capacity -
            planned_quantity
        )

        utilization = 0

        if capacity > 0:

            utilization = round(
                (
                    planned_quantity
                    / capacity
                ) * 100,
                2
            )

        if utilization >= 100:
            status = "OVERBOOKED"

        elif utilization >= 90:
            status = "WARNING"

        else:
            status = "SAFE"

        greenhouse_status.append(
            {
                "greenhouse": greenhouse,
                "capacity": capacity,
                "planned": planned_quantity,
                "remaining": remaining,
                "utilization": utilization,
                "status": status,
            }
        )

    return render(
        request,
        "planning/dashboard.html",
        {
            "total_batches": total_batches,
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "sticking_plans": sticking_plans,
            "greenhouse_status": greenhouse_status,
        }
    )

def revalidate_batch(request, batch_id):

    batch = get_object_or_404(
        ImportBatch,
        id=batch_id
    )

    rows = (
        ImportedStickingPlanRow.objects.filter(
            import_batch=batch
        )
    )

    valid_rows = 0
    invalid_rows = 0

    for row in rows:

        row.validate_row()

        if row.validation_status == "VALID":
            valid_rows += 1
        else:
            invalid_rows += 1

    batch.status = "VALIDATED"
    batch.save()

    return render(
        request,
        "planning/revalidate_batch.html",
        {
            "batch": batch,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
        }
    )
def batch_detail(request, batch_id):

    batch = get_object_or_404(
        ImportBatch,
        id=batch_id
    )

    rows = (
        ImportedStickingPlanRow.objects.filter(
            import_batch=batch
        )
        .order_by("row_number")
    )

    valid_rows = rows.filter(
        validation_status="VALID"
    ).count()

    invalid_rows = rows.filter(
        validation_status="INVALID"
    ).count()

    return render(
        request,
        "planning/batch_detail.html",
        {
            "batch": batch,
            "rows": rows,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
        }
    )
def greenhouse_recommendations(request):

    recommendations = []

    for greenhouse in Greenhouse.objects.all():

        planned_quantity = (
            StickingPlanLine.objects.filter(
                greenhouse=greenhouse
            )
            .aggregate(
                total=models.Sum(
                    "planned_quantity"
                )
            )["total"]
            or 0
        )

        remaining_capacity = (
            greenhouse.total_capacity
            - planned_quantity
        )

        recommendations.append(
            {
                "greenhouse": greenhouse,
                "remaining_capacity": remaining_capacity,
                "planned_quantity": planned_quantity,
                "capacity": greenhouse.total_capacity,
            }
        )

    recommendations.sort(
        key=lambda x: x["remaining_capacity"],
        reverse=True
    )

    return render(
        request,
        "planning/recommendations.html",
        {
            "recommendations": recommendations
        }
    )
def variety_recommendations(request, variety_code):

    try:

        variety = Variety.objects.get(
            variety_code=variety_code
        )

    except Variety.DoesNotExist:

        return render(
            request,
            "planning/variety_recommendations.html",
            {
                "error": "Variety not found"
            }
        )

    recommendations = []

    for greenhouse in Greenhouse.objects.all():

        planned_quantity = (
            StickingPlanLine.objects.filter(
                greenhouse=greenhouse
            )
            .aggregate(
                total=models.Sum(
                    "planned_quantity"
                )
            )["total"]
            or 0
        )

        remaining_capacity = (
            greenhouse.total_capacity -
            planned_quantity
        )

        greenhouse_groups = set(
            StickingPlanLine.objects.filter(
                greenhouse=greenhouse
            )
            .values_list(
                "variety__growing_group__growing_group_code",
                flat=True
            )
        )

        compatibility = (
            variety.growing_group.growing_group_code
            in greenhouse_groups
        )

        recommendations.append(
            {
                "greenhouse": greenhouse,
                "capacity": greenhouse.total_capacity,
                "planned_quantity": planned_quantity,
                "remaining_capacity": remaining_capacity,
                "compatible": compatibility,
            }
        )

    recommendations.sort(
        key=lambda x: (
            x["compatible"],
            x["remaining_capacity"]
        ),
        reverse=True
    )

    return render(
        request,
        "planning/variety_recommendations.html",
        {
            "variety": variety,
            "recommendations": recommendations,
        }
    )
def allocation_proposal(request, variety_code):

    try:

        variety = Variety.objects.get(
            variety_code=variety_code
        )

    except Variety.DoesNotExist:

        return render(
            request,
            "planning/allocation_proposal.html",
            {
                "error": "Variety not found"
            }
        )

    candidates = []

    for greenhouse in Greenhouse.objects.all():

        planned_quantity = (
            StickingPlanLine.objects.filter(
                greenhouse=greenhouse
            )
            .aggregate(
                total=models.Sum(
                    "planned_quantity"
                )
            )["total"]
            or 0
        )

        remaining_capacity = (
            greenhouse.total_capacity -
            planned_quantity
        )

        greenhouse_groups = set(
            StickingPlanLine.objects.filter(
                greenhouse=greenhouse
            )
            .values_list(
                "variety__growing_group__growing_group_code",
                flat=True
            )
        )

        compatible = (
            variety.growing_group.growing_group_code
            in greenhouse_groups
        )

        candidates.append(
            {
                "greenhouse": greenhouse,
                "remaining_capacity": remaining_capacity,
                "compatible": compatible,
            }
        )

    candidates.sort(
        key=lambda x: (
            x["compatible"],
            x["remaining_capacity"]
        ),
        reverse=True
    )

    recommendation = None

    if candidates:
        recommendation = candidates[0]

    return render(
        request,
        "planning/allocation_proposal.html",
        {
            "variety": variety,
            "recommendation": recommendation,
        }
    )
def create_allocation_proposal(
    request,
    sticking_plan_line_id
):

    line = get_object_or_404(
        StickingPlanLine,
        id=sticking_plan_line_id
    )

    greenhouse = line.greenhouse

    proposal = AllocationProposal.objects.create(
        sticking_plan_line=line,
        greenhouse=greenhouse,
        proposed_capacity=line.planned_quantity,
    )

    return render(
        request,
        "planning/allocation_created.html",
        {
            "proposal": proposal
        }
    )
def accept_allocation(request, proposal_id):

    proposal = get_object_or_404(
        AllocationProposal,
        id=proposal_id
    )

    proposal.status = "ACCEPTED"
    proposal.save()

    proposal.sticking_plan_line.status = (
        "ALLOCATED"
    )

    proposal.sticking_plan_line.save()

    return render(
        request,
        "planning/allocation_accepted.html",
        {
            "proposal": proposal
        }
    )
def allocation_dashboard(request):

    proposals = (
        AllocationProposal.objects.all()
        .order_by("-created_at")
    )

    proposed_count = (
        AllocationProposal.objects.filter(
            status="PROPOSED"
        ).count()
    )

    accepted_count = (
        AllocationProposal.objects.filter(
            status="ACCEPTED"
        ).count()
    )

    rejected_count = (
        AllocationProposal.objects.filter(
            status="REJECTED"
        ).count()
    )

    total_allocated = (
        AllocationProposal.objects.filter(
            status="ACCEPTED"
        )
        .aggregate(
            total=models.Sum(
                "proposed_capacity"
            )
        )["total"]
        or 0
    )

    return render(
        request,
        "planning/allocation_dashboard.html",
        {
            "proposals": proposals,
            "proposed_count": proposed_count,
            "accepted_count": accepted_count,
            "rejected_count": rejected_count,
            "total_allocated": total_allocated,
        }
    )
from masterdata.models import GreenhouseBed


def create_bed_allocation(
    request,
    allocation_id
):

    allocation = get_object_or_404(
        AllocationProposal,
        id=allocation_id
    )

    bed = (
        GreenhouseBed.objects.filter(
            greenhouse=allocation.greenhouse
        )
        .first()
    )

    if not bed:

        return render(
            request,
            "planning/bed_allocation.html",
            {
                "error": (
                    "No beds found for "
                    f"{allocation.greenhouse.greenhouse_code}"
                )
            }
        )

    bed_allocation = (
        BedAllocation.objects.create(
            allocation=allocation,
            bed=bed,
            allocated_quantity=(
                allocation.proposed_capacity
            )
        )
    )

    return render(
        request,
        "planning/bed_allocation.html",
        {
            "bed_allocation": bed_allocation,
        }
    )