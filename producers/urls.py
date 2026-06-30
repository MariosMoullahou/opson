from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="producer_dashboard"),
    path("suborder/<int:pk>/transition/", views.transition_suborder, name="producer_transition_suborder"),
    path("products/new/", views.product_create, name="producer_product_create"),
]
