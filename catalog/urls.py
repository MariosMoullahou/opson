from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    path("producer/<str:slug>/", views.producer_detail, name="producer_detail"),
]
