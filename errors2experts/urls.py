from django.contrib import admin
from django.conf import settings
from django.urls import include, path
from django.views.generic import TemplateView
from django.conf.urls.static import static

urlpatterns = [
    path(
        "google13c44c25fab6e4bb.html",
        TemplateView.as_view(
            template_name="google13c44c25fab6e4bb.html",
        ),
        name="google_site_verification",
    ),
    path("admin/", admin.site.urls),
    path("workshop/", include(("workshops.urls", "workshops"), namespace="workshops")),
    path("", include("main.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
