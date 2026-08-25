from django.urls import path

from producers import views

urlpatterns = [
    path('', views.dashboard, name='producer-dashboard'),
    path('profile/', views.profile_update, name='producer-profile'),
    path('products/new/', views.product_create, name='producer-product-create'),
    path('products/<int:pk>/edit/', views.product_update, name='producer-product-edit'),
    path('suborders/<int:pk>/transition/', views.transition_suborder, name='producer-suborder-transition'),
]
