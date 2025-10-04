"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import json

def health_check(request):
    """Simple health check endpoint"""
    try:
        return JsonResponse({
            'message': 'StockSense Backend API is running',
            'timestamp': datetime.now().isoformat(),
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'message': f'Health check failed: {str(e)}',
            'service': 'StockSense Backend',
            'timestamp': datetime.now().isoformat()
        }, status=503)

urlpatterns = [
    path('', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/watchlists/', include('watchlists.urls')),
    path('api/stocks/', include('stocks.urls')),
]
