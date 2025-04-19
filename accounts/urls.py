from django.urls import path
from .views import (
    LoginView, RegisterView,
    dashboard_user, dashboard_admin,
    logout_view, dashboard_redirect  # ✅ tambahkan ini
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('dashboard/', dashboard_redirect, name='dashboard_redirect'),  # ✅ endpoint utama dashboard
    path('dashboard/user/', dashboard_user, name='dashboard_user'),
    path('dashboard/admin/', dashboard_admin, name='dashboard_admin'),
    path('logout/', logout_view, name='logout'),
]
