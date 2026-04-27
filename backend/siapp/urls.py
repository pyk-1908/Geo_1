from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .api import api
from .base_views import uploaddb_view, uploadspendcube_view

urlpatterns = [
    path("uploaddb/", uploaddb_view, name="uploaddb"),
    path("uploadspendcube/", uploadspendcube_view, name="uploadspendcube"),
    path("api/", api.urls),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
