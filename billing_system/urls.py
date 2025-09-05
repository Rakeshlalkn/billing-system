# billing_system/urls.py
from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # auth
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', accounts_views.signup, name='signup'),

    # billing app
    path('', include('billing.urls')),
]
