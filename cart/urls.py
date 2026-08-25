from django.urls import path

from cart import views

urlpatterns = [
    path('', views.cart_view, name='cart'),
    path('add/<int:product_id>/', views.cart_add, name='cart-add'),
    path('update/<int:product_id>/', views.cart_update, name='cart-update'),
    path('remove/<int:product_id>/', views.cart_remove, name='cart-remove'),
]
