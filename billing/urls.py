from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('billing/', views.billing_page, name='billing_page'),
    path('invoice/<int:purchase_id>/', views.invoice_page, name='invoice_page'),
    path('history/', views.bill_history, name='bill_history'),
]
