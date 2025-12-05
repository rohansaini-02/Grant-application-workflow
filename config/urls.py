"""
URL configuration for Grant Application Workflow project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # App URLs
    path('', RedirectView.as_view(url='/dashboard/login/', permanent=False), name='home'),
    path('dashboard/', include('apps.users.urls')),
    path('calls/', include('apps.applications.call_urls')),
    path('applications/', include('apps.applications.urls')),
    path('reviews/', include('apps.reviews.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('reports/', include('apps.reports.urls')),
    
    # API URLs
    path('api/', include('apps.applications.api_urls')),
    path('api/', include('apps.reviews.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "Grant Application Workflow Admin"
admin.site.site_title = "Grant Workflow Admin"
admin.site.index_title = "Welcome to Grant Application Workflow Administration"
