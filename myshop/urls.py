from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from store import views as store_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Store app
    path('', include('store.urls')),
]

# For serving media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


from django.conf.urls import handler404, handler500
from django.shortcuts import render

def custom_404(request, exception=None):
    return render(request, "404.html", status=404)

if settings.DEBUG:
    handler404 = custom_404
def custom_500(request):
    return render(request, "500.html", status=500)

handler500 = custom_500