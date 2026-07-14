from django.urls import path

from .views import (
    dashboard,
    upload_sticking_plan,
    validation_errors,
    approve_batch,
    batch_list,
    revalidate_batch,
    batch_detail,
    greenhouse_recommendations,
    variety_recommendations,
    allocation_proposal,
    create_allocation_proposal,
    accept_allocation,
    allocation_dashboard,
    create_bed_allocation,

)

urlpatterns = [

    path(
        "",
        dashboard,
        name="dashboard",
    ),

    path(
        "upload/",
        upload_sticking_plan,
        name="upload_sticking_plan",
    ),

    path(
        "validation-errors/",
        validation_errors,
        name="validation_errors",
    ),

    path(
        "approve/<int:batch_id>/",
        approve_batch,
        name="approve_batch",
    ),

    path(
        "revalidate/<int:batch_id>/",
        revalidate_batch,
        name="revalidate_batch",
    ),

    path(
        "batches/",
        batch_list,
        name="batch_list",
    ),
    path(
    "batch/<int:batch_id>/",
    batch_detail,
    name="batch_detail",
),
    path(
    "recommendations/",
    greenhouse_recommendations,
    name="greenhouse_recommendations",
),
path(
    "recommendations/<str:variety_code>/",
    variety_recommendations,
    name="variety_recommendations",
),
path(
    "allocation/<str:variety_code>/",
    allocation_proposal,
    name="allocation_proposal",
),
path(
    "allocation/create/<int:sticking_plan_line_id>/",
    create_allocation_proposal,
    name="create_allocation_proposal",
),
path(
    "allocation/accept/<int:proposal_id>/",
    accept_allocation,
    name="accept_allocation",
),
path(
    "allocations/",
    allocation_dashboard,
    name="allocation_dashboard",
),
path(
    "bed-allocation/create/<int:allocation_id>/",
    create_bed_allocation,
    name="create_bed_allocation",
),
]