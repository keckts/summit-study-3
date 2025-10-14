from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('myapp.urls')),
    path('progress', include('progress.urls')),
    path('service/', include('service.urls')),
    path('extras/', include('extras.urls')),
    path("select2/", include("django_select2.urls")),
    path('accounts/', include('accounts.urls'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)