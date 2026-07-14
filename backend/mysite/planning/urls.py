from django.urls import path

from .views import (
    upload_sticking_plan,
)

urlpatterns = [

    path(
        "upload/",
        upload_sticking_plan,
        name="upload_sticking_plan",
    ),

]
