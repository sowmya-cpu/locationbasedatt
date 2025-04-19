from django.urls import path
from main_auth import views

urlpatterns = [
    path('',                views.index,            name='index'),
    path('register/',       views.register,         name='register'),
    path('register',        views.register),                  # ← add this
    path('verify/',         views.verify,           name='verify'),
    path('verify',          views.verify),                    # ← add this too
    path('attendance/',     views.today_attendance, name='today_attendance'),
    path('admin-login/',    views.admin_login,      name='admin_login'),
]
