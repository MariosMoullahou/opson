from django.urls import path

from catalog import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:pk>/', views.product_detail, name='product-detail'),
    path('producer/<int:pk>-<str:slug>/', views.producer_detail, name='producer-detail'),
]
