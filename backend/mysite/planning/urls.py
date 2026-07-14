from django.urls import path

from .views import (
    upload_sticking_plan,
    validation_errors,
    approve_batch,
)

urlpatterns = [

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
]