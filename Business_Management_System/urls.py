
from django.contrib import admin
from django.urls import path , include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_application.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

from django.conf.urls import handler400, handler403, handler404, handler500

handler400 = 'main_application.views.error_400_view'
handler403 = 'main_application.views.error_403_view'
handler404 = 'main_application.views.error_404_view'
handler500 = 'main_application.views.error_500_view'

# This allows media files to be served even when DEBUG = False (for dev/testing)
if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]


    
