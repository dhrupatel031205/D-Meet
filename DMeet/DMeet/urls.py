"""
URL configuration for DMeet project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Core app URLs (events, home, etc.)
    path('', include('core.urls')),
    
    # Authentication and user management
    path('accounts/', include('accounts.urls')),
    
    # Video meetings
    path('meetings/', include('meetings.urls')),
    
    # Notifications
    path('notifications/', include('notifications.urls')),
    
    # Dashboards
    path('dashboard/', include('dashboard.urls')),
    
    # API endpoints
    path('api/', include('core.api_urls')),
    path('api/accounts/', include('accounts.api_urls')),
    path('api/meetings/', include('meetings.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin customization
admin.site.site_header = 'DMeeet Administration'
admin.site.site_title = 'DMeeet Admin'
admin.site.index_title = 'Welcome to DMeeet Administration'
