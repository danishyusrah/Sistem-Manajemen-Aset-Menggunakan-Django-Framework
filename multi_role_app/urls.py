from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect 
from django.urls import path
from accounts.views import dashboard_user, dashboard_admin
from accounts.views import (
    RegisterView, LoginView, dashboard_redirect,  # ✅ import redirect
     LogoutView
)

urlpatterns = [
    path('', lambda request: redirect('login', permanent=False)), 
    path('admin/', admin.site.urls),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('dashboard/', dashboard_redirect, name='dashboard_redirect'),  # ✅ ganti jadi redirect
    path('dashboard/user/', dashboard_user, name='dashboard_user'),
    path('dashboard/admin/', dashboard_admin, name='dashboard_admin'),
    path('assets/', include('assets.urls')),   


]
