from django.urls import path

from orders import views

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('mine/', views.my_orders, name='my-orders'),
    path('<int:pk>/', views.order_detail, name='order-detail'),
]
