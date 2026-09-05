from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path(
        "google13c44c25fab6e4bb.html",
        TemplateView.as_view(
            template_name="google13c44c25fab6e4bb.html",
        ),
        name="google_site_verification",
    ),
    path("admin/", admin.site.urls),
    path("", include("main.urls")),
]
