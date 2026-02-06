from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Agregamos esto para activar login, logout, reset password, etc.
    path('accounts/', include('django.contrib.auth.urls')), 
    path('', include('dashboard.urls')),
]